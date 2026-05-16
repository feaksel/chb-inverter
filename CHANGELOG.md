# Changelog

All notable changes to the 5-Level Cascaded H-Bridge Inverter firmware and the
companion PC dashboard. Loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions are tagged to commits in the repo; pre-release versions track the
state of `main` at that point in time.

Each release lists what changed and the design decisions that were made along
with the change, so a reader can reconstruct *why* the code looks the way it
does without having to dig through the diff.

---

## [0.5.0-dev] — branch `pwm-rewrite-configurable` — PSC-PWM + runtime config

Branched from `main` at commit `f5ff93f` (the reverted-MCP3201-shift state).
Adds a second modulator alongside the bench-validated STAIR, makes the PWM
runtime-configurable from UART/dashboard, and adds an auto-start path so
the system runs standalone with safe defaults when no UART is connected.

### Added
- **`pwm_modulator.c/h` + `pwm_config.h`** — new module that owns all
  PWM-related state: sine LUT, phase accumulator, period, precharge counters,
  modulator dispatch, timer reconfig, both modulator implementations. The
  TIM1 update IRQ handler now lives here as `Pwm_TIM1_UpdateHandler`; the
  bare-metal init in [main.c](Core/Src/main.c) just calls `Pwm_Init()`.
- **PSC modulator** — unipolar phase-shifted-carrier SPWM at the configured
  switching frequency. TIM8 CNT preset to `PWM_PERIOD/2` at config time gives
  the 90° carrier shift required for natural 5-level output from two
  cascaded cells. Same precharge sequence, same fault-trip path, same
  telemetry as STAIR. Bridge 1 and bridge 2 carry equal switching load — the
  point of the rewrite.
- **STAIR modulator** — the bench-validated 500 Hz quantize-to-5-levels
  implementation, moved verbatim from `main.c` into `pwm_modulator.c`. The
  duty math, `quantize_5level`, `bridge_level_to_duty`, and the precharge
  sequence are byte-for-byte the OLD code. Selectable at runtime so you can
  A/B compare against PSC on the bench without reflashing.
- **Runtime PWM configuration** ([pwm_config.h](Core/Inc/pwm_config.h)) with
  safe defaults that match the OLD bench-validated PWM (STAIR / 500 Hz /
  BOTH / MI 0.95 / 50 Hz fundamental). All settable in IDLE via UART.
- **New UART commands** (with dashboard buttons/dropdowns to match):
  - `MOD STAIR|PSC` — pick modulator algorithm
  - `FSW <hz>` — switching frequency (100..20000 Hz)
  - `BRIDGE BOTH|B1|B2` — single-bridge test mode (the inactive bridge is
    driven into freewheel so its contribution to the cascaded output is 0 V;
    the active bridge produces its normal 3-level swing)
  - `FFUND <hz>` — fundamental frequency (10..400 Hz)
  - `CONFIG` — print the current `$C,mod=...,fsw=...,bridge=...,ffund=...,mi=...`
    line; also emitted on every config change for the dashboard log
  - `HELP` updated to list all new commands
- **Auto-start path** ([fsm.c](Core/Src/fsm.c)). If no UART byte is received
  within `PWM_AUTOSTART_DELAY_MS = 3000 ms` after `FSM_Init` completes, the
  FSM issues its own START using the loaded defaults and emits
  `$A,AUTO_START` so any later-attached dashboard sees the event. Any UART
  RX byte cancels auto-start permanently — operator presence overrides
  standalone behavior. Detection uses `UART_ActivitySeen()`, which is set
  in the USART2 RX IRQ on any byte (not just valid commands).
- **Bridge isolation in both modulators** — `BRIDGE_B1_ONLY` forces bridge 2
  into freewheel state (both legs at LOW clamp duty, contribution ≈ 0 V) and
  vice versa. Active bridge produces 3-level (−Vdc / 0 / +Vdc) output.
- **Dashboard PWM Config panel** — `MOD`/`FSW`/`BRIDGE`/`FFUND` controls
  inside the existing Controls group, plus a `CONFIG` button. `FSW` is a
  presets dropdown (500 / 1000 / 2000 / 5000 / 10000 Hz) with free-form
  custom-value input. Bottom panel grown to 220–360 px to fit.
- **Sim controller stubs** for all new commands ([sim.py](dashboard/visual_twin_dashboard/sim.py))
  so scenario playback continues to mirror firmware behavior; 4 new unit
  tests verify the config-change happy path, range rejection, IDLE-only
  gating, and the `config_summary()` formatting.

### Changed
- **`main.c` slimmed from 367 → 122 lines.** Everything PWM-related moved
  to `pwm_modulator.c`. `main.c` now owns only: clock config, GPIO setup,
  NVIC priorities, SysTick, and `main()` itself.
- **TIM1_UP_TIM16 IRQ handler** ([stm32f3xx_it.c](Core/Src/stm32f3xx_it.c))
  now calls `Pwm_TIM1_UpdateHandler` instead of the old `PWM_Update_IRQHandler`.
- **`MI` command** routes through the new lightweight `Pwm_SetModulationIndex`
  helper so the cached config struct stays in sync with `g_pwm_modulation_index`
  without triggering an unnecessary timer reconfig.
- **`FSM_Init`** now emits a `$C` config line right after `BOOT_SELF_TEST_DONE`
  so any dashboard connecting on boot sees the active PWM configuration
  immediately without having to issue `CONFIG`.

### Decisions
- **Two modulators behind a runtime switch, not a build-time flag.**
  Lets the user A/B test on the same bench session without reflashing,
  and keeps the "known-good fallback" property of STAIR while PSC is
  being characterised. The dispatch is a single `if` at the bottom of
  `Pwm_TIM1_UpdateHandler` — negligible ISR overhead.
- **All PWM state lives in `pwm_modulator.c`, including the OLD STAIR
  globals (`g_precharge_ticks`, etc.).** Originally these were in `main.c`
  and `fsm.c` accessed them via extern. Centralising in the modulator means
  `main.c` becomes just system bring-up, and timing-critical state has one
  owner. `fsm.c` still uses extern declarations for the precharge handshake.
- **STAIR is moved, not duplicated.** The OLD STAIR ISR logic is moved
  verbatim into `stair_modulate()` in `pwm_modulator.c` — quantize, level
  mapping, duty clamp, CCR writes are byte-for-byte the same as the
  bench-validated `main.c` ISR. The only additions are: (a) reading
  `g_pwm_period` instead of the `PWM_PERIOD` macro, so FSW can change at
  runtime; and (b) the `g_pwm_bridge_select` check after the level
  computation to support single-bridge test mode.
- **PSC carrier phase shift via TIM8 CNT preset, not via slave-mode
  triggering.** Simpler and good enough — both timers share a clock, so
  once the offset is set at `Pwm_SetConfig` time they stay locked. Slight
  drift over many hours is theoretically possible but the LUT-driven sine
  re-aligns the phase relationship every fundamental period anyway.
- **PSC uses 0.05/0.95 duty clamps; STAIR keeps 0.01/0.95.** PSC actively
  modulates both legs symmetrically, so both clamps bind. STAIR's "off"
  leg sits at ~1% duty (HS almost off, LS almost on) — bootstrap is fine
  on that leg, the 5% rule only constrains the "on" leg's HS.
- **Auto-start fires regardless of sensing mode.** Even if the mode
  auto-demoted to `OPEN_LOOP` (no sensors connected), auto-start still
  fires after 3 s with a UART warning ("$E,WARNING_OPEN_LOOP_NO_PROTECTION"
  follows the "$A,AUTO_START"). The alternative — blocking auto-start in
  OPEN — would defeat the standalone-demo use case. The "no UART = no
  operator" assumption is the safety boundary; the operator who deployed
  the firmware without sensors accepted the OPEN risk.
- **`Pwm_SetConfig` always reconfigures the timer**, even for fields that
  don't affect the timer (like `bridge_select` or `modulation_index`).
  Simpler than tracking which fields changed. A reconfig in IDLE is
  invisible to the operator (MOE off, no output disruption) and cheap
  (~20 instruction cycles plus EGR_UG). The `Pwm_SetModulationIndex`
  helper exists only because `MI` is a hot path the operator may tweak
  repeatedly during bringup.
- **Bridge isolation = freewheel, not high-Z.** The inactive bridge's
  outputs are driven to LOW duty (both HS off, both LS on, ≈99% of period),
  which holds its terminals at the bridge's local 0 V. Net contribution to
  the cascaded output is 0 V. Alternative — disabling the timer outputs
  entirely (CCxE=0) — would let the output float and let body diodes
  potentially conduct, which is worse than a controlled freewheel.
- **Telemetry `$T,...` format unchanged.** Dashboard parser still works
  with no modification. New PWM-config information rides on the existing
  `$S,...` STATUS line (and the new `$C,...` config line). This keeps
  v0.3.0 dashboards forward-compatible with this firmware — they'll just
  ignore the `$C` line.

### Known-issue impact
- **Bridge 1 thermal/current imbalance** (the headline reason for this
  branch) — fix path: switch to `MOD PSC` at runtime. Bench validation
  step is to run STAIR for 5 min, measure both bridges' MOSFET case temps,
  then switch to PSC for 5 min and re-measure; they should converge to
  within ~3 °C. If they do, this branch is the win and the guide's IPD
  recommendation can be updated to PSC in v3.2.
- **HAL cleanup** still deferred — orthogonal to this branch.

### Bringup sequence on this branch
A full phase-by-phase procedure with what-to-expect, scope captures, and
troubleshooting lives in [HARDWARE_BRINGUP.md](HARDWARE_BRINGUP.md). High-level:
1. Boot emits `$A,BOOT_SELF_TEST_DONE` + `$C` config line + (if applicable)
   `$E,MODE_DEMOTED` + (if applicable) `$E,WARNING_OPEN_LOOP_NO_PROTECTION`.
2. Send any UART byte within 3 s to cancel auto-start; otherwise look for
   `$A,AUTO_START`.
3. `CONFIG` → STAIR baseline → measure thermals → switch to PSC → re-measure.
4. Per-bridge isolation tests with `BRIDGE B1` / `BRIDGE B2`.
5. If PSC checks out, flip `PWM_DEFAULT_MODULATOR` in
   [pwm_config.h](Core/Inc/pwm_config.h) to `MODULATOR_PSC` and merge to `main`.

### Build verification (2026-05-16)
Compiled and linked locally using STM32CubeIDE 1.17's bundled toolchain
(`arm-none-eabi-gcc 12.3.1`, the same compiler the IDE invokes) so the
branch is known-good before any bench bringup:

```
Build flags (matches .cproject):
  -mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb
  -DDEBUG -DUSE_HAL_DRIVER -DSTM32F303xE
  -ICore/Inc -IDrivers/STM32F3xx_HAL_Driver/Inc/Legacy
  -IDrivers/STM32F3xx_HAL_Driver/Inc
  -IDrivers/CMSIS/Device/ST/STM32F3xx/Include -IDrivers/CMSIS/Include
  -O0 -g3 -Wall -Wextra -Wshadow -Wundef
  -ffunction-sections -fdata-sections

Link flags:
  -TSTM32F303RETX_FLASH.ld -Wl,--gc-sections -static
  --specs=nano.specs --specs=nosys.specs -u_printf_float
  -Wl,--start-group -lc -lm -Wl,--end-group
```

Result: 11 Core/Src .c files + 14 HAL drivers + startup.s → ELF
35.5 KB code / 468 B data / 3.7 KB BSS. Total Flash 36 KB of 512 KB
available, total RAM 4.1 KB of 64 KB. **Zero warnings** under the strict
warning set above.

`nm` against the linked ELF confirms every new symbol from this branch
is present and resolved:
- `Pwm_TIM1_UpdateHandler`, `Pwm_Init`, `Pwm_SetConfig`, `Pwm_GetConfig`,
  `Pwm_SetModulationIndex`, `Pwm_HandlePrechargeStep`,
  `Pwm_ParseModulator`, `Pwm_ParseBridgeSelect`, `Pwm_ModulatorName`,
  `Pwm_BridgeName`, `psc_modulate`
- `do_start`, `handle_mod`, `handle_bridge`, `handle_fsw`, `handle_ffund`,
  `emit_pwm_config_line`, `g_auto_start_done`
- `UART_ActivitySeen`, `UART_SendPwmConfig`
- All global config state defined exactly once
  (`g_pwm_modulator`, `g_pwm_bridge_select`, `g_pwm_period`, etc.)

Flashable artifacts produced under `build/`:
- `5levelchb.elf` — debug symbols for CubeIDE/gdb (1.07 MB)
- `5levelchb.bin` — raw binary for drag-and-drop to the Nucleo's USB
  mass-storage drive (36.5 KB)
- `5levelchb.hex` — Intel HEX for ST-LINK Utility / STM32CubeProgrammer
  (100 KB)
- `5levelchb.map` — link map for symbol/section debugging (445 KB)

### Dashboard test verification
19 / 19 unit tests pass — the 15 pre-existing protocol + sim tests plus
4 new tests in [dashboard/tests/test_sim.py](dashboard/tests/test_sim.py)
covering:
- Default PWM config values match firmware defaults.
- Each setter (`set_modulator`, `set_bridge`, `set_switching_freq`,
  `set_fundamental_freq`) updates state and returns the expected ack string.
- Out-of-range values return the correct error string.
- All four setters reject when not in IDLE.
- `config_summary()` format matches what the firmware emits on `$C`.

Run from `dashboard/`:
```
py -3 -m unittest discover tests -v
```

---

## [Unreleased] — 2026-05-16 — Pre-bringup fixes + build-guide cross-reference

End-to-end review of the firmware before applying high voltage, followed by
a parameter-by-parameter cross-reference against the team's official build
guide v3.1 (`CHB_Inverter_Build_Guide_v3_1.pdf`, dated February 2026).

PWM generation in [main.c](Core/Src/main.c) was deliberately left untouched
because the 500 Hz quantize-staircase modulator was bench-validated in an
earlier session. The decision to replace it with PSC-PWM (deviating from
the guide's documented IPD LS-PWM) is captured under "Decisions" below and
will land in a dedicated branch.

### Fixed
- **Status line and telemetry line disagreed on "sensor valid"**
  ([uart_telem.c:449-454](Core/Src/uart_telem.c#L449)). `UART_SendStatus`
  used `channel.initialized` (sticky once true), while `UART_SendTelemetry`
  used `channel.available` (can flip back to 0 when a sensor goes lost).
  A sensor that booted OK and later disappeared would still show a stale
  number in `STATUS` but `NAN` in telemetry. Both now use `available`.

### Changed
- **Duty cycle clamp tightened to 95% per build guide v3.1 section 7.4**
  ([main.c:30-34](Core/Src/main.c#L30-L34)). `DUTY_HIGH_CLAMP` reduced from
  `0.99f` to `0.95f`. Ensures the low-side gets ≥5% on-time per period to
  refresh the bootstrap cap (UF4007 + 10 µF). Output amplitude drops by
  ~4% (50 V bus → +47.5 V max bridge contribution instead of +49.5 V).
  `DUTY_LOW_CLAMP` left at `0.01f` — that clamp constrains the opposite
  leg whose LS is already on ~99% of the period and is not bootstrap-bound.

### Reverted
- **MCP3201 bit-shift change.** In an earlier pass the shift was changed
  from `(raw >> 3) & 0x0FFF` to `(raw >> 1) & 0x0FFF` based on one
  interpretation of the MCP3201 datasheet's 1.5 SCK sample window. The
  build guide section 7.3 documents `(raw >> 3) & 0x0FFF` with the bit
  layout `[NULL][B11..B0][X][X][X]` — i.e., NULL at the 1st rising edge
  sample. Reverted to match the guide. The driver now contains a
  bringup-verification comment ([spi_mcp3201.c:132-145](Core/Src/spi_mcp3201.c#L132-L145))
  explaining how to swap to `>> 1` if the bench reading at a known DC
  input (e.g. 5 V → expected raw ~199) comes back ~8× off.

### Added
- **N-of-M debounce on protection trips** ([protection.h:14-17](Core/Inc/protection.h#L14-L17),
  [protection.c](Core/Src/protection.c)). Each fault bit (UV, OV, OC, IMBAL)
  has its own consecutive-hit counter. A fault must be observed in
  `PROTECTION_TRIP_COUNT = 3` back-to-back 1 kHz sensor scans before it
  trips. Any clean read resets the counter. Counters are also zeroed in
  `Protection_ClearLatched` so re-entering RUN after a CLEAR starts fresh.
  Trip latency is 3 ms — guide section 5 documents "~1 ms" target, the
  3 ms is a conscious trade for noise rejection during bringup.
- **`RESCAN` UART command** ([uart_telem.h](Core/Inc/uart_telem.h),
  [uart_telem.c](Core/Src/uart_telem.c),
  [fsm.c:181-199](Core/Src/fsm.c#L181-L199)). Re-runs `Sensing_SelfTest`
  to re-mark sensors available after a transient loss without rebooting
  the board. Allowed in `IDLE` and `FAULT` only. If the current mode's
  required sensors are still missing afterwards, auto-demotes to the
  best available mode and emits `MODE_DEMOTED`. Updates the help string.
- **Dashboard `RESCAN` button** ([app.py](dashboard/visual_twin_dashboard/app.py),
  [sim.py](dashboard/visual_twin_dashboard/sim.py),
  [sources.py](dashboard/visual_twin_dashboard/sources.py)). Live serial
  sends `RESCAN` to the firmware. Simulator clears the `sensor_lost`
  scenario flag so the PC twin mirrors the firmware behavior.

### Removed
- `CONFIG_PRECHARGE_TIMEOUT_MS` from [config.h](Core/Inc/config.h). Defined
  in the FSM commit but never referenced.

### Verified (no code change)
- **TLP250 gate driver polarity** (concern #10 in the review). The TLP250
  is non-inverting (LED ON → output HIGH → MOSFET ON). Confirmed by user
  and consistent with build guide section 3.3.2 (controller PWM pin →
  220 Ω → pin 2 anode, pin 3 cathode → GND_System — i.e., source config).
  With BDTR `OSSI=1` driving all four TIM outputs LOW when `MOE=0`, all
  MOSFETs are OFF in IDLE/FAULT/BOOT — safe at boot, stop, and fault.

### Build-guide v3.1 cross-reference — parameters that match
Verified item-by-item against the official build guide:
- DC sensor divider 100 kΩ / 5.1 kΩ with 5 V reference → `CONFIG_VDC_DIVIDER_GAIN`,
  `CONFIG_VDC_ADC_REF` ([config.h](Core/Inc/config.h)). Resolution 0.252 V/count.
- ACS712 sensor: 100 mV/A, 2.5 V zero, 0.6 divider, 3.3 V ref → all four
  `CONFIG_ACS_*` and `CONFIG_CUR_ADC_REF` constants match exactly.
- Protection thresholds: UV<40 V, OV>58 V, OC>15 A, IMBAL>10 V — match
  guide section 5.1 byte-for-byte.
- Bootstrap precharge 5–10 ms → firmware uses 6 ms full-LS-on (functionally
  equivalent to guide's "50% duty for 5–10 ms" suggestion; both leave the
  bootstrap cap fully charged).
- SPI ≤ 1 MHz with 6N137 round-trip margin → bit-bang runs at ~140 kHz,
  well under the guide's 2 MHz hard limit.
- Pin header signals (header pins 9–18: SCK, three CS, three MISO, FAULT_OUT,
  +5 V, +3.3 V, GND, GND) — all match firmware GPIO usage.

### Build-guide v3.1 cross-reference — documentation errors found in the guide
These are guide-side errors; the firmware is correct. Flagged here so the
team can publish a v3.2 errata.
- **PWM_1L pin (header pin 4).** Guide lists "PA10 (TIM1_CH2N)". PA10 has
  no TIM1_CH2N alternate function on the STM32F303RE. The only valid
  TIM1_CH2N pins on this package are PA12, PB0, and PB14. Firmware uses
  **PA12 (AF6)** — confirmed by user as the actual board wiring.
- **TIM8 channel pins (header pins 5–8).** Guide lists PC6/PC7/PC8/PC9 as
  TIM8_CH1/CH1N/CH2/CH2N. On F303RE, PC6 = TIM8_CH1 ✓ but PC7 = TIM8_CH2
  (not CH1N), PC8 = TIM8_CH3 (not CH2), PC9 = TIM8_CH4 (not CH2N). Firmware
  uses **PB6/PB3/PB8/PB0** which do map correctly to TIM8 CH1/CH1N/CH2/CH2N
  — confirmed by user as the actual board wiring.

### Build-guide v3.1 cross-reference — deliberate firmware deviations from guide
- **Modulation strategy.** Guide section 1.2 specifies "In-Phase Disposition
  Level-Shifted PWM (IPD LS-PWM)". Firmware currently runs a 500 Hz
  quantize-to-5-levels staircase, which is neither IPD nor PSC and matches
  the guide only in producing a 5-level output. The upcoming rebalance
  branch will replace this with **PSC-PWM (phase-shifted carriers, unipolar
  per cell, 90° shift between the two bridges)** rather than IPD. Reason:
  PSC is naturally bridge-balanced, whereas IPD has an inherent bridge-loss
  asymmetry that needs an additional bridge-swap each fundamental cycle to
  even out. The user has accepted this deviation and will publish a guide
  v3.2 erratum.
- **Switching frequency.** Guide specifies 5 kHz; current firmware runs at
  500 Hz. Will be raised to 5 kHz in the PSC-PWM branch.
- **Protection scan rate.** Guide implies ≥20 kHz ("4+ scans per 5 kHz
  period"); firmware uses 1 kHz. Raising this requires speeding up the
  bit-bang SPI (currently ~140 kHz, can go to ~1 MHz). Deferred pending
  the switching-frequency change above.
- **Dead-time.** Guide specifies 500 ns – 1 µs; firmware uses 2 µs (more
  conservative). Bench-validated, left as-is.
- **System clock.** Guide example uses 72 MHz (needs external HSE crystal);
  firmware uses 64 MHz from HSI. All PWM and timer arithmetic is derived
  from the actual clock, so the numbers stay self-consistent.

### Decisions
- **MCP3201 bit-shift trusts the build guide over my datasheet reading.**
  Two readings of the MCP3201 timing are defensible: (a) NULL bit appears
  at the 1st SCK rising edge sample → shift `>> 3` (guide); (b) NULL appears
  at the 3rd SCK rising edge sample after the documented 1.5 SCK sample
  window → shift `>> 1` (my earlier analysis). Both depend on how
  aggressively the device drives DOUT after CS↓. Without bench evidence
  to break the tie, defer to the team's documented design and keep
  `>> 3`. Bringup verification step added in code comment.
- **PSC-PWM chosen over the guide's IPD LS-PWM** for the upcoming
  rebalance branch. The user's reported bridge-1 thermal/current imbalance
  is exactly the failure mode IPD induces (one bridge always handles the
  inner band, the other the outer band). PSC fixes this naturally without
  the cycle-by-cycle bridge-swap that IPD would need. Trade-off: deviation
  from the documented design — a v3.2 guide erratum will be issued.
- **95% duty clamp accepted as a guide-compliance change**, even though
  it touches PWM. The clamp is a parameter, not a modulation-algorithm
  change, and is required by the guide for bootstrap safety.
- **Protection filter strategy: N-of-M consecutive, not IIR-on-protection.**
  Three options were on the table — single-sample raw (status quo, prone
  to nuisance trips), IIR-filtered values (smooth but adds ~20–30 ms lag
  and could miss a short overcurrent spike), and N-of-M consecutive
  (rejects single-sample noise while keeping fast trip on a sustained
  event). Picked N-of-M because the protection path needs to be fast
  *and* immune to glitches.
- **`RESCAN` allowed in IDLE and FAULT, not just IDLE.** Allowing it in
  FAULT means a sensor that disappeared can be recovered without first
  having to clear the latched fault (which would itself be blocked by
  `FAULT_SENSOR_LOST` being active). Blocked in PRECHARGE/RUN because
  `Sensing_SelfTest` performs blocking SPI reads that should not race
  with the sense loop.
- **Status and telemetry use `available`, not `initialized`.** Both lines
  should reflect *current* reality, not history. A lost sensor reads
  `NAN` everywhere; this matches operator expectation.
- **HAL cleanup deferred.** The Drivers/ tree (~10–15 KB of dead Flash)
  and the `extern TIM_HandleTypeDef htim1` stub in `stm32f3xx_it.c` were
  left in place to keep the diff focused on bringup-blocking issues. The
  only HAL call that actually runs is `HAL_IncTick()` from SysTick, which
  just increments an unused `uwTick`. Cleanup is a future task once the
  board is up.
- **PWM generation untouched.** The bridge-level quantization in
  `PWM_Update_IRQHandler` ([main.c:285-366](Core/Src/main.c#L285-L366))
  always uses bridge 1 for the ±1 step, leaving bridge 2 freewheeling.
  This produces unequal switching loss between bridges (confirmed in
  hardware: one of bridge 1's MOSFETs runs hotter, and bridge 1 carries
  more current than bridge 2). The fix is tracked as [#known-issue-1](#known-issues)
  and will be done in a dedicated branch — it touches the modulator
  itself and deserves separate attention.

### Known issues
- **Bridge 1 thermal/current imbalance** (concern #8 from the review).
  See "Decisions" above and the [README](README.md). Will be addressed
  in a separate branch.
- **Lost sensors only recover via `RESCAN` or reboot.** No automatic
  re-arm. Intentional: a sensor that flickered out once probably has a
  wiring issue that should be diagnosed before trusting it again.
- **Protection uses single-sample raw ADC counts**, now wrapped in a
  3-sample debounce. Still no per-channel IIR for the protection path
  (telemetry has IIR with `alpha=0.1`, but protection reads `last_raw`).
  If hardware bringup reveals slow drift faults that the debounce misses,
  consider adding a slow-drift filter alongside.

---

## [0.3.0] — 2026-05-15 — Dashboard added

Commit `7402281`. PC-side companion app for visualization, sim-only fault
playback, and live serial control.

### Added
- `dashboard/` Python application built on PySide6 + pyqtgraph + pyserial.
  - `protocol.py` — NMEA-style line parser, matches firmware checksums.
  - `models.py` — `TelemetryFrame` dataclass, mode/fault enum mirrors.
  - `sim.py` — `SimController` with deterministic step()-based timeline
    and 8 pre-baked scenario presets.
  - `sources.py` — `BaseSource` / `SimSource` / `SerialSource` /
    `ReplaySource` adapters. All emit the same `frame_received` signal.
  - `widgets.py` — FSM strip, fault badge, modulation/output twin, sensor
    gauges.
  - `app.py` — main window, command panel, scenario presets, log pane.
- `dashboard/tests/test_protocol.py` and `test_sim.py` — unit tests that
  do **not** require PySide6 to run, so CI can verify parser + sim logic.

### Decisions
- **Sim and serial sources are fully separate.** Scenario buttons are
  disabled when "Arm live START" is checked; scenarios always play
  against the simulator. The simulator never injects fake sensor values
  into the firmware. This was deliberate — a fault-demo button that
  accidentally trips a real power stage is exactly the kind of footgun
  that defeats the purpose of having a dashboard.
- **"Arm live START" guard.** Live `START` is blocked behind a checkbox
  the operator has to flip explicitly. Other commands (`STOP`, `STATUS`,
  `MODE`, `MI`, `CLEAR`) are not gated.
- **Frames carry a `source` field.** `_handle_frame` filters by source
  so simulator frames don't pollute the live serial view and vice versa
  when the user switches sources mid-session.
- **PySide6 + pyqtgraph instead of matplotlib.** pyqtgraph integrates
  with Qt's event loop and stays smooth at 20 Hz telemetry without the
  matplotlib backend redraws stuttering. Tests intentionally don't import
  Qt so they run in a headless environment.
- **Telemetry parser is forgiving.** Lines with a bad checksum still
  produce a `TelemetryFrame` (marked `checksum_valid=False`) instead of
  being dropped, so operators can still see *something* during bringup
  if a wire is noisy.

---

## [0.2.0] — 2026-05-13 — FSM, sensing, protection, UART (`fsm: Initial commit`)

Commit `0198b96`. The bulk of the firmware. Brings the project from a
PWM-only CubeMX skeleton to a complete supervisory firmware with sensing,
protection, mode management, and UART control. ~1745 lines added.

### Added
- **FSM** ([fsm.c](Core/Src/fsm.c)): `BOOT → IDLE → PRECHARGE → RUN → FAULT`.
  Boot runs an ADC self-test, selects the best sensing mode, and drops
  to IDLE. START enables MOE and arms a bootstrap precharge; the PWM ISR
  forces low-sides ON for 3 PWM periods (6 ms at 500 Hz). When
  `g_precharge_done` is set, the main loop transitions to RUN. STOP and
  fault entry both drop MOE and reset precharge state.
- **MCP3201 bit-banged SPI** ([spi_mcp3201.c](Core/Src/spi_mcp3201.c)):
  One shared SCK on PA5, three independent MISOs on PA6/PC3/PC4, three
  CS lines on PC0/PC1/PC2. Reads all selected channels in parallel
  during a single SCK sweep.
- **Sensing layer** ([sensing.c](Core/Src/sensing.c)): TIM6 at 1 kHz
  sets `g_sense_pending`; main loop calls `Sensing_Service` to do the
  blocking SPI read. Per-channel IIR with `alpha=0.1` for telemetry,
  rail-stuck detector that demotes a channel to "unavailable" after 5
  consecutive `0x000` or `0xFFF` reads.
- **Protection** ([protection.c](Core/Src/protection.c)): UV/OV/OC/IMBAL
  thresholds (40/58/15/10), per-mode protection set, latched faults that
  require `CLEAR` after the underlying condition is gone.
- **Six sensing modes** with graceful boot-time degradation: `FULL`,
  `DC_ONLY`, `CUR_ONLY`, `OPEN`, `DC1`, `DC2`. Boot picks the most
  capable mode that the available sensors support.
- **UART telemetry + command** ([uart_telem.c](Core/Src/uart_telem.c)):
  USART2 @ 115200 8N1, line-based commands (`START`/`STOP`/`CLEAR`/`MODE
  <0..5>`/`STATUS`/`HELP`/`MI <x>`), NMEA-style telemetry at 20 Hz with
  XOR checksums, `$A`/`$E`/`$F`/`$H`/`$S`/`$T` line prefixes.
- **FSM_NOTES.md** with the state diagram and per-mode protection table.

### Changed
- `main.c` clock init refactored to enable HSI→PLL→64 MHz without
  external crystal. SysTick configured to 1 kHz for `FSM_Millis()`.
  System init order rearranged so all peripherals are up before
  `FSM_Init()` runs the self-test.
- `stm32f3xx_it.c` wired SysTick → `FSM_SysTickISR`, TIM1_UP →
  `PWM_Update_IRQHandler`, TIM6_DAC → `Sensing_TIM6_IRQHandler`, USART2
  → `UART_USART2_IRQHandler`. HAL stub vectors remain for any unused
  IRQs.
- README expanded to document pinout, sensing modes, command and
  telemetry protocol, bringup notes, and safety warnings.

### Decisions
- **Bare-metal CMSIS, not HAL.** All new peripheral code uses direct
  register writes (`RCC->`, `TIM1->`, etc.). HAL files are still
  compiled in but only `HAL_IncTick()` actually runs (from SysTick). The
  reason: deterministic, transparent timing for the PWM ISR — HAL adds
  layers of indirection that are awkward to reason about for a hard
  real-time control loop.
- **Bit-banged SPI for MCP3201 instead of hardware SPI1.** The isolated
  6N137 optocouplers on the three MISO lines don't tri-state cleanly, so
  the three MISOs can't share a bus. Bit-banging clocks all three with
  one SCK and reads three GPIO inputs in parallel. Hardware SPI1 was
  not used because it only supports one MISO.
- **Independent 6N137 isolation per MISO line.** Documented in the README
  as the reason MISOs aren't bussed. Trade-off: more parts, but cleaner
  signals.
- **TIM6 ISR sets a flag; main loop does the SPI read.** Keeps the ISR
  short (~10 cycles) and isolates the bit-bang timing from interrupt
  context where higher-priority IRQs can stretch it. SPI bit period
  becomes ~3 µs (well under the MCP3201's 1.6 MHz max) but absolute
  timing isn't critical — only edge ordering matters.
- **Protection uses `last_raw`, not `filtered_value`.** Fast trip wins
  over smooth display. Telemetry/STATUS use the filtered value.
  (Pre-existing nuisance-trip risk addressed in the 2026-05-16 fixes
  via N-of-M debounce.)
- **`OPEN` mode is allowed but warns.** Boot and `MODE` selection both
  emit `WARNING_OPEN_LOOP_NO_PROTECTION`. Intended for demos where the
  sensor wiring isn't done yet; disables all protection.
- **Lost sensors don't auto-recover.** Once `available=0`, the channel
  is dropped from the scan mask and stays dropped until reboot. The
  RESCAN command added in 2026-05-16 gives an explicit recovery path.
- **IRQ priorities: TIM1=0, TIM6=2, USART2=3, SysTick=15.** TIM1 update
  is highest because PWM CCR updates must not be late. TIM6 is short and
  just sets a flag. USART is one byte at a time at 87 µs intervals.
  SysTick only increments a counter — lowest priority is fine.
- **Telemetry at 20 Hz.** Comfortably below the UART's 115200-baud
  capacity (~80 bytes per 50 ms ≈ 16 kbps), leaves headroom for command
  echoes and async error/fault messages.
- **NMEA-style line protocol with XOR checksum.** Easy to parse in any
  language, human-readable on a terminal, robust against half-typed
  commands during interactive bringup.
- **5-level CHB modulation by quantization, not phase-shifted carriers.**
  The PWM ISR quantizes the sine reference into {−2, −1, 0, +1, +2} via
  hard thresholds and routes each level to a fixed bridge state. Bridge 1
  is *always* the one carrying the ±1 step. (This is the source of the
  thermal imbalance noted in 2026-05-16.)
- **500 Hz PWM, 256-sample sine LUT at 50 Hz fundamental.** Phase
  increment = (50/500) × 256 = 25.6 samples/ISR. PWM period 2 ms,
  fundamental period 20 ms.
- **2 µs dead-time via BDTR.DTG = 0x80 at 64 MHz.** Matches typical
  power MOSFET turn-off times with margin.
- **6 ms bootstrap precharge (3 PWM periods).** Long enough to charge
  100 nF bootstrap caps through typical 100 Ω–1 kΩ paths many times over.
- **`OSSR=1` and `OSSI=1` in BDTR.** Outputs are forced to their inactive
  level (LOW, with default polarity) whenever any of CCxE/CCxNE is 0 or
  MOE is 0. Combined with the TLP250 non-inverting topology, this means
  every state where the firmware *thinks* the bridge is off actually
  drives all MOSFETs off. Confirmed safe (see 2026-05-16 entry).
- **DC sensor scale: `105.1 / 5.1` divider, 5.0 V ADC reference.**
  Full-scale ≈ 103 V. With 40/58 V protection limits, the DC bus is
  expected to sit around 50 V per bridge.
- **Current sensor: 0.1 V/A sensitivity, 2.5 V zero, 0.6 divider, 3.3 V
  ADC reference.** Implies a Hall-effect transducer with a passive
  divider into the MCP3201's input range. Exact part number is in the
  hardware schematic, not in firmware.

---

## [0.1.0] — 2026-05-12 — Project skeleton + README (`Initial commit`, `Add README`)

Commits `4ac72e7` and `453fc1b`.

### Added
- STM32CubeIDE project for STM32F303RETx (Nucleo-F303RE), 64-pin LQFP.
- CubeMX-generated HAL skeleton: `Drivers/STM32F3xx_HAL_Driver`,
  `Drivers/CMSIS`, `Core/Src/main.c` (PWM-only), `Core/Src/syscalls.c`,
  `Core/Src/sysmem.c`, `Core/Src/stm32f3xx_hal_msp.c`,
  `Core/Startup/startup_stm32f303retx.s`, `STM32F303RETX_FLASH.ld`.
- Initial `main.c` with TIM1 + TIM8 complementary PWM generating the
  5-level cascaded H-bridge output. Verified on the bench at this stage
  — this is the "old PWM" that subsequent commits preserve unchanged.
- Top-level README placeholder.

### Decisions
- **STM32F303RE on the Nucleo-64.** Chosen for: dual advanced-control
  timers (TIM1 + TIM8) with complementary outputs and configurable
  dead-time, hardware FPU, on-board ST-LINK for both flashing and the
  VCP used by the UART protocol.
- **TIM1 = bridge 1, TIM8 = bridge 2.** Each timer drives two
  complementary leg pairs (CH1/CH1N + CH2/CH2N), giving the four
  half-bridge gate signals per H-bridge.
- **No external crystal.** HSI/2 × PLL = 64 MHz. Saves the crystal BOM
  and avoids the unsupported-PLL-macro paths in older CMSIS headers.

---

## Known Issues (active)

1. **Bridge-1 thermal/current imbalance.** Bridge 1 always carries the
   ±1 step in 5-level mode; bridge 2 only switches for the ±2 levels.
   Bench observation: one of bridge 1's MOSFETs runs hot, and bridge 1
   carries more current than bridge 2. Will be addressed in a dedicated
   branch — either a quick rebalance (alternate which bridge handles
   ±1 each fundamental cycle) or a full PSC-PWM rewrite with
   phase-shifted carriers.
2. **HAL is compiled but unused.** ~10–15 KB of dead Flash and a stray
   `extern TIM_HandleTypeDef htim1` in `stm32f3xx_it.c`. Cleanup
   deferred until after first hardware bringup.
3. **`delay_half_period` is slower than the comment implies.** Volatile
   loop overhead pushes SCK to ~140 kHz instead of the documented "below
   1 MHz" target. Doesn't matter functionally (MCP3201 doesn't care)
   but worth replacing with a DWT cycle counter if precise timing is
   ever needed.
4. **PA5 doubles as Nucleo's LD2 LED.** It flickers dimly during every
   ADC scan. Cosmetic only.
