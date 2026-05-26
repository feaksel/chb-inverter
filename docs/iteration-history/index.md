# Iteration history

The story of the hardware as it evolved from first board to final demo. Each iteration page documents **what was attempted, what failed, and what was learned** — written honestly, with the failures in plain view rather than smoothed over.

!!! info "Phase 5 placeholder"
    The per-iteration narratives are written in Phase 5 from the firmware CHANGELOG, the prior-iteration KiCad files (where they survive), and the team's own memory of the bench sessions.

## Iterations

| Iteration | Headline | Status |
|---|---|---|
| Iteration 1 | First-pass single dual-bridge layout. IRFZ44N MOSFETs, IPD LS-PWM. | Superseded |
| Iteration 2 | Revised gate-drive routing; surfaced the bootstrap fundamentals. | Superseded |
| Iteration 3 | Exposed the 5V_GND ↔ 50V_GND coupling issue; isolation rework. | Superseded |
| Iteration 4 | Two identical single-bridge modules, IRFB4110, PSC-PWM. | **As-built / demonstrated** |

Where iteration KiCad files have survived, they live in [`hardware/legacy/`](https://github.com/feaksel/chb-inverter/tree/main/hardware/legacy) in the repository.
