# Bootstrap fundamentals

!!! info "Phase 5 stub"
    Full content arrives in Phase 5. This page exists so the navigation and cross-links from the glossary and the iteration-history resolve.

The bootstrap arrangement on the IR2110 high-side driver — diode, capacitor, and the timing constraints that govern when the bootstrap supply is *refreshed* — is the single most surprising thing for first-time gate-drive designers. Two of the earlier iterations had bootstrap-related bring-up issues; this page documents the failure modes and the fix that landed in single-bridge v4.

Full discussion comes in Phase 5 from:
- The firmware CHANGELOG entries that called out bootstrap-related fixes.
- [Build Guide v4.0 — §6 Gate drive](../hardware/build-guide-v4.md).
- The iteration-2 and iteration-3 bench notes.
