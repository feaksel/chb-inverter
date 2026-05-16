#ifndef PWM_MODULATOR_H
#define PWM_MODULATOR_H

#include "pwm_config.h"
#include <stdint.h>

/* Shared timer parameters derived from the runtime config. The ISR in main.c
 * reads g_pwm_period and g_phase_increment every period; FSM/UART handlers
 * update them via Pwm_SetConfig. All volatile for ISR/main coherence. */
extern volatile uint32_t g_pwm_period;
extern volatile uint32_t g_precharge_ticks_max;
extern volatile float    g_phase_increment;
extern volatile modulator_type_t g_pwm_modulator;
extern volatile bridge_select_t  g_pwm_bridge_select;

/* One-time init at boot. Loads defaults from pwm_config.h, configures TIM1
 * and TIM8 with the default switching frequency, leaves MOE=0 so outputs are
 * disabled until the FSM enables them in PRECHARGE. */
void Pwm_Init(void);

/* Apply a new config at runtime. Caller must ensure the FSM is in IDLE
 * (i.e. MOE is already off). Recomputes period, phase increment, precharge
 * ticks; reconfigures TIM1/TIM8 ARR; presets TIM8->CNT for the 90 deg phase
 * shift when MODULATOR_PSC is selected. Returns 1 on success, 0 if the new
 * config is out of range (caller should keep current state and emit error). */
uint8_t Pwm_SetConfig(const pwm_config_t *cfg);

/* Read-only snapshot of current config. */
const pwm_config_t *Pwm_GetConfig(void);

/* Lightweight setter for modulation index only — does not reconfigure timers.
 * Keeps the cached config struct in sync with g_pwm_modulation_index so
 * CONFIG queries return the live value. Caller must validate range (0..0.95). */
void Pwm_SetModulationIndex(float mi);

/* TIM1 update ISR entry point. Called from TIM1_UP_TIM16_IRQHandler in
 * stm32f3xx_it.c. Owns the dispatch between STAIR and PSC modulators, the
 * sine accumulator advance, and the precharge state machine. */
void Pwm_TIM1_UpdateHandler(void);

/* Internals re-exposed for legacy / debugging use. Normal callers should use
 * Pwm_TIM1_UpdateHandler. */
void Pwm_PscIsrBody(void);
uint8_t Pwm_HandlePrechargeStep(void);

/* Resolve UART-supplied modulator/bridge keywords. Returns 1 on match
 * (and writes *out), 0 if the keyword is unknown. */
uint8_t Pwm_ParseModulator(const char *text, modulator_type_t *out);
uint8_t Pwm_ParseBridgeSelect(const char *text, bridge_select_t *out);
const char *Pwm_ModulatorName(modulator_type_t m);
const char *Pwm_BridgeName(bridge_select_t b);

#endif /* PWM_MODULATOR_H */
