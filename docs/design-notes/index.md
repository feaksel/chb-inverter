# Design notes

Standalone explanations of the engineering decisions that shaped the as-built design. Each note answers a single "why did we do it this way?" question.

!!! info "Phase 5 placeholder"
    Content is synthesized from the firmware CHANGELOG, the ELE 401 term report, and the prior-chat design discussion in Phase 5.

## Planned notes

| Note | Question it answers |
|---|---|
| Bootstrap fundamentals | How the high-side gate driver gets a reference, and what goes wrong when it doesn't. |
| CHB isolation | Why GND_HV must float, and what specifically breaks when it doesn't. |
| PSC vs. LSPWM | The cascade-balance argument that drove the switch from IPD to phase-shifted carriers. |
| IGBT vs. MOSFET | The crossover analysis from the build guide — at what switching frequency and current does each win. |
| Grounding fix | The 5V_GND ↔ 50V_GND coupling issue, why it bit us, and how it was resolved on the populated boards. |
