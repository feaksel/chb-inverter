# Firmware

<figure markdown="span">
  ![STM32 + the firmware/dashboard architecture](../assets/images/stm32-only-diagram.png){ loading=lazy width=75% }
  <figcaption>The STM32 F303RE drives both bridges over TIM1 (Bridge 1) and TIM8 (Bridge 2). Bit-banged MCP3201 sensing crosses the isolation barrier through 6N137 optocouplers; UART telemetry feeds the PySide6 dashboard.</figcaption>
</figure>

STM32 source for the controller and the PySide6 operator dashboard.

The firmware tree is imported via `git subtree` from the upstream repository [feaksel/5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE](https://github.com/feaksel/5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE), branch `pwm-rewrite-configurable`. All 11 upstream commits are preserved in this repo's `git log`.

## Pages in this section

| Page | What it covers |
|---|---|
| [Overview](overview.md) | What the firmware does, module map, control flow, footprint. |
| [Pin map](pin-map.md) | Corrected GPIO assignments — supersedes the v3.1 errata. |
| [State machine](state-machine.md) | The supervisory FSM, transitions, per-mode protection. |
| [UART protocol](uart-protocol.md) | Operator command set, telemetry frame, line prefixes. |
| [Modulators](modulators.md) | STAIR, PSC, STAIR_ALT — when each is used and why. |
| [Protection](protection.md) | The six sensing modes and the protection thresholds. |

## Source files

| Document | Source path |
|---|---|
| Firmware README | [`firmware/stm32-f303re/README.md`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/README.md) |
| Firmware CHANGELOG | [`firmware/stm32-f303re/CHANGELOG.md`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/CHANGELOG.md) |
| FSM notes | [`firmware/stm32-f303re/FSM_NOTES.md`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/FSM_NOTES.md) |
| First bench session | [`firmware/stm32-f303re/FIRST_BENCH_SESSION.md`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/FIRST_BENCH_SESSION.md) → also rendered into the [bring-up section](../bringup/first-session.md). |
| Hardware bring-up reference | [`firmware/stm32-f303re/HARDWARE_BRINGUP.md`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/HARDWARE_BRINGUP.md) → also rendered at [Bring-up reference](../bringup/reference.md). |
