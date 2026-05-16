# Changelog

All notable changes to the 5-Level Cascaded H-Bridge Inverter firmware and the
companion PC dashboard. Loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions are tagged to commits in the repo; pre-release versions track the
state of `main` at that point in time.

Each release lists what changed and the design decisions that were made along
with the change, so a reader can reconstruct *why* the code looks the way it
does without having to dig through the diff.

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
