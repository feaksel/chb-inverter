---
title: Glossary
---

# Glossary

Short definitions for terms used across this site. Not exhaustive — when in doubt, the [Build Guide v4.0](../hardware/build-guide-v4.md) is authoritative.

| Term | Meaning |
|---|---|
| **CHB** | Cascaded H-Bridge. A multilevel inverter topology where multiple H-bridges have their outputs summed. |
| **PSC-PWM** | Phase-Shifted Carrier Pulse-Width Modulation. Each bridge's carrier is shifted by 360°/N for N bridges, distributing switching events evenly across the cycle and giving better cascade balance than IPD. The as-built default. See [PSC vs. LSPWM](psc-vs-lspwm.md). |
| **IPD LS-PWM** | In-Phase Disposition Level-Shifted PWM. Earlier modulation strategy used in the project; superseded by PSC after the bridge-loss asymmetry showed up on the bench. |
| **STAIR / STAIR_ALT** | Two non-PWM modulators the firmware also ships — static-level selection rather than real PWM. STAIR is the known-good fallback; STAIR_ALT alternates which bridge carries the ±1 step. |
| **Dead time** | The deliberate gap between turning off one MOSFET of a half-bridge and turning on the other, preventing shoot-through. 3 µs on the as-built IRFB4110 stage; was 2 µs on the older IRFZ44N stage. |
| **Bootstrap** | The capacitor + diode arrangement that supplies the high-side gate driver's reference. Works for ground-referenced bridges; fundamentally cannot drive a floating CHB bridge. See [bootstrap fundamentals](bootstrap-fundamentals.md). |
| **TLP250** | Optically isolated gate driver (2.5 kV galvanic, LED → photodetector + MOSFET output stage) used on this project for every gate. Replaces the IR2110 bootstrap path that doesn't work in CHB. |
| **IR2110** | High-and-low-side bootstrap gate driver. Evaluated in Simulink for this project; the simulation collapsed on the upper bridge because bootstrap can't supply gate voltage referenced to a floating V<sub>S</sub>. Not used in the as-built. |
| **B0515S** | 1 W isolated 5 V → 15 V DC-DC converter; one per bridge, supplies the TLP250 rail without sharing ground with the controller. |
| **Isolated sensing** | ADC readings are taken on the floating bridge ground and crossed to the controller ground via opto-isolation (6N137 per signal). Keeps the controller from being damaged by bridge-side faults. |
| **SPIINV** | Runtime firmware command that sets a per-line inversion mask (bit 0 = SCK, bit 1 = CS, bit 2 = MISO) so the 6N137 inverters can be compensated without reflashing. `SPIINV 7` = all three lines inverted = standard one-6N137-per-line wiring. |
| **THD** | Total Harmonic Distortion — the fraction of the waveform's RMS that lies in harmonics other than the fundamental. Lower is better. Simulation predicted ~4.9% pre-filter at the headline operating point. |
| **MCP3201** | 12-bit successive-approximation ADC, DIP-8, SPI. Used for the isolated bridge-side voltage/current sensing, bit-banged at ≈ 140 kHz. |
| **ACS712** | Hall-effect-based current sensor, SOIC-8. One per bridge, on the bridge return. |
| **IRFB4110** | The N-channel power MOSFET used in the as-built single-bridge v4 modules. 100 V V<sub>DSS</sub>, 4.5 mΩ R<sub>DS(on)</sub>, 180 A. Replaces the IRFZ44N (55 V) from build-guide v3.1. |
| **IRFZ44N** | The build-guide-v3.1 MOSFET (55 V, 17.5 mΩ). Replaced by the IRFB4110 in iteration 4 for V<sub>DSS</sub> headroom and to resolve the TVS-clamp / V<sub>DSS</sub> mismatch. |
| **6N137** | High-speed (10 Mbit/s) digital optocoupler. One per SPI signal per island. Inverts (LED on → output low); the firmware compensates via SPIINV. |
| **VNOM** | Operator-set nominal per-bridge bus voltage (5–60 V). The firmware derives all DC-bus protection thresholds (UV, OV, IMBAL) as fractions of VNOM, so the inverter can be safely bench-tested below the 50 V design point. |
| **N-of-M debounce** | The firmware protection's noise-rejection scheme — a fault must be observed in 3 consecutive 1 kHz sensor scans (3 ms) before it trips. Single noisy samples don't trip. |
| **STM32 F303RE** | The MCU on the Nucleo-64 board used as the controller. Runs at 64 MHz from HSI/2 × PLL — no external crystal. |
| **Cereyan Hacıları** | Project team name. Literally "Current Pilgrims" in Turkish. |
