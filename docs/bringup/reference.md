# Hardware bring-up reference

The comprehensive phase-by-phase bring-up reference. Companion to Build Guide v4.0 §12 — the guide covers what to *do* on the hardware; this document covers what the **firmware** does at each step, what to expect on UART, what scope captures should look like, and the troubleshooting trees.

This page renders [`firmware/stm32-f303re/HARDWARE_BRINGUP.md`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/HARDWARE_BRINGUP.md) verbatim — the file ships in the firmware repository and is the authoritative copy.

> **Read this top to bottom. Do not skip phases.** Each phase builds confidence for the next. Skipping risks damaging components that took weeks to source.
>
> For a faster, focused single-session walkthrough, use the [first bench session](first-session.md) page instead. Come back here when something doesn't match the first-session doc.

---

{%
  include-markdown "../../firmware/stm32-f303re/HARDWARE_BRINGUP.md"
  heading-offset=1
  start="## Step 0 — Getting the firmware onto the board"
%}
