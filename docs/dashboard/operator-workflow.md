# Operator workflow

A typical bring-up + run session, from "dashboard not running" to "5-level output on the scope."

## 1. Bring the dashboard up

```powershell
cd firmware/stm32-f303re
dashboard\.venv\Scripts\python dashboard\run_dashboard.py
```

The dashboard opens in **Simulator** mode by default — safe for confirming the UI works before touching hardware.

## 2. Connect the Nucleo (live serial)

1. Plug in the Nucleo over the ST-LINK USB.
2. In the dashboard, choose **Source → Live serial**.
3. Pick the COM port (Windows assigns one named `STM32 STLink (COMx)`).
4. Click **Connect**.

On connect, the dashboard sends `STATUS`. This both confirms two-way communication and **cancels the firmware's 3 s auto-start window** — the operator now has full control.

The log pane shows the firmware's startup lines:

- `$A,BOOT_SELF_TEST_DONE`
- `$C,mod=STAIR,fsw=500,bridge=BOTH,ffund=50,mi=0.95,cntoff=0,lock=OK`
- `$P,vnom=50.00,uv=40.00,ov=58.00,oc=15.00,imbal=10.00`
- (if sensors aren't fully connected) `$E,MODE_DEMOTED` or `$E,WARNING_OPEN_LOOP_NO_PROTECTION`

## 3. Configure PWM (before arming)

In the **PWM Config** panel, set:

- **MOD** → `PSC` (the project deliverable; bridges are thermally balanced).
- **FSW** → `5000` Hz (preset dropdown).
- **BRIDGE** → `BOTH`.
- **FFUND** → `50` Hz.

Each change emits a fresh `$C,...` line in the log. Confirm `lock=OK` — if it shows `lock=BAD`, the PSC carrier shift didn't land; either rerun the config or fall back to `STAIR_ALT`.

If bench-testing below 50 V, also set `VNOM` to match the supply voltage (e.g. `12` for a 12 V bench supply). Confirm the new thresholds on the `$P` line.

## 4. Arm and start

1. Check **Arm live START**.
2. Click **START**.

The log shows:

```
$A,START
```

The FSM advances `IDLE → PRECHARGE → RUN`. The sensor graph starts updating at 20 Hz. The scope should show 5 distinct cascade output levels (or 5-level PWM on PSC).

## 5. Sustained run

Watch:

- **Telemetry sanity** — `vdc1` and `vdc2` track the bench supplies; `iout` matches the load. Any `NAN` means the channel is unavailable (likely a sensor wiring issue).
- **Thermal balance** — touch-check both bridges' MOSFETs after 5 minutes. PSC should give convergence within ~3 °C.
- **No spurious fault lines** — if `$F,...` appears, the dashboard fault badge highlights the offending bit.

## 6. Stop

Click **STOP**. The FSM returns to IDLE; PWM outputs go off via `BDTR.MOE = 0` (all MOSFETs off via the TLP250 + OSSI=1 chain).

## Fault recovery

| Fault | What likely happened | Path back |
|---|---|---|
| `UV` | Bus dropped below `0.8 × VNOM`. | Investigate the supply. Once it recovers, `CLEAR`. |
| `OV` | Bus exceeded `1.16 × VNOM`. | Reduce the supply. `CLEAR`. |
| `OC` | Output current exceeded `OC` setting. | Check the load. `CLEAR`. |
| `IMBAL` | One bridge bus drifted from the other by > `0.2 × VNOM`. | Check the two isolated supplies. `CLEAR`. |
| `SENSOR_LOST` | A required sensor went stuck-at-rail. | Investigate wiring. `RESCAN` (allowed in FAULT) to re-check. If recovered, `CLEAR`. |
| `MANUAL` | Operator pressed **FORCE FAULT**. | `CLEAR`. |

## Scenarios (simulator only)

The scenario buttons (`Undervoltage`, `Overvoltage`, `Overcurrent`, `DC imbalance`, `Sensor lost`, `Open loop / no protection`, `Mode demotion`, `Nominal run`) play against the simulator. They never inject into the firmware. Use them to demo the fault chain to a reviewer without touching the bench.

If a simulator fault is active, use **Normalize sim sensors** before `CLEAR` — same requirement as the firmware (the active condition must be gone before the latch clears).
