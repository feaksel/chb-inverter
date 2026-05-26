# Installation

The dashboard targets **Python 3.11** specifically — `PySide6==6.5.3` (the pinned wheel) is built for Python 3.7–3.11 and does not yet have a 3.12 build.

## Fresh install (recommended — virtualenv)

```powershell
cd firmware/stm32-f303re
py -3.11 -m venv dashboard\.venv
dashboard\.venv\Scripts\python -m pip install --upgrade pip
dashboard\.venv\Scripts\python -m pip install -r dashboard\requirements.txt
```

Pinned versions (`dashboard/requirements.txt`):

```
PySide6==6.5.3
pyserial==3.5
pyqtgraph==0.13.7
numpy<2.0
```

## Run

```powershell
dashboard\.venv\Scripts\python dashboard\run_dashboard.py
```

## Troubleshooting

### `Unable to import Shiboken` or `DLL load failed`

The Qt stack didn't install cleanly. Rebuild the venv with the pinned versions:

```powershell
Remove-Item -Recurse -Force dashboard\.venv
py -3.11 -m venv dashboard\.venv
dashboard\.venv\Scripts\python -m pip install --upgrade pip
dashboard\.venv\Scripts\python -m pip install -r dashboard\requirements.txt
dashboard\.venv\Scripts\python dashboard\run_dashboard.py
```

If the same DLL error persists after a clean rebuild, install the latest **Microsoft Visual C++ Redistributable for x64**, then re-run the dashboard.

### Tests run but dashboard window is empty

`pyqtgraph` widgets need PySide6 to be the active Qt binding. If you have PyQt5 / PyQt6 installed system-wide, they can interfere. The venv-based install above isolates the right Qt — that's why it's recommended.

### Running the unit tests headless

The parser and simulator tests do **not** require PySide6, pyserial, or pyqtgraph and complete in under a second:

```powershell
cd firmware/stm32-f303re/dashboard
py -3 -m unittest discover tests -v
```

The Phase 1 `dashboard-tests` GitHub Actions workflow runs these on every push that touches the dashboard tree.
