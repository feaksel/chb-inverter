# Firmware

STM32 firmware (CMSIS bare-metal with HAL bring-up shim) and the PySide6 operator dashboard for the 5-Level CHB Inverter.

The [`stm32-f303re/`](stm32-f303re/) tree is imported via `git subtree` from the upstream repository at https://github.com/feaksel/5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE (branch `pwm-rewrite-configurable`). All upstream commits are preserved in this repo's `git log`.

## Quick reference

| Document | Where |
|---|---|
| Firmware README | [`stm32-f303re/README.md`](stm32-f303re/README.md) |
| Firmware CHANGELOG | [`stm32-f303re/CHANGELOG.md`](stm32-f303re/CHANGELOG.md) |
| Finite-state machine | [`stm32-f303re/FSM_NOTES.md`](stm32-f303re/FSM_NOTES.md) |
| First bench session | [`stm32-f303re/FIRST_BENCH_SESSION.md`](stm32-f303re/FIRST_BENCH_SESSION.md) |
| Hardware bring-up reference | [`stm32-f303re/HARDWARE_BRINGUP.md`](stm32-f303re/HARDWARE_BRINGUP.md) |
| Operator dashboard | [`stm32-f303re/dashboard/`](stm32-f303re/dashboard/) |

These files are also rendered into the [published docs site](https://feaksel.github.io/chb-inverter/) under [`docs/firmware/`](../docs/firmware/) and [`docs/bringup/`](../docs/bringup/) via `mkdocs-include-markdown-plugin`.

## Build and flash

### STM32CubeIDE (normal path)

1. Open `firmware/stm32-f303re/` in STM32CubeIDE 1.17+.
2. Build (`Project → Build All` or the hammer icon).
3. Plug in the Nucleo-F303RE over USB.
4. Flash with the Run/Debug button.

Expected size: ≈ 36 KB Flash, ≈ 4 KB RAM. Zero warnings under `-Wall -Wextra -Wshadow -Wundef`.

### Command-line / CI

The Phase 1 `firmware-build` GitHub Actions workflow runs `make` against `firmware/stm32-f303re/Debug/makefile` if present, and falls back to a per-file syntax check using `arm-none-eabi-gcc -fsyntax-only` otherwise. The full toolchain invocation that CubeIDE uses is documented in [`stm32-f303re/README.md`](stm32-f303re/README.md) under **Build and Flash → Command-line build**.

## Run the dashboard

The dashboard is a PySide6 desktop application that connects over UART (115200 8N1) and provides commands + 20 Hz telemetry visualization.

```powershell
cd firmware/stm32-f303re/dashboard
py -3.11 -m pip install -r requirements.txt
py -3.11 run_dashboard.py
```

> Use Python **3.11** for the dashboard. The pinned PySide6 wheel (`PySide6==6.5.3`) ships binaries for Python 3.7–3.11 and is not available on 3.12 yet.

The unit tests under `dashboard/tests/` are pure Python and run without Qt:

```powershell
cd firmware/stm32-f303re/dashboard
py -3 -m unittest discover tests -v
```

## Important runtime behaviors

- **Auto-start** — if no UART byte arrives within 3 s of boot, the firmware issues its own `START` using the defaults in [`Core/Inc/pwm_config.h`](stm32-f303re/Core/Inc/pwm_config.h). Sending any UART byte during those 3 s cancels auto-start permanently for that boot cycle. The dashboard's `SerialSource` transmits `STATUS` on connect (and on every detected `BOOT_SELF_TEST_DONE`) to suppress auto-start whenever an operator is present.
- **SPIINV** — every MCP3201 SPI line crosses the isolation barrier through a 6N137 optocoupler, which inverts. The `SPIINV <0..7>` UART command sets a per-line inversion mask at runtime. Once bench-validated, set `SPI_DEFAULT_INVERT_MASK` in [`Core/Inc/spi_mcp3201.h`](stm32-f303re/Core/Inc/spi_mcp3201.h) so the right polarity is the boot default.
- **VNOM scaling** — DC-bus protection thresholds (UV / OV / IMBAL) scale with the runtime `VNOM` setting (5–60 V). The factory default is 50 V. Bench-testing at 12 V is supported by setting `VNOM 12`.
- **OPEN sensing mode** is allowed (for hardware where the sensors aren't wired yet) but disables all protection and emits a UART warning.

Full per-command and per-state reference in [`docs/firmware/`](../docs/firmware/).
