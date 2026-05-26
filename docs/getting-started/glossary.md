# Glossary

Short definitions for terms used across this site. Not exhaustive — when in doubt, the [Build Guide v4.0](../hardware/build-guide-v4.md) is authoritative.

| Term | Meaning |
|---|---|
| **CHB** | Cascaded H-Bridge. A multilevel inverter topology where multiple H-bridges have their outputs summed. |
| **PSC-PWM** | Phase-Shifted Carrier Pulse-Width Modulation. Each bridge's carrier is shifted by 360°/N for N bridges, distributing switching events evenly across the cycle and giving better cascade balance than IPD. |
| **IPD LS-PWM** | In-Phase Disposition Level-Shifted PWM. Earlier modulation strategy used in the project; superseded by PSC. See [PSC vs. LSPWM](../design-notes/psc-vs-lspwm.md). |
| **Dead time** | The deliberate gap between turning off one MOSFET of a half-bridge and turning on the other, preventing shoot-through. |
| **Bootstrap** | The capacitor + diode arrangement that supplies the high-side gate driver's reference. See [bootstrap fundamentals](../design-notes/bootstrap-fundamentals.md). |
| **Isolated sensing** | ADC readings are taken on the floating bridge ground and crossed to the controller ground via opto-isolation (here: 6N137). Keeps the controller from being damaged by bridge-side faults. |
| **THD** | Total Harmonic Distortion — the fraction of the waveform's RMS that lies in harmonics other than the fundamental. Lower is better. Simulation predicted ~4.9% pre-filter at the headline operating point. |
| **MCP3201** | 12-bit successive-approximation ADC, DIP-8, SPI. Used for the isolated bridge-side voltage/current sensing, bit-banged. |
| **ACS712** | Hall-effect-based current sensor, SOIC-8. One per bridge, on the bridge return. |
| **IR2110** | High-and-low-side gate driver, used per H-bridge for both legs. |
| **IRFB4110** | The N-channel power MOSFET used in the as-built single-bridge v4 modules. |
| **STM32 F303RE** | The MCU on the Nucleo-64 board used as the controller. |
| **Cereyan Hacıları** | Project team name. Literally "Current Pilgrims" in Turkish. |
