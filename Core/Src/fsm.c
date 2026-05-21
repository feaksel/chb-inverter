#include "fsm.h"
#include "protection.h"
#include "pwm_config.h"
#include "pwm_modulator.h"
#include "sensing.h"
#include "uart_telem.h"

extern volatile uint8_t g_precharge_done;
extern volatile uint32_t g_precharge_ticks;
extern volatile uint8_t g_pwm_precharge_armed;
extern volatile int8_t g_pwm_last_level;
extern volatile float g_pwm_modulation_index;

static volatile uint32_t g_ms_ticks = 0u;
static fsm_state_t g_state = FSM_STATE_BOOT;
static sensing_mode_t g_mode = MODE_OPEN_LOOP;
static uint32_t g_last_telem_ms = 0u;
static uint32_t g_boot_ms = 0u;
static uint8_t  g_auto_start_done = 0u;

static void pwm_disable_and_reset_precharge(void)
{
    TIM1->BDTR &= ~TIM_BDTR_MOE;
    TIM8->BDTR &= ~TIM_BDTR_MOE;
    g_pwm_precharge_armed = 0u;
    g_precharge_ticks = 0u;
    g_precharge_done = 0u;
}

static void pwm_enable_for_precharge(void)
{
    g_precharge_ticks = 0u;
    g_precharge_done = 0u;
    g_pwm_precharge_armed = 1u;
    TIM1->BDTR |= TIM_BDTR_MOE;
    TIM8->BDTR |= TIM_BDTR_MOE;
}

static sensing_mode_t select_best_mode(void)
{
    uint8_t available = Sensing_GetAvailableMask();

    if ((available & SENSOR_MASK_ALL) == SENSOR_MASK_ALL) {
        return MODE_FULL;
    }
    if ((available & (SENSOR_MASK_DC1 | SENSOR_MASK_DC2)) == (SENSOR_MASK_DC1 | SENSOR_MASK_DC2)) {
        return MODE_DC_ONLY;
    }
    if ((available & (SENSOR_MASK_DC1 | SENSOR_MASK_CUR)) == (SENSOR_MASK_DC1 | SENSOR_MASK_CUR)) {
        return MODE_DC1_ONLY;
    }
    if ((available & (SENSOR_MASK_DC2 | SENSOR_MASK_CUR)) == (SENSOR_MASK_DC2 | SENSOR_MASK_CUR)) {
        return MODE_DC2_ONLY;
    }
    if ((available & SENSOR_MASK_CUR) != 0u) {
        return MODE_CURRENT_ONLY;
    }
    if ((available & SENSOR_MASK_DC1) != 0u) {
        return MODE_DC1_ONLY;
    }
    if ((available & SENSOR_MASK_DC2) != 0u) {
        return MODE_DC2_ONLY;
    }
    return MODE_OPEN_LOOP;
}

static void warn_if_open_loop(void)
{
    if (g_mode == MODE_OPEN_LOOP) {
        UART_SendError("WARNING_OPEN_LOOP_NO_PROTECTION");
    }
}

/* FAULT_OUT hardware pin (build guide header pin 16), active-low:
 * LOW = a fault is latched, HIGH = no fault. The pin is configured as a
 * push-pull output and driven HIGH in main.c GPIO_Config before the FSM
 * starts. */
static void fault_out_drive(uint8_t fault_active)
{
    if (fault_active != 0u) {
        FAULT_OUT_PORT->BSRR = (uint32_t)1u << (FAULT_OUT_PIN + 16u);  /* LOW */
    } else {
        FAULT_OUT_PORT->BSRR = (uint32_t)1u << FAULT_OUT_PIN;          /* HIGH */
    }
}

static void enter_idle(void)
{
    pwm_disable_and_reset_precharge();
    fault_out_drive(0u);
    g_state = FSM_STATE_IDLE;
}

static void enter_fault(uint8_t faults)
{
    pwm_disable_and_reset_precharge();
    Protection_Latch(faults);
    fault_out_drive(1u);
    g_state = FSM_STATE_FAULT;
    UART_SendFault(Protection_GetLatched());
}

static uint8_t active_faults_for_clear(void)
{
    uint8_t unavailable_required;

    unavailable_required = (uint8_t)(Sensing_ModeRequiredMask(g_mode) & ~Sensing_GetAvailableMask());
    if (unavailable_required != 0u) {
        return FAULT_SENSOR_LOST;
    }

    return Protection_Check(Sensing_GetData(), g_mode);
}

/* Common arm-and-go path used by both the UART START command and the
 * auto-start logic. Pass the original command text for the Ack, or NULL to
 * emit "$A,AUTO_START" instead. Returns 1 on success, 0 on rejection. */
static uint8_t do_start(const char *ack_text)
{
    if (g_state != FSM_STATE_IDLE) {
        UART_SendError("START_ALLOWED_ONLY_IN_IDLE");
        return 0u;
    }
    if (Sensing_ModeSensorsAvailable(g_mode) == 0u) {
        UART_SendError("MODE_SENSOR_UNAVAILABLE");
        return 0u;
    }

    if (ack_text != (const char *)0) {
        UART_SendAck(ack_text);
    } else {
        UART_WriteString("$A,AUTO_START\r\n");
    }
    warn_if_open_loop();
    Protection_ClearLatched();
    pwm_enable_for_precharge();
    g_state = FSM_STATE_PRECHARGE;
    return 1u;
}

static void handle_start(const uart_command_t *cmd)
{
    (void)do_start(cmd->raw);
}

static void handle_stop(const uart_command_t *cmd)
{
    if ((g_state != FSM_STATE_RUN) && (g_state != FSM_STATE_PRECHARGE)) {
        UART_SendError("STOP_ALLOWED_ONLY_WHILE_RUNNING");
        return;
    }

    UART_SendAck(cmd->raw);
    enter_idle();
}

static void handle_clear(const uart_command_t *cmd)
{
    uint8_t active;

    if (g_state != FSM_STATE_FAULT) {
        UART_SendError("CLEAR_ALLOWED_ONLY_IN_FAULT");
        return;
    }

    active = active_faults_for_clear();
    if (active != FAULT_NONE) {
        UART_SendError("FAULT_STILL_ACTIVE");
        UART_SendFault(active);
        return;
    }

    UART_SendAck(cmd->raw);
    Protection_ClearLatched();
    enter_idle();
}

static void handle_mode(const uart_command_t *cmd)
{
    sensing_mode_t requested;

    if ((g_state != FSM_STATE_IDLE) && (g_state != FSM_STATE_FAULT)) {
        UART_SendError("MODE_CHANGE_REQUIRES_STOP");
        return;
    }

    requested = (sensing_mode_t)cmd->mode_arg;
    if ((requested >= MODE_COUNT) || (Sensing_ModeSensorsAvailable(requested) == 0u)) {
        UART_SendError("MODE_SENSOR_UNAVAILABLE");
        return;
    }

    g_mode = requested;
    UART_SendAck(cmd->raw);
    warn_if_open_loop();
}

static void handle_mi(const uart_command_t *cmd)
{
    if (g_state != FSM_STATE_IDLE) {
        UART_SendError("MI_ALLOWED_ONLY_IN_IDLE");
        return;
    }
    if ((cmd->float_arg < 0.0f) || (cmd->float_arg > 0.95f)) {
        UART_SendError("MI_RANGE_0_TO_0_95");
        return;
    }

    Pwm_SetModulationIndex(cmd->float_arg);
    UART_SendAck(cmd->raw);
}

static void handle_rescan(const uart_command_t *cmd)
{
    if ((g_state != FSM_STATE_IDLE) && (g_state != FSM_STATE_FAULT)) {
        UART_SendError("RESCAN_REQUIRES_IDLE_OR_FAULT");
        return;
    }

    Sensing_SelfTest();
    UART_SendAck(cmd->raw);

    if (Sensing_ModeSensorsAvailable(g_mode) == 0u) {
        sensing_mode_t previous = g_mode;
        g_mode = select_best_mode();
        if (g_mode != previous) {
            UART_SendError("MODE_DEMOTED");
        }
    }
    warn_if_open_loop();
}

static void emit_pwm_config_line(void)
{
    const pwm_config_t *cfg = Pwm_GetConfig();
    UART_SendPwmConfig(Pwm_ModulatorName(cfg->modulator),
                       cfg->switching_freq_hz,
                       Pwm_BridgeName(cfg->bridge_select),
                       cfg->fundamental_freq_hz,
                       cfg->modulation_index,
                       g_pwm_measured_cnt_offset,
                       g_pwm_phase_locked);
}

static void emit_protection_config_line(void)
{
    UART_SendProtectionConfig(Protection_GetNominalVoltage(),
                              Protection_GetUndervoltage(),
                              Protection_GetOvervoltage(),
                              Protection_GetOvercurrent(),
                              Protection_GetImbalance());
}

static uint8_t require_idle_for_pwm_config(void)
{
    if (g_state != FSM_STATE_IDLE) {
        UART_SendError("PWM_CONFIG_REQUIRES_IDLE");
        return 0u;
    }
    return 1u;
}

static void handle_mod(const uart_command_t *cmd)
{
    if (!require_idle_for_pwm_config()) return;

    pwm_config_t cfg = *Pwm_GetConfig();
    cfg.modulator = (modulator_type_t)cmd->mode_arg;
    if (Pwm_SetConfig(&cfg) == 0u) {
        UART_SendError("PWM_CONFIG_REJECTED");
        return;
    }
    UART_SendAck(cmd->raw);
    emit_pwm_config_line();
}

static void handle_bridge(const uart_command_t *cmd)
{
    if (!require_idle_for_pwm_config()) return;

    pwm_config_t cfg = *Pwm_GetConfig();
    cfg.bridge_select = (bridge_select_t)cmd->mode_arg;
    if (Pwm_SetConfig(&cfg) == 0u) {
        UART_SendError("PWM_CONFIG_REJECTED");
        return;
    }
    UART_SendAck(cmd->raw);
    emit_pwm_config_line();
}

static void handle_fsw(const uart_command_t *cmd)
{
    if (!require_idle_for_pwm_config()) return;

    uint32_t hz = (uint32_t)cmd->float_arg;
    if ((hz < PWM_FSW_MIN_HZ) || (hz > PWM_FSW_MAX_HZ)) {
        UART_SendError("FSW_RANGE_100_TO_20000");
        return;
    }
    pwm_config_t cfg = *Pwm_GetConfig();
    cfg.switching_freq_hz = hz;
    if (Pwm_SetConfig(&cfg) == 0u) {
        UART_SendError("PWM_CONFIG_REJECTED");
        return;
    }
    UART_SendAck(cmd->raw);
    emit_pwm_config_line();
}

static void handle_ffund(const uart_command_t *cmd)
{
    if (!require_idle_for_pwm_config()) return;

    if ((cmd->float_arg < PWM_FUNDAMENTAL_MIN_HZ) ||
        (cmd->float_arg > PWM_FUNDAMENTAL_MAX_HZ)) {
        UART_SendError("FFUND_RANGE_10_TO_400");
        return;
    }
    pwm_config_t cfg = *Pwm_GetConfig();
    cfg.fundamental_freq_hz = cmd->float_arg;
    if (Pwm_SetConfig(&cfg) == 0u) {
        UART_SendError("PWM_CONFIG_REJECTED");
        return;
    }
    UART_SendAck(cmd->raw);
    emit_pwm_config_line();
}

/* Protection thresholds may be changed in IDLE or FAULT. FAULT is allowed so
 * that if the inverter tripped UV because the bus is at a low test voltage,
 * the operator can set VNOM appropriately and then CLEAR. */
static uint8_t require_idle_or_fault_for_protection(void)
{
    if ((g_state != FSM_STATE_IDLE) && (g_state != FSM_STATE_FAULT)) {
        UART_SendError("PROTECTION_CONFIG_REQUIRES_IDLE_OR_FAULT");
        return 0u;
    }
    return 1u;
}

static void handle_vnom(const uart_command_t *cmd)
{
    if (!require_idle_or_fault_for_protection()) return;

    if (Protection_SetNominalVoltage(cmd->float_arg) == 0u) {
        UART_SendError("VNOM_RANGE_5_TO_60");
        return;
    }
    UART_SendAck(cmd->raw);
    emit_protection_config_line();
}

static void handle_oc(const uart_command_t *cmd)
{
    if (!require_idle_or_fault_for_protection()) return;

    if (Protection_SetOvercurrent(cmd->float_arg) == 0u) {
        UART_SendError("OC_RANGE_0_5_TO_20");
        return;
    }
    UART_SendAck(cmd->raw);
    emit_protection_config_line();
}

static void handle_command(const uart_command_t *cmd)
{
    switch (cmd->type) {
    case UART_CMD_START:
        handle_start(cmd);
        break;
    case UART_CMD_STOP:
        handle_stop(cmd);
        break;
    case UART_CMD_CLEAR:
        handle_clear(cmd);
        break;
    case UART_CMD_MODE:
        handle_mode(cmd);
        break;
    case UART_CMD_STATUS:
        UART_SendAck(cmd->raw);
        UART_SendStatus(FSM_Millis(), g_state, g_mode, Protection_GetLatched(),
                        Sensing_GetData(), g_pwm_modulation_index);
        break;
    case UART_CMD_HELP:
        UART_SendAck(cmd->raw);
        UART_SendHelp();
        break;
    case UART_CMD_MI:
        handle_mi(cmd);
        break;
    case UART_CMD_RESCAN:
        handle_rescan(cmd);
        break;
    case UART_CMD_MOD:
        handle_mod(cmd);
        break;
    case UART_CMD_BRIDGE:
        handle_bridge(cmd);
        break;
    case UART_CMD_FSW:
        handle_fsw(cmd);
        break;
    case UART_CMD_FFUND:
        handle_ffund(cmd);
        break;
    case UART_CMD_VNOM:
        handle_vnom(cmd);
        break;
    case UART_CMD_OC:
        handle_oc(cmd);
        break;
    case UART_CMD_CONFIG:
        UART_SendAck(cmd->raw);
        emit_pwm_config_line();
        emit_protection_config_line();
        break;
    case UART_CMD_INVALID:
    default:
        UART_SendError("UNKNOWN_COMMAND");
        break;
    }
}

static void handle_sensing(uint32_t now)
{
    uint8_t lost = Sensing_Service(g_mode, now);

    if (lost != 0u) {
        if ((lost & Sensing_ModeRequiredMask(g_mode)) != 0u) {
            if ((g_state == FSM_STATE_PRECHARGE) || (g_state == FSM_STATE_RUN)) {
                enter_fault(FAULT_SENSOR_LOST);
            } else {
                UART_SendError("SENSOR_LOST_REQUIRED_FOR_MODE");
            }
        } else {
            UART_SendError("SENSOR_LOST_NOT_REQUIRED");
        }
    }

    if ((g_state == FSM_STATE_PRECHARGE) || (g_state == FSM_STATE_RUN)) {
        uint8_t faults = Protection_Check(Sensing_GetData(), g_mode);
        if (faults != FAULT_NONE) {
            enter_fault(faults);
        }
    }
}

void FSM_Init(void)
{
    g_state = FSM_STATE_BOOT;
    pwm_disable_and_reset_precharge();
    Protection_ClearLatched();
    Sensing_SelfTest();

    g_mode = select_best_mode();
    UART_WriteString("$A,BOOT_SELF_TEST_DONE\r\n");
    emit_pwm_config_line();
    emit_protection_config_line();
    if (g_mode != MODE_FULL) {
        UART_SendError("MODE_DEMOTED");
    }
    warn_if_open_loop();
    enter_idle();

    g_boot_ms = FSM_Millis();
    g_auto_start_done = 0u;
}

void FSM_Run(void)
{
    uart_command_t cmd;
    uint32_t now = FSM_Millis();

    while (UART_GetCommand(&cmd) != 0u) {
        handle_command(&cmd);
    }

    handle_sensing(now);

    /* Auto-start: if no UART byte has been received within PWM_AUTOSTART_DELAY_MS
     * of FSM_Init completing, issue our own START so the inverter runs
     * standalone with the safe defaults from pwm_config.h. Operator presence
     * (any UART RX byte) cancels auto-start permanently. */
    if ((g_auto_start_done == 0u) && (g_state == FSM_STATE_IDLE)) {
        if (UART_ActivitySeen() != 0u) {
            g_auto_start_done = 1u;
        } else if ((uint32_t)(now - g_boot_ms) >= PWM_AUTOSTART_DELAY_MS) {
            g_auto_start_done = 1u;
            (void)do_start((const char *)0);
        }
    }

    if ((g_state == FSM_STATE_PRECHARGE) && (g_precharge_done != 0u)) {
        g_state = FSM_STATE_RUN;
        UART_WriteString("$A,RUN\r\n");
    }

    if ((uint32_t)(now - g_last_telem_ms) >= CONFIG_TELEMETRY_PERIOD_MS) {
        g_last_telem_ms = now;
        UART_SendTelemetry(now, g_state, g_mode, Protection_GetLatched(),
                           Sensing_GetData(), g_pwm_last_level);
    }
}

void FSM_SysTickISR(void)
{
    g_ms_ticks++;
}

uint32_t FSM_Millis(void)
{
    return g_ms_ticks;
}

fsm_state_t FSM_GetState(void)
{
    return g_state;
}

sensing_mode_t FSM_GetMode(void)
{
    return g_mode;
}
