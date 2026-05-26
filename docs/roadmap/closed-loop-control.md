---
title: Closed-loop control
---

# Closed-loop control

The as-built system is **open loop** — the operator sets the modulation index by hand (`MI` UART command), and the output voltage is whatever falls out of `MI × V<sub>DC</sub>`. The output voltage is not measured and not regulated. This roadmap item adds output-voltage feedback so the inverter regulates against load variation and DC-bus drift.

## What the team had planned

From the ELE 401 interim report §6.3, the planned control hierarchy:

| Loop | Rate | Controller | Bandwidth | Response |
|---|---:|---|---:|---:|
| **Inner (current control)** | 5 kHz (synchronized with PWM period) | Proportional-Resonant (PR) tuned to 50 Hz | ≈ 1 kHz | < 5 ms |
| **Outer (voltage control)** | 2 kHz | PI controller | ≈ 100 Hz | ≈ 20 ms |
| **Balancing (DC-link)** | 100 Hz | Active balancing via modulation-index correction | per-bridge | ±5 % between modules |

The architecture was specified before the team committed to open-loop demo for the graduation deliverable. The firmware already exposes the sense channels (MCP3201 × 3) and the `MI` setter; closed-loop is **mostly a software task plus a tuned controller**, not a hardware change.

## What still needs deciding

### 1. Where the AC output-voltage feedback comes from

Today, the three MCP3201 channels are: DC1 bus, DC2 bus, output current (via ACS712). **There is no AC output voltage sense** in the as-built design. Adding closed-loop control requires:

| Option | Description | Cost |
|---|---|---|
| **Isolated AC voltage divider + ADC** | Add a 4th MCP3201 on the output node, with a high-V-rated divider on the cascade-output side and 6N137-isolated SPI back to the controller. | 1 MCP3201 + isolation chain = ~150 TL per board. Schematic + layout change. |
| **Reconstruct from `vdc1`, `vdc2`, and `level`** | The cascade output is mathematically `level × V<sub>DC</sub>` (for STAIR) or some fraction of it (for PSC). Reconstruct from existing telemetry. | No hardware change. Less accurate; doesn't pick up load-side voltage drop. |
| **External AC voltmeter via separate UART** | Plug a calibrated AC voltmeter into the firmware via a second UART or I2C. | Cheap; requires an extra meter on the bench. |

The first option (isolated AC sense) is the right long-term answer. Option two is a useful interim because it requires zero hardware change and can validate the control-loop math before any silicon respin.

### 2. PR vs. synchronous-frame PI

For a single-phase inverter:

- **Proportional-Resonant (PR)** at the fundamental frequency has zero steady-state error on sinusoidal references. Good response and standard for grid-tied single-phase inverters.
- **Synchronous-frame PI** in the dq frame is more powerful (zero error on DC quantities) but requires a frame transformation that's harder to debug.

PR is the team's planned choice and is the right starting point. Synchronous-frame can be added if PR doesn't give enough stability margin under varying load impedance.

### 3. How to detune

A naively-tuned PR controller will oscillate the moment the load impedance moves away from its design point. Standard practice is to add **damping** (a small `+ k_d · s / (1 + s/ω_p)` term) and then detune by reducing the controller gain until oscillation stops with margin. The dashboard's replay mechanism is the right place to characterise the tuning — capture telemetry under a step-load change, run the tuning script offline, repeat.

## Implementation hints

- `pwm_modulator.c` already exposes `Pwm_SetModulationIndex` as a hot path — the closed-loop output would call this every control cycle, not the `Pwm_SetConfig` heavyweight path.
- The control loop runs in the main loop, not the PWM ISR — `Sensing_Service()` already sets the cadence at 1 kHz. Increasing to 5 kHz for the inner loop requires the bit-banged MCP3201 to keep up; current bit-bang at ≈ 140 kHz SCK supports it.
- Add a `LOOP <OPEN|VOLTAGE|CURRENT>` UART command to runtime-select between open-loop and the new closed-loop modes. Same pattern as `MOD`. Keeps the dashboard simulation workflows usable.
- Add `Kp`, `Ki`, `Kr` (PR coefficients), `LIM` (modulation-index limit) as `set`/`get` UART commands so tuning can be done from the dashboard without reflashing.

## Effort estimate

| Sub-item | Engineer-time |
|---|---|
| Add AC voltage sense channel (hardware) | 2 weeks (schematic + PCB respin + parts + assembly) |
| OR reconstruct from existing telemetry (software-only) | 2 days |
| Implement PR + outer PI in firmware | 1 week |
| Tune at multiple load points | 1 week bench |
| Dashboard controls (`Kp`, `Ki`, `LOOP` selector) | 2 days |

Total (with hardware respin): ≈ 6 engineer-weeks. With software-only feedback reconstruction: ≈ 2 engineer-weeks.

## Why this is gated on the LC filter

Closed-loop voltage control on an unfiltered cascade output is unstable — the controller would try to regulate the cascade-step harmonics. The [LC filter](lc-filter.md) gives the controller something clean to regulate against. Build the LC filter first; closed-loop second.
