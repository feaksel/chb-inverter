# Bring-up

<figure markdown="span">
  ![Lab power sources during bench test](../assets/images/lab-power-sources-test.jpeg){ loading=lazy width=80% }
  <figcaption>Bench power supplies on a bring-up session — two independent isolated DC sources, one per bridge, plus a separate 15 V for the gate drive.</figcaption>
</figure>

Two documents cover putting the populated boards on the bench:

| Page | When to use it |
|---|---|
| [First bench session](first-session.md) | The first time you bring the new branch up. Linear procedure with explicit pass/fail checkpoints; covers Step 0, Phases 2–7b, Phase 8 of the reference, plus TLP250-protection checks at every step. **Start here.** |
| [Bring-up reference](reference.md) | Comprehensive phase-by-phase reference with what-the-firmware-does, scope captures, UART output, and troubleshooting trees. Consult when the first-session doc doesn't match what you're seeing. |

The procedural reference is also in [Build Guide v4.0 — §12 Bring-up procedure](../hardware/build-guide-v4.md). Where the first-session notes contradict the guide, **the session notes win** — they describe what was actually seen, not what was expected.
