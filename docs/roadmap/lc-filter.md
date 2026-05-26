# LC output filter

!!! info "Phase 5 stub"
    The team simulated two LC filter values during the design phase ([THD analysis](../simulation/thd-analysis.md)) but did **not** build a physical filter — the demonstration ran the inverter into a resistive load and the 5-level cascade is visible directly on the scope.

The roadmap item is to build the LC stage so the deployed system can drive non-trivial loads (transformer, motor, grid) without injecting unfiltered cascade-step harmonics into the network.

## Two values that were simulated

| Variant | L | C | f<sub>c</sub> |
|---|---:|---:|---:|
| Initial design (R load) | 15 mH | 22 µF | 325 Hz |
| Revised for RL load | 15 mH | 30 µF | 237 Hz |

## What needs doing

- Pick the f<sub>c</sub>: tighter f<sub>c</sub> attenuates the 5 kHz switching harmonics harder but soft-couples to the dynamic response. The 237 Hz value is the team's most-recent recommendation per the LC discussion notes.
- Source the L: 15 mH at 10 A means a core with at least that much inductance under DC bias — not trivial in a bench-friendly package.
- Source the C: 30 µF at the inverter output peak (≈ 100 V) wants a polypropylene film cap, not electrolytic.
- Layout: the filter belongs between the cascade-output node and the load, with the cap return going back to the load's return, not to the inverter ground.
