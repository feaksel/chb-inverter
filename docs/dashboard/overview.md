# Dashboard overview

The dashboard is a Windows-friendly PySide6 desktop application that talks to the STM32 over UART (115200 8N1) and provides:

- **Live monitoring** of the existing USART2 telemetry from the Nucleo (20 Hz frames).
- **A PC-only simulator** for safe demos that do not touch hardware.
- **Operator controls** — every command the firmware supports.
- **Sensor graphing**, **modulation visualization**, and **5-level output reconstruction**.

Source lives at [`firmware/stm32-f303re/dashboard/`](https://github.com/feaksel/chb-inverter/tree/main/firmware/stm32-f303re/dashboard) after the Phase 2 subtree import.

## Architecture

| Module | Purpose |
|---|---|
| `protocol.py` | NMEA-style line parser. Matches the firmware's XOR checksum format. Forgiving — lines with bad checksums still produce a `TelemetryFrame` (marked `checksum_valid=False`). |
| `models.py` | `TelemetryFrame` dataclass; mirror enums for FSM mode / fault bits. |
| `sim.py` | `SimController` — deterministic step()-based timeline with 8 pre-baked scenario presets. |
| `sources.py` | `BaseSource` / `SimSource` / `SerialSource` / `ReplaySource` adapters. All emit the same `frame_received` signal. |
| `widgets.py` | FSM strip, fault badge, modulation/output twin, sensor gauges. |
| `app.py` | Main window, command panel, scenario presets, log pane. |
| `tests/test_protocol.py` & `tests/test_sim.py` | Pure-Python unit tests — no Qt required. CI runs these on every push. |

## Safety design

- **`Arm live START` checkbox.** Live `START` is gated behind a checkbox the operator must flip explicitly. Other commands (`STOP`, `STATUS`, `MODE`, `MI`, `CLEAR`) are not gated.
- **Sim and serial are fully separate.** Scenario buttons (which inject synthetic faults) are disabled when `Arm live START` is checked; scenarios always play against the simulator. The simulator never injects fake sensor values into the firmware.
- **Auto-cancel of firmware auto-start.** The `SerialSource` transmits `STATUS` on connect and on every detected `$A,BOOT_SELF_TEST_DONE`. A connected dashboard always suppresses the firmware's 3 s auto-start, including across Nucleo resets.
- **Frames carry a `source` field.** `_handle_frame` filters by source so simulator frames don't pollute the live serial view (and vice versa) when sources are switched mid-session.

## Visual twin

The visual-twin area has two tabs:

| Tab | What it shows |
|---|---|
| **Modulation** | Sine reference, triangle carrier, 5-level decision bands. The sine amplitude follows the modulation index. |
| **Output steps** | The reconstructed 5-level output step view from telemetry. |

Sensor graph auto-follows the latest telemetry by default. `Zoom in` / `Zoom out` / the time-window control inspect shorter or longer intervals. Mouse pan/zoom turns off `Follow graph`; `Reset view` re-enables it.
