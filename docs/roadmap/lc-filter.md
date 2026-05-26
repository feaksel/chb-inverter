---
title: LC output filter
---

# LC output filter

The team simulated two LC filter values during the design phase but did **not** build a physical filter — the demonstration ran the inverter into a resistive load, and the 5-level cascade is visible directly on the scope (see [headline result](../hardware/populated-photos.md#headline--100-v-output-5-distinct-cascade-levels)). This roadmap item is to build the LC stage so the deployed system can drive non-trivial loads.

## What was simulated

Two cutoff values, both in the `chb-5level-rl-nospike.slx` model:

| Variant | L | C | f<sub>c</sub> |
|---:|---:|---:|---:|
| Initial (R load) | 15 mH | 22 µF | 325 Hz |
| Revised (RL load) | 15 mH | 30 µF | 237 Hz |

The team's notes from the design discussion (preserved in the Drive `LC` document) settled on the **237 Hz variant** as the recommended starting point for an inductive load.

## Filter design

Where this sits in the topology: between the cascade-output node and the load. The cap return goes to the **load's return**, not to the inverter ground — this matters because the inverter ground (5V_GND or 50V_GND on the upper bridge) is not the same as the load ground.

### Why f<sub>c</sub> = 237 Hz?

- Fundamental is 50 Hz → f<sub>c</sub> needs to be high enough above 50 Hz that the fundamental passes essentially unattenuated. 237 Hz is ≈ 5× the fundamental, giving < 1 % attenuation at 50 Hz.
- Switching frequency is 5 kHz → f<sub>c</sub> needs to be well below 5 kHz to attenuate the switching harmonics. 237 Hz is ≈ 21× below 5 kHz, giving ≈ 40 dB attenuation at the first switching harmonic.
- The RL load adds its own dynamics; lower f<sub>c</sub> keeps the filter dominant over the load's natural roll-off.

### Component sourcing

| Part | Spec | Sourcing concern |
|---|---|---|
| L = 15 mH | At ≥ 10 A continuous; iron-powder or ferrite core; air gap to prevent saturation under DC bias | The bench loads quoted in iteration testing went up to 5 A; sourcing 15 mH @ 10 A in a bench-friendly package is not trivial — Direnc.net carries iron-powder toroids that work |
| C = 30 µF | Polypropylene film cap (NOT electrolytic — electrolytic ESR + DC bias both kill performance); rated for at least 2× peak output voltage = ≥ 200 V | Motorobit / Direnc.net both stock 30 µF / 250 V film caps. Three 10 µF / 250 V caps in parallel is the cheaper assembly approach |
| Bleeder resistor | 100 kΩ / 1 W across the cap to discharge after shutdown | Already in the BOM (line C.12) |

### Layout considerations

- The L should be mounted **off the PCB** — toroid inductors that big won't fit on the single-bridge module.
- The C should be on a small **filter PCB** that mates between the cascade output and the load terminals. Two screw terminals each side.
- Keep the loop area (inverter output → L → C → load → return) **small** to limit radiated EMI. Tight twisted-pair routing or a coaxial-style return for the output cable.

## Expected effect on THD

The Simulink predicted THD pre-filter is 4.9 %; with the 237 Hz LC, the model showed THD drop to **< 1 %** at the same operating point. The first-switching-harmonic content is attenuated ≈ 40 dB, which is the dominant THD contributor.

## Effort estimate

| Sub-item | Engineer-time |
|---|---|
| Source L + C parts (10–14-day delivery from Direnc.net) | 1 day procurement |
| Design + fabricate filter PCB | 3 days (KiCad + JLCPCB turn) |
| Assembly + bench bring-up | 1 day |
| FFT measurement + write-up | 1 day |

Total: ≈ 2 engineer-weeks calendar including parts delivery.

## Why this is the next item

The LC filter is the **prerequisite for every downstream roadmap item** — closed-loop control needs a filtered output to control against, grid tie requires it for interconnection compliance, thermal enclosure has to dissipate the LC's losses too. Doing the LC first keeps the rest of the roadmap unblocked.
