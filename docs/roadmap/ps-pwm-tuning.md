# PSC-PWM tuning

!!! info "Phase 5 stub"
    Per-item roadmap content is written in Phase 5. The item below is the headline; the page will expand it.

PSC-PWM is the as-built default and was bench-validated. The roadmap item is **further tuning** beyond what was demonstrated:

- Sweep the switching frequency (5 kHz today; the firmware supports 100 Hz – 20 kHz) and characterize how THD, switching loss, and thermal balance trade off.
- Compare carrier phase shift values (90° today, the textbook value for 2 cells) against measured cascade balance under partial bridge mismatch.
- Add a closed-loop carrier-lock that detects `lock=BAD` from the `$C` line and either auto-falls back to `STAIR_ALT` or re-attempts the phase shift.

Tooling exists: the firmware exposes `cntoff` and `lock` diagnostics on every `$C` config line ([see modulators](../firmware/modulators.md)). The dashboard surfaces them. The bench just needs a structured sweep plan.
