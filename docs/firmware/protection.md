# Protection

Four protection conditions are checked after every 1 kHz sensor scan. Each has its own N-of-M debounce counter — a fault must hold for **3 consecutive scans (3 ms)** before it trips.

## Conditions

| Bit | Name | Trip condition | Default threshold |
|---:|---|---|---:|
| `0x01` | `UV`    | DC bus < UV threshold | 40 V (at VNOM = 50 V) |
| `0x02` | `OV`    | DC bus > OV threshold | 58 V (at VNOM = 50 V) |
| `0x04` | `OC`    | |Iout| > OC threshold | 15 A |
| `0x08` | `IMBAL` | |Vdc1 - Vdc2| > IMBAL threshold | 10 V (at VNOM = 50 V) |
| `0x10` | `SENSOR_LOST` | Required sensor stuck at rail | — (latches when detected) |
| `0x20` | `MANUAL` | Operator `TRIP` command | — |

## Runtime-tunable thresholds (`VNOM`)

The DC-bus thresholds (`UV`, `OV`, `IMBAL`) are not fixed — they scale with a single runtime-set nominal bus voltage so the inverter can be bench-tested below the 50 V design point without UV firing immediately.

- `VNOM <v>` sets the nominal per-bridge bus voltage, 5–60 V.
- The firmware derives:
    - `UV = 0.80 × VNOM`
    - `OV = 1.16 × VNOM`
    - `IMBAL = 0.20 × VNOM`

At `VNOM = 50` these reproduce the original 40 / 58 / 10 V design values. At `VNOM = 12` (a typical bench supply) they become 9.6 / 13.92 / 2.4 V — so low-voltage testing actually leaves PRECHARGE without an instant UV trip.

Overcurrent (`OC`) is independent of `VNOM` because it is a load property, not a bus property — set it separately with `OC <amps>` (0.5–20 A).

The active protection config is reported on the `$P` line, emitted at boot, on any `VNOM`/`OC` change, and on `CONFIG`:

```text
$P,vnom=12.00,uv=9.60,ov=13.92,oc=15.00,imbal=2.40
```

## Sensing modes and per-mode protection

| ID | Mode | Sensors | Active protection |
|---:|---|---|---|
| 0 | `FULL`     | DC1, DC2, current  | UV, OV, OC, IMBAL |
| 1 | `DC_ONLY`  | DC1, DC2           | UV, OV, IMBAL |
| 2 | `CUR_ONLY` | Current            | OC |
| 3 | `OPEN`     | None               | **None** — emits a UART warning |
| 4 | `DC1`      | DC1 (+ optional current) | DC1 UV/OV + OC if available |
| 5 | `DC2`      | DC2 (+ optional current) | DC2 UV/OV + OC if available |

At boot, each ADC is read four times. Sensors stuck at `0x000` or `0xFFF` are marked unavailable and the FSM auto-demotes to the most capable supported mode (and emits `$E,MODE_DEMOTED`).

## OPEN mode — explicitly unprotected

`OPEN` mode is allowed (for hardware where the sensors aren't yet wired) but emits `$E,WARNING_OPEN_LOOP_NO_PROTECTION` whenever it is selected or started. Auto-start still fires in OPEN mode — the standalone-demo use case is the reason the warning is a warning and not a block. The operator who deployed firmware in OPEN mode accepted the risk.

## Fault path

When a debounced fault trips, the FSM:

1. Forces `BDTR.MOE = 0` on both TIM1 and TIM8. Outputs go to LOW via `OSSI=1`, MOSFETs off via TLP250 non-inverting.
2. Latches the fault bit(s) in `g_protection_latched`.
3. Pulls `FAULT_OUT` (PB5) LOW.
4. Emits `$F,<bits>,vdc1=<v>,vdc2=<v>,cur=<a>` on UART.

The fault stays latched until `CLEAR` is sent **and** the active condition is gone. If the operator clears while UV is still active, the FSM re-evaluates and stays in FAULT.

## Recovery

| Situation | Path |
|---|---|
| Fault triggered, condition cleared | `CLEAR` → FAULT → IDLE → `START` |
| Fault triggered by sensor loss | `RESCAN` (allowed in FAULT) → re-check sensors → `CLEAR` if recovered |
| Bench testing below 50 V | `VNOM <v>` (allowed in FAULT) → `CLEAR` if UV/IMBAL was the trip → `START` |
| `lock=BAD` reported on `$C` for PSC | `MOD STAIR_ALT` as hard fallback while debugging the carrier phase |

## See also

- The state-machine view: [State machine](state-machine.md).
- The raw source: [`Core/Src/protection.c`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/Core/Src/protection.c) and [`Core/Inc/protection.h`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/Core/Inc/protection.h).
