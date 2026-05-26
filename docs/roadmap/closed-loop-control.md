# Closed-loop control

!!! info "Phase 5 stub"
    The as-built system is **open loop** — modulation index is set by the operator (UART `MI` command), output voltage is not measured back into the modulator.

The roadmap item is to add output-voltage feedback so the inverter regulates against load variation and DC-bus drift.

## What the team had planned (per ELE 401 interim report)

- **Inner loop** (current control): 5 kHz execution, Proportional-Resonant (PR) controller tuned to 50 Hz, ≈ 1 kHz bandwidth, < 5 ms response.
- **Outer loop** (voltage control): 2 kHz, PI controller, ≈ 100 Hz bandwidth, ≈ 20 ms response.
- **Balancing loop** (DC-link voltage): 100 Hz, active balancing through modulation-index corrections, ±5 % tolerance between modules.

This architecture was specified before the team committed to open-loop demo for the graduation deliverable. The firmware already exposes the sense channels and the `MI` setter; closed-loop is mostly a software task plus a tuned controller, not a hardware change.

## What still needs deciding

- Where the output-voltage feedback comes from. Today the MCP3201 channels sense the DC bus, not the AC output. Adding an isolated AC voltage sense channel is the prerequisite.
- Whether to start with PR (resonant at 50 Hz) or a synchronous-frame PI on the rotating-frame quantities.
- How to detune the PR for stability margin under varying load impedance.
