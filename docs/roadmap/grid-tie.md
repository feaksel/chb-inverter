# Grid tie

!!! info "Phase 5 stub"
    The as-built inverter is **stand-alone** — it drives a passive load with no synchronization or anti-islanding. Grid coupling is non-trivial and outside the graduation deliverable.

The roadmap item is the path to a grid-interactive inverter:

1. **PLL** on the grid voltage to lock the modulator's reference phase to the utility frequency (50 Hz nominal in Türkiye, ±0.5 Hz operational band).
2. **Anti-islanding** detection that drops the output if the grid disappears. Active or passive method per the regional standard.
3. **Soft start** so the inverter doesn't slam current onto the grid at the start of a session.
4. **Compliance** — IEEE 1547-2018 for distributed energy resources, plus the local Turkish utility-interconnection rules.

## Hardware implications

- The LC output filter ([roadmap item](lc-filter.md)) is a prerequisite — grid tie without filtering injects the cascade-step harmonics into the utility network, which fails every interconnection standard immediately.
- Additional sensing: grid voltage (isolated), grid current (separate from the bridge return current sensor), zero-crossing detector.
- Physical disconnect: a contactor that the firmware can drop within ms of detecting anti-island.

## Why this is graduation-out-of-scope

Grid coupling carries real safety implications (linemen, utility equipment, neighbouring loads). The graduation deliverable demonstrates the **inverter** part of the system; the **grid-side integration** is a separate body of work that deserves its own project.
