# FSM Notes

```text
                  sensor fault / UV / OV / OC / imbalance
 BOOT --> IDLE ----------------------------------------------+
          |                                                  |
          | START                                            v
          v                                             +---------+
      PRECHARGE -- g_precharge_done --> RUN -- fault --> | FAULT  |
          |                              |                +---------+
          | STOP                         | STOP                |
          v                              v                     | CLEAR
         IDLE <------------------------- IDLE <----------------+
```

`BOOT` initializes hardware, runs the ADC self-test, and chooses the most
capable available sensing mode. `IDLE` keeps both advanced-timer MOE bits low
and accepts commands. `PRECHARGE` enables MOE and lets the existing PWM ISR run
the bootstrap precharge. `RUN` keeps PWM enabled and checks protection after
each 1 kHz sensor scan. `FAULT` clears MOE, latches fault bits, and requires
`CLEAR` after the active condition is gone.

## Modes

`FULL` uses DC1, DC2, and current sensing. It enables undervoltage,
overvoltage, overcurrent, and DC-bus imbalance protection.

`DC_ONLY` uses both DC-bus sensors. It enables undervoltage, overvoltage, and
imbalance protection, but current telemetry is `NAN` and overcurrent protection
is disabled.

`CUR_ONLY` uses only the output current sensor. It enables overcurrent
protection and reports DC-bus channels as `NAN`.

`OPEN` uses no sensors. All protection is disabled, and the firmware prints a
warning whenever the mode is selected or started.

`DC1` uses bridge 1 DC sensing and optionally current sensing when available.
It protects bridge 1 against undervoltage/overvoltage and adds overcurrent
protection only if the current ADC passed self-test.

`DC2` uses bridge 2 DC sensing and optionally current sensing when available.
It protects bridge 2 against undervoltage/overvoltage and adds overcurrent
protection only if the current ADC passed self-test.
