# Simulink

The 5-level CHB Simulink model and its analysis scripts.

| File | Purpose |
|---|---|
| `chb-5level.slx` | The full 5-level cascaded H-bridge model, PSC-PWM modulation, ideal switches. **(To be added in Phase 4.)** |
| `thd-analysis.m` | Loads simulation output, computes the FFT, prints the per-harmonic content and the total THD figure. |
| `results/` | Exported FFT plots and the numerical THD output (4.9% pre-filter at the headline operating point). |

Open the `.slx` in Simulink R2023b or later. The model uses only blocks from the Simscape Electrical toolbox.

## How the bench validation compares

The simulation was an idealized design-time aid: ideal switches, no parasitic inductance, no dead time. The bench results differ in expected ways — see [`../../docs/simulation/thd-analysis.md`](../../docs/simulation/thd-analysis.md) for the side-by-side comparison once measurements are imported.
