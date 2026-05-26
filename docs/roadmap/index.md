# Roadmap

Future work — what we'd pick up after the graduation deliverable, in roughly the order we'd recommend tackling it. Drawn from [Build Guide v4.0 §15](../hardware/build-guide-v4.md).

!!! info "Phase 5 placeholder"
    Per-topic pages are filled out in Phase 5 with the *why this is next*, *how hard it is*, and *what changes if we do it*.

## Tracks

| Track | One-liner |
|---|---|
| PS-PWM tuning | Already implemented — this page covers further tuning beyond what was demonstrated. |
| LC filter | A staged LC filter on the inverter output to drop THD further before any load. |
| Closed-loop control | Output-voltage feedback into the modulator — currently open-loop. |
| Grid tie | Synchronization, anti-islanding, and the safety implications of grid coupling. |
| Thermal enclosure | The boards are bench-thermally-balanced; an enclosed deployment needs forced air or a heatsink redesign. |
| Product path | What turning the project from a graduation deliverable into a product would actually take. |

The [experimental tracks](https://github.com/feaksel/chb-inverter/tree/main/experimental) (RISC-V SoC, FPGA controller) are deliberately not in this list — they have no validated path to the as-built hardware.
