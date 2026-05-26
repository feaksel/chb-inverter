# Simulation

Pre-hardware simulation work that informed the topology and modulation choices.

| Path | Contents |
|---|---|
| [`simulink/`](simulink/) | The 5-level CHB Simulink model (`.slx`) and the analysis scripts that consume its outputs. |
| [`matlab/`](matlab/) | Helper `.m` files used during analysis and report generation. |

The simulation predicted ~4.9% THD at the 5-level output before any LC filtering. That number is the headline result reported in the ELE 401 term report; the validated bench number lives in [`docs/simulation/thd-analysis.md`](../docs/simulation/thd-analysis.md).

> The Simulink work was a design-time aid, not a live model. It is not part of the production firmware or hardware flow.
