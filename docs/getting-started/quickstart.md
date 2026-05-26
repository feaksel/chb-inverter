# Quickstart

This page is the **shortest path** from a fresh clone to a running dashboard talking to a flashed STM32 Nucleo-F303RE.

!!! info "Phase 2 will populate this page"
    Once the firmware tree is imported, this page becomes a step-by-step that you can follow end-to-end. For now, the canonical procedure is in [Build Guide v4.0 — §12 Bring-up procedure](../hardware/build-guide-v4.md).

## What you'll need (preview)

| Thing | Notes |
|---|---|
| STM32 Nucleo-F303RE board | Hardware controller. |
| Two populated single-bridge PCBs | See [hardware](../hardware/index.md). |
| Isolated DC supplies | One per bridge, plus 5 V logic. |
| Oscilloscope, multimeter | For bring-up, not for normal operation. |
| STM32CubeIDE | To flash; alternatively `arm-none-eabi-gcc` + `st-flash`. |
| Python 3.11+ | For the operator dashboard. |

## The two-minute path (preview)

1. Clone this repository.
2. Open `firmware/stm32-f303re/` in STM32CubeIDE and flash to the Nucleo.
3. Connect the Nucleo via UART (115200 8N1) and start the dashboard:

       cd firmware/stm32-f303re/dashboard
       py -3.12 -m pip install -r requirements.txt
       py -3.12 main.py

4. The dashboard talks to the Nucleo; commands and telemetry flow over UART per the [UART protocol](../firmware/uart-protocol.md).

For the **full bench bring-up** procedure (including the safe power-up order, the per-bridge isolation checks, and what to look for on the scope), follow [Build Guide v4.0 — §12](../hardware/build-guide-v4.md) and the [first-session bring-up notes](../bringup/first-session.md) once Phase 2 is in.
