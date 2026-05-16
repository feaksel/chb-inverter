#include "pwm_modulator.h"
#include "stm32f3xx.h"
#include <math.h>
#include <string.h>

#define PI_F 3.14159265358979323846f

#define SINE_SAMPLES 256u
#define TIMER_CLK_HZ 64000000u
#define BOOTSTRAP_PRECHARGE_MS 6u
#define PWM_PRESCALER 0u
#define TIM_DTG_2US_AT_64MHZ 0x80u

/* Dead-time matches the bench-validated OLD PWM (2 us). Build guide v3.1
 * suggests 500 ns-1 us but the conservative 2 us was tested with the actual
 * TLP250 + IRFZ44N propagation on this hardware. Change with caution. */
#define PWM_DEAD_TIME_DTG TIM_DTG_2US_AT_64MHZ

/* STAIR thresholds + duty clamps — preserved verbatim from the OLD PWM in
 * main.c. The 0.95 high clamp was added in the pre-bringup fixes to comply
 * with build guide v3.1 section 7.4 (95% max HS duty for bootstrap refresh). */
#define FIVE_LEVEL_T1         0.2f
#define FIVE_LEVEL_T2         0.6f
#define STAIR_DUTY_LOW_CLAMP  0.01f
#define STAIR_DUTY_HIGH_CLAMP 0.95f

/* PSC active-duty window is symmetric around 50% because both legs are
 * continuously modulated. Inactive bridge uses NEUTRAL = ~freewheel for
 * minimum switching loss in single-bridge test mode. */
#define PSC_DUTY_LOW     0.05f
#define PSC_DUTY_HIGH    0.95f
#define PSC_DUTY_NEUTRAL 0.01f

static float sine_lut[SINE_SAMPLES];
static volatile float g_phase_accumulator = 0.0f;

volatile uint32_t g_pwm_period = 0u;
volatile uint32_t g_precharge_ticks_max = 0u;
volatile float    g_phase_increment = 0.0f;
volatile modulator_type_t g_pwm_modulator = PWM_DEFAULT_MODULATOR;
volatile bridge_select_t  g_pwm_bridge_select = PWM_DEFAULT_BRIDGE_SELECT;

/* Shared with the FSM (which arms/disarms precharge and reads back the level).
 * These were previously defined in main.c; consolidated here as the canonical
 * home of all PWM-related state. */
volatile uint32_t g_precharge_ticks = 0u;
volatile uint8_t  g_precharge_done = 0u;
volatile uint8_t  g_pwm_precharge_armed = 0u;
volatile int8_t   g_pwm_last_level = 0;
volatile float    g_pwm_modulation_index = PWM_DEFAULT_MI;

static pwm_config_t g_cfg;

static float clamp_f(float v, float lo, float hi)
{
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

static int8_t quantize_5level(float ref)
{
    if (ref >= FIVE_LEVEL_T2)  return 2;
    if (ref >= FIVE_LEVEL_T1)  return 1;
    if (ref <= -FIVE_LEVEL_T2) return -2;
    if (ref <= -FIVE_LEVEL_T1) return -1;
    return 0;
}

static void stair_bridge_level_to_duty(int8_t level, float *duty_a, float *duty_b)
{
    if (level > 0) {
        *duty_a = STAIR_DUTY_HIGH_CLAMP;
        *duty_b = STAIR_DUTY_LOW_CLAMP;
        return;
    }
    if (level < 0) {
        *duty_a = STAIR_DUTY_LOW_CLAMP;
        *duty_b = STAIR_DUTY_HIGH_CLAMP;
        return;
    }
    *duty_a = STAIR_DUTY_LOW_CLAMP;
    *duty_b = STAIR_DUTY_LOW_CLAMP;
}

static void generate_sine_lut(void)
{
    for (uint32_t i = 0; i < SINE_SAMPLES; i++) {
        sine_lut[i] = sinf(2.0f * PI_F * (float)i / (float)SINE_SAMPLES);
    }
}

static uint32_t compute_period(uint32_t fsw_hz)
{
    return (TIMER_CLK_HZ / (fsw_hz * 2u)) - 1u;
}

static uint32_t compute_precharge_ticks(uint32_t fsw_hz)
{
    return (uint32_t)((((uint64_t)BOOTSTRAP_PRECHARGE_MS) * fsw_hz + 999u) / 1000u);
}

static float compute_phase_increment(float ffund_hz, uint32_t fsw_hz)
{
    return (ffund_hz / (float)fsw_hz) * (float)SINE_SAMPLES;
}

static void timer_base_config(TIM_TypeDef *t)
{
    t->CR1 = 0u;
    t->CR2 = 0u;
    t->SMCR = 0u;
    t->DIER = 0u;
    t->CCMR1 = 0u;
    t->CCER = 0u;
    t->BDTR = 0u;

    t->PSC = PWM_PRESCALER;
    t->ARR = g_pwm_period;
    t->RCR = 1u;
    t->CCR1 = g_pwm_period / 2u;
    t->CCR2 = g_pwm_period / 2u;

    t->CR1 |= TIM_CR1_ARPE | TIM_CR1_CMS_0 | TIM_CR1_URS;

    t->CCMR1 |= TIM_CCMR1_OC1M_2 | TIM_CCMR1_OC1M_1;
    t->CCMR1 |= TIM_CCMR1_OC2M_2 | TIM_CCMR1_OC2M_1;
    t->CCMR1 |= TIM_CCMR1_OC1PE | TIM_CCMR1_OC2PE;

    t->CCER = TIM_CCER_CC1E | TIM_CCER_CC1NE |
              TIM_CCER_CC2E | TIM_CCER_CC2NE;

    t->BDTR = (PWM_DEAD_TIME_DTG << TIM_BDTR_DTG_Pos) | TIM_BDTR_OSSR | TIM_BDTR_OSSI;
}

/* Last measured carrier offset between TIM1 and TIM8 in counter ticks, as
 * seen at the end of timer_apply_period_and_phase. For PSC mode the target
 * is g_pwm_period/2; for STAIR/STAIR_ALT the target is 0. Exposed for the
 * $C diagnostic line and for HARDWARE_BRINGUP Phase 8 verification. */
volatile uint32_t g_pwm_measured_cnt_offset = 0u;
volatile uint8_t  g_pwm_phase_locked = 0u;

static void timer_apply_period_and_phase(void)
{
    /* MOE is the caller's responsibility (FSM enforces IDLE before reconfig).
     * Sequence: stop counters, write ARR + recenter CCRs, force UG to load
     * shadow regs and reset CNT, restart counters, then preset TIM8 CNT for
     * PSC's 90 deg carrier phase shift. The CNT write is performed AFTER
     * CR1_CEN is set so the timer doesn't immediately reset it through
     * another UG sequence; in center-aligned modes CNT can be written at
     * any time and takes effect on the next clock edge. */
    TIM1->CR1 &= ~TIM_CR1_CEN;
    TIM8->CR1 &= ~TIM_CR1_CEN;

    TIM1->ARR = g_pwm_period;
    TIM8->ARR = g_pwm_period;
    TIM1->CCR1 = g_pwm_period / 2u;
    TIM1->CCR2 = g_pwm_period / 2u;
    TIM8->CCR1 = g_pwm_period / 2u;
    TIM8->CCR2 = g_pwm_period / 2u;

    TIM1->CNT = 0u;
    TIM8->CNT = 0u;

    TIM1->EGR = TIM_EGR_UG;
    TIM8->EGR = TIM_EGR_UG;
    TIM1->SR = 0u;
    TIM8->SR = 0u;

    /* Enable both counters as close to atomically as possible. With both
     * timers on APB2 (64 MHz) and back-to-back register writes (~2 cycles
     * each), the start skew is < 50 ns -- negligible at 5 kHz. */
    TIM1->CR1 |= TIM_CR1_CEN;
    TIM8->CR1 |= TIM_CR1_CEN;

    /* For PSC the carriers must be 180 deg / N = 90 deg apart for N=2 cells,
     * which is PWM_PERIOD/2 ticks (a quarter of the full 2*PWM_PERIOD center-
     * aligned cycle). Writing TIM8->CNT post-CEN ensures the UG sequence
     * above cannot clobber it. STAIR / STAIR_ALT keep carriers in phase. */
    if (g_pwm_modulator == MODULATOR_PSC) {
        TIM8->CNT = g_pwm_period / 2u;
    }

    /* Verify the actual offset shortly after the preset. Read both counters
     * with IRQs disabled so the value isn't perturbed by a TIM1 update IRQ
     * landing between the two reads. Both timers tick at the same rate so
     * the offset is constant once locked. */
    uint32_t cnt1;
    uint32_t cnt8;
    __disable_irq();
    cnt1 = TIM1->CNT;
    cnt8 = TIM8->CNT;
    __enable_irq();

    int32_t offset = (int32_t)cnt8 - (int32_t)cnt1;
    if (offset < 0) {
        offset += (int32_t)(g_pwm_period + 1u);
    }
    g_pwm_measured_cnt_offset = (uint32_t)offset;

    uint32_t expected = (g_pwm_modulator == MODULATOR_PSC) ? (g_pwm_period / 2u) : 0u;
    uint32_t tolerance = (g_pwm_period / 20u) + 4u;   /* 5% of period + a few-cycle slack */
    uint32_t err = (offset > (int32_t)expected) ?
                       (uint32_t)offset - expected :
                       expected - (uint32_t)offset;
    g_pwm_phase_locked = (err <= tolerance) ? 1u : 0u;
}

void Pwm_Init(void)
{
    g_cfg.modulator           = PWM_DEFAULT_MODULATOR;
    g_cfg.switching_freq_hz   = PWM_DEFAULT_SWITCHING_HZ;
    g_cfg.bridge_select       = PWM_DEFAULT_BRIDGE_SELECT;
    g_cfg.modulation_index    = PWM_DEFAULT_MI;
    g_cfg.fundamental_freq_hz = PWM_DEFAULT_FUNDAMENTAL_HZ;

    g_pwm_modulator        = g_cfg.modulator;
    g_pwm_bridge_select    = g_cfg.bridge_select;
    g_pwm_modulation_index = g_cfg.modulation_index;
    g_pwm_period           = compute_period(g_cfg.switching_freq_hz);
    g_precharge_ticks_max  = compute_precharge_ticks(g_cfg.switching_freq_hz);
    g_phase_increment      = compute_phase_increment(g_cfg.fundamental_freq_hz, g_cfg.switching_freq_hz);
    g_phase_accumulator    = 0.0f;

    generate_sine_lut();

    RCC->APB2ENR |= RCC_APB2ENR_TIM1EN | RCC_APB2ENR_TIM8EN;

    timer_base_config(TIM1);
    timer_base_config(TIM8);

    /* Only TIM1 fires the update IRQ; the ISR writes both timers' CCRs. */
    TIM1->DIER = TIM_DIER_UIE;

    TIM1->CR1 |= TIM_CR1_CEN;
    TIM8->CR1 |= TIM_CR1_CEN;
}

uint8_t Pwm_SetConfig(const pwm_config_t *cfg)
{
    if (cfg == (const pwm_config_t *)0) {
        return 0u;
    }
    if ((cfg->modulator != MODULATOR_STAIR) &&
        (cfg->modulator != MODULATOR_PSC) &&
        (cfg->modulator != MODULATOR_STAIR_ALT)) {
        return 0u;
    }
    if ((cfg->bridge_select != BRIDGE_BOTH) &&
        (cfg->bridge_select != BRIDGE_B1_ONLY) &&
        (cfg->bridge_select != BRIDGE_B2_ONLY)) {
        return 0u;
    }
    if ((cfg->switching_freq_hz < PWM_FSW_MIN_HZ) || (cfg->switching_freq_hz > PWM_FSW_MAX_HZ)) {
        return 0u;
    }
    if ((cfg->fundamental_freq_hz < PWM_FUNDAMENTAL_MIN_HZ) ||
        (cfg->fundamental_freq_hz > PWM_FUNDAMENTAL_MAX_HZ)) {
        return 0u;
    }
    if ((cfg->modulation_index < 0.0f) || (cfg->modulation_index > 0.95f)) {
        return 0u;
    }

    /* Reset shared precharge state so the next START re-runs the bootstrap
     * charge with the new switching period. */
    g_pwm_precharge_armed = 0u;
    g_precharge_done = 0u;
    g_precharge_ticks = 0u;

    g_cfg = *cfg;

    g_pwm_modulator        = g_cfg.modulator;
    g_pwm_bridge_select    = g_cfg.bridge_select;
    g_pwm_modulation_index = g_cfg.modulation_index;
    g_pwm_period           = compute_period(g_cfg.switching_freq_hz);
    g_precharge_ticks_max  = compute_precharge_ticks(g_cfg.switching_freq_hz);
    g_phase_increment      = compute_phase_increment(g_cfg.fundamental_freq_hz, g_cfg.switching_freq_hz);
    g_phase_accumulator    = 0.0f;

    timer_apply_period_and_phase();
    return 1u;
}

const pwm_config_t *Pwm_GetConfig(void)
{
    return &g_cfg;
}

void Pwm_SetModulationIndex(float mi)
{
    g_pwm_modulation_index = mi;
    g_cfg.modulation_index = mi;
}

uint8_t Pwm_HandlePrechargeStep(void)
{
    if (g_pwm_precharge_armed == 0u) {
        g_precharge_ticks = 0u;
        g_precharge_done = 0u;
        return 1u;
    }

    if (g_precharge_done != 0u) {
        return 0u;
    }

    /* Bootstrap precharge: identical sequence to the OLD bench-validated PWM.
     * Both bridges' low-sides on, both high-sides off, for ~6 ms. */
    TIM1->CCER &= ~(TIM_CCER_CC1E | TIM_CCER_CC2E);
    TIM1->CCER |= (TIM_CCER_CC1NE | TIM_CCER_CC2NE);
    TIM8->CCER &= ~(TIM_CCER_CC1E | TIM_CCER_CC2E);
    TIM8->CCER |= (TIM_CCER_CC1NE | TIM_CCER_CC2NE);

    TIM1->CCR1 = 0u;
    TIM1->CCR2 = 0u;
    TIM8->CCR1 = 0u;
    TIM8->CCR2 = 0u;

    g_precharge_ticks++;
    if (g_precharge_ticks < g_precharge_ticks_max) {
        return 1u;
    }

    TIM1->CCER |= (TIM_CCER_CC1E | TIM_CCER_CC2E);
    TIM8->CCER |= (TIM_CCER_CC1E | TIM_CCER_CC2E);
    g_precharge_done = 1u;
    return 0u;
}

static void stair_emit(int8_t bridge1, int8_t bridge2)
{
    /* Single-bridge test mode: force the inactive bridge to level 0 so it
     * contributes ~0 V to the cascaded output. The active bridge still
     * produces its full 3-level swing. */
    if (g_pwm_bridge_select == BRIDGE_B1_ONLY) {
        bridge2 = 0;
    } else if (g_pwm_bridge_select == BRIDGE_B2_ONLY) {
        bridge1 = 0;
    }

    float d1a = STAIR_DUTY_LOW_CLAMP, d1b = STAIR_DUTY_LOW_CLAMP;
    float d2a = STAIR_DUTY_LOW_CLAMP, d2b = STAIR_DUTY_LOW_CLAMP;
    stair_bridge_level_to_duty(bridge1, &d1a, &d1b);
    stair_bridge_level_to_duty(bridge2, &d2a, &d2b);

    uint32_t period = g_pwm_period;
    TIM1->CCR1 = (uint32_t)(d1a * (float)period);
    TIM1->CCR2 = (uint32_t)(d1b * (float)period);
    TIM8->CCR1 = (uint32_t)(d2a * (float)period);
    TIM8->CCR2 = (uint32_t)(d2b * (float)period);
}

static void stair_modulate(float ref)
{
    int8_t level = quantize_5level(ref);
    g_pwm_last_level = level;

    int8_t bridge1 = 0;
    int8_t bridge2 = 0;

    if (level >= 2) {
        bridge1 = 1;  bridge2 = 1;
    } else if (level == 1) {
        bridge1 = 1;  bridge2 = 0;
    } else if (level == 0) {
        bridge1 = 0;  bridge2 = 0;
    } else if (level == -1) {
        bridge1 = -1; bridge2 = 0;
    } else {
        bridge1 = -1; bridge2 = -1;
    }

    stair_emit(bridge1, bridge2);
}

/* STAIR_ALT: same output waveform as STAIR, but the bridge that carries the
 * +/-1 step alternates every time we re-enter the +/-1 level. Bridges +/-2
 * are unchanged (both bridges contribute, by definition). Effect: averaged
 * over ~2 fundamental cycles each bridge handles +/-1 equally often, fixing
 * the OLD STAIR thermal imbalance without changing the output shape.
 *
 * Limitation: this is still NOT real PWM (levels held statically). Output is
 * a 500 Hz staircase, not a 5 kHz PWM waveform. Use this only if PSC is
 * proven non-viable on the bench. PSC is what the project actually wants. */
static int8_t  g_alt_prev_level = 0;
static uint8_t g_alt_use_bridge2 = 0u;

static void stair_alt_modulate(float ref)
{
    int8_t level = quantize_5level(ref);
    g_pwm_last_level = level;

    /* Toggle ownership each time we (re-)enter a +/-1 step. */
    if ((level != g_alt_prev_level) && ((level == 1) || (level == -1))) {
        g_alt_use_bridge2 = (uint8_t)!g_alt_use_bridge2;
    }
    g_alt_prev_level = level;

    int8_t bridge1 = 0;
    int8_t bridge2 = 0;

    if (level >= 2) {
        bridge1 = 1;  bridge2 = 1;
    } else if (level == 1) {
        if (g_alt_use_bridge2) { bridge1 = 0; bridge2 = 1; }
        else                   { bridge1 = 1; bridge2 = 0; }
    } else if (level == 0) {
        bridge1 = 0;  bridge2 = 0;
    } else if (level == -1) {
        if (g_alt_use_bridge2) { bridge1 = 0;  bridge2 = -1; }
        else                   { bridge1 = -1; bridge2 = 0;  }
    } else {
        bridge1 = -1; bridge2 = -1;
    }

    stair_emit(bridge1, bridge2);
}

static void psc_modulate(float ref)
{
    /* Coarse 5-level indicator for the $T telemetry <level> field so the
     * dashboard interprets both modulators consistently. */
    if (ref >= 0.6f)       g_pwm_last_level = 2;
    else if (ref >= 0.2f)  g_pwm_last_level = 1;
    else if (ref <= -0.6f) g_pwm_last_level = -2;
    else if (ref <= -0.2f) g_pwm_last_level = -1;
    else                   g_pwm_last_level = 0;

    /* Unipolar SPWM per H-bridge: leg_a gets +ref, leg_b gets -ref, both
     * compared to the same triangle (the timer's center-aligned counter).
     * TIM8 CNT was preset to PWM_PERIOD/2 at config time, so the two bridges'
     * carriers are 90 deg apart and the cascaded output naturally has 5
     * levels without any quantization in software. */
    float duty_a = clamp_f(0.5f + 0.5f * ref, PSC_DUTY_LOW, PSC_DUTY_HIGH);
    float duty_b = clamp_f(0.5f - 0.5f * ref, PSC_DUTY_LOW, PSC_DUTY_HIGH);

    float d1a = duty_a, d1b = duty_b;
    float d2a = duty_a, d2b = duty_b;

    if (g_pwm_bridge_select == BRIDGE_B1_ONLY) {
        d2a = PSC_DUTY_NEUTRAL;
        d2b = PSC_DUTY_NEUTRAL;
    } else if (g_pwm_bridge_select == BRIDGE_B2_ONLY) {
        d1a = PSC_DUTY_NEUTRAL;
        d1b = PSC_DUTY_NEUTRAL;
    }

    uint32_t period = g_pwm_period;
    TIM1->CCR1 = (uint32_t)(d1a * (float)period);
    TIM1->CCR2 = (uint32_t)(d1b * (float)period);
    TIM8->CCR1 = (uint32_t)(d2a * (float)period);
    TIM8->CCR2 = (uint32_t)(d2b * (float)period);
}

void Pwm_PscIsrBody(void)
{
    /* Retained for the public header; the unified handler is preferred. */
    if (Pwm_HandlePrechargeStep() != 0u) {
        return;
    }

    g_phase_accumulator += g_phase_increment;
    if (g_phase_accumulator >= (float)SINE_SAMPLES) {
        g_phase_accumulator -= (float)SINE_SAMPLES;
    }

    uint32_t sine_index = (uint32_t)g_phase_accumulator;
    float ref = clamp_f(g_pwm_modulation_index * sine_lut[sine_index], -1.0f, 1.0f);
    psc_modulate(ref);
}

void Pwm_TIM1_UpdateHandler(void)
{
    if ((TIM1->SR & TIM_SR_UIF) == 0u) {
        return;
    }
    TIM1->SR &= ~TIM_SR_UIF;

    /* Sine accumulator advances every ISR regardless of precharge so the
     * fundamental stays aligned with wall-clock time. Matches the OLD
     * bench-validated ISR ordering. */
    g_phase_accumulator += g_phase_increment;
    if (g_phase_accumulator >= (float)SINE_SAMPLES) {
        g_phase_accumulator -= (float)SINE_SAMPLES;
    }

    uint32_t sine_index = (uint32_t)g_phase_accumulator;
    float sine_value = g_pwm_modulation_index * sine_lut[sine_index];

    if (Pwm_HandlePrechargeStep() != 0u) {
        return;
    }

    float ref = clamp_f(sine_value, -1.0f, 1.0f);

    if (g_pwm_modulator == MODULATOR_PSC) {
        psc_modulate(ref);
    } else if (g_pwm_modulator == MODULATOR_STAIR_ALT) {
        stair_alt_modulate(ref);
    } else {
        stair_modulate(ref);
    }
}

uint8_t Pwm_ParseModulator(const char *text, modulator_type_t *out)
{
    if ((text == (const char *)0) || (out == (modulator_type_t *)0)) {
        return 0u;
    }
    if (strcmp(text, "STAIR") == 0)     { *out = MODULATOR_STAIR;     return 1u; }
    if (strcmp(text, "PSC") == 0)       { *out = MODULATOR_PSC;       return 1u; }
    if (strcmp(text, "STAIR_ALT") == 0) { *out = MODULATOR_STAIR_ALT; return 1u; }
    return 0u;
}

uint8_t Pwm_ParseBridgeSelect(const char *text, bridge_select_t *out)
{
    if ((text == (const char *)0) || (out == (bridge_select_t *)0)) {
        return 0u;
    }
    if (strcmp(text, "BOTH") == 0) { *out = BRIDGE_BOTH;    return 1u; }
    if (strcmp(text, "B1") == 0)   { *out = BRIDGE_B1_ONLY; return 1u; }
    if (strcmp(text, "B2") == 0)   { *out = BRIDGE_B2_ONLY; return 1u; }
    return 0u;
}

const char *Pwm_ModulatorName(modulator_type_t m)
{
    if (m == MODULATOR_PSC)       return "PSC";
    if (m == MODULATOR_STAIR_ALT) return "STAIR_ALT";
    return "STAIR";
}

const char *Pwm_BridgeName(bridge_select_t b)
{
    if (b == BRIDGE_B1_ONLY) return "B1";
    if (b == BRIDGE_B2_ONLY) return "B2";
    return "BOTH";
}
