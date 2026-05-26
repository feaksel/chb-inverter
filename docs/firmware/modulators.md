# Modulators

Three modulators ship in the firmware. The active one is selected at runtime over UART (`MOD STAIR|PSC|STAIR_ALT`) without reflashing.

## Comparison

| Modulator | What it is | When to use it |
|---|---|---|
| **`STAIR`** *(default boot)* | 500 Hz quantize-to-5-levels staircase. Bridge 1 always carries the ±1 step. **Not real PWM** — each level is held statically with only ≈ 1 % bootstrap-refresh switching. | Known-good fallback, immediately produces 5 distinct levels on the scope. Has a built-in bridge-1 thermal imbalance — use only for short demos. |
| **`PSC`** | Unipolar phase-shifted carrier SPWM at the configured switching frequency (default 5 kHz). TIM8 CNT preset to `PWM_PERIOD/2` at config time gives the 90° carrier shift between the two cells. Bridge 1 and bridge 2 carry equal switching load. | **The project deliverable.** Use for any sustained run. The carrier shift gives natural 5-level output and thermal balance. |
| **`STAIR_ALT`** | Same staircase output as STAIR — but the bridge that carries the ±1 step alternates each time the level is re-entered. | Hard-fallback if PSC's 90° shift cannot be made to work on the bench. Fixes the thermal imbalance without changing the visible output shape. Still not real PWM. |

## Why PSC over the build guide's IPD LS-PWM

Build Guide v3.1 §1.2 specified IPD LS-PWM. The firmware deviates: it runs **PSC** instead. The reason — captured in the firmware CHANGELOG entry for `pwm-rewrite-configurable`:

> IPD has an inherent bridge-loss asymmetry that needs an additional bridge-swap each fundamental cycle to even out. PSC is naturally bridge-balanced.

This deviation was accepted by the team and is reflected in Build Guide v4.0 §9.

## PSC phase-lock diagnostic

PSC depends on the TIM8 ↔ TIM1 counter offset being exactly `ARR/2`. If the offset drifts (e.g. because something clobbers `TIM8->CNT` after `CR1_CEN` is set), PSC degrades to 3-level output and the cascade-output spec fails.

To make the failure visible without a scope, the firmware reads back the actual counter offset after every `Pwm_SetConfig` call and exposes two diagnostics on the `$C` line:

- `cntoff=<ticks>` — the measured TIM8 - TIM1 counter delta.
- `lock=OK|BAD` — `OK` if `cntoff` is within `±5` ticks of `ARR/2`, `BAD` otherwise.

An operator who sees `lock=BAD` on the dashboard knows immediately that PSC won't produce 5-level output, and can switch to `STAIR_ALT` as a hard fallback while debugging.

The hardening fix (writing `TIM8->CNT` *after* `CR1_CEN` is set so the post-UG sequence cannot clobber it) is in [`Core/Src/pwm_modulator.c::timer_apply_period_and_phase`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/Core/Src/pwm_modulator.c).

## Bridge isolation (`BRIDGE B1` / `BRIDGE B2`)

For per-bridge bring-up tests, `BRIDGE B1` forces bridge 2 into freewheel (both legs at LOW clamp duty, contribution ≈ 0 V) and vice versa. The active bridge produces its normal 3-level (−Vdc / 0 / +Vdc) swing.

Freewheel rather than high-Z is used deliberately: disabling the timer outputs entirely (CCxE=0) would let the output float and the body diodes potentially conduct, which is worse than a controlled freewheel.

## Duty clamps

| Modulator | LOW clamp | HIGH clamp |
|---|---:|---:|
| STAIR     | 0.01 | 0.95 |
| STAIR_ALT | 0.01 | 0.95 |
| PSC       | 0.05 | 0.95 |

The 95 % high clamp ensures the low-side gets ≥ 5 % on-time per period to refresh the bootstrap cap. PSC's higher 5 % low clamp is because PSC actively modulates both legs symmetrically — both clamps bind on both legs. STAIR's "off" leg sits at ~1 % duty (HS almost off, LS almost on); bootstrap is fine on that leg and the 5 % rule only constrains the "on" leg's HS.

## Defaults

The boot defaults live in [`Core/Inc/pwm_config.h`](https://github.com/feaksel/chb-inverter/blob/main/firmware/stm32-f303re/Core/Inc/pwm_config.h):

| | Value |
|---|---|
| Modulator | `STAIR` (the known-good fallback) |
| Switching frequency | 500 Hz |
| Fundamental | 50 Hz |
| Modulation index | 0.95 |
| Bridge select | `BOTH` |
| Sine LUT size | 256 samples |
| Dead-time | 3 µs (`PWM_DEAD_TIME_DTG = TIM_DTG_3US_AT_64MHZ`, `BDTR.DTG = 0xA0`) — sized for the IRFB4110's ~150 nC gate charge |
| Bootstrap precharge | 6 ms (3 PWM periods at 500 Hz) |

After the team's PSC bench validation, flip `PWM_DEFAULT_MODULATOR` to `MODULATOR_PSC` so a fresh boot runs the as-built configuration without a manual `MOD PSC`.
