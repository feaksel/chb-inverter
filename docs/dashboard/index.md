# Dashboard

<figure markdown="span">
  ![Lab testing setup — the dashboard running live alongside the bench rig](../assets/images/lab-testing-setup-hero.jpeg){ loading=lazy width=80% }
  <figcaption>The PySide6 operator dashboard running on the bench PC during a live PSC session. The dashboard handles every command the firmware supports plus 20 Hz telemetry visualization, fault display, and replay-log capture.</figcaption>
</figure>

The PySide6 operator dashboard that talks to the STM32 over UART.

| Page | What it covers |
|---|---|
| [Overview](overview.md) | Architecture, modules, the data model, safety design. |
| [Installation](installation.md) | `py -3.11 -m venv …` setup, pinned versions, troubleshooting. |
| [Operator workflow](operator-workflow.md) | A typical session — bring up, configure, arm, run, stop, recover. |

Source: [`firmware/stm32-f303re/dashboard/`](https://github.com/feaksel/chb-inverter/tree/main/firmware/stm32-f303re/dashboard) (imported via subtree in Phase 2).

The dashboard's own README is in the source tree at [`firmware/stm32-f303re/dashboard/README.md`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/dashboard/README.md).
