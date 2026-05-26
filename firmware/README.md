# Firmware

STM32 firmware and the PySide6 operator dashboard.

The contents of `stm32-f303re/` are imported via `git subtree` from the firmware repository, preserving commit history. Source of truth upstream:

- Repository: https://github.com/feaksel/5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE
- Branch: `pwm-rewrite-configurable`

> **Phase 2 placeholder.** The subtree import happens in Phase 2 of the consolidation. After that, this README is expanded with: build instructions (STM32CubeIDE + `arm-none-eabi-gcc`), flash procedure, dashboard install (`py -m pip install -r dashboard/requirements.txt`), and a per-module map of `Core/` and the dashboard.

## Where to look once imported

| Document | Location |
|---|---|
| Firmware README | `stm32-f303re/README.md` |
| Firmware CHANGELOG | `stm32-f303re/CHANGELOG.md` |
| First bench session | `stm32-f303re/FIRST_BENCH_SESSION.md` |
| Hardware bring-up reference | `stm32-f303re/HARDWARE_BRINGUP.md` |
| State machine notes | `stm32-f303re/FSM_NOTES.md` |
| Operator dashboard | `stm32-f303re/dashboard/` |

These files are also rendered into the published docs site under [`docs/firmware/`](../docs/firmware/) and [`docs/bringup/`](../docs/bringup/) via `mkdocs-include-markdown-plugin`.
