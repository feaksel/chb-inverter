---
title: Grid tie
---

# Grid tie

The as-built inverter is **stand-alone** — it drives a passive load with no synchronization or anti-islanding. Grid coupling is the largest single roadmap item and is **outside the graduation deliverable scope**. This page covers what would be required.

## Why this is the hardest track

Grid tie carries real safety implications: linemen working on the utility lines, utility equipment that expects a specific impedance and harmonic profile, neighbouring loads that don't expect injected harmonics. Every utility's interconnection requirements are designed to keep all of those parties safe, and they are stricter than anything a bench prototype has had to meet.

In Türkiye specifically, the relevant references are:

| Requirement | Source |
|---|---|
| Frequency tolerance: 50 Hz ± 0.5 Hz | EPDK (Energy Market Regulatory Authority) interconnection rules |
| Voltage tolerance: nominal ± 10 % | Same |
| Anti-islanding: trip within 2 s of grid loss | IEEE 1547-2018 §4.6 + EPDK |
| Harmonic limits: voltage THD < 5 % at PCC | IEEE 519-2022 (project already targets < 5 %) |
| Galvanic isolation between DER and grid | Distribution-utility specific; usually required for low-voltage tie |

## What needs to be built

### 1. Output filter — prerequisite

The [LC filter](lc-filter.md) is the precondition. No utility will accept a 5 kHz-switching inverter coupled directly to their network. The 237 Hz LC variant the team specified is acceptable for low-voltage tie; for medium-voltage, more aggressive filtering would be needed.

### 2. Phase-locked loop on grid voltage

The modulator's reference phase must track the grid. Standard approach:

- Add a galvanically-isolated grid-voltage sense channel (separate from the bench-output sense added for [closed-loop](closed-loop-control.md)).
- Implement a single-phase SOGI (Second-Order Generalised Integrator) PLL in firmware. The SOGI gives the orthogonal pair the PLL needs without requiring a per-cycle delay buffer.
- Lock window: ± 5° within 200 ms of grid present.

### 3. Anti-islanding

Required by all utility-tie standards. Two families of methods:

- **Passive**: monitor frequency / voltage / phase for sudden change. Simple to implement; can be fooled by matched loads ("non-detection zone"). Insufficient on its own.
- **Active**: inject a small perturbation (phase, frequency, or impedance) and watch the grid's response. Standard active methods include slip-mode frequency shift (SMS), Sandia frequency shift (SFS), and reactive-power injection.

A combined passive + active scheme is what utilities actually accept. Trip-and-disconnect within 2 s of grid loss is the headline requirement.

### 4. Soft start + soft disconnect

Cold-starting the inverter must not slam current onto the grid:

- Start in PRECHARGE (already there in the firmware FSM) → ramp `MI` from 0 to nominal over ≈ 5 s after grid sync detected.
- On disconnect, ramp `MI` back to 0 over 100 ms before opening the physical contactor.

### 5. Physical disconnect

A contactor between the LC filter and the grid, controlled by the firmware. On anti-island trip:

1. Drop the contactor immediately.
2. Drive `MI` to 0.
3. Set `BDTR.MOE = 0`.

The contactor must have utility-rated AC contacts (not a relay rated only for DC switching).

### 6. Galvanic isolation

For low-voltage distribution tie, the DER must be galvanically isolated from the grid. A line-frequency transformer between the LC filter output and the contactor is the standard approach. Adds significant mass and cost — typically the largest single BOM line on the deployed unit.

## Software work

| Module | Estimated effort |
|---|---|
| SOGI-PLL implementation + tuning | 2 weeks |
| Anti-islanding (passive + active SMS) | 3 weeks |
| Soft-start state machine extensions to the existing FSM | 1 week |
| Disconnect-contactor driver + supervision | 1 week |
| Grid-side telemetry additions to the UART protocol | 1 week |

## Hardware work

| Item | Estimated effort |
|---|---|
| AC sense channel (isolated) | 1 week design + parts + 1 week assembly |
| Contactor + driver | 1 week sourcing + 1 week integration |
| Line-frequency isolation transformer | 2 weeks sourcing + integration |

## Compliance work

| Test | Where |
|---|---|
| Harmonic measurement (IEC 61000-4-7) at the PCC | Accredited test lab |
| Anti-islanding trip-time validation | Accredited test lab with utility-impedance simulator |
| Local utility witness test | EPDK-approved engineer + utility representative |

Compliance testing typically costs as much as the inverter itself in lab time.

## Total estimate

**4–6 engineer-months** for software + hardware, plus ≈ 2 calendar months for procurement, plus compliance lab time.

## Recommendation

Don't attempt grid tie as the next step. The path is:

1. [LC filter](lc-filter.md) — unblocks everything else.
2. [Closed-loop control](closed-loop-control.md) — needed for grid tie anyway.
3. [Thermal enclosure](thermal-enclosure.md) — required for a real-load deployment.
4. **Grid tie last**, with a clear engineering owner, a funded test-lab plan, and a utility relationship.

If grid tie isn't really the goal — if the actual use case is **off-grid PV + battery** — then this whole track collapses: the LC filter + closed-loop suffice, and the inverter ties to a battery bank instead of a utility. That's a much smaller project.
