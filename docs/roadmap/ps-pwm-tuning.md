---
title: PSC-PWM tuning
---

# PSC-PWM tuning

PSC-PWM is the as-built default modulator (see [modulators](../firmware/modulators.md)) and was bench-validated at 5 kHz with both bridges thermally matched. This roadmap item covers **further tuning** beyond what was demonstrated.

## What's already in place

| | Status |
|---|---|
| 90° carrier phase shift between TIM8 and TIM1 | Working — `lock=OK` reported consistently |
| Carrier-phase lock diagnostic (`g_pwm_measured_cnt_offset` + `g_pwm_phase_locked`) | Published on every `$C,...,cntoff=N,lock=OK\|BAD` config line |
| Runtime switching-frequency sweep via `FSW` UART command | 100 Hz – 20 kHz allowed |
| Hard fallback to `STAIR_ALT` if PSC `lock=BAD` | Operator-selectable from dashboard |
| Bench validation at 5 kHz | Five distinct cascade levels at 100 V, bridges thermally matched within ≈ 3 °C |

## What this item covers

### Switching-frequency sweep

A structured sweep across the firmware's allowed `FSW` range (100 Hz to 20 kHz) to characterise the tradeoffs:

| f<sub>sw</sub> | What changes |
|---:|---|
| Lower (≤ 1 kHz) | Lower switching loss; lower thermal load; output ripple becomes audible / larger; LC filter needs to be bigger |
| Headline 5 kHz | Bench-validated; balance of loss + filter size |
| Higher (≥ 10 kHz) | Switching loss climbs (dead time becomes a larger fraction of period); ripple energy moves up where smaller LC filters work; gate-loop parasitics become more important to control |

Deliverables: per-frequency measurement of cascade-output THD (pre-filter), bridge case-temperature delta, gate-loop ringing on the scope. A 5-point sweep (500 Hz, 1 kHz, 5 kHz, 10 kHz, 20 kHz) of 5 minutes per point would be a one-session experiment. Telemetry replay from each run is in the dashboard's replay format.

### Carrier-phase offset sweep

The PSC carrier phase shift is currently fixed at 90° (TIM8 CNT preset to `ARR/2`). For 2 cells this is textbook-optimal — phase shift = 360°/N = 180° for 2 cells, but unipolar modulation uses half that = 90°. The roadmap question: does fine-tuning the phase by a few degrees give measurable improvement under partial bridge mismatch (e.g. different supply rails, different MOSFET binning)?

Implementation hint: add a runtime `PHASE <offset_ticks>` UART command that adjusts the TIM8 CNT preset away from `ARR/2`. The lock-detection logic then checks `cntoff` against the new target, not against ARR/2. Tunable by sweep, measurable by FFT.

### Closed-loop carrier lock

Today, if `lock=BAD` is reported, the operator manually falls back to `STAIR_ALT`. A closed-loop variant would have the firmware:

1. Detect `lock=BAD` after every config change.
2. Auto-retry the phase-shift application up to N times.
3. If still bad, auto-select `STAIR_ALT` and emit a UART notification.

Implementation hint: a few additional state transitions in [`fsm.c`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/Core/Src/fsm.c) plus a counter. No hardware change.

## Effort estimate

| Sub-item | Engineer-time |
|---|---|
| Switching-frequency sweep + write-up | 1 day bench + 1 day analysis |
| Phase-offset sweep | 1 day bench + 1 day analysis (requires the runtime PHASE command) |
| Closed-loop carrier lock | 2 days firmware + bench verification |

## Why this matters

The carrier-shift `lock=OK\|BAD` diagnostic was added defensively before the first bench session — it caught a real issue immediately ([iteration-4](../iteration-history/iteration-4.md)). Extending it to auto-recovery and adding structured sweep data is the next step in making PSC robust enough to ship in any product version of this design.
