---
title: IGBT vs. MOSFET
---

# IGBT vs. MOSFET

> **Single-sentence summary.** At the project's operating point (50 V per bridge, 5 kHz switching, ≈ 400 W total), every loss term favors MOSFETs. The choice was unambiguous and quantitative — not a preference call.

## The classical crossover

For a power switch in an inverter, the relevant figures of merit are **conduction loss** (the loss while the switch is fully on, carrying current) and **switching loss** (the loss during the transition between on and off, each PWM period). The two technologies make opposite trade-offs:

|  | MOSFET | IGBT |
|---|---|---|
| On-state behavior | Resistive: V<sub>DS</sub> ≈ I × R<sub>DS(on)</sub> | Voltage-source: V<sub>CE(sat)</sub> ≈ constant (≈ 1.4 V regardless of current) |
| Conduction loss at low I | Very low (quadratic with current) | Constant V × I (linear) |
| Conduction loss at high I | High (R<sub>DS(on)</sub> grows with temperature; loss scales I²) | Bounded by V<sub>CE(sat)</sub> |
| Switching transition | Fast, clean | Slower; tail current adds switching-off energy |
| Switching loss at low f<sub>sw</sub> | Negligible | Significant (tail current loss × frequency) |
| Switching loss at high f<sub>sw</sub> | Significant | Dominant |
| Body diode | Built in (free-wheeling) | None — external freewheeling diode required |

The **crossover point** — where IGBTs start to win — is somewhere around 250 V V<sub>DS</sub> and 20 kHz, depending on the exact part. Below those numbers, MOSFETs are better on every term that matters.

## This project's numbers

| Parameter | Value |
|---|---|
| V<sub>DC</sub> per bridge | 50 V |
| Switching frequency | 5 kHz (PSC default) |
| Output current (RMS) | ≈ 5 A |
| Output current (peak) | ≈ 7 A |
| Output power | ≈ 400 W |

At 50 V / 5 kHz, we're solidly in MOSFET territory. The math:

### Conduction loss per device

Using the as-built **IRFB4110** (R<sub>DS(on)</sub> = 4.5 mΩ at V<sub>GS</sub> = 10 V):

> P<sub>cond,MOSFET</sub> = I<sup>2</sup> × R<sub>DS(on)</sub> = 5<sup>2</sup> × 0.0045 ≈ **0.11 W per device**

For comparison, a typical 60 V IGBT at I = 5 A:

> P<sub>cond,IGBT</sub> = V<sub>CE(sat)</sub> × I = 1.4 × 5 = **7.0 W per device**

That's a **63× difference** in conduction loss alone. With 4 devices per bridge × 2 bridges = 8 devices in the system, the totals are:

- MOSFET conduction loss: **0.88 W system-wide**
- IGBT conduction loss: **56 W system-wide**

### Switching loss per device

The IRFB4110 has Q<sub>G(tot)</sub> ≈ 150 nC. With the project's 22 Ω gate-series resistor and 15 V drive voltage, the gate transition takes ≈ 220 ns.

Per-switching-event loss (turn-on + turn-off, half each at 25 V × 7 A peak per bridge):

> P<sub>sw,MOSFET</sub> ≈ ½ × V<sub>DS</sub> × I<sub>peak</sub> × t<sub>rise+fall</sub> × f<sub>sw</sub>
> ≈ 0.5 × 25 × 7 × 440e-9 × 5000 ≈ **0.19 W per device**

For an IGBT in the same role, the **tail current** adds a large additional loss term (typically 5–10 µJ per switching event):

> P<sub>sw,IGBT</sub> ≈ E<sub>sw</sub> × f<sub>sw</sub> ≈ 8e-6 × 5000 = **40 mW from switching transitions + ≈ 5 W tail current loss = 5.04 W per device**

System totals:

- MOSFET switching loss: **1.5 W system-wide**
- IGBT switching loss: **40 W system-wide**

### Combined

| | MOSFET total | IGBT total |
|---|---:|---:|
| Conduction loss | 0.88 W | 56 W |
| Switching loss | 1.5 W | 40 W |
| **Power-stage loss** | **≈ 2.4 W** | **≈ 96 W** |
| **Implied efficiency (at 400 W)** | **≈ 99.4 %** | **≈ 80 %** |

(The IGBT efficiency is so bad because both axes — conduction and switching — are in its worst-case region. At 400 V / 50 kHz, the picture inverts.)

## The IRFB4110 specifically

Build Guide v3.1 specified **IRFZ44N** (55 V V<sub>DSS</sub>, 49 A, 17.5 mΩ R<sub>DS(on)</sub>). The as-built v4 hardware uses **IRFB4110** (100 V V<sub>DSS</sub>, 180 A, 4.5 mΩ R<sub>DS(on)</sub>) instead. Three reasons for the swap:

1. **V<sub>DSS</sub> headroom.** IRFZ44N at 55 V V<sub>DSS</sub> for a 50 V bus + switching spikes is uncomfortably tight. The 1.5KE62A TVS clamps at 84.5 V — well above the IRFZ44N's V<sub>DSS</sub>, meaning a TVS firing event would still cause MOSFET damage. The IRFB4110 at 100 V V<sub>DSS</sub> sits comfortably above the TVS clamp, so the protection chain actually protects.
2. **R<sub>DS(on)</sub> headroom.** 4.5 mΩ vs. 17.5 mΩ is a 4× improvement in conduction loss. At 5 A this is the difference between 0.11 W and 0.44 W per device — small in absolute terms, but it means the MOSFETs run cool enough to skip forced air on a bench prototype.
3. **Gate charge tradeoff.** The IRFB4110's higher current rating comes with ~2× the gate charge of the IRFZ44N (150 nC vs. ~67 nC). With the same TLP250 + 22 Ω gate resistor, transitions take ~2× longer. The firmware compensates with **3 µs dead time** (`PWM_DEAD_TIME_DTG = TIM_DTG_3US_AT_64MHZ`, BDTR.DTG = 0xA0), up from the IRFZ44N's 2 µs. This is documented in the firmware CHANGELOG and Build Guide v4.0 §6.

The IRFZ44N → IRFB4110 substitution is one of the project's more important course corrections — it eliminated a latent BOM hazard (the TVS / V<sub>DSS</sub> mismatch), gave better thermal margin, and only cost a slightly longer dead time.

## What to remember

- For 50 V / 5 kHz inverters, the answer is always MOSFET. No exceptions worth discussing.
- The crossover where IGBTs start to win is around 250 V V<sub>DS</sub> + 20 kHz, but in practice modern Si and SiC MOSFETs keep pushing that frontier higher.
- Check V<sub>DSS</sub> against your TVS clamp voltage. If TVS clamps above MOSFET breakdown, the protection chain is broken.
- When swapping MOSFETs, recompute the gate-charge → switching-time → dead-time chain. The firmware's dead-time value is the most likely thing to need updating.

Related: [Build Guide v4.0 §4 Power stage](../hardware/build-guide-v4.md), [Modulators](../firmware/modulators.md) (for the dead-time constants), and the [iteration-3 narrative](../iteration-history/iteration-3.md) where the MOSFET swap actually happened.
