# PC Visual Twin Dashboard

This dashboard is a Windows-friendly Python desktop app for the STM32 5-level
cascaded H-bridge inverter project. It can monitor the existing USART2
telemetry from the Nucleo, or run as a PC-only visual twin for safe demos.

The fault scenarios are synthetic and stay on the PC. They do not inject fake
sensor values into the firmware and do not add any firmware-side fault hooks.

## Install

```powershell
py -3 -m venv dashboard\.venv
dashboard\.venv\Scripts\python -m pip install --upgrade pip
dashboard\.venv\Scripts\python -m pip install -r dashboard\requirements.txt
```

## Run

```powershell
dashboard\.venv\Scripts\python dashboard\run_dashboard.py
```

Use `Simulator` for no-hardware demos. Use `Live serial` to connect to the
ST-LINK virtual COM port at `115200 8N1`.

The sensor graph auto-follows the latest telemetry by default. Use `Zoom in`,
`Zoom out`, or the time-window control to inspect a shorter or longer interval.
Mouse pan/zoom turns off `Follow graph`; `Reset view` enables follow again.

## Live Controls

The dashboard sends only commands already supported by the firmware:

- `START`
- `STOP`
- `CLEAR`
- `MODE 0..5`
- `STATUS`
- `HELP`
- `MI 0.0..0.95`

For live serial, `START` is blocked until `Arm live START` is checked. Scenario
buttons switch to the simulator so fault demonstrations cannot trip real
hardware.

## Scenario Presets

- Nominal run
- Undervoltage
- Overvoltage
- Overcurrent
- DC imbalance
- Sensor lost
- Open loop / no protection
- Mode demotion

The visual twin area has two tabs:

- `Modulation`: sine reference, triangle carrier, and 5-level decision bands.
  The sine amplitude follows the modulation index.
- `Output steps`: the reconstructed 5-level output step view from telemetry.

If a simulator fault is active, use `Normalize sim sensors` before `CLEAR`, just
like the firmware requires the active fault condition to be gone before clearing
the latch.

## Tests

The parser and simulator tests do not require PySide6, pyserial, or pyqtgraph:

```powershell
py -3 -m unittest discover dashboard\tests
```

## Troubleshooting

If PySide6 fails with `Unable to import Shiboken` or `DLL load failed`, rebuild
the venv so pip uses the pinned Qt stack from `requirements.txt`:

```powershell
Remove-Item -Recurse -Force dashboard\.venv
py -3 -m venv dashboard\.venv
dashboard\.venv\Scripts\python -m pip install --upgrade pip
dashboard\.venv\Scripts\python -m pip install -r dashboard\requirements.txt
dashboard\.venv\Scripts\python dashboard\run_dashboard.py
```

If the same DLL error remains after rebuilding, install the latest Microsoft
Visual C++ Redistributable for x64, then run the last command again.
