# First Bench Session — Breadboard CHB, Two Bridges, All Three Modulators

This is a **linear walkthrough** of one bench session. Goal: take code
from the `pwm-rewrite-configurable` git branch and confirm — on the
fully built breadboard cascaded H-bridge — that all three modulators
(STAIR, STAIR_ALT, PSC) work safely, ending with PSC producing 5
distinct cascade levels.

It folds together the relevant bits of `HARDWARE_BRINGUP.md` (Step 0,
Phases 2–7b, Phase 8) into one continuous procedure so you don't have
to jump around mid-bench.

**Estimated time:** 2–3 hours including thermal soaks. Two people is
better than one — one watches the scope, the other handles supplies.

**Headline safety goal:** do not burn a TLP250, do not burn a MOSFET.
Every step below has explicit pass/fail criteria; **if anything is
unexpected, STOP** and consult [HARDWARE_BRINGUP.md](HARDWARE_BRINGUP.md)
troubleshooting before continuing.

---

## What to have ready at the bench

- [ ] USB cable (Nucleo ST-LINK end to PC)
- [ ] **Two** bench DC supplies, 0–60 V, with current limiting
- [ ] One 15 V bench supply for gate drive (or use the B0515S after Phase 3)
- [ ] Dummy load: 100 Ω, 10 W+ resistor (a few in parallel is fine)
- [ ] Oscilloscope, 2+ channels, 50 MHz+ bandwidth, with **two** probes
- [ ] Multimeter
- [ ] **Heatsinks attached to all 8 MOSFETs** — no exceptions
- [ ] Safety glasses, hands clear of the breadboard during operation
- [ ] A way to instantly cut DC bus power (bench-supply output enable button)
- [ ] A second person if possible

---

## Session pass/fail checklist (track top-to-bottom)

- [ ] A. Code + dashboard ready
- [ ] B. First boot verified, defaults loaded, `lock=OK`
- [ ] C. Sensors read known voltage correctly (5 V → vdc ≈ 5 V)
- [ ] D. All 8 gates switch cleanly under STAIR with **no DC bus**
- [ ] E. STAIR cascaded at 10 V — 5-level staircase confirmed
- [ ] F. STAIR_ALT cascaded at 10 V — same staircase, bridges balance
- [ ] G. PSC single bridge at 5 V — 3-level PWM, other bridge silent
- [ ] H. PSC cascaded at 5 V — **5-level PWM visible** ← the project deliverable
- [ ] I. PSC ramped to 50 V step-by-step without trouble
- [ ] J. PSC sustained run, bridges thermally matched

---

## Section A — Code and dashboard ready

### A.1 — On the dev PC: commit and push the branch

If you've already pushed since the last code change, skip to A.2.

```powershell
cd C:\Users\furka\Projects\5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE
git status
git branch --show-current     # must print: pwm-rewrite-configurable

git add -A
git commit -m "PSC-PWM rewrite: configurable modulator, STAIR_ALT fallback, auto-cancel on dashboard connect"
git push -u origin pwm-rewrite-configurable
```

### A.2 — On the bench PC: clone the repo (if empty folder)

The bench PC starts with an empty folder, no git history yet. Open
PowerShell:

```powershell
# Make a Projects folder if you don't already have one
mkdir C:\Projects -ErrorAction SilentlyContinue
cd C:\Projects

# Clone your fork (the one we pushed to in A.1)
git clone https://github.com/feaksel/5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE.git

# Enter the freshly-cloned directory
cd 5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE

# Switch to the working branch (git clone defaults to main)
git checkout pwm-rewrite-configurable

# Confirm the newest commit matches what you pushed in A.1
git log --oneline -3
```

**First-time HTTPS clone:** GitHub will prompt for credentials. Password
auth is deprecated — use a Personal Access Token instead. Create one
at GitHub → Settings → Developer settings → Personal access tokens →
Tokens (classic) → Generate new. Scope: `repo`. Paste the token when
prompted for the password. Windows Credential Manager will remember
it for subsequent operations.

**If git isn't installed on the bench PC:** download from
[git-scm.com/download/win](https://git-scm.com/download/win), accept
all defaults during install, restart PowerShell, then run the clone.

**If the folder already has the repo from a previous session**
(skip this if you just cloned fresh):
```powershell
cd C:\Projects\5-Level-Cascaded-H-bridge-Inverter-with-STM32-Nucleo-F303RE
git fetch
git checkout pwm-rewrite-configurable
git pull
git log --oneline -3
```

### A.3 — Set up the dashboard (first time only)

```powershell
cd <repo>
py -3 -m venv dashboard\.venv
dashboard\.venv\Scripts\python -m pip install --upgrade pip
dashboard\.venv\Scripts\python -m pip install -r dashboard\requirements.txt
```

### A.4 — Verify dashboard launches

```powershell
dashboard\.venv\Scripts\python dashboard\run_dashboard.py
```

The dashboard window opens. Close it for now.

✅ **Pass A:** dashboard launched without errors.

---

## Section B — Flash and first boot

> ⚠️ **Critical ordering: dashboard FIRST, flash SECOND.**
> The firmware auto-starts 3 s after every reset. With the dashboard
> already connected when CubeIDE resets the Nucleo at end-of-flash,
> the dashboard auto-cancels by sending `STATUS` the instant it sees
> the boot message. Without the dashboard, you race the 3 s timer.

### B.1 — Plug USB into the Nucleo's ST-LINK end

The big USB connector at the top of the Nucleo board. Wait ~5 s for
Windows to enumerate two devices:
- STMicroelectronics ST-LINK (debugger)
- USB Serial Device / STLink Virtual COM Port (your UART)

Note the COM number from Device Manager → Ports.

### B.2 — Open dashboard, connect to COM port — BEFORE flashing

```powershell
dashboard\.venv\Scripts\python dashboard\run_dashboard.py
```

In the dashboard:
1. Source dropdown → **Live serial**
2. Click **Refresh** → your COM port appears
3. Select it → click **Connect**
4. Status changes to "Connected to COMx"
5. Event log shows `[TX] STATUS (auto-cancel)` immediately

If the old firmware is running, you'll see `$E,UNKNOWN_COMMAND` in
response to `STATUS` — that's expected; the old firmware doesn't know
the new commands. Ignore it.

### B.3 — Open the project in STM32CubeIDE

1. Launch STM32CubeIDE, pick a workspace folder
2. **File → Open Projects from File System...**
3. Browse to the repo root → Finish
4. Wait for indexing to finish (bottom-right progress bar)

### B.4 — Build

**Project → Build All** (or Ctrl+B). Console should end with:
```
arm-none-eabi-size  Debug/5levelchb.elf
   text    data     bss     dec     hex filename
  36660     468    3668   40796    9f5c Debug/5levelchb.elf
Finished building target: 5levelchb.elf
```

Build errors? Check Console panel; usually toolchain or missing
include. Don't proceed to flash if build failed.

### B.5 — Flash

**Run → Run As → STM32 C/C++ Application** (or click green play arrow).
First time: accept the default Debug Configuration. CubeIDE flashes
and resets the Nucleo.

### B.6 — Verify boot in dashboard

Watch the event log. Within 1 s of flash completion you should see:

```
[ACK]    BOOT_SELF_TEST_DONE
[TX]     STATUS (auto-cancel post-reset)
[ACK]    STATUS
[STATUS] ms=42,state=IDLE,mode=...
[CONFIG] mod=STAIR,fsw=500,bridge=BOTH,ffund=50.00,mi=0.95,cntoff=0,lock=OK
[TELEMETRY ARRIVING] $T,...                   ← 20 Hz
```

Confirm:
- [ ] `$A,BOOT_SELF_TEST_DONE` arrived
- [ ] `STATUS (auto-cancel post-reset)` event present → auto-start cancelled
- [ ] `$C` config line shows defaults: `STAIR / 500 / BOTH / mi=0.95`
- [ ] `lock=OK` (for STAIR at FSW=500, `cntoff=0` and `lock=OK`)
- [ ] Telemetry frames arriving at ~20 Hz (dashboard plot updates)

✅ **Pass B:** boot clean, defaults loaded, dashboard in control.

❌ If `lock=BAD` here, something's wrong with the diagnostic itself
(in STAIR mode, expected offset is 0, so it should always be OK).
Stop and investigate.

---

## Section C — Sensor decode verification (no power stages)

This catches the MCP3201 shift problem early. Phase 4 of the main
bringup doc, condensed.

### C.1 — DC inputs disconnected, 5 V bench supply standalone

1. With both bridge DC inputs disconnected, take a separate small bench
   supply, set it to **5.0 V exactly**, current limit 100 mA.
2. Touch its + lead to bridge 1's DC bus input terminal, − to GND_HV
   for that bridge. **Just touch, no permanent wiring yet** — this is
   a one-shot test.
3. Dashboard: send `STATUS`. Watch the `$S,...` response.
4. The `vdc1` field should read **4.7–5.3 V**.

| `vdc1` reading | Diagnosis | Action |
|---|---|---|
| 4.7–5.3 V | ✅ MCP3201 decode correct | Proceed to C.2 |
| ~64 V | ❌ Bit-shift is `>> 3` but should be `>> 1` | See [HARDWARE_BRINGUP.md Phase 4 fix](HARDWARE_BRINGUP.md) — swap and reflash before continuing |
| 0 V / NAN | ❌ Sensor not seeing the input | Check wiring of voltage divider |
| Stuck mid-scale | ❌ Sensor hardware fault | Check 78L05 supply, MCP3201 power |

### C.2 — Repeat for bridge 2

Same procedure on bridge 2's DC input. `vdc2` should read 4.7–5.3 V.

✅ **Pass C:** both sensors track applied voltage linearly.

---

## Section D — Gate drive verification, DC bus DISCONNECTED

> ⚠️ **DC bus inputs MUST be physically disconnected during this section.**
> Bench supply OFF is not enough — pull the wires from the bridge DC
> input terminals so a slipped finger on the supply button can't
> energize anything.

> ⚠️ **TLP250 protection points:**
> - 15 V supply must be ≤ 16 V. Don't apply 20 V "for headroom." TLP250
>   absolute max VCC is 20 V; the 100 nF bypass cap is rated 25 V.
> - 220 Ω input limit resistor must be in place — without it, MCU pin
>   sees direct LED forward voltage and overcurrent.
> - 100 nF bypass cap **must be directly across Pin 5 / Pin 8**, leads
>   bent to touch the IC. Breadboard hop of >2 cm causes oscillation
>   at 5 kHz and the TLP250 will heat fast.

### D.1 — Gate-drive supply on

External 15 V bench supply (or B0515S if you've validated those in
Phase 3 of the main doc) connected to **+15V_Drive** and **Drive_GND**
rails on both bridges. Current limit 200 mA per bridge.

### D.2 — STAIR baseline at 500 Hz (default mode)

Dashboard:
```
STOP                  (in case auto-start has fired — it should not have)
CONFIG                (verify STAIR/500/BOTH defaults)
MI 0.5                (moderate amplitude so all 5 levels are exercised)
START
```

Look for `$A,RUN` in event log within ~10 ms.

### D.3 — Scope each gate

With STAIR running, scope **Vgs** (gate-to-source) of each of the 8
MOSFETs one at a time. Expected at 500 Hz with MI 0.5:

- HS gates (Q1/Q3 of each bridge): 0 V ↔ ~14 V transitions, but with
  STAIR these happen **slowly** (level transitions every 2 ms or so).
- LS gates (Q2/Q4): complementary to their HS partners.
- Dead-time gap visible (~2 µs) on every transition.

Touch-test each TLP250 package. Should be **cool to the touch (room
temperature)** — STAIR is gentle on the drivers.

### D.4 — Bridge isolation at the gate level

```
STOP
BRIDGE B1
START
```

Now ONLY bridge 1's gates should switch. Bridge 2's 4 gates should
be silent (Q5/Q7 HS at 0 V; Q6/Q8 LS at ~14 V — freewheel state).

Scope to confirm. Then:

```
STOP
BRIDGE B2
START
```

Now bridge 2's gates switch and bridge 1's are silent. Confirm.

```
STOP
BRIDGE BOTH
```

### D.5 — Quick PSC gate check (still no DC bus)

```
MOD PSC
FSW 5000
MI 0.3
CONFIG                (confirm cntoff ~ 3199, lock=OK)
START
```

⚠️ **Stop in 30 seconds maximum.** This is just a sanity check — we
don't want to thermal-soak TLP250s at 5 kHz without bypass-cap
verification yet.

Scope **PWM_1H (PA8) and PWM_3H (PB6) simultaneously**:
- Both should switch every 200 µs (5 kHz)
- Rising edges offset by ~50 µs (90°)
- Vgs amplitude 0–14 V, clean transitions

Touch-test TLP250s. **They should still be cool.** If any TLP250 is
already warm after 30 s, STOP — that driver's bypass cap is
inadequate and will fail under load.

```
STOP
```

### D.6 — Verdict on TLP250 health

After Section D, all 8 TLP250s should be:
- [ ] At room temperature
- [ ] Producing clean Vgs waveforms (no ringing, no slow edges)
- [ ] Maintaining dead-time on every transition
- [ ] Responding to bridge-isolation commands correctly

✅ **Pass D:** gate drive is solid. Safe to add DC bus voltage.

❌ If any TLP250 is warm, oscillating, or has malformed Vgs — STOP.
Apply fixes from [HARDWARE_BRINGUP.md Phase 7b](HARDWARE_BRINGUP.md)
troubleshooting (bypass cap closer, shorter gate wires, etc.) and
re-run Section D. Do NOT add DC bus voltage until D passes cleanly.

---

## Section E — STAIR cascaded at 10 V (baseline / regression)

The OLD bench-validated PWM. If this doesn't work, the new branch has
broken something — fix that before going further.

### E.1 — Hook up DC buses and load

1. Bench supplies OFF, output disabled
2. Set both supplies: **10.0 V, current limit 500 mA**
3. Connect supply 1 to bridge 1 DC input (+ to + terminal, − to bridge 1
   GND_HV)
4. Connect supply 2 to bridge 2 DC input
5. Connect 100 Ω dummy load across the cascade AC output through the
   ACS712 (Node_X1 → ACS712 → 100Ω → Node_Y2)

### E.2 — Run STAIR

Dashboard:
```
STOP
MOD STAIR
FSW 500
BRIDGE BOTH
MI 0.95
CONFIG                (verify settings)
START
```

Wait for `$A,RUN`.

### E.3 — Bring up bus voltage

1. Bench supply 1: output ON. Watch ammeter — should be < 50 mA.
2. Bench supply 2: output ON. Same.

Dashboard `vdc1` and `vdc2` should both read ~10 V.

### E.4 — Scope the cascade output

Set scope:
- Vertical: 5 V/div (cascade should swing ±20 V)
- Horizontal: 2 ms/div
- Vsource: differential probe or A−B math

Expect a **5-level staircase**: clear voltage steps at −20, −10, 0, +10,
+20 V, each held for various integer multiples of 2 ms. Total waveform
period 20 ms (50 Hz).

### E.5 — Touch test after 1 minute

After 1 minute at 10 V:
- Bridge 1 MOSFETs: noticeably warm
- Bridge 2 MOSFETs: cooler than bridge 1
- TLP250s: still cool to touch
- DC bus caps: ambient

**This thermal asymmetry between bridges IS the concern #8 problem
that PSC fixes.** Confirming it here proves the imbalance is real and
your hardware is producing it.

### E.6 — Stop

```
STOP
```

Both bench supplies OFF.

✅ **Pass E:** STAIR works as expected. Baseline established.

---

## Section F — STAIR_ALT cascaded at 10 V (verify the easy fallback)

Same setup as E. Confirms STAIR_ALT compiles and runs and that the
bridge alternation logic is doing what it should.

### F.1 — Switch to STAIR_ALT

```
MOD STAIR_ALT
CONFIG                (verify mod=STAIR_ALT)
START
```

### F.2 — Bring up bus voltage

Both supplies ON at 10 V, 500 mA limit.

### F.3 — Scope

Same as E.4 — should be **identical 5-level staircase output**.
STAIR_ALT doesn't change the output shape, only which bridge handles
each ±1 step.

### F.4 — Thermal check after 2–3 minutes

This is where STAIR_ALT differs from STAIR:
- Bridge 1 MOSFETs: warm
- Bridge 2 MOSFETs: warm (more than under STAIR)
- The two bridges should converge toward similar temperature

You're alternating ±1-step ownership ~12 times per fundamental cycle,
so over 2–3 fundamental cycles each bridge has done the same work.

### F.5 — Stop

```
STOP
```

Both bench supplies OFF.

✅ **Pass F:** STAIR_ALT works, bridges balance. This is your
no-PSC-needed fallback for the demo if PSC misbehaves.

---

## Section G — PSC single bridge at 5 V (low-risk PSC entry)

> ⚠️ **Drop the voltage to 5 V here.** PSC at 5 kHz is more demanding
> on every component than STAIR at 500 Hz. We're starting low so any
> first-time PSC failure is recoverable.

### G.1 — Set supplies to 5 V

Both supplies: **5.0 V, current limit 200 mA**, OFF.

### G.2 — PSC bridge 1 only

```
STOP
MOD PSC
FSW 5000
BRIDGE B1
MI 0.5
CONFIG                (check: cntoff=3199, lock=OK)
START
```

❌ If `lock=BAD`, STOP. The 90° shift didn't take. Try `MOD STAIR`,
then `MOD PSC` again (toggles cause a re-init). If still BAD, see
[HARDWARE_BRINGUP.md PSC carrier shift troubleshooting](HARDWARE_BRINGUP.md#troubleshooting-psc-carrier-shift).

### G.3 — Energize bridge 1 only

Bench supply 1: ON. Watch ammeter — should be < 50 mA.
**Do NOT turn on supply 2 yet.**

### G.4 — Scope cascade output

Set scope:
- Vertical: 2 V/div
- Horizontal: 50 µs/div
- Persistence mode if available

Expect **3 distinct voltage bands**: −5 V, 0 V, +5 V. PWM switching
at 5 kHz between them. Because only bridge 1 is active, only 3 levels
are possible.

### G.5 — Verify bridge 2 silent

Scope bridge 2's MOSFETs gates briefly. Q5/Q7 (HS) should sit at 0 V.
Q6/Q8 (LS) should sit at ~14 V (freewheel). No switching.

### G.6 — Touch test after 30 s

- Bridge 1 MOSFETs: warm
- Bridge 2 MOSFETs: cool (ambient — only LS conducting freewheel
  current, which is ~0 with no current through the silent half)
- TLP250s: still cool

### G.7 — Stop

```
STOP
```

Supply 1 OFF.

✅ **Pass G:** PSC works on a single bridge at low voltage.

### G.8 — Repeat for bridge 2

```
BRIDGE B2
START
```

Supply 2 ON (not supply 1).

Same expectations: 3-level output, bridge 1 silent, MOSFETs warm only
on bridge 2.

```
STOP
```

Supply 2 OFF.

✅ **Pass G (full):** both bridges run PSC independently.

---

## Section H — PSC cascaded at 5 V (the 5-level moment of truth)

The single most important test in the session. **If this passes, the
project deliverable is achieved.**

### H.1 — Re-arm cascade mode

```
STOP
BRIDGE BOTH
MI 0.5
CONFIG                (one more sanity check on lock=OK)
START
```

### H.2 — Energize both supplies SIMULTANEOUSLY

Both supplies still at 5 V, 200 mA limit.

Either supply 1 and supply 2 both have a master "Output Enable" you
can press together, or have a helper press one while you press the
other. **Both bridges must come up within ~100 ms of each other.**

If they come up separately, one bridge will briefly drive the cascade
against the other bridge's freewheel — not damaging at 5 V, but it
muddies the test.

### H.3 — Scope the cascade output

Same scope settings as G.4 (vertical 2 V/div, horizontal 50 µs/div,
persistence on). 

Now expect **5 distinct horizontal voltage bands**:
- −10 V (both bridges at −Vdc)
- −5 V (one bridge at −Vdc, other at 0 — the new intermediate level!)
- 0 V (both at 0 or balanced)
- +5 V (one bridge at +Vdc, other at 0)
- +10 V (both at +Vdc)

The density of points at each level varies over the fundamental cycle
— more time at ±10 V near sine peaks, more time at 0 V at zero
crossings.

| Scope shows | Diagnosis | Action |
|---|---|---|
| 5 distinct bands as described | ✅ **PSC working, project deliverable achieved** | Proceed to Section I |
| Only 3 bands (−10, 0, +10) | 90° phase shift not effective on hardware despite `lock=OK` | STOP supplies. Try toggling `MOD STAIR` → `MOD PSC`. If still 3-level, see HARDWARE_BRINGUP.md Fix A/D. Worst case fall back to STAIR_ALT and ship that |
| Asymmetric (some levels stronger than others) | Bridge mismatch — DC supplies not equal, or one bridge's gate drive marginal | STOP. Verify both supplies exactly equal, re-scope gates |
| Constantly faulting | Sensors tripping under PSC switching noise | STOP. EMI from PSC may be coupling into MCP3201 SPI. See troubleshooting |

### H.4 — DC bus current sanity

Watch both supply ammeters. They should be similar within ~20 %. If
one bridge is drawing significantly more current than the other under
PSC with `BRIDGE BOTH`, the bridges are not symmetric in hardware —
investigate before raising voltage.

### H.5 — Touch test

After 30 s:
- Both bridges' MOSFETs: warm, similar temperature to each other
- TLP250s: cool to slightly warm — both bridges' TLP250s should be
  similar to each other. **Any single TLP250 that's noticeably hotter
  than the others is the one that will fail first** — STOP and
  investigate before raising voltage
- Snubber resistors (22 Ω 2 W): warm (they dissipate switching energy)

### H.6 — Stop

```
STOP
```

Both supplies OFF.

✅ **Pass H:** 5-level cascade output confirmed at low voltage. The
PSC modulator works on your hardware. Ready to ramp.

---

## Section I — PSC voltage ramp (5 V → 50 V)

Stepwise increase of bus voltage. At each step, run briefly, confirm
nothing is degrading, then continue.

> ⚠️ **At any step, if you see:**
> - Smoke, smell, or audible noise from the breadboard → STOP IMMEDIATELY
> - Any MOSFET hotter than ~70 °C → STOP, let cool
> - Any TLP250 hotter than ~60 °C → STOP, check bypass cap on that
>   driver (will fail at higher voltage if hot now)
> - Fault trip that won't `CLEAR` after the condition is gone → STOP,
>   investigate
> - Output waveform losing one of the 5 levels → STOP, may indicate
>   a MOSFET starting to fail
> - Bus voltage drooping more than 10 % under load → cap inadequate,
>   STOP before damage

### I.1 — Ramp procedure (repeat for each voltage)

For each `V_target = 10, 20, 30, 40, 50` V:

1. `STOP` from previous step
2. Both supplies OFF
3. Set both supplies to V_target
4. Adjust current limits:
   - V ≤ 20 V: 500 mA each
   - V = 30 V: 1 A each
   - V ≥ 40 V: 2 A each (or your load's max)
5. `START` (mode still PSC, FSW 5000, BRIDGE BOTH, MI 0.5)
6. Both supplies ON simultaneously
7. Scope cascade output — 5 bands present at ±2·V_target
8. Watch dashboard for ~30 s:
   - No fault lines
   - `vdc1`, `vdc2` track supply settings
   - `iout` peak ≈ 2·V_target·MI / 100 Ω (e.g. at 30 V → ~300 mA)
9. Touch-test MOSFETs and TLP250s briefly
10. `STOP`, both supplies OFF
11. Wait 30 s for thermal recovery
12. Next voltage

### I.2 — Pass criteria for each step

- [ ] 10 V: pass
- [ ] 20 V: pass
- [ ] 30 V: pass
- [ ] 40 V: pass
- [ ] 50 V: pass

✅ **Pass I:** PSC operates cleanly at full bus voltage.

---

## Section J — Sustained PSC run at 50 V

Final characterization. 5–15 minutes at design conditions.

### J.1 — Final config

```
STOP
MOD PSC
FSW 5000
BRIDGE BOTH
MI 0.95            (full modulation depth)
FFUND 50.0         (50 Hz fundamental)
CONFIG             (final check, all values as expected, lock=OK)
START
```

Both supplies at 50 V, current limits set to your expected load
current + margin.

### J.2 — Run for 5–15 minutes

Monitor continuously. Log every 2 minutes:
- Bridge 1 heatsink temperature
- Bridge 2 heatsink temperature
- TLP250 package temperatures (sample one per bridge)
- DC bus cap temperatures
- Supply currents
- Any UART events

### J.3 — Pass criteria for the sustained run

- [ ] Bridge 1 and Bridge 2 heatsinks within 5 °C of each other at
      steady state
- [ ] All TLP250s under 70 °C (well under 100 °C absolute max)
- [ ] All MOSFETs under 80 °C (with TO-220 clip-on heatsinks this is
      easy at the project's 700 W target)
- [ ] DC bus caps under 60 °C
- [ ] Zero fault trips during the run
- [ ] Scope shows clean 5-level output for the entire run, no level
      degradation or asymmetry developing over time

✅ **Pass J:** **PSC is bench-validated for the demo.** You're done.

### J.4 — Stop and shut down

```
STOP
```

Both bench supplies OFF, then disconnect.

Disconnect gate-drive supplies.

Save the dashboard event log to disk for the project report:
**File → Save Log... → name it `bench_session_YYYY-MM-DD.txt`** (or
just copy-paste the event panel contents).

---

## Section K — Making PSC the default

If Sections G–J all passed, you may want PSC to be the auto-start
default for the demo (so the inverter comes up in PSC mode on a fresh
boot, no UART needed).

Edit [Core/Inc/pwm_config.h](Core/Inc/pwm_config.h):

```c
#define PWM_DEFAULT_MODULATOR       MODULATOR_PSC       /* was MODULATOR_STAIR */
#define PWM_DEFAULT_SWITCHING_HZ    5000u               /* was 500u */
```

Rebuild and re-flash. Boot now starts in PSC mode and auto-start (if
no UART) fires PSC at 5 kHz with cascade mode and MI 0.95.

Verify by resetting and watching the `$C` line after boot — should
show `mod=PSC,fsw=5000`.

---

## "What's burning?" — quick triage if something goes wrong

If you see, smell, or hear something bad **STOP IMMEDIATELY** (bench
supply Output Off button). Then diagnose by symptom:

| Symptom | Likely cause | Action |
|---|---|---|
| TLP250 hot (>70 °C) | Bypass cap inadequate, gate ringing at 5 kHz | Add 100 nF directly on Pin 5/8. Verify with scope at MI 0.3 in Step A |
| TLP250 instantly hot on power-up | Shorted output / MOSFET gate-source short | Replace MOSFET, check 10 kΩ gate-pulldown installed |
| MOSFET hot fast / smoking | Shoot-through or stuck-on | Verify dead-time on scope. Bump from 2 µs to 3 µs in `PWM_DEAD_TIME_DTG` and reflash |
| MOSFET hot evenly over time | High switching loss at 5 kHz | Better heatsink, lower FSW (`FSW 2000`), or lower MI |
| One bridge much hotter than other | Bridge mismatch in hardware (different MOSFET, missing snubber, etc.) | Inspect both bridges component-by-component |
| DC bus cap warm | High ripple current — PSC stresses bus caps more than STAIR | Add another 1000 µF in parallel right at the bridge DC input |
| 78L05 hot | Sensing island drawing too much | Check for short on +5V_Island rail |
| Smell of burning insulation | Wire too thin for current, or insulation contact with hot part | Inspect every wire, replace if discolored |
| Pop + smoke | Capacitor reversed or overvoltage | Definite component replacement, inspect what caused overvoltage |

## Never-do list

- ❌ Never apply > 55 V to a single bridge DC bus (IRFZ44N is 55 V rated, TVS clamps at 84.5 V but you don't want to live there)
- ❌ Never increase MI above 0.95 (firmware enforces — but don't try)
- ❌ Never run at > 100 % HS duty for any leg (firmware enforces 95 % clamp — but verify by scoping CCR if you change anything)
- ❌ Never start with both supplies at significantly different voltages
- ❌ Never short the AC output (no resistor, just a wire) under any modulator
- ❌ Never `START` if `$C` shows `lock=BAD` and the modulator is PSC — that's broken
- ❌ Never assume a passing Phase E (STAIR) means PSC will work — different physics, different stress
- ❌ Never walk away from the bench mid-run

## Always-do list

- ✅ Always have the dashboard connected before flashing (auto-start protection)
- ✅ Always start at low voltage and ramp gradually
- ✅ Always check `lock=OK` before starting PSC
- ✅ Always have both supplies' Output buttons reachable
- ✅ Always touch-test components frequently (back of hand only — never grip a hot part)
- ✅ Always `STOP` between voltage steps to let things cool briefly
- ✅ Always save the event log after a session

---

## Post-session

- Disconnect everything in reverse order (load → DC bus → gate drive → USB)
- Save dashboard log
- Note observations (especially: did PSC produce 5 levels? bridge thermals matched?)
- Decide which modulator goes into the demo:
  - PSC if Sections G–J all passed → most impressive (real PWM, 5 levels)
  - STAIR_ALT if PSC didn't deliver 5 levels → safest fallback (5 levels visible, bridges balanced, not real PWM)
  - STAIR if you had problems with both → original behavior, has the bridge imbalance but proven reliable

Update [CHANGELOG.md](CHANGELOG.md) with the session outcome.

If PSC works, you've solved concern #8 and met the project's 5-level
PWM-controlled deliverable. That's the headline result.
