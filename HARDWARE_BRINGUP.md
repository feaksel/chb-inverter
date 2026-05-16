# Hardware Bringup — 5-Level CHB Inverter

Companion to the team's `CHB_Inverter_Build_Guide_v3_1.pdf` section 6
("Test Procedures"). The guide covers what to *do* on the hardware; this
document covers what the **firmware** does at each step, the UART
commands to send, the telemetry/scope outputs to expect, and what to do
when something is off.

**Read this from top to bottom. Do not skip phases.** Each phase builds
confidence for the next. Skipping risks damaging components that took
weeks to source.

---

## Pre-bringup checklist

- [ ] Branch `pwm-rewrite-configurable` flashed (verified by `$C,...` line
      appearing on UART after boot — older firmware doesn't emit `$C`).
- [ ] Build guide v3.1 Phase 1 (continuity check, no power) passed.
- [ ] Dashboard installed (`dashboard/.venv` exists with PySide6, pyserial,
      pyqtgraph). Optional but strongly recommended.
- [ ] ST-LINK VCP enumerated (Device Manager → Ports → STMicroelectronics
      STLink Virtual COM Port → note COM number).
- [ ] Terminal program ready as backup (PuTTY, Tera Term, or screen): 115200 8N1.
- [ ] Bench supplies set to current-limit mode, output OFF.
- [ ] **Auto-start awareness:** the firmware auto-issues `START` 3 s after
      boot if no UART activity. To avoid surprise PWM during bench work,
      either keep the dashboard / terminal attached or pull the Nucleo's
      reset line low until you're ready.

---

## Phase 0 — Firmware sanity (just flashed, no power stages)

**Goal:** confirm firmware boots, UART works, sensors self-test correctly,
defaults are loaded.

**Setup:** Nucleo powered via USB only. Power stages disconnected (or
unpowered). No DC bus, no gate drive 15 V.

**Steps:**
1. Open dashboard (`py -3 dashboard/run_dashboard.py`) or terminal,
   connect to ST-LINK VCP at 115200 8N1.
2. Press the Nucleo's black reset button.
3. Within 3 s of boot, type any character (e.g. press Enter) to cancel
   auto-start. The dashboard's command pane does this implicitly when you
   click any button.

**Expected UART output within ~1 second of reset:**
```
$A,BOOT_SELF_TEST_DONE
$C,mod=STAIR,fsw=500,bridge=BOTH,ffund=50.00,mi=0.95
$E,MODE_DEMOTED                              ← only if some sensors absent
$E,WARNING_OPEN_LOOP_NO_PROTECTION           ← only if no sensors at all
$T,<ms>,IDLE,<mode>,0x00,<vdc1>,<vdc2>,<iout>,0*<chk>   ← starts at 20 Hz
```

If `$A,AUTO_START` appears: you missed the 3 s window. Send `STOP`
immediately, then reset.

**Verify:**
- [ ] `$C` line present and matches defaults exactly.
- [ ] `$T` telemetry frames arrive at ~20 Hz.
- [ ] `STATUS` command returns a single `$S,...` line with the same fields.
- [ ] `HELP` lists all commands including the new ones (`MOD`, `FSW`,
      `BRIDGE`, `FFUND`, `CONFIG`, `RESCAN`).
- [ ] If sensors connected: `vdc1`, `vdc2` show non-NAN values (DC bus is
      0 V, so expected ≈ 0 V — but with sensors floating you may see noise).
- [ ] No unexpected `$E,...` errors or `$F,...` faults.

**Troubleshooting:**
- **No UART output at all:** wrong COM port / wrong baud / ST-LINK VCP
  driver not installed.
- **Garbled UART output:** baud mismatch (must be 115200) or wrong UART
  framing (must be 8 data bits, no parity, 1 stop bit).
- **`$E,WARNING_OPEN_LOOP_NO_PROTECTION`:** none of the three MCP3201
  ADCs returned valid samples in self-test. Most likely the sensing
  island isn't powered yet (B0515S off) — that's expected at this phase.
- **`$E,MODE_DEMOTED`:** at least one ADC is missing/broken but others
  work. Continue — protection still works for available channels.
- **`$T` frames not arriving:** check FSM state — should be IDLE not
  BOOT. If stuck in BOOT, the sensing self-test hung (likely SPI wiring).

---

## Phase 1 — Continuity (no power)
Follow build guide section 6 Phase 1. No firmware involvement.

---

## Phase 2 — Gate drive test with external 15 V

**Goal:** confirm each TLP250 + MOSFET gate channel works individually,
*before* applying high voltage. Verifies pin assignments and dead-time.

**Setup:** Per build guide Phase 2. External 15 V bench supply (200 mA
limit) connected directly to **one bridge's** `+15V_Drive` and
`Drive_GND` rails, B0515S disconnected. Nucleo powered via USB. **No DC
bus voltage.**

**Strategy:** we use the per-bridge isolation feature (new on this branch)
to drive *only* the bridge under test, and run STAIR at the default
500 Hz so each gate has a clear, slow waveform on the scope.

### 2a. Bridge 1 channels

1. Reset Nucleo, immediately send any UART byte to cancel auto-start.
2. Send commands:
   ```
   MOD STAIR
   FSW 500
   BRIDGE B1
   MI 0.5
   START
   ```
3. Scope each of bridge 1's 4 MOSFET gates (Vgs, gate vs source):
   - **Q1 HS, Q3 HS:** should switch between ~0 V and +14–15 V at the
     50 Hz fundamental rhythm (NOT 500 Hz — STAIR holds each level for
     many PWM periods).
   - **Q2 LS, Q4 LS:** complementary to their HS partners. When HS is
     high, LS is low, and vice versa. Visible 2 µs dead-time on every
     transition.
4. Measure DC current draw from the 15 V supply: should be ~20–50 mA per
   bridge depending on switching activity.
5. `STOP` when done with bridge 1.

**Verify:**
- [ ] All 4 gates show clean square waves, no ringing, no missing edges.
- [ ] Dead-time visible on the LS-to-HS and HS-to-LS transitions (~2 µs).
- [ ] No simultaneous HS+LS on the same leg at any point (would be
      shoot-through).
- [ ] Bridge 2's gates (Q5–Q8) should be **silent** — all four sit in the
      freewheel state (HS off, LS on) for the entire test.

### 2b. Bridge 2 channels
1. `STOP`, `BRIDGE B2`, `START`.
2. Repeat the gate measurements on bridge 2's MOSFETs (Q5–Q8). Bridge 1
   should now be silent.

**Troubleshooting:**
- **A gate stays at 0 V even when its leg should be switching:** that pin
  is not actually driven by the firmware. Most likely wired to the wrong
  STM32 pin. Check against the actual firmware pin map:
  - PWM_1H = PA8 (TIM1_CH1), PWM_1L = PA7 (TIM1_CH1N)
  - PWM_2H = PA9 (TIM1_CH2), PWM_2L = **PA12** (TIM1_CH2N) ← guide says PA10, wrong
  - PWM_3H = PB6 (TIM8_CH1), PWM_3L = PB3 (TIM8_CH1N)
  - PWM_4H = PB8 (TIM8_CH2), PWM_4L = PB0 (TIM8_CH2N) ← guide says PC6–9, wrong
- **Gate switches but Vgs amplitude is <10 V:** bootstrap cap not charging.
  Check UF4007 orientation and the 10 µF cap.
- **HS and LS both high simultaneously (any duration):** dead-time
  failure → catastrophic shoot-through risk. Stop everything, check
  `PWM_DEAD_TIME_DTG` in [pwm_modulator.c](Core/Src/pwm_modulator.c).
- **Some bridge gates switch when `BRIDGE B1` is set:** bridge isolation
  bug. Send `CONFIG` to verify firmware actually got the `BRIDGE B1`
  command. Should report `bridge=B1`.

---

## Phase 3 — B0515S isolated supply test
Follow build guide section 6 Phase 3. No firmware involvement beyond
keeping the inverter in `IDLE` (i.e. send `STOP` if PRECHARGE/RUN is
active, or just don't `START`).

---

## Phase 4 — Sensing island + **MCP3201 decode verification**

**Goal:** confirm the bit-banged SPI is decoding ADC counts correctly.
This is where the `>> 3` vs `>> 1` question gets settled empirically.

**Setup:** B0515S supplies running (Phase 3 passed). DC bus terminals
accessible but bus capacitors NOT charged (or use a small bench supply,
NOT the 50 V rail).

**Steps:**
1. Reset Nucleo, cancel auto-start.
2. With DC bus at 0 V and current sensor unloaded, send `STATUS`.
3. Note the displayed `vdc1`, `vdc2`, `iout` values.
4. Apply a small known voltage to bridge 1's DC input — start with **5 V**
   from a bench supply (current-limited to 100 mA). `STATUS`.
5. Increase to 10 V, 20 V, 30 V in steps. `STATUS` at each step.

**Expected values:**

| Input | `vdc1` should read | If you see ~64 V instead |
|---|---|---|
| 0 V | 0.0–0.5 V (noise floor) | shift is `>> 1`, see fix below |
| 5 V | 4.7–5.3 V | shift is `>> 1` |
| 10 V | 9.5–10.5 V | shift is `>> 1` |
| 30 V | 29–31 V | shift is `>> 1` |

Resolution at the divider settings is ~0.25 V/count, so error of
~0.5 V at any value is normal.

**Verify:**
- [ ] `vdc1` tracks the bench supply linearly within ±5 %.
- [ ] `vdc2` similarly when you move the test supply to bridge 2's input.
- [ ] `iout` reads close to 0 A with no load (within ±0.5 A is normal
      for an unconnected ACS712 input).
- [ ] No new `$E,...` errors appear during the test.

**If the MCP3201 decode is wrong** (readings ~8× too high or stuck near
mid-scale):
1. Open [Core/Src/spi_mcp3201.c](Core/Src/spi_mcp3201.c) lines 132–150.
2. Change all three `>> 3` to `>> 1`.
3. Rebuild and re-flash.
4. Repeat Phase 4 — readings should now track input linearly.
5. Note this in CHANGELOG as guide section 7.3 documentation needing v3.2.

**Other failures:**
- **All three channels read the same value:** SPI MISOs are wired
  together or one MISO is shorting the others.
- **One channel reads NAN consistently:** that ADC's `available` flag
  went to 0 in self-test. Check its CS line and the 6N137 optocoupler
  for that channel. Send `RESCAN` after fixing.
- **Readings jitter wildly (±10 V):** ground loop. The sensing island
  ground (GND_Island) should be tied to the bridge's local floating
  ground via the 78L05 only — *not* to system ground.

---

## Phase 5 — Low-voltage power test (STAIR at 500 Hz, 10 V bus)

**Goal:** end-to-end test of the OLD bench-validated PWM path on the
fully assembled hardware, at a voltage low enough that mistakes don't
destroy anything.

**Setup:** Per build guide Phase 5. Both bridges' DC inputs at 10 V
(current-limited to 2 A). Load = 100 Ω resistor or 60 W incandescent
bulb in series with the ACS712.

**Steps:**
1. Reset Nucleo, cancel auto-start.
2. `CONFIG` — confirm `mod=STAIR,fsw=500,bridge=BOTH,ffund=50.00,mi=0.95`.
3. `STATUS` — confirm both DC buses read ~10 V, iout ≈ 0 A.
4. `START`. Look for `$A,START`, then `$A,RUN` after ~6 ms precharge.
5. Scope the AC output (Node_X1 to Node_Y2) → expect a 5-level
   staircase swinging between roughly ±20 V at 50 Hz.
6. Watch telemetry. `iout` should swing sinusoidally with peak ~0.2 A
   (for 100 Ω load, 20 V/100 Ω = 0.2 A).
7. Run 5 minutes. Touch-test the bridge MOSFET heatsinks (with the back
   of your hand — never grip): you should already be able to feel that
   bridge 1's heatsink runs noticeably warmer than bridge 2's. **This is
   the concern #8 imbalance** that PSC fixes.
8. `STOP`.

**Verify:**
- [ ] AC output is a clean 5-level staircase, not 3-level (would mean
      one bridge isn't switching).
- [ ] No fault trips during the 5-minute run.
- [ ] `vdc1` and `vdc2` stay within 1 V of each other under load.
- [ ] Bridge 1's heatsink is warmer than bridge 2's (expected baseline
      to improve with PSC).

---

## Phase 6 — Single-bridge isolation test (new on this branch)

**Goal:** validate the `BRIDGE B1` / `BRIDGE B2` test mode. Use it to
characterize each bridge independently, e.g. when chasing a thermal
hotspot or a gate-drive marginality.

**Setup:** Same as Phase 5 (10 V bus, 100 Ω load).

**Steps for bridge 1 in isolation:**
1. `STOP` (if running).
2. `BRIDGE B1` — wait for `$A,BRIDGE B1` and `$C,...,bridge=B1,...`.
3. `START`.
4. Scope the cascaded AC output → expect a **3-level** output (-10 V / 0 / +10 V)
   instead of 5-level, because bridge 2 contributes 0 V.
5. Bridge 2's MOSFETs should be cold (only LS on, no switching).
6. `STOP`.

**Steps for bridge 2:**
1. `BRIDGE B2`, `START`.
2. Scope output → same 3-level shape, but now bridge 1 is silent.
3. `STOP`.

**Return to cascaded operation:**
1. `BRIDGE BOTH`, `START` → 5-level again.

**Verify:**
- [ ] Output amplitude in single-bridge mode is roughly half of cascaded
      mode (±10 V vs ±20 V at 10 V bus).
- [ ] Active bridge's MOSFETs warm up similarly to before; inactive
      bridge stays at ambient (only LS conducting freewheel current, ~0).
- [ ] Switching back to `BRIDGE BOTH` returns to 5-level output.

**Use cases:**
- **Diagnosing a hot MOSFET:** isolate the offending bridge, see if heat
  is from switching or conduction (turn MI down — if it cools, it was
  switching loss; if it stays hot, conduction).
- **Verifying one bridge before adding the other:** if you've replaced a
  failed MOSFET on bridge 2, run `BRIDGE B2` first to confirm it's
  healthy before reconnecting to the cascade.

---

## Phase 7 — Full voltage on STAIR (50 V bus)

Per build guide section 6 Phase 6. Same firmware commands as Phase 5,
just at 50 V instead of 10 V.

**Verify:**
- [ ] AC output = 5-level staircase swinging ±100 V.
- [ ] No fault trips during ramp-up (10 → 20 → 30 → 40 → 50 V).
- [ ] THD < 5 % (if your scope supports FFT).
- [ ] Bridge 1 heatsink temperature after 15 min — log it for the PSC
      comparison in Phase 8.

---

## Phase 8 — PSC switchover and thermal comparison (the headline test)

**Goal:** prove that PSC fixes the bridge-1 thermal imbalance.

**Setup:** Same as Phase 7 (50 V bus, rated load). Bridge 1 heatsink
temperature from end of Phase 7 noted.

**Steps:**
1. `STOP` (if running).
2. Let the bridges cool to ambient (5 min, or use a fan).
3. Switch to PSC:
   ```
   MOD PSC
   FSW 5000
   ```
   Expect `$A,MOD PSC`, `$C,...,mod=PSC,fsw=5000,...`.
4. `START`.
5. Scope the AC output:
   - Should be a high-frequency PWM (5 kHz carrier) that LC-filters to a
     50 Hz sine. **It will not look like a staircase** — that's correct.
   - Average voltage profile (use scope's average mode or low-pass it)
     should still trace a clean 50 Hz sine swinging ±100 V.
6. Scope **two gates simultaneously**: PWM_1H (PA8) and PWM_3H (PB6).
   Both should switch every 200 µs (5 kHz). Their rising edges should
   be offset by ~50 µs (90° of the 400 µs full center-aligned cycle).
   This is the PSC carrier phase shift.
7. Run 15 min at full load. Log both bridges' heatsink temperatures
   every 3 minutes.

**Verify (this is the moment of truth):**
- [ ] Bridge 1 and bridge 2 heatsinks converge to **within ~5 °C** of
      each other at steady state.
- [ ] Total temperature is similar to or slightly lower than the Phase 7
      STAIR baseline (PSC has more switching but more even distribution).
- [ ] No fault trips during the 15-minute run.
- [ ] AC output looks like clean SPWM in the high-frequency view and
      clean 50 Hz sine after filtering.
- [ ] PWM_1H and PWM_3H are 90° ± 5 µs apart.

**If the 90° phase shift is wrong** — see [Troubleshooting: PSC carrier shift](#troubleshooting-psc-carrier-shift) below. **Important:**
the bridge thermal imbalance will still be fixed even if the phase shift
is wrong, because both bridges see the same continuous modulation either
way. The phase shift only affects waveform shape (5-level vs 3-level)
and DC bus stress, not bridge symmetry.

**If PSC works:** edit
[Core/Inc/pwm_config.h](Core/Inc/pwm_config.h#L32)
line `#define PWM_DEFAULT_MODULATOR MODULATOR_STAIR` to
`MODULATOR_PSC`, also change `PWM_DEFAULT_SWITCHING_HZ` from `500u` to
`5000u`. Rebuild, re-flash. Now PSC is the auto-start default.

---

## Phase 9 — Frequency sweep (optional, characterization)

**Goal:** find the best FSW for your hardware/filter combination.

**Steps:**
- `STOP`, `FSW 1000`, `START` → 10 min, log thermals.
- `STOP`, `FSW 2000`, `START` → 10 min, log thermals.
- `STOP`, `FSW 5000`, `START` → 10 min, log thermals.
- `STOP`, `FSW 10000`, `START` → 10 min, log thermals.

Higher FSW = lower output ripple but higher switching loss. Plot total
loss vs FSW; the minimum is your sweet spot. Typical IRFZ44N + TLP250
will be around 5–10 kHz.

**Verify per step:**
- [ ] Output looks correct (5-level if PSC + BOTH, 3-level if single
      bridge).
- [ ] No fault trips.
- [ ] Thermals are stable (no thermal runaway).

---

## Phase 10 — Fault injection and protection verification

**Goal:** confirm protection trips correctly without actually breaking
anything.

**With protection enabled (mode = FULL or similar):**
1. **Overvoltage:** ramp DC bus above 58 V (set bench supply to 60 V).
   Expect `$F,0x02,OV` within 3–4 ms and immediate PWM shutdown.
   `CLEAR` blocked until you drop bus back below 58 V.
2. **Undervoltage:** drop DC bus below 40 V while running. Expect
   `$F,0x01,UV`.
3. **DC imbalance:** raise one bridge's supply 11 V above the other.
   Expect `$F,0x08,IMBAL`.
4. **Overcurrent:** load the output until current crosses 15 A. Expect
   `$F,0x04,OC`. **Test with a fuse upstream and current-limited
   supplies** — protection latency is 3 ms.
5. **Sensor lost:** disconnect one MCP3201's signal during RUN. Expect
   `$F,0x10,SENSOR_LOST` after 5 consecutive bad reads. `RESCAN`
   recovers it after you reconnect.

**Verify:**
- [ ] Every fault type latches and shuts down MOE within a few ms.
- [ ] `CLEAR` is rejected (`$E,FAULT_STILL_ACTIVE`) while the underlying
      condition persists.
- [ ] `CLEAR` succeeds (`$A,CLEAR`) once the condition clears.
- [ ] Telemetry continues during FAULT state.

---

## Troubleshooting

### Auto-start fired when I didn't want it
You missed the 3 s window. Either:
- Always keep the dashboard or a terminal attached so the boot byte
  fires immediately.
- Or, build a "no-autostart" variant by changing `PWM_AUTOSTART_DELAY_MS`
  in [Core/Inc/pwm_config.h](Core/Inc/pwm_config.h) to a very large
  number (e.g. `0xFFFFFFFFu`).

### Telemetry stops but the inverter is still running
TX buffer overflow. Should not happen at 20 Hz with 80-byte payloads
(16 kbit/s into 115200 baud), but if it does, lower telemetry rate via
`CONFIG_TELEMETRY_PERIOD_MS` in [Core/Inc/config.h](Core/Inc/config.h).

### `$C` not emitted after a config change
Either the config command was rejected (look for the corresponding
`$E,PWM_CONFIG_REJECTED` or range-error response) or the FSM wasn't in
IDLE. PWM-config changes require IDLE state.

### <a name="troubleshooting-psc-carrier-shift"></a>PSC carrier shift is wrong
**Symptom:** PSC mode produces 3-level output instead of 5-level, or
the cascaded output looks asymmetric.

**Diagnosis:**
1. Scope PWM_1H (PA8) and PWM_3H (PB6) simultaneously.
2. Set `MI 0.3` so both are clearly switching.
3. Measure phase offset between the two rising edges.

| Measured offset (at FSW 5 kHz) | Diagnosis |
|---|---|
| ~50 µs (90°) | Working as intended |
| ~0 µs (in phase) | TIM8 CNT preset didn't stick. See *Fix A* below |
| ~100 µs (180°) | TIM8 CNT preset was applied as full ARR not ARR/2. See *Fix B* below |
| Drifting | TIM1/TIM8 not sharing clock domain. See *Fix C* below |

**Consequences (don't panic):**
- Bridge 1 ↔ Bridge 2 thermal balance is **still fixed** by PSC
  regardless of phase shift, because both bridges see the same continuous
  modulation. The thermal imbalance from concern #8 is solved even with
  broken phase shift.
- What you lose with broken phase shift:
  - Output reverts to 3-level (instead of 5-level) when both bridges
    switch simultaneously → bigger filter requirement, more THD.
  - DC bus capacitors see 2× ripple current → potentially more cap
    heating long-term, but not an immediate failure.

So if Phase 8 thermal comparison passes but the scope shows 3-level
output, **the headline goal is achieved.** You can ship as-is and fix
the phase shift later, or apply one of the fixes below.

**Fix A — TIM8 CNT preset not sticking:**
In [Core/Src/pwm_modulator.c](Core/Src/pwm_modulator.c) around line 147:
```c
if (g_pwm_modulator == MODULATOR_PSC) {
    TIM8->CNT = g_pwm_period / 2u;
} else {
    TIM8->CNT = 0u;
}
```
Make sure this runs **after** `TIM_EGR_UG` (which resets CNT). Currently
it does — verify it didn't get reordered. As a fallback, also write CNT
again immediately after `TIM_CR1_CEN` is set on TIM8:
```c
TIM8->CR1 |= TIM_CR1_CEN;
if (g_pwm_modulator == MODULATOR_PSC) {
    TIM8->CNT = g_pwm_period / 2u;  /* second write, post-enable */
}
```

**Fix B — Offset is full period, not half:**
Change `g_pwm_period / 2u` to `g_pwm_period / 4u`. The math: full
center-aligned cycle = 2 × ARR ticks; 90° = 1/4 of full = ARR/2. If you
see 180° offset with ARR/2, the timer is interpreting the offset
differently — try ARR/4.

**Fix C — Timers not clock-locked:**
Both TIM1 and TIM8 should be on APB2 timer clock (64 MHz). The RCC config
in [main.c:30-39](Core/Src/main.c#L30-L39) sets PPRE2 = /1 so APB2 = 64 MHz
and TIM2CLK_APB2 = 64 MHz. If somehow they're on different clocks you'd
see drift. Verify with `RCC_CFGR` register read in debugger.

**Fix D — Hardware sync via slave mode:**
If software CNT preset proves unreliable, switch to hardware-triggered
slaving. Configure TIM1 to output TRGO on update; configure TIM8 in
gated/trigger mode with ITR0 (TIM1) as source. This requires deeper
changes — only worth doing if A/B/C all fail.

### Bridge isolation isn't working
**Symptom:** `BRIDGE B1` selected, but bridge 2 gates still switch (or
vice versa).

**Diagnosis:**
1. Send `CONFIG` — verify the firmware actually got the command. Should
   report `bridge=B1`.
2. If yes: check that the ISR is reading `g_pwm_bridge_select`. In STAIR,
   look at [pwm_modulator.c:288-294](Core/Src/pwm_modulator.c#L288-L294).
   In PSC: [pwm_modulator.c:344-354](Core/Src/pwm_modulator.c#L344-L354).

### Sensor reads correct on one phase but wrong on another
The MCP3201 bit-bang reads all 3 channels in parallel with one SCK
sweep. If one channel reads correctly and another doesn't, the issue is
specific to that channel's MISO path (its 6N137 optocoupler or the
pull-up). Replace the 6N137 for that channel.

### Auto-start fires but enters FAULT immediately
Sensors disagree with reality and protection trips during PRECHARGE.
Common cause: stale DC bus reading (capacitors not yet charged or sensor
miscalibration). Use a known-good bench supply, or send `STOP` then
manual `START` once supplies are at target voltage.

---

## What to log during bringup

For each phase, record:
- Date/time, ambient temperature.
- Firmware commit SHA (`git rev-parse --short HEAD`).
- Bench supply voltages and current limits.
- Load resistance / type.
- UART log (dashboard's event panel captures everything).
- Scope captures of: AC output, two representative gates, bus current
  (if you have a current probe).
- Heatsink temps every few minutes.
- Any error/fault lines.

This log is what justifies the design decisions to graders, and what
lets us debug remotely if something surprises you mid-test.
