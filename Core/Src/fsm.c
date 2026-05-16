#include "fsm.h"
#include "protection.h"
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

static void enter_idle(void)
{
    pwm_disable_and_reset_precharge();
    g_state = FSM_STATE_IDLE;
}

static void enter_fault(uint8_t faults)
{
    pwm_disable_and_reset_precharge();
    Protection_Latch(faults);
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

static void handle_start(const uart_command_t *cmd)
{
    if (g_state != FSM_STATE_IDLE) {
        UART_SendError("START_ALLOWED_ONLY_IN_IDLE");
        return;
    }
    if (Sensing_ModeSensorsAvailable(g_mode) == 0u) {
        UART_SendError("MODE_SENSOR_UNAVAILABLE");
        return;
    }

    UART_SendAck(cmd->raw);
    warn_if_open_loop();
    Protection_ClearLatched();
    pwm_enable_for_precharge();
    g_state = FSM_STATE_PRECHARGE;
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

    g_pwm_modulation_index = cmd->float_arg;
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
    if (g_mode != MODE_FULL) {
        UART_SendError("MODE_DEMOTED");
    }
    warn_if_open_loop();
    enter_idle();
}

void FSM_Run(void)
{
    uart_command_t cmd;
    uint32_t now = FSM_Millis();

    while (UART_GetCommand(&cmd) != 0u) {
        handle_command(&cmd);
    }

    handle_sensing(now);

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
