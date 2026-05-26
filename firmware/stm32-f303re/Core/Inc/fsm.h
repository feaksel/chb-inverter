#ifndef FSM_H
#define FSM_H

#include "config.h"
#include "uart_telem.h"
#include <stdint.h>

void FSM_Init(void);
void FSM_Run(void);
void FSM_SysTickISR(void);
uint32_t FSM_Millis(void);
fsm_state_t FSM_GetState(void);
sensing_mode_t FSM_GetMode(void);

#endif /* FSM_H */
