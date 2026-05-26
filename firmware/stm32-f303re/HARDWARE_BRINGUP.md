# Hardware Bringup — 5-Level CHB Inverter

Companion to the team's `CHB_Inverter_Build_Guide_v3_1.pdf` section 6
("Test Procedures"). The guide covers what to *do* on the hardware; this
document covers what the **firmware** does at each step, the UART
commands to send, the telemetry/scope outputs to expect, and what to do
when something is off.

**Read this from top to bottom. Do not skip phases.** Each phase builds
confidence for the next. Skipping risks damaging components that took
weeks to source.

> 📘 **Looking for a faster, focused walkthrough?**
> [FIRST_BENCH_SESSION.md](FIRST_BENCH_SESSION.md) is a linear single-session
> procedure that folds together the relevant bits of this doc (Step 0,
> Phases 2–7b, Phase 8) and adds explicit TLP250-protection checks.
> Use it the first time you bench-test the new branch. Come back here
> for the comprehensive reference and troubleshooting trees.

---

## Step 0 — Getting the firmware onto the board

This is the end-to-end procedure from "the code lives in the
`pwm-rewrite-configurable` branch on the dev PC" to "the firmware is
running on the Nucleo and the dashboard is showing telemetry."

If everything is already on the bench PC and flashed, skip to
[Pre-bringup checklist](#pre-bringup-checklist).

### 0.A — Commit the branch (on the dev PC, if not yet committed)

Check current state:
```powershell
cd C:\Users\furka\Projects\5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE
git status
git branch --show-current     # must print: pwm-rewrite-configurable
```

If `git status` shows modified or untracked files, commit them:
```powershell
git add -A
git commit -m "PSC-PWM rewrite: configurable modulator, runtime config, auto-start, STAIR_ALT"
```

Push to remote so the bench PC can pull:
```powershell
git push -u origin pwm-rewrite-configurable
```

After the first push, confirm the branch is visible on GitHub
(or whatever remote you use).

### 0.B — Clone (or pull) onto the bench PC

**Fresh bench PC, empty folder, no git history yet:**
```powershell
# Make a Projects folder if you don't have one yet
mkdir C:\Projects -ErrorAction SilentlyContinue
cd C:\Projects

# Clone your fork (the one we pushed to in 0.A)
git clone https://github.com/feaksel/5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE.git
cd 5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE

# Default branch on clone is main; switch to the working branch
git checkout pwm-rewrite-configurable
```

GitHub will prompt for credentials on the first clone — use a Personal
Access Token (Settings → Developer settings → Personal access tokens →
Tokens (classic) → Generate new, scope `repo`). Paste the token as the
password; Windows Credential Manager remembers it after that.

If git isn't installed: get it from
[git-scm.com/download/win](https://git-scm.com/download/win),
accept defaults, restart PowerShell.

**Bench PC already has the repo from a previous session:**
```powershell
cd C:\Projects\5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE
git fetch
git checkout pwm-rewrite-configurable
git pull
```

**Verify you got the right branch and the latest code:**
```powershell
git log --oneline -3
git branch --show-current     # must print: pwm-rewrite-configurable
```

The newest commit message should match what you pushed in 0.A.

### 0.C — Build in STM32CubeIDE

> 💡 **Recommended ordering of the remaining sub-steps:** 0.C build →
> 0.E install/launch dashboard and connect to COM port → 0.D flash. The
> reason is the auto-start race explained at the top of 0.D — having the
> dashboard already connected before the flash completes guarantees
> auto-start gets cancelled on the post-flash reset.

1. Launch **STM32CubeIDE**.
2. Pick a workspace folder when prompted (any empty folder — the workspace
   is just project metadata, not the source).
3. **File → Open Projects from File System...**
4. Click **Directory...** and browse to the cloned repo root (the folder
   containing `.project` and `5levelchb.ioc`).
5. Click **Finish**. CubeIDE imports the project and starts indexing.
6. Wait for indexing to finish (~30-60 s — watch progress bar bottom
   right; it says things like *"C/C++ Indexer"*).
7. **Project → Build All** (or `Ctrl+B`, or click the hammer icon in
   the toolbar).
8. When the build finishes the Console panel at the bottom should show:
   ```
   arm-none-eabi-size  Debug/5levelchb.elf
      text    data     bss     dec     hex filename
     36660     468    3668   40796    9f5c Debug/5levelchb.elf

   Finished building target: 5levelchb.elf
   ```
9. Build artifacts land in `Debug/`:
   - `5levelchb.elf` — for CubeIDE flashing / debugging
   - `5levelchb.bin` — for drag-and-drop flashing
   - `5levelchb.hex` — for STM32CubeProgrammer
   - `5levelchb.map` — link map

Build errors? Read the first error in the Console panel and fix.
Common ones:
- *"Cannot resolve include ... arm-none-eabi-gcc"* — CubeIDE toolchain
  not installed. **Help → Check for Updates** and install missing pieces.
- *"undefined reference to ..."* — a `.c` file isn't being picked up.
  Right-click the file in Project Explorer → **Resource Configurations
  → Reset to Default**.

### 0.D — Flash the Nucleo

> ⚠️ **Critical ordering: open the dashboard and connect to the COM port
> BEFORE you flash.** The firmware auto-starts 3 seconds after every
> reset (including the reset CubeIDE issues at the end of programming).
> If the dashboard isn't connected and listening, you'll race the
> auto-start countdown. The dashboard auto-cancels by sending `STATUS`
> the moment it sees the boot message in the RX stream, so as long as
> it's already connected when the flash completes, you're safe.
>
> The ST-LINK exposes two independent USB endpoints — SWD (used by
> CubeIDE for programming) and VCP (used by the dashboard for UART) —
> so the two can run simultaneously without conflict.
>
> For Phase 0–1 (no power stages connected) auto-start firing is
> harmless — the MOSFET gates are unwired. From Phase 2 onward (gate
> drivers powered) this matters. **Make "dashboard first, then flash"
> a habit from the very first flash so you don't forget later.**

Pick **one** of these three methods. CubeIDE method is easiest if you
already have it open.

**Method 1 — CubeIDE Run/Debug button (recommended on first flash):**
1. Plug the Nucleo-F303RE into the PC via USB (the larger USB connector
   on the ST-LINK side, not the user USB).
2. Wait ~10 s for ST-LINK enumeration. The red LED on the ST-LINK side
   stops blinking and turns solid (or off, depending on board rev).
3. In CubeIDE: **Run → Run As → STM32 C/C++ Application**, or click the
   green play arrow in the toolbar.
4. First run only: CubeIDE pops up a "Debug Configurations" dialog.
   Accept defaults, click **OK**.
5. CubeIDE flashes the device. Status bar shows:
   ```
   Erasing flash... Programming... Verifying... Programming complete.
   ```
6. Nucleo resets and starts running the new firmware.

**Method 2 — Drag and drop (no CubeIDE needed after build):**
1. Plug Nucleo in via USB.
2. A removable drive named **NODE_F303RE** appears in File Explorer
   (one of the ST-LINK USB drives).
3. Open Explorer, drag `Debug\5levelchb.bin` onto the `NODE_F303RE`
   drive.
4. The drive's LED flickers, drive disconnects briefly (~3-5 s), then
   reappears. Flash complete.
5. Nucleo auto-resets and starts running.

**Method 3 — STM32CubeProgrammer CLI:**
```powershell
& "C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin\STM32_Programmer_CLI.exe" `
    -c port=SWD `
    -w Debug\5levelchb.hex `
    -rst
```

### 0.E — Set up the dashboard

First-time setup (skip if `dashboard\.venv` already exists):
```powershell
cd C:\Users\furka\Projects\5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE
py -3 -m venv dashboard\.venv
dashboard\.venv\Scripts\python -m pip install --upgrade pip
dashboard\.venv\Scripts\python -m pip install -r dashboard\requirements.txt
```

Every time after that:
```powershell
dashboard\.venv\Scripts\python dashboard\run_dashboard.py
```

In the dashboard window:
1. **Source** dropdown (top-left) → select **"Live serial"**.
2. Click **Refresh** next to the COM dropdown — your ST-LINK VCP port
   appears (typically `COMx` where x is some number; check Windows
   Device Manager → Ports if unsure).
3. Select that port, click **Connect**.
4. Status label changes to **"Connected to COMx"**.

If the COM dropdown shows "No ports": the ST-LINK USB driver isn't
installed. Download **ST-LINK USB driver** from [st.com](https://www.st.com/)
and reboot.

### 0.F — First boot verification (no power stages)

1. **Verify auto-start is cancelled by the dashboard.** The dashboard
   does two things to permanently prevent auto-start while connected:
   - On serial connect → sends `STATUS`, flipping
     `UART_ActivitySeen()` on the MCU.
   - On every detected `$A,BOOT_SELF_TEST_DONE` (i.e. every Nucleo
     reset while the dashboard is connected) → re-sends `STATUS`, so
     the flag is set again before the fresh 3 s window expires.

   Look for `[TX] STATUS (auto-cancel)` after the SERIAL connect
   message, and `[TX] STATUS (auto-cancel post-reset)` after each
   reset. With the dashboard connected you have full manual control
   and the inverter will NOT start on its own.

2. Press the Nucleo's **black reset button**.
3. Watch the Raw UART event log on the dashboard. Within ~1 second of
   reset you should see:
   ```
   $A,BOOT_SELF_TEST_DONE
   $C,mod=STAIR,fsw=500,bridge=BOTH,ffund=50.00,mi=0.95,cntoff=0,lock=OK
   $E,MODE_DEMOTED                         ← only if some sensors are absent
   $E,WARNING_OPEN_LOOP_NO_PROTECTION      ← only if no sensors present
   ```
   Followed by `$T,...` telemetry frames arriving at ~20 Hz.

4. Send `STATUS` — should get back one `$S,...` line summarising state.

5. Send `HELP` — should list all available commands including
   `MOD STAIR|PSC|STAIR_ALT`, `FSW`, `BRIDGE`, `FFUND`, `CONFIG`, `RESCAN`.

If you missed the 3 s window and see `$A,AUTO_START` followed by
`$A,RUN` — don't panic. With no power stages connected nothing is
energised. Send `STOP` to bring the FSM back to IDLE, then reset the
Nucleo if you want to start over.

**Verify before continuing:**
- [ ] `$C` line shows the expected STAIR / 500 / BOTH defaults.
- [ ] `lock=OK` in the `$C` line (will be `OK` for STAIR with `cntoff=0`).
- [ ] Telemetry arrives at ~20 Hz (visible in the dashboard plot).
- [ ] `STATUS`, `HELP`, `CONFIG` all respond.

If all four pass, the firmware is alive. Proceed to the
[Pre-bringup checklist](#pre-bringup-checklist) and then [Phase 1](#phase-1--continuity-no-power).

---

## Pre-bringup checklist

- [ ] [Step 0](#step-0--getting-the-firmware-onto-the-board) complete
      (branch flashed, dashboard connected, boot sequence verified).
- [ ] Build guide v3.1 Phase 1 (continuity check, no power) passed.
- [ ] ST-LINK VCP enumerated (Device Manager → Ports → STMicroelectronics
      STLink Virtual COM Port → note COM number).
- [ ] Terminal program ready as backup (PuTTY, Tera Term, or screen): 115200 8N1.
- [ ] Bench supplies set to current-limit mode, output OFF.
- [ ] **Auto-start awareness:** the firmware auto-issues `START` 3 s after
      boot if no UART byte has been received. Behavior by scenario:
      - **USB unplugged → auto-start fires** (standalone deployment).
      - **USB plugged, no PC software listening → auto-start fires** (USB
        is just powering the Nucleo).
      - **Dashboard connected → auto-start cancelled automatically.**
        The dashboard sends `STATUS` the moment it opens the serial port,
        which flips the firmware's `UART_ActivitySeen()` flag and blocks
        auto-start. You get full manual control.
      - **PuTTY / Tera Term connected but you don't type anything → auto-start
        fires after 3 s.** Type any character (or send a CR) to cancel.

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
     high, LS is low, and vice versa. Visible 3 µs dead-time on every
     transition.
4. Measure DC current draw from the 15 V supply: should be ~20–50 mA per
   bridge depending on switching activity.
5. `STOP` when done with bridge 1.

**Verify:**
- [ ] All 4 gates show clean square waves, no ringing, no missing edges.
- [ ] Dead-time visible on the LS-to-HS and HS-to-LS transitions (~3 µs).
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

> ⚠️ **Set `VNOM` to your test bus voltage before `START`.** The default
> protection thresholds assume a 50 V bus (UV = 40 V). At a 10 V test
> bus the firmware trips undervoltage immediately and never leaves
> PRECHARGE. `VNOM 10` rescales UV/OV/IMBAL to 8 / 11.6 / 2 V. This
> applies to every powered phase from here on — always match `VNOM` to
> the bus voltage you are about to apply.

**Steps:**
1. Reset Nucleo, cancel auto-start.
2. `VNOM 10` — rescale protection for the 10 V test bus. Confirm the
   `$P` line shows `uv=8.00,ov=11.60,imbal=2.00`.
3. `CONFIG` — confirm `mod=STAIR,fsw=500,bridge=BOTH,ffund=50.00,mi=0.95`.
4. `STATUS` — confirm both DC buses read ~10 V, iout ≈ 0 A.
5. `START`. Look for `$A,START`, then `$A,RUN` after ~6 ms precharge.
6. Scope the AC output (Node_X1 to Node_Y2) → expect a 5-level
   staircase swinging between roughly ±20 V at 50 Hz.
7. Watch telemetry. `iout` should swing sinusoidally with peak ~0.2 A
   (for 100 Ω load, 20 V/100 Ω = 0.2 A).
8. Run 5 minutes. Touch-test the bridge MOSFET heatsinks (with the back
   of your hand — never grip): you should already be able to feel that
   bridge 1's heatsink runs noticeably warmer than bridge 2's. **This is
   the concern #8 imbalance** that PSC fixes.
9. `STOP`.

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

## Phase 7b — Safe PSC bringup on the breadboard (do this BEFORE Phase 8)

**When to use this:** you've built the cascaded H-bridge on a breadboard
(not a PCB) and want to test PSC-PWM at 5 kHz directly. This is the
most demanding electrical condition the firmware will run on this
hardware. STAIR at 500 Hz tolerated breadboard parasitics easily;
PSC's 5 kHz switching with 90° interleave between bridges is much less
forgiving. Go through this BEFORE the full-voltage Phase 8.

**Why Phase 5–7 (STAIR at 500 Hz) doesn't prove PSC will work:**
- 10× more switching events per second → 10× the dI/dt-driven ringing
  in any parasitic inductance.
- Both bridges switch simultaneously through the same DC bus → 2× the
  capacitor ripple current of any single-bridge state.
- Gate-drive bandwidth requirements go up by 10×.
- Bootstrap caps refresh every 200 µs instead of every 2 ms — fine in
  steady state, marginal during transient duty-cycle changes.

### Breadboard-specific pre-flight (no power)

- [ ] **Branch flashed**, `$C,...,lock=OK,cntoff~=3199` visible in dashboard log
- [ ] **Phase 0–4 passed** (firmware boots, sensing self-tests correctly,
      gate drivers verified individually in Phase 2)
- [ ] **DC bus caps mounted directly across MOSFET drain-source nodes** —
      not via 5 cm of breadboard wire. If they're far, add 100 nF
      ceramic right at the package leads as a local snubber.
- [ ] **Gate wires < 5 cm each** between TLP250 output, the 22 Ω series
      resistor, and the MOSFET gate
- [ ] **TLP250 100 nF bypass cap directly on Pin 5 / Pin 8** — bend the
      cap leads to touch the IC pins, no breadboard hop
- [ ] **Heatsinks on all 8 MOSFETs** (clip-on TO-220 minimum)
- [ ] **Bench supplies OFF**, current limits set to 200 mA each
- [ ] **Dummy load:** 100 Ω, 10 W+ resistor across cascade AC output via ACS712
- [ ] **Scope ready** with 2 channels minimum, ground clip securely
      attached to GND_System (not a floating bridge node)
- [ ] **Emergency stop method identified** — bench-supply output button
      reachable without bending around the breadboard
- [ ] **Safety glasses on** — DC bus caps reversed or shorted can fail
      explosively

### Step A — Gates only, no DC bus

Goal: confirm PSC produces clean gate signals at the new switching
frequency with nothing on the bus to convert. If gates ring or
oscillate here, no point applying high voltage.

1. **Physically disconnect** both DC bus inputs from the bridges
   (unplug the wires from the bridge DC terminals — bench-supply OFF
   is not enough; the wires must be out so a slipped finger on the
   bench-supply switch can't energize the bus).
2. 15 V gate-drive supplies on.
3. Dashboard:
   ```
   MOD PSC
   FSW 5000
   BRIDGE BOTH
   MI 0.3
   ```
   Expect `$C,mod=PSC,fsw=5000,bridge=BOTH,ffund=50.00,mi=0.30,cntoff=3199,lock=OK`.
   **If `lock=BAD`, stop here** — fix the phase shift per the
   troubleshooting section before going further.
4. `START`.
5. Scope **PWM_1H (PA8) and PWM_3H (PB6) simultaneously**:
   - Both square waves at 5 kHz (200 µs period).
   - Rising edges offset by ~50 µs (90° at 5 kHz center-aligned).
   - Voltage swing 0 ↔ ~14 V.
6. Scope each of the 8 MOSFET gates one at a time (Vgs):
   - Clean rising/falling edges, ~50–100 ns rise time through the 22 Ω
     gate resistor.
   - **No ringing** during the flat ON or OFF portions.
   - Dead-time gap visible (~3 µs) on every complementary transition.
7. Watch the gate-drive 15 V supply current — should be < 50 mA per
   bridge at MI 0.3.
8. `STOP`. Disconnect 15 V if you're going to walk away.

**If gates look clean:** proceed to Step B.

**If gates oscillate / ring / show partial transitions:** the breadboard
gate-drive layout is the limit, not the firmware. Common fixes:
- Add a second 100 nF ceramic directly across TLP250 Pin 5 / Pin 8 on
  every driver.
- Shorten gate wires.
- Add a 10 kΩ Gate-Source pull-down (per build guide section 3.3.2 —
  may have been omitted).
- Move TLP250 supply ground return to star-ground at the MOSFET source.

### Step B — Single-bridge, very low DC bus

Goal: confirm one bridge produces correct 3-level PWM output, with the
other bridge silent. Catches gross PSC bugs and bridge isolation bugs
at the lowest possible energy.

1. Reconnect bridge 1's DC input. Leave bridge 2's input disconnected.
2. Bench supply 1: **5 V, 200 mA limit** (yes, 5 V, not 10 V — we're
   being paranoid). Output OFF.
3. Dashboard: `STOP` (if running), then
   ```
   MOD PSC
   FSW 5000
   BRIDGE B1
   MI 0.5
   ```
   `lock=OK` should still report.
4. `START`. (FSM goes through PRECHARGE → RUN; bridge 2 gates are silent
   because BRIDGE=B1 forces bridge 2 to freewheel.)
5. Bench supply 1: **output ON**. Watch current draw — should be
   < 100 mA at this voltage with 100 Ω load.
6. Scope cascade output (Node_X1 to Node_Y2):
   - Should see PWM at 5 kHz switching between **3 distinct levels**:
     `-5 V`, `0 V`, `+5 V`.
   - The "envelope" of the PWM follows a 50 Hz sine of amplitude ~±5 V
     × MI = ±2.5 V.
7. Watch DC bus current on the supply ammeter — should be small and
   roughly sinusoidal.
8. Touch-test bridge 1 MOSFETs after 30 s (back of hand only) — should
   be warm at most, not hot.
9. `STOP`, bench supply 1 OFF.

**If you see only `0 V` and `±5 V` (no intermediate level):** wait,
that IS 3-level for a single bridge — that's correct. The 5-level
cascade output only appears when both bridges contribute (Step D).

**If you see strange waveforms or fault trips:** STOP, post-mortem
before continuing.

### Step C — Repeat for bridge 2

1. Disconnect bridge 1 DC input. Reconnect bridge 2.
2. Bench supply 2: 5 V, 200 mA limit, OFF.
3. Dashboard: `STOP`, `BRIDGE B2`, `START`.
4. Bench supply 2 ON.
5. Scope: same 3-level PWM, bridge 1 gates now silent.
6. `STOP`, supply 2 OFF.

**If either Step B or C fails but the other works:** the firmware is
fine, the problem is hardware on the failing bridge. Inspect gate
wiring, bootstrap diode/cap, MOSFETs.

### Step D — Cascaded, very low DC bus — the 5-level moment of truth

Goal: prove 5 levels appear at the output with both bridges contributing.
Still at very low voltage so a failure mode is recoverable.

1. Reconnect both bridge DC inputs.
2. Both bench supplies: **5 V, 200 mA limit**, OFF.
3. Dashboard: `STOP`, `BRIDGE BOTH`, `START`.
4. **Both supplies ON simultaneously** (or as close as you can manage).
5. Scope cascade output, sweep at 50 µs/div, vertical 5 V/div:
   - Expect **5 distinct levels**: `-10 V`, `-5 V`, `0 V`, `+5 V`, `+10 V`.
   - PWM at 5 kHz between them.
   - Density of points at each level varies over the 50 Hz fundamental.
   - Use persistence mode if your scope supports it — bands light up clearly.
6. Watch DC bus currents on both supplies — both should be similar
   (within 10–20 % of each other). **If one bridge draws much more
   than the other, you have a different problem from concern #8 — stop
   and investigate.**
7. Run 30 s. Touch-test MOSFETs on both bridges — should be similar
   temperatures.
8. `STOP`, both supplies OFF.

**If only 3 levels visible (-10 V, 0 V, +10 V) instead of 5:** the
phase shift is broken. STOP, check `$C,...,lock=` — was it `OK` when
you started? If yes, the firmware thinks the shift is locked but the
hardware isn't honoring it. Apply Fix A or D from the
[Troubleshooting](#troubleshooting-psc-carrier-shift) section, or
fall back to STAIR_ALT (Phase 8b).

**If 5 levels visible:** ✅ this is the project deliverable working.
Proceed to Step E.

### Step E — Gradual voltage ramp

Goal: confirm everything stays stable as voltage and current go up.

For each voltage step `V_target = 10, 20, 30, 40, 50` V:

1. `STOP`. Both supplies OFF.
2. Set both supplies to `V_target`, **current limit 500 mA initially**
   (raise to 1 A once V_target ≥ 30 V, to 5 A at 50 V).
3. Dashboard: confirm `MOD PSC`, `FSW 5000`, `BRIDGE BOTH`, `MI 0.5`.
4. `START`.
5. Both supplies ON.
6. Scope: 5 levels still present at `±2·V_target`. Envelope a clean
   ~50 Hz sine.
7. Check dashboard telemetry:
   - `vdc1` and `vdc2` both within 1 V of supply setting under load
   - `iout` peak ≈ `2 · V_target · MI / R_load`. For 20 V bus, MI 0.5,
     100 Ω load: peak ≈ 200 mA.
   - No `$F,...` fault lines.
8. Watch supplies' actual current draw — should match `iout` (averaged).
9. Touch-test MOSFETs after 30 s at each step.
10. `STOP` between steps for cool-down (longer at higher voltages).

**Stop the ramp at the first sign of any of these:**
- Output waveform degrades (extra levels appearing, asymmetry growing)
- A MOSFET getting noticeably hotter than its mates
- DC bus voltage drooping more than ~2 V under load (cap or supply
  inadequate for ripple)
- Any `$F,...` fault line
- Visible smoke (this should not need saying, but…)
- Smell of hot insulation

### Step F — MI ramp at target voltage

Once you've reached your target bus voltage stably:

1. `STOP`. `MI 0.5`. `START`. Confirm output is sinusoidal envelope.
2. `STOP`. `MI 0.7`. `START`. Output amplitude scales up.
3. `STOP`. `MI 0.95`. `START`. Maximum output amplitude.
4. At each MI, run 30 s and confirm:
   - Output still 5-level.
   - Bridge 1 and Bridge 2 MOSFETs at similar temperatures.
   - No fault trips.

### Step G — Sustained run

Once Steps A–F all pass cleanly:

1. `STOP`. Set everything to your final operating point (50 V bus,
   MI 0.95, BRIDGE BOTH, FSW 5000, MOD PSC).
2. `START`.
3. Run 5–15 minutes, **watching the scope and thermals the whole time**.
4. Log heatsink temperatures every 2 minutes.
5. Compare bridge 1 vs bridge 2 thermals at steady state — should be
   within 5 °C. This is the headline result.

### Breadboard-specific failure modes to watch for

- **Gates oscillating mid-pulse** — TLP250 supply bypass insufficient
  for 5 kHz switching. Add 100 nF directly on Pin 5/8.
- **Output waveform "fuzzy" at level boundaries** — ground bounce from
  high dI/dt. Star-ground the gate-drive returns at each MOSFET source.
- **Output level voltage sagging under load** — DC bus cap too far from
  switches. Add 1 µF ceramic directly across drain-source pairs.
- **Random fault trips even at low voltage** — EMI corrupting MCP3201
  SPI reads. Move SPI wires away from the H-bridge wires; route SPI
  ground separately back to the safe-side ground.
- **MOSFET smoking** — shoot-through. Verify dead-time on scope at the
  exact moment of failure; dead-time is already 3 µs (`TIM_DTG_3US_AT_64MHZ`)
  for the IRFB4110, but if the breadboard gate drive is slow you may need
  to go to 4 µs — change `PWM_DEAD_TIME_DTG` to `TIM_DTG_4US_AT_64MHZ` in
  [pwm_modulator.c](Core/Src/pwm_modulator.c) and reflash.
- **No 5-level output despite `lock=OK`** — phase shift good in
  firmware but breadboard parasitic L/C distorting the cascade. Add
  a snubber across each MOSFET drain-source (already in BOM:
  22 Ω + 2.2 nF series).

If everything passes through Step G, you're ready for the full Phase 8
sustained-load characterization on a real load.

---

## Phase 8 — PSC switchover and 5-level verification (the headline test)

**Goal:** prove PSC delivers both (a) the **5 distinct cascade levels**
the project requires when run without an output filter, and (b) the
bridge-thermal balance from concern #8.

> **Why this matters more than thermal alone:** STAIR (the OLD modulator)
> only *looks* like a 5-level output. It's static voltage selection at
> 500 Hz, holding each level for 2 ms — the legs only "switch" 1 % of the
> time for bootstrap refresh. It is **not real PWM** and a power-electronics
> grader will notice. PSC produces true PWM modulation where the cascaded
> output switches at 5 kHz between 5 distinct levels in a pattern that
> averages (over the carrier period) to the reference sine. **This is
> what the project actually requires.**

**Setup:** Same as Phase 7 (50 V bus, rated load — a 100 Ω dummy resistor
or similar; NO LC filter at the output, that's deliberate). Bridge 1
heatsink temperature from end of Phase 7 noted.

**Steps:**
1. `STOP` (if running).
2. Let the bridges cool to ambient (5 min, or use a fan).
3. Switch to PSC:
   ```
   MOD PSC
   FSW 5000
   ```
4. **Check the firmware-side phase-lock diagnostic** in the `$C` line
   that's emitted automatically on the config change:
   ```
   $C,mod=PSC,fsw=5000,bridge=BOTH,ffund=50.00,mi=0.95,cntoff=3200,lock=OK
   ```
   `cntoff` is the measured TIM8-vs-TIM1 counter offset in clock ticks.
   For PSC at 5 kHz with the 64 MHz timer clock, `PWM_PERIOD = 6399`
   and the target offset is `6399 / 2 = 3199` (≈ 50 µs of 200 µs period
   = 90° of the 400 µs center-aligned cycle). `lock=OK` means the
   measured offset is within ±5 % of target. **`lock=BAD` means the
   90° shift didn't take and the output will be 3-level instead of
   5-level** — see [Troubleshooting: PSC carrier shift](#troubleshooting-psc-carrier-shift)
   before proceeding.
5. `START`.
6. **Scope the cascade output (Node_X1 to Node_Y2) — this is the
   5-level verification.** Set:
   - Vertical: 25 V/div (so ±2Vdc = ±100 V fits with headroom).
   - Horizontal: 50 µs/div for the carrier view, OR 2 ms/div for the
     envelope view.
   - Probe: use a differential probe or two grounded probes with math
     (A−B). The output is floating.
   - Trigger: AC line or self.

   **Expected with `lock=OK`:** the trace at 50 µs/div sweeps between
   5 distinct horizontal voltage bands — `-100 V`, `-50 V`, `0 V`,
   `+50 V`, `+100 V`. The density of points at each level varies over
   the fundamental cycle (more time at ±100 V near the sine peaks,
   more time at 0 V near zero-crossings). Use persistence mode if your
   scope supports it; you'll see all 5 bands light up clearly.

   **Expected with `lock=BAD`:** the trace shows only 3 bands —
   `-100 V`, `0 V`, `+100 V`. The intermediate ±50 V steps are absent
   because both bridges switch in phase. Bridge thermals will still
   balance (PSC's structural fix), but the project's 5-level
   requirement is not met. Fix the phase shift before proceeding.

7. **Scope two gates simultaneously**: PWM_1H (PA8) and PWM_3H (PB6),
   at MI 0.3 so both are clearly switching. The rising edges should be
   offset by ~50 µs at FSW=5 kHz. This visually confirms the same
   90° phase shift that the `cntoff` diagnostic reports.
8. Set MI back to 0.95: `STOP`, `MI 0.95`, `START`.
9. Run 15 min at full load. Log both bridges' heatsink temperatures
   every 3 minutes.

**Verify (this is the moment of truth):**
- [ ] `$C,...,lock=OK` appears after the `MOD PSC` command.
- [ ] Cascade output scope shows **5 distinct voltage bands** at
      −100 / −50 / 0 / +50 / +100 V (not just 3).
- [ ] PWM_1H and PWM_3H scoped together show ~50 µs offset between
      rising edges.
- [ ] Bridge 1 and bridge 2 heatsinks converge to **within ~5 °C** of
      each other at steady state.
- [ ] Total temperature is similar to or slightly lower than the Phase 7
      STAIR baseline (PSC has more switching events but more even
      distribution between bridges).
- [ ] No fault trips during the 15-minute run.

**If 5-level output is NOT visible** (only 3 levels) — the 90° shift is
broken. See [Troubleshooting: PSC carrier shift](#troubleshooting-psc-carrier-shift).
**The project requirement is not met until 5 levels show up on the
scope.** Apply the troubleshooting fixes before continuing. If none of
them work, fall back to `MOD STAIR_ALT` (Phase 8b) — you lose true PWM
modulation but keep 5 visible levels and balanced bridges.

**If PSC works:** edit
[Core/Inc/pwm_config.h](Core/Inc/pwm_config.h#L32)
line `#define PWM_DEFAULT_MODULATOR MODULATOR_STAIR` to
`MODULATOR_PSC`, also change `PWM_DEFAULT_SWITCHING_HZ` from `500u` to
`5000u`. Rebuild, re-flash. Now PSC is the auto-start default.

---

## Phase 8b — STAIR_ALT fallback (only if PSC won't deliver 5 levels)

**Goal:** keep the project's 5-level deliverable AND fix the bridge-1
thermal imbalance, even if PSC's 90° phase shift cannot be made to work.

**What STAIR_ALT is:** same staircase output as the OLD STAIR — 5 levels
held statically for 2 ms each, only 1 % bootstrap-refresh "switching."
**Not real PWM**, same caveat as STAIR. The improvement: the bridge that
carries the ±1 step alternates every time the level is re-entered, so
over ~2 fundamental cycles each bridge handles ±1 equally often.

**When to use:** ONLY if PSC mode produces 3-level output and the
troubleshooting steps don't recover 5-level. STAIR_ALT preserves the
5-visible-levels deliverable; PSC at 3 levels does not.

**Steps:**
1. `STOP`, `MOD STAIR_ALT`, `FSW 500`, `START`.
2. Scope the cascade output — should look identical to Phase 7 STAIR:
   5-level staircase, slow steps, no fast PWM activity. 5 levels are
   trivially present because STAIR_ALT uses the same level-selection
   logic.
3. Run 15 min at full load. Heatsink temperatures should converge to
   within ~5 °C as the bridge-1/bridge-2 ownership of ±1 alternates.
4. Caveat for grading: be honest that this is not real PWM modulation.
   The 5 levels are shown but the inverter is operating as a
   programmable staircase generator, not a multilevel PWM converter.

---

## Phase 9 — Frequency sweep (optional, characterization)

**Goal:** find the best FSW for your hardware/filter combination.

**Steps:**
- `STOP`, `FSW 1000`, `START` → 10 min, log thermals.
- `STOP`, `FSW 2000`, `START` → 10 min, log thermals.
- `STOP`, `FSW 5000`, `START` → 10 min, log thermals.
- `STOP`, `FSW 10000`, `START` → 10 min, log thermals.

Higher FSW = lower output ripple but higher switching loss. Plot total
loss vs FSW; the minimum is your sweet spot. With IRFB4110 (low 4.5 mOhm
Rds(on) but ~150 nC gate charge) + TLP250, expect the sweet spot around
5–10 kHz — conduction loss is very low so switching loss dominates as
FSW rises.

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
**Symptom:** PSC mode produces 3-level output instead of 5-level at the
cascade. **For this project this is a hard failure — 5 levels are the
deliverable.**

**Two diagnostics, in order:**

**Step 1 — firmware self-report (instant, no scope).** Look at the `$C`
line that was emitted on the `MOD PSC` command:
```
$C,mod=PSC,fsw=5000,bridge=BOTH,ffund=50.00,mi=0.95,cntoff=N,lock=OK|BAD
```
`cntoff` is the measured TIM8-TIM1 counter offset in clock ticks (one
tick = 15.625 ns at 64 MHz). At FSW=5 kHz the expected value is 3199
(±5 %). `lock=OK` means the firmware confirms the shift took.
`lock=BAD` means it didn't.

**Step 2 — scope confirmation.** Scope PWM_1H (PA8) and PWM_3H (PB6)
simultaneously at MI 0.3.

| Measured scope offset (at FSW 5 kHz) | `cntoff` value | Diagnosis | Action |
|---|---|---|---|
| ~50 µs (90°) | ~3199 | Working as intended | Continue to Phase 8 |
| ~0 µs (in phase) | <300 or >6099 | TIM8 CNT preset didn't stick | Try *Fix A* |
| ~100 µs (180°) | ~6399 or ~0 | Wrong divisor | Try *Fix B* |
| Drifts over many ms | varies | Timers not clock-locked | *Fix C* |
| `lock=BAD` but `cntoff` looks right | — | Tolerance too tight | *Fix E* |

**Why this matters for the project:** unlike the previous version of
this doc, broken phase shift is now a project-blocking issue because
the deliverable is 5 visible cascade levels without an output filter.
3-level output fails the project spec.

**However:** if all four fixes below fail, **fall back to STAIR_ALT
(Phase 8b)**, which preserves 5 visible levels (statically) and the
bridge balance, at the cost of giving up on real PWM modulation.

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

**Fix E — Loosen the lock tolerance:**
The firmware reports `lock=BAD` when measured offset is >5 % off the
expected ARR/2. If the scope shows correct ~50 µs separation but the
firmware reports `lock=BAD`, the tolerance is too tight (likely because
the post-CEN CNT read happened a few cycles into the count). Edit
[Core/Src/pwm_modulator.c](Core/Src/pwm_modulator.c) the line:
```c
uint32_t tolerance = (g_pwm_period / 20u) + 4u;
```
Increase the additive slack from `4u` to e.g. `64u` (1 µs at 64 MHz).
Rebuild. Only do this if the scope confirms the actual offset is correct
and only the diagnostic is over-strict.

**Fall-back if all of A–E fail:**
Use `MOD STAIR_ALT` (Phase 8b). Keeps 5 visible levels at the cascade
output, balances bridges via alternation, sacrifices true PWM modulation.
The scope will show the same 5-step staircase as OLD STAIR, not the
high-frequency PWM modulation that PSC produces. This is the
project-grade backstop.

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
