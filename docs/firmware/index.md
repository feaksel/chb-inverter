# Firmware

STM32 source for the controller and the PySide6 operator dashboard.

!!! info "Phase 2 in progress"
    The firmware tree is imported in Phase 2 via `git subtree`, preserving commit history from the upstream repository at [feaksel/5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE](https://github.com/feaksel/5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE), branch `pwm-rewrite-configurable`.

## What's on this section (after Phase 2)

| Page | Source | Purpose |
|---|---|---|
| Overview | written here | What the firmware does, at a glance. |
| Pin map | Build Guide v4 §7.1 | Corrected GPIO assignments — supersedes the v3.1 errata. |
| State machine | `firmware/.../FSM_NOTES.md` rendered as Mermaid | Controller FSM, transitions, fault states. |
| UART protocol | Build Guide v4 §8.7 | Operator command + telemetry frame reference. |
| Modulators | Build Guide v4 §9 + firmware CHANGELOG | PSC, PSC ALT, IPD LS-PWM — when to use which. |
| Protection | Build Guide v4 §10 | Over-current trip, fault propagation. |

## Companion source

| Document | Path (after Phase 2) |
|---|---|
| Firmware README | `firmware/stm32-f303re/README.md` |
| Firmware CHANGELOG | `firmware/stm32-f303re/CHANGELOG.md` |
| First bench session | `firmware/stm32-f303re/FIRST_BENCH_SESSION.md` |
| Hardware bring-up reference | `firmware/stm32-f303re/HARDWARE_BRINGUP.md` |
| State machine notes | `firmware/stm32-f303re/FSM_NOTES.md` |
