# First bench session

The linear, single-session walkthrough for putting the populated boards on the bench for the first time and getting all three modulators (STAIR, STAIR_ALT, PSC) verified end-to-end.

This page renders [`firmware/stm32-f303re/FIRST_BENCH_SESSION.md`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/FIRST_BENCH_SESSION.md) verbatim — the file ships in the firmware repository and is the authoritative copy.

> **Headline safety goal:** do not burn a TLP250, do not burn a MOSFET. Every step has explicit pass/fail criteria; **if anything is unexpected, STOP** and consult the [bring-up reference](reference.md) troubleshooting before continuing.

---

{%
  include-markdown "../../firmware/stm32-f303re/FIRST_BENCH_SESSION.md"
  heading-offset=1
  start="## What to have ready at the bench"
%}
