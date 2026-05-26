# Firmware overview

The firmware is **bare-metal CMSIS** (with a thin HAL bring-up shim retained from CubeMX) running on the STM32F303RE at 64 MHz from the HSI/2 × PLL — no external crystal required.

## Module map

| File | Responsibility |
|---|---|
| [`Core/Src/main.c`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/Core/Src/main.c) | Clock + GPIO + NVIC bring-up; calls `Pwm_Init()` and `FSM_Init()` then enters the main loop. Now ≈ 122 lines after the modulator rewrite. |
| [`Core/Src/pwm_modulator.c`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/Core/Src/pwm_modulator.c) | Owns all PWM state: sine LUT, phase accumulator, period, precharge counters, modulator dispatch (`STAIR`, `PSC`, `STAIR_ALT`), and the TIM1 update ISR. |
| [`Core/Src/fsm.c`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/Core/Src/fsm.c) | Supervisory state machine (`BOOT → IDLE → PRECHARGE → RUN → FAULT`), command handlers, mode transitions, fault propagation. |
| [`Core/Src/sensing.c`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/Core/Src/sensing.c) | TIM6-triggered sense loop; per-channel IIR filter for telemetry; rail-stuck detection. |
| [`Core/Src/spi_mcp3201.c`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/Core/Src/spi_mcp3201.c) | Bit-banged MCP3201 driver with SPIINV (per-line inversion mask) for the 6N137 isolated SPI. |
| [`Core/Src/protection.c`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/Core/Src/protection.c) | UV / OV / OC / IMBAL thresholds with N-of-M debounce; runtime-tunable via `VNOM` / `OC`. |
| [`Core/Src/uart_telem.c`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/Core/Src/uart_telem.c) | USART2 RX command parser; 20 Hz telemetry emitter; XOR checksum. |

## Control flow

1. **`main()`** initializes clock → SysTick → sine LUT → GPIO → timers (TIM1, TIM8, TIM6) → UART → NVIC → FSM.
2. **TIM1 update IRQ** (5 kHz with PSC, 500 Hz with STAIR) → `Pwm_TIM1_UpdateHandler` dispatches to the active modulator. The active modulator owns all PWM CCR writes.
3. **TIM6** (1 kHz) sets `g_sense_pending`. The main loop calls `Sensing_Service()` for the blocking bit-banged SPI reads — keeps the bit-banger out of interrupt context.
4. **Main loop** runs `FSM_Run()` — handles UART commands, services sensing, runs protection, manages state transitions, and emits the 20 Hz telemetry frame.

## Footprint

| | Value |
|---|---:|
| Flash | 36 KB / 512 KB available |
| RAM | 4.1 KB / 64 KB available |
| Warnings | 0 under `-Wall -Wextra -Wshadow -Wundef` |

## Per-page deep dives

| Page | What it covers |
|---|---|
| [Pin map](pin-map.md) | Corrected GPIO assignments — supersedes the v3.1 errata. |
| [State machine](state-machine.md) | The supervisory FSM, transitions, and per-mode protection table. |
| [UART protocol](uart-protocol.md) | Operator command set, telemetry frame format, checksum, line prefixes. |
| [Modulators](modulators.md) | STAIR, PSC, and STAIR_ALT — when each is used and why. |
| [Protection](protection.md) | The six sensing modes, the protection thresholds, the debounce policy. |
