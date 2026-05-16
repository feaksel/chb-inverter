#ifndef UART_TELEM_H
#define UART_TELEM_H

#include "config.h"
#include "sensing.h"
#include <stdint.h>

typedef enum {
    UART_CMD_NONE = 0,
    UART_CMD_START,
    UART_CMD_STOP,
    UART_CMD_CLEAR,
    UART_CMD_MODE,
    UART_CMD_STATUS,
    UART_CMD_HELP,
    UART_CMD_MI,
    UART_CMD_RESCAN,
    UART_CMD_MOD,       /* set modulator: STAIR | PSC */
    UART_CMD_FSW,       /* set switching frequency (Hz) */
    UART_CMD_BRIDGE,    /* set bridge select: BOTH | B1 | B2 */
    UART_CMD_FFUND,     /* set fundamental frequency (Hz) */
    UART_CMD_CONFIG,    /* print current PWM config */
    UART_CMD_INVALID
} uart_cmd_type_t;

typedef struct {
    uart_cmd_type_t type;
    uint8_t mode_arg;
    float float_arg;
    char raw[40];
} uart_command_t;

typedef enum {
    FSM_STATE_BOOT = 0,
    FSM_STATE_IDLE,
    FSM_STATE_PRECHARGE,
    FSM_STATE_RUN,
    FSM_STATE_FAULT
} fsm_state_t;

void UART_Init(void);
void UART_USART2_IRQHandler(void);
void UART_WriteString(const char *text);
uint8_t UART_GetCommand(uart_command_t *cmd);
uint8_t UART_ActivitySeen(void);   /* 1 if any RX byte received since boot */
void UART_SendAck(const char *cmd);
void UART_SendError(const char *reason);
void UART_SendFault(uint8_t faults);
void UART_SendHelp(void);
void UART_SendPwmConfig(const char *modulator_name,
                        uint32_t switching_freq_hz,
                        const char *bridge_name,
                        float fundamental_freq_hz,
                        float modulation_index);
void UART_SendStatus(uint32_t ms,
                     fsm_state_t state,
                     sensing_mode_t mode,
                     uint8_t faults,
                     const sensing_data_t *data,
                     float modulation_index);
void UART_SendTelemetry(uint32_t ms,
                        fsm_state_t state,
                        sensing_mode_t mode,
                        uint8_t faults,
                        const sensing_data_t *data,
                        int8_t level);
const char *UART_StateName(fsm_state_t state);
const char *UART_ModeName(sensing_mode_t mode);

#endif /* UART_TELEM_H */
