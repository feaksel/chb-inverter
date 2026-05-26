# PSC vs. LSPWM

!!! info "Phase 5 stub"
    Full content arrives in Phase 5. This page exists so the navigation and cross-links from the glossary and the iteration history resolve.

The team's modulation choice evolved across iterations:

| | What | Result |
|---|---|---|
| Iteration 1–3 | IPD level-shifted PWM | Worked but gave uneven cascade balance, which translated into asymmetric thermal loading. |
| Iteration 4 (as-built) | Phase-shifted carriers | Each bridge sees the same average switching duty; thermal balance and harmonic distribution improve. |

The full argument, with the harmonic content side-by-side and the bench data that backs the choice, lives in [Build Guide v4.0 — §9 Modulators](../hardware/build-guide-v4.md) and is expanded here in Phase 5.

Related: [Modulators reference](../firmware/modulators.md) (Phase 2).
