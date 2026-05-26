# Simulink

The 5-level CHB Simulink models and analysis scripts.

| File | What it is |
|---|---|
| [`chb-5level-v1.slx`](chb-5level-v1.slx) | First-pass IPD LS-PWM model with ideal switches. Produced the headline **THD = 4.9 %** figure. |
| [`chb-5level-v2.slx`](chb-5level-v2.slx) | Added IR2110 vs. TLP250 gate-driver behavioural sweep — the simulation that killed the IR2110 path. |
| [`chb-5level-rl-nospike.slx`](chb-5level-rl-nospike.slx) | Adds LC filter + RL load + snubber-tuned switching (no V<sub>DS</sub> spike). |

All three models open in **MATLAB R2023b** (or later) with the **Simscape Electrical** toolbox.

## Run

```matlab
>> open('chb-5level-v1.slx');     % opens the model
>> sim('chb-5level-v1');           % runs simulation
>> thd(simout.OutputVoltage.Data, simout.OutputVoltage.Time(2) - simout.OutputVoltage.Time(1), 50)
ans = 4.9012
```

## Results

Simulation result captures, FFT plots, and THD CSV exports live in `results/` (currently empty — to be repopulated when the team next exports from MATLAB).

## See also

- [Simulation overview in the docs site](https://feaksel.github.io/chb-inverter/simulation/overview/)
- [THD analysis page](https://feaksel.github.io/chb-inverter/simulation/thd-analysis/)
- [Model architecture page](https://feaksel.github.io/chb-inverter/simulation/models/)
