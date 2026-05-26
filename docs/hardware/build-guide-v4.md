# 5-Level Cascaded H-Bridge Inverter — Build & Reference Guide v4.0

**Version 4.0 — May 2026 — As-built engineering reference**

ELE 401/402 Graduation Project — Hacettepe University, Department of Electrical & Electronics Engineering
Project Group "Cereyan Hacıları" — Furkan Emir Aksel · Ahmet Koçak · Faruk Gökhan Abay · Mücahit Aydın
Supervisor: Assoc. Prof. Dr. Rasım Doğan

---

## Document Status

This guide is the canonical engineering reference for the modular 5-Level Cascaded H-Bridge Inverter and the firmware that drives it. It supersedes **Build Guide v3.1** (February 2026) in its entirety.

v3.1 documented an earlier iteration (single dual-bridge PCB, IRFZ44N MOSFETs, IPD LS-PWM, 3-MISO sensing) with two pin-assignment errors and predates the final hardware architecture, modulation strategy, sensing topology, and operator dashboard. Where v4 disagrees with v3.1, **v4 is the authoritative reference** — see §13 for the errata.

This document describes what was actually fabricated, populated, bench-validated, and demonstrated:
- Two identical single-bridge PCB modules (4-layer, JLCPCB)
- IRFB4110 power MOSFETs
- PSC-PWM at 5 kHz, 5 distinct cascade output levels confirmed on oscilloscope
- Bridges thermally balanced under sustained load
- Bit-banged MCP3201 + 6N137 isolated sensing
- PySide6 desktop dashboard with full operator control

### Companion documents (firmware repository)

| Document | Purpose |
|---|---|
| `README.md` | Firmware overview and quick command reference |
| `CHANGELOG.md` | Design-decision history per release |
| `FIRST_BENCH_SESSION.md` | Linear walkthrough for first-time bring-up |
| `HARDWARE_BRINGUP.md` | Comprehensive phase-by-phase test procedure |
| `FSM_NOTES.md` | Control state machine diagram |
| `dashboard/README.md` | Dashboard installation and usage |

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Decisions](#2-architecture-decisions)
3. [Hardware Bill of Materials](#3-hardware-bill-of-materials)
4. [Power Stage Detail](#4-power-stage-detail)
5. [Gate Drive Subsystem](#5-gate-drive-subsystem)
6. [Sensing Subsystem](#6-sensing-subsystem)
7. [Controller Interface](#7-controller-interface)
8. [Control Firmware](#8-control-firmware)
9. [PSC-PWM Modulation Explained](#9-psc-pwm-modulation-explained)
10. [Protection System](#10-protection-system)
11. [Dashboard & Operator Workflow](#11-dashboard--operator-workflow)
12. [Bring-Up & Test](#12-bring-up--test)
13. [V3.1 Errata](#13-v31-errata)
14. [Safety](#14-safety)
15. [Future Work](#15-future-work)

---

## 1. System Overview

The inverter converts two independent isolated DC sources into a single-phase AC output with a 5-level staircase waveform, suitable for cascaded grid-tie applications, photovoltaic energy harvesting, or stand-alone resistive loads. The cascaded multilevel topology produces lower harmonic distortion than a conventional two-level inverter, eliminates the need for an output transformer, and naturally supports series connection of independent DC sources.

### 1.1 Specifications

| Parameter | Value |
|---|---|
| Topology | Single-phase 5-Level Cascaded H-Bridge (CHB) |
| Power cells | 2 × full H-bridge, AC outputs in series |
| Per-bridge DC bus | 50 V nominal (5–60 V operating range) |
| Peak AC output | ±100 V (at MI = 0.95) |
| Continuous power | ~700 W into resistive load |
| Fundamental frequency | 50 Hz default (10–400 Hz configurable at runtime) |
| Switching frequency | 5 kHz (PSC, default); 100–20 000 Hz configurable |
| Modulation | Unipolar Phase-Shifted Carrier (PSC) SPWM, 90° between cells |
| Output levels | 5 (+2Vdc, +Vdc, 0, −Vdc, −2Vdc) — confirmed on bench |
| Dead-time | 3 µs (sized for IRFB4110) |
| Maximum duty | 95 % (firmware-enforced for bootstrap refresh) |
| Controller | STM32F303RE (Nucleo-F303RE, 64 MHz HSI/PLL) |
| Telemetry | NMEA-style ASCII over USART2/VCP @ 115 200 8N1, 20 Hz |
| Operator interface | PySide6 desktop dashboard, simulator + live serial sources |
| THD (simulated, no filter) | <5 % at 50 V bus, MI = 0.95 |

### 1.2 Modular Two-Board Architecture

The system is built as **two electrically identical single-bridge PCB modules** with their AC outputs connected in series:

```
       50 V Supply 1                          50 V Supply 2
             │                                       │
             │ (isolated)                            │ (isolated)
        ┌────▼─────────┐                       ┌────▼─────────┐
        │   Bridge 1   │                       │   Bridge 2   │
        │   (TIM1)     │                       │   (TIM8)     │
        │ Q1H Q1L Q2H Q2L│                     │Q3H Q3L Q4H Q4L│
        └─┬───────────┬─┘                       └─┬───────────┬─┘
          │ X1     Y1 │                           │ X2     Y2 │
          │           └─────── series tap ────────┘           │
          │           (Bridge 2 GND_HV floats here)           │
          │                                                   │
          └───────[ACS712]──────[ LOAD ]──────────────────────┘
                              AC output
```

Bridge 2's local DC negative (`GND_HV`) floats at Bridge 1's output node — **not** at system ground. Galvanic isolation between the two bridges' gate drives and sensing islands is therefore mandatory. This is the central electrical constraint of the design and dictates every isolation barrier choice that follows.

### 1.3 Power and Signal Domains

The system has four distinct electrical reference domains:

| Domain | Reference | Powered by | Purpose |
|---|---|---|---|
| `GND_System` | System ground | USB or external 5 V supply | STM32, dashboard interface |
| `GND_HV_B1` / `Drive_GND_B1` | Bridge 1 DC negative | Bridge 1 supply | Bridge 1 power stage and gate drive return |
| `GND_HV_B2` / `Drive_GND_B2` | Bridge 2 DC negative (floating) | Bridge 2 supply | Bridge 2 power stage and gate drive return |
| `GND_Island` (×2) | Local to each sensing island | 78L05 from +15V_Drive | MCP3201 ADC reference |

These domains connect only at their defined points: B0515S isolated DC-DC for the gate-drive supply crossover; TLP250 optocouplers for the gate-drive signal crossover; 6N137 optocouplers for the SPI crossover. Mixing them creates ground loops, measurement errors, and in the worst case, shoot-through.

---

## 2. Architecture Decisions

This section explains *why* the design looks the way it does. The reasoning matters as much as the schematic — future students or product engineers picking up the project need to understand the constraints that drove each choice.

### 2.1 Why Cascaded H-Bridge (not NPC or Flying-Capacitor)

Three multilevel topologies were considered:

| Topology | Pros | Cons | Decision |
|---|---|---|---|
| Neutral-Point Clamped (NPC) | Single DC source | Requires clamping diodes; capacitor-voltage balancing is non-trivial | Rejected |
| Flying Capacitor | Single DC source | Control complexity scales badly with level count | Rejected |
| Cascaded H-Bridge (CHB) | Modular, fault-tolerant, natural fit for independent PV sources | Requires N isolated DC sources for N+1 levels | **Selected** |

The CHB requirement for independent isolated DC sources is a natural match for photovoltaic strings and stacked battery banks, and is trivially satisfied on the bench with two laboratory power supplies.

### 2.2 Why IRFB4110 (not IRFZ44N or IGBTs)

The original v3.1 BOM specified IRFZ44N (55 V, 49 A, 17.5 mΩ). Bench experience and re-analysis identified two problems:

1. **Voltage headroom is insufficient.** At a 50 V steady-state bus, the IRFZ44N has only 5 V of margin to its 55 V V_DSS. The 1.5KE62A TVS clamps at 84.5 V — well above the IRFZ44N rating. A single transient could destroy the device.
2. **Modular re-spin cost was modest.** Moving to a 100 V class FET added pennies per device.

The IRFB4110 (100 V, 180 A, 4.5 mΩ) was selected as the replacement. The R_DS(on) reduction (17.5 mΩ → 4.5 mΩ) reduces conduction losses by ~4×, and the 100 V rating provides comfortable margin against the TVS clamp voltage.

IGBTs were considered and rejected for the operating point. At ~50 V and ~7 A, the IGBT's fixed V_CE(sat) (typically 1.5–2.5 V) dominates over MOSFET conduction losses. The cross-over current where IGBT becomes more efficient than the IRFB4110 is well above 85 A — far outside this project's operating range.

### 2.3 Why PSC-PWM (not LS-PWM)

v3.1 specified In-Phase Disposition Level-Shifted PWM (IPD LS-PWM). Bench testing of the earlier STAIR quantize-to-5-levels modulator revealed that the simpler approach — and IPD by extension — has an inherent **bridge-load asymmetry**: one bridge always carries the inner band (±1 step), the other only switches for the outer band (±2). This produced measurable thermal imbalance, with one of Bridge 1's MOSFETs running noticeably hotter than the rest.

Phase-Shifted Carrier (PSC) PWM resolves this structurally. With both cells running the same modulating reference against carriers offset by 360°/N (here 180°/2 = 90° per cell, or 180° between the two cells' carriers), each bridge handles an equal share of the switching workload. Output ripple frequency at the cascaded node doubles to 2·F_sw, which reduces filter requirements.

PSC was bench-validated against the requirement at the demo:
- ✅ 5 distinct cascade voltage levels visible on the oscilloscope without an LC filter
- ✅ Bridge 1 and Bridge 2 MOSFET case temperatures within ~3 °C at steady state
- ✅ No fault trips during sustained operation at the 50 V / 700 W design point

### 2.4 Why Two Identical Single-Bridge PCBs (not one dual-bridge PCB)

Earlier iterations placed both bridges on a single PCB. Three problems emerged:

1. **Repair cost.** A failure in one bridge required reworking the entire board.
2. **Isolation complexity.** Drawing both ground domains on one board made the isolation barrier visually ambiguous and easy to violate during layout edits.
3. **Reuse value.** A single-bridge module is also a useful standalone test fixture and a building block for higher-level inverters.

The modular approach uses two identical 4-layer PCBs. Each board has its own gate drive, its own sensing island, and its own connector to the controller. The only inter-board connection is the series AC output tap.

### 2.5 Why Bit-Banged MCP3201 + 6N137 (not analog op-amp sensing)

Bridge 2's DC bus must be measured at a potential that floats at Bridge 1's output node. Three options:

| Approach | Pros | Cons |
|---|---|---|
| Analog isolation amplifier (e.g., ISO124) | Continuous analog signal | Expensive, limited bandwidth, calibration drift |
| Differential resistor divider into MCU ADC | Cheap | Common-mode voltage exceeds ADC range at high bus |
| Digital ADC + optocoupler SPI return | Cheap parts, flexible, immune to common-mode | Requires careful SPI timing |

The third approach was selected. Each bridge has a local MCP3201 (12-bit single-channel SPI ADC) referenced to its own GND_Island, with the SPI lines crossing the isolation barrier through 6N137 optocouplers. Total parts per island: one MCP3201, three 6N137, one 78L05 — readily available, hand-solderable in DIP packages.

Hardware SPI peripheral usage was considered and rejected: the three MISO returns cannot be tri-stated cleanly (the 6N137 output stage doesn't release the line high-impedance), so bus-sharing the MISOs is not viable. Bit-banged GPIO SPI is used instead, with one shared SCK clocking all three ADCs while each MISO is read on its own GPIO pin.

### 2.6 Why VNOM-Derived Protection (not fixed thresholds)

Fixed protection thresholds sized for the 50 V design point trip immediately at any bench test below 40 V (the original UV threshold). This made low-voltage step-up testing impossible without disabling protection.

The firmware now derives the three voltage thresholds from a single runtime-configurable nominal bus voltage `VNOM`:

- UV = 0.80 × VNOM
- OV = 1.16 × VNOM
- IMBAL = 0.20 × VNOM

At VNOM = 50 the derived values reproduce the original 40 / 58 / 10 V design exactly. At VNOM = 12 (a typical low-voltage bench test) they become 9.6 / 13.9 / 2.4 V. The operator sets VNOM via UART or the dashboard before applying bus voltage.

The overcurrent threshold (`OC`) is independent of VNOM because it is a load property rather than a bus property.

---

## 3. Hardware Bill of Materials

All quantities below are **per single-bridge module**. The complete inverter uses two modules. Spare quantities are included in parentheses where applicable.

### 3.1 Per-Module Power Stage

| Component | Qty | Spec | Source |
|---|---|---|---|
| IRFB4110 MOSFET | 4 (+2) | TO-220, 100 V, 180 A, 4.5 mΩ | Motorobit / Direnc |
| TLP250 optocoupler | 4 (+1) | DIP-8, 1.5 A peak, 2 500 V_rms isolation | Motorobit |
| B0515S-1WR3 | 2 (+1) | SIP-4, 5 V→15 V, 1 W isolated | Motorobit |
| UF4007 | 2 (+2) | DO-41, 1 A, 75 ns recovery | Direnc |
| 1N5408 | 1 (+1) | DO-201, 3 A, 1 000 V | Direnc |
| 1.5KE62A | 1 (+1) | DO-201, 53 V standoff, 84.5 V clamp | Motorobit |
| 15 A blade fuse + holder | 1 (+1) | Automotive blade | Robotistan |

### 3.2 Per-Module Sensing

| Component | Qty | Spec | Source |
|---|---|---|---|
| MCP3201 ADC | 1 (+1) | DIP-8, 12-bit SPI, single channel | Direnc |
| 6N137 | 3 (+1) | DIP-8, 10 Mbit/s, photodiode + buffer | Direnc / Motorobit |
| ACS712-20A | 1 (+1) | SOIC-8, Hall-effect, 100 mV/A | Robotistan |
| 78L05 | 1 (+1) | TO-92, 5 V/100 mA LDO | Direnc |

The ACS712 is populated on both boards (footprint and current-path traces are mandatory in the AC output path) but the downstream signal conditioning is wired up only on the lower bridge. The `CS_EN` solder-bridge jumper on each board selects whether its MCP3201 current channel is connected to the SPI bus.

### 3.3 Per-Module Power Passives

| Component | Value | Qty | Role |
|---|---|---|---|
| Electrolytic capacitor | 1 000 µF / 100 V | 1 | DC link bulk storage |
| Ceramic capacitor | 100 nF / 100 V | 1 | DC bus HF bypass, near MOSFETs |
| Bleeder resistor | 100 kΩ / 2 W | 1 | Safety discharge for DC link cap |
| Film capacitor | 2.2 nF / 630 V | 4 | Snubber across each MOSFET D-S |
| Resistor | 22 Ω / 2 W | 4 | Snubber damping (in series with film cap) |

### 3.4 Per-Module Gate Drive Passives

| Component | Value | Qty | Role |
|---|---|---|---|
| Resistor | 220 Ω / 0.25 W | 4 | TLP250 LED current limit (controller side) |
| Resistor | 22 Ω / 0.25 W | 4 | MOSFET gate series resistor |
| Resistor | 10 kΩ / 0.25 W | 4 | MOSFET gate-source pull-down |
| Ceramic capacitor | 100 nF / 25 V | 4 | TLP250 VCC-GND bypass |
| UF4007 | 2 | DO-41 | Bootstrap charge diode (HS channels only) |
| Electrolytic capacitor | 10 µF / 25 V | 2 | Bootstrap energy storage (HS channels only) |

### 3.5 Per-Module Sensing Passives

| Component | Value | Qty | Role |
|---|---|---|---|
| Resistor | 100 kΩ / 1 % metal film | 1 | DC bus divider upper leg |
| Resistor | 5.1 kΩ / 1 % metal film | 1 | DC bus divider lower leg |
| Resistor | 220 Ω / 0.25 W | 3 | 6N137 LED current limit |
| Resistor | 4.7 kΩ / 0.25 W | 3 | 6N137 output pull-up |
| Ceramic capacitor | 100 nF / 25 V | 6 | Bypass: MCP3201, 6N137 (×3), 78L05 in/out filter |
| Ceramic capacitor | 1 µF / 25 V | 1 | 78L05 input filter |
| Electrolytic capacitor | 10 µF / 16 V | 1 | 78L05 output filter |
| Resistor (current path) | 1 kΩ / 0.25 W | 1 | ACS712 → ADC divider upper (lower bridge only) |
| Resistor (current path) | 1.5 kΩ / 0.25 W | 1 | ACS712 → ADC divider lower (lower bridge only) |
| Diagnostic LED | green 3 mm | 1 (DNP) | DC bus power indicator |
| Diagnostic LED | yellow 5 mm | 4 (DNP) | PWM activity per MOSFET channel |
| Diagnostic LED | red 5 mm | 1 (DNP) | Fault indication |

The diagnostic LEDs are populated as Do-Not-Place footprints — useful for debugging on the bench, omitted in normal operation to reduce part count.

### 3.6 Connectors

| Connector | Qty per board | Role |
|---|---|---|
| 2-position screw terminal, 15 A+ | 2 | DC input (+, −) and AC output |
| 2×10 pin header, 2.54 mm | 1 | Controller interface |
| TO-220 clip-on heatsink | 4 | MOSFET thermal management |

### 3.7 Supplier Strategy

The project sources all components from Turkish domestic suppliers to minimize lead time and shipping cost:

- **Motorobit** — integrated circuits, isolated DC-DC, MOSFETs
- **Direnc.net** — passives, MCP3201, 6N137, 78L05, diodes
- **Robotistan** — mechanical hardware, ACS712 modules, heatsinks
- **Komponentci.net** — connectors and additional passives

All SMD capacitors specified in v3.1 were converted to THT in v4 to ease hand soldering. The ACS712 remains SOIC-8 (the easiest SMD package for hand-assembly, and required to carry the wide AC current trace).

---

## 4. Power Stage Detail

Each bridge consists of four IRFB4110 MOSFETs arranged as a full H-bridge, with each leg's complementary pair driven through a TLP250 optocoupler.

### 4.1 H-Bridge Topology (per bridge)

```
                     Node_A (+50 V)
                  ┌──────┴──────┐
                  │             │
              ┌───┴───┐     ┌───┴───┐
              │ Q_H_L │     │ Q_H_R │   High-side MOSFETs
              │ (HS)  │     │ (HS)  │   (bootstrap driven)
              └───┬───┘     └───┬───┘
        Node_X───●               ●───Node_Y     AC output tap
                  │             │
              ┌───┴───┐     ┌───┴───┐
              │ Q_L_L │     │ Q_L_R │   Low-side MOSFETs
              │ (LS)  │     │ (LS)  │   (direct driven)
              └───┬───┘     └───┬───┘
                  └──────┬──────┘
                     GND_HV
              (= local Drive_GND for this bridge)
```

The bridge's AC output is `Node_X − Node_Y`. Each MOSFET has an associated snubber (22 Ω 2 W + 2.2 nF / 630 V in series) across its drain-source to damp turn-off ringing.

### 4.2 DC Input Protection Chain

Five components in parallel between `Node_A` and `GND_HV`:

| Element | Wiring | Function |
|---|---|---|
| 1N5408 diode | Cathode to Node_A, anode to GND_HV | Reverse-polarity protection (conducts on reverse, blows the fuse) |
| 1.5KE62A TVS | Cathode to Node_A, anode to GND_HV | Transient clamp at 84.5 V max (within IRFB4110's 100 V rating) |
| 1 000 µF / 100 V electrolytic | + to Node_A, − to GND_HV | Bulk energy storage for switching transients |
| 100 nF / 100 V ceramic | Across Node_A and GND_HV, near MOSFETs | High-frequency bypass |
| 100 kΩ / 2 W bleeder | Across Node_A and GND_HV | Discharges DC link cap after power-off (~8 min to safe voltage) |

A 15 A blade fuse sits in series with the (+) input terminal upstream of all the above.

**WARNING:** Bridge 2's `GND_HV` is **not** system ground. It floats at the series tap. Never tie the two bridges' `GND_HV` nodes together.

---

## 5. Gate Drive Subsystem

The gate drive must:
- Switch four MOSFETs per bridge with adequate dead-time
- Provide galvanic isolation between the controller and each MOSFET source (mandatory for high-side switching on a floating bridge)
- Maintain its own +15 V supply referenced to the bridge's local Drive_GND

### 5.1 Isolated +15 V Generation (per bridge)

Two B0515S-1W modules are paralleled per bridge, producing a combined 2 W output rail:

```
System +5 V ──┬── B0515S_A pin 2 (V_in+)       100 nF bypass cap on each
              └── B0515S_B pin 2 (V_in+)       module's input

System GND ───┬── B0515S_A pin 1 (V_in−)
              └── B0515S_B pin 1 (V_in−)
              ════ isolation barrier ════

B0515S_A pin 4 ─ 1 Ω ─┐
B0515S_B pin 4 ─ 1 Ω ─┴── +15V_Drive (per bridge)
                          + 100 µF/25 V electrolytic
                          + 100 nF ceramic

B0515S_A pin 3 ─┐
B0515S_B pin 3 ─┴── Drive_GND (= bridge low-side MOSFET sources)
```

The 1 Ω balancing resistors force current sharing between the two unregulated modules. At a typical 50 mA combined load the drop across each is only 25 mV. Total gate-drive supply load per bridge is approximately 0.75–1.25 W (4 TLP250s + 78L05 island regulator), well within the paralleled 2 W capacity.

### 5.2 TLP250 Gate Driver (per MOSFET)

Pinout and per-MOSFET wiring:

| Pin | Name | Connection |
|---|---|---|
| 1 | N/C | unconnected |
| 2 | LED anode | Controller PWM pin → 220 Ω → pin 2 |
| 3 | LED cathode | `GND_System` (controller side) |
| 4 | N/C | unconnected |
| 5 | GND (driver side) | See §5.3 / §5.4 below |
| 6 | V_out | → 22 Ω → MOSFET gate |
| 7 | V_out (inverted) | Tie to pin 5 through 10 kΩ for noise immunity, or leave open |
| 8 | VCC | See §5.3 / §5.4 below |

A 100 nF ceramic bypass capacitor sits across pin 8 and pin 5 of every TLP250, placed as close to the IC as physically possible. **This is the single most important gate-drive layout detail.** A long bypass path causes 5 kHz oscillation and rapid TLP250 thermal failure.

Per-MOSFET gate circuit:
- TLP250 pin 6 → 22 Ω → MOSFET gate (limits peak gate current to ~0.68 A)
- MOSFET gate → 10 kΩ → MOSFET source (pull-down, ensures OFF during power-up)
- MOSFET drain-source: 22 Ω 2 W + 2.2 nF / 630 V in series (snubber)

LED input current is set by the 220 Ω resistor: (3.3 V − 1.2 V) / 220 Ω = 9.5 mA, within the TLP250's 5–16 mA reliable operating range.

### 5.3 Low-Side TLP250 (Q_L_L and Q_L_R, ×2 per bridge)

The low-side MOSFETs' sources are tied to the bridge's `Drive_GND`. Their TLP250 drivers connect directly:

- Pin 8 (VCC) → `+15V_Drive` rail
- Pin 5 (GND) → `Drive_GND`

### 5.4 High-Side TLP250 with Bootstrap (Q_H_L and Q_H_R, ×2 per bridge)

High-side MOSFETs' sources switch between `Drive_GND` (when the low-side of that leg is ON) and `+50V` (when the high-side is ON). The TLP250 driving the high-side must "ride" this switching node, which requires a bootstrap supply:

```
+15V_Drive ──┬── UF4007 anode    The UF4007 conducts when V_switch is low,
             │                   charging the 10 µF bootstrap cap to ~14.3 V.
             │   UF4007 cathode  When V_switch goes high, the diode reverse-
             ●── Node_Boot       biases and the cap floats with the source.
             │
             │   10 µF/25 V cap
             │ ── + terminal
             │
             │
HS MOSFET    │
source ──────┼── Node_VS (switching node)
             │ ── − terminal of 10 µF cap

TLP250 pin 8 (VCC) ── Node_Boot
TLP250 pin 5 (GND) ── Node_VS  (= MOSFET source)
TLP250 pin 5–8 bypass: 100 nF as close to IC as possible
```

How the bootstrap works:
1. When the low-side of that leg is ON, the switching node is pulled to `Drive_GND` (≈ 0 V). The UF4007 forward-biases. The 10 µF cap charges to ~14.3 V (15 V minus 0.7 V diode drop).
2. When the high-side turns ON, the switching node rises to +50 V. The UF4007 reverse-biases (blocks). The cap provides a floating 14.3 V supply to the TLP250.
3. The cap discharges through the TLP250's quiescent current (~16 mA). At 95 % duty cycle at 5 kHz, on-time = 190 µs, so droop = (16 mA × 190 µs) / 10 µF = 0.3 V. The TLP250's 10 V minimum is easily maintained.
4. On the next low-side ON period the cap recharges.

**WARNING:** Maximum duty cycle 95 %. At 100 % duty the low-side never turns ON, the bootstrap cap never recharges, and high-side drive collapses. The firmware enforces this clamp.

### 5.5 Bootstrap Pre-Charge

At power-up all bootstrap caps are uncharged. The firmware runs a 6 ms pre-charge sequence at every START: both bridges' low-side MOSFETs are turned fully ON, both high-sides fully OFF. This charges all four bootstrap caps before normal modulation begins.

### 5.6 Dead-Time Selection

Dead-time is set to **3 µs** for the IRFB4110 power stage. The IRFB4110 has roughly 2× the gate charge of the IRFZ44N (~150 nC vs ~67 nC), so with the same 22 Ω gate series resistor the turn-on/turn-off transitions take about twice as long. The OLD bench-validated 2 µs (sized for IRFZ44N) no longer leaves enough shoot-through margin.

The dominant term remains the TLP250 propagation delay (0.5 µs typical, 1.5 µs maximum), which is independent of the MOSFET choice.

At 5 kHz switching, 3 µs is 1.5 % of the period — negligible output amplitude impact.

The dead-time is encoded in the STM32 advanced timer's `BDTR.DTG` register as `0xA0` (corresponds to `TIM_DTG_3US_AT_64MHZ` in the firmware).

---

## 6. Sensing Subsystem

The sensing subsystem measures three quantities and reports them to the controller:
- Bridge 1 DC bus voltage (isolated, on Bridge 1's PCB)
- Bridge 2 DC bus voltage (isolated, on Bridge 2's PCB)
- AC output current (safe-side, on the lower bridge's PCB)

### 6.1 Isolated Sensing Island Architecture

Each bridge PCB hosts a self-contained sensing island powered from the local +15 V_Drive rail through a 78L05 regulator:

```
+15V_Drive ─ 1 µF ─┬─ 78L05 IN ─ 78L05 OUT ─┬─ +5V_Island
                   │                          │
                   │   78L05 GND              ├─ 100 nF ceramic
                   │                          ├─ 10 µF/16 V electrolytic
                   │                          │
                   │                          ▼
Drive_GND ─────────┼──────────────────── GND_Island
```

78L05 dissipation: (15 V − 5 V) × 25 mA ≈ 0.25 W, easily handled by the TO-92 package without a heatsink.

The +5V_Island rail powers the MCP3201's VDD (which is also its analog reference) and the output side of the three 6N137 optocouplers.

### 6.2 DC Bus Voltage Divider (per bridge)

```
Node_A (+50 V) ── 100 kΩ ──●── 5.1 kΩ ── GND_Island
                            │
                            ├── 100 nF (noise filter)
                            │
                            └── MCP3201 pin 2 (IN+)
                                MCP3201 pin 3 (IN−) ── GND_Island
```

At 50 V input: divider output = 50 × 5.1 / 105.1 ≈ 2.42 V, using 48 % of the ADC's 0–5 V range. At 60 V (OV threshold + margin): 2.91 V — still safely within range.

Resolution: 50 V / (4096 × 0.0485) ≈ 0.252 V per ADC count.

### 6.3 ACS712 Current Path (lower bridge only)

The ACS712 is wired in series with the AC output:

```
Bridge 1 X1 ── [load wire] ── ACS712 IP+ ── ACS712 IP− ── [load wire] ── Bridge 2 Y2
                                  │
                                  └── OUT (2.5 V at zero current, ±100 mV per A)

ACS712 OUT ── 1 kΩ ── ADC_Node ── 1.5 kΩ ── GND_System
                          │
                          └── 100 nF (RC filter, f_c ≈ 1.6 kHz)
                          └── MCP3201 (current) pin 2 (IN+)
```

Divider ratio 1.5 / (1 + 1.5) = 0.6. At zero current: 2.5 × 0.6 = 1.5 V at ADC. At ±20 A (sensor max): 2.7 V or 0.3 V. Comfortably within the safe-side MCP3201's 0–3.3 V range.

### 6.4 MISO Topology — Two Lines, Not Three

**This is the single most important departure from v3.1.** v3.1 specified three independent MISO returns (one per ADC, each through its own 6N137). The built hardware uses **two** physical MISO return lines:

| MISO line | Carries | Reason |
|---|---|---|
| `MISO_DC1` (STM32 PA6) | Lower-bridge DC ADC only | Lower-bridge island has its own isolated MISO |
| `MISO_DC2` / `MISO_CUR` (STM32 PC3) | Upper-bridge DC ADC **and** the current ADC | Wire-shared on the upper-bridge island |

Because the DC2 and CUR ADCs share one wire on the upper island, the firmware must read them **sequentially, one chip-select at a time** — never both selected together. The bit-banged SPI driver enforces this with a single-channel read loop.

This change cuts down on a 6N137 per system, simplifies the upper-bridge island layout, and matches what is electrically tractable on a hand-built breadboard.

### 6.5 6N137 SPI Isolation (3 per island)

The 6N137 is a 10 Mbit/s photodiode + buffer optocoupler with an active-low output (LED ON → output LOW). Each line crosses one 6N137:

| Line | Direction | LED side | Output side |
|---|---|---|---|
| SCK | Controller → island | Controller PA5 → 220 Ω → 6N137 pin 2 | 6N137 pin 6 → 4.7 kΩ → +5V_Island; pin 6 → MCP3201 CLK |
| CS | Controller → island | Controller PC0/PC1/PC2 → 220 Ω → 6N137 pin 2 | 6N137 pin 6 → 4.7 kΩ → +5V_Island; pin 6 → MCP3201 CS |
| MISO | Island → controller | MCP3201 DOUT → 220 Ω → 6N137 pin 2 | 6N137 pin 6 → 4.7 kΩ → +3.3V (controller side); pin 6 → STM32 MISO pin |

Each 6N137 has 100 nF bypass across pins 5 and 8, and pin 7 (enable) tied permanently low (enabled).

**The 6N137 inverts.** Without compensation, the MCP3201 sees an inverted clock, an inverted (high-when-active) chip-select, and inverted data. The firmware handles this with the runtime-configurable `SPIINV` mask (see §8.7).

### 6.6 SPI Timing

The bit-banged SPI runs at ~140 kHz (limited by the volatile-loop half-period delay). The MCP3201's 1.6 MHz absolute maximum is comfortably honored. The 6N137 round-trip propagation delay (~150 ns) is well below the half-period at this speed.

For higher sense rates a hardware SPI peripheral could be added later, but at the current 1 kHz scan rate (60 µs read time × 3 sequential channels = 180 µs total) there is no benefit.

---

## 7. Controller Interface

The STM32F303RE Nucleo board connects to the two bridges through a single 2×10 header (2.54 mm pitch) on each PCB.

### 7.1 STM32 Pin Map (As Built — Supersedes v3.1)

| Signal | STM32 pin | Alternate function | Role |
|---|---|---|---|
| PWM_1H | **PA8** | TIM1_CH1 (AF6) | Bridge 1, Q_H_L (high-side, left leg) |
| PWM_1L | **PA7** | TIM1_CH1N (AF6) | Bridge 1, Q_L_L (low-side, left leg) |
| PWM_2H | **PA9** | TIM1_CH2 (AF6) | Bridge 1, Q_H_R (high-side, right leg) |
| PWM_2L | **PA12** | TIM1_CH2N (AF6) | Bridge 1, Q_L_R (low-side, right leg) |
| PWM_3H | **PB6** | TIM8_CH1 (AF5) | Bridge 2, Q_H_L |
| PWM_3L | **PB3** | TIM8_CH1N (AF4) | Bridge 2, Q_L_L |
| PWM_4H | **PB8** | TIM8_CH2 (AF10) | Bridge 2, Q_H_R |
| PWM_4L | **PB0** | TIM8_CH2N (AF4) | Bridge 2, Q_L_R |
| SCK (shared) | **PA5** | GPIO output | MCP3201 SPI clock, bit-banged |
| CS_DC1 | **PC0** | GPIO output | Lower bridge DC ADC chip-select |
| CS_DC2 | **PC1** | GPIO output | Upper bridge DC ADC chip-select |
| CS_CUR | **PC2** | GPIO output | Current ADC chip-select |
| MISO_DC1 | **PA6** | GPIO input | Lower bridge DC ADC data (own line) |
| MISO_DC2 / MISO_CUR | **PC3** | GPIO input | Upper bridge DC ADC + current ADC data (shared line) |
| FAULT_OUT | **PB5** | GPIO output | Active-low hardware fault indicator |
| USART2_TX | **PA2** | USART2_TX (AF7) | ST-LINK VCP transmit |
| USART2_RX | **PA3** | USART2_RX (AF7) | ST-LINK VCP receive |

**This pin map differs from v3.1 in two important places** — see §13 for the errata.

### 7.2 Power Supply Inputs

| Supply | Voltage | Current | Purpose |
|---|---|---|---|
| Bridge 1 DC input | 50 V (5–60 V tested) | 0–15 A | Bridge 1 power stage |
| Bridge 2 DC input | 50 V (5–60 V tested) | 0–15 A | Bridge 2 power stage |
| System 5 V | 5.0 V ± 0.25 V | ≤ 1.2 A | B0515S inputs + ACS712 + safe-side MCP3201 |
| USB | 5 V | ≤ 0.2 A | Nucleo via ST-LINK |

The system 5 V can alternatively be derived from Bridge 1's 50 V bus through an LM2596 buck module — useful for portable demos that reduce the supply count to two.

### 7.3 Header Pinout (per board)

| Pin | Signal | Direction | Notes |
|---|---|---|---|
| 1 | PWM_1H (board 1) / PWM_3H (board 2) | In | From TIM1_CH1 or TIM8_CH1 |
| 2 | PWM_1L (board 1) / PWM_3L (board 2) | In | From TIM1_CH1N or TIM8_CH1N |
| 3 | PWM_2H / PWM_4H | In | |
| 4 | PWM_2L / PWM_4L | In | |
| 5 | SCK | In | Shared 1 MHz max bit-bang clock |
| 6 | CS (this board's DC ADC) | In | |
| 7 | CS_CUR (lower board only) | In | Only used on board with CS_EN populated |
| 8 | MISO (this board) | Out | Through 6N137, pulled up to controller I/O voltage |
| 9 | FAULT_OUT | Out | Active-low hardware fault |
| 10 | +5 V_System | Power | |
| 11 | +3.3 V (controller I/O ref) | Power | For MISO 6N137 output pull-up |
| 12 | GND_System | Power | |
| (unused pins) | reserved | | |

The two boards are wired identically. Differentiation between "Bridge 1" and "Bridge 2" is purely which timer drives that board (TIM1 vs TIM8) and which DC source feeds it.

---

## 8. Control Firmware

The firmware is a CMSIS bare-metal implementation on the STM32F303RE running at 64 MHz from the internal HSI through the PLL (no external crystal). Build artifacts: ~36 KB Flash, ~4 KB RAM.

### 8.1 State Machine

```
                  sensor fault / UV / OV / OC / imbalance
 BOOT ──▶ IDLE ─────────────────────────────────────────┐
          │                                              │
          │ START                                        ▼
          ▼                                         ┌─────────┐
       PRECHARGE ── precharge_done ──▶ RUN ─ fault ─▶  FAULT  │
          │                            │              └─────────┘
          │ STOP                       │ STOP             │
          ▼                            ▼                  │ CLEAR
        IDLE  ◀───────────────────── IDLE ◀───────────────┘
```

- **BOOT** initializes hardware, runs the ADC self-test, chooses the most capable available sensing mode, drops to IDLE.
- **IDLE** keeps both timers' MOE bits low (all gates off), accepts commands.
- **PRECHARGE** enables MOE and runs the 6 ms bootstrap pre-charge sequence (both LS on, both HS off).
- **RUN** runs the active modulator and checks protection after each 1 kHz sensor scan.
- **FAULT** clears MOE, latches the fault bits, drives FAULT_OUT low, requires CLEAR after the active condition is gone.

### 8.2 Sensing Modes

Six modes with graceful boot-time degradation:

| ID | Mode | Sensors used | Active protection |
|---|---|---|---|
| 0 | `FULL` | DC1, DC2, current | UV, OV, OC, imbalance |
| 1 | `DC_ONLY` | DC1, DC2 | UV, OV, imbalance |
| 2 | `CUR_ONLY` | Current | OC |
| 3 | `OPEN` | None | None (warns operator) |
| 4 | `DC1` | DC1, optional current | DC1 UV/OV + OC if available |
| 5 | `DC2` | DC2, optional current | DC2 UV/OV + OC if available |

At boot, each MCP3201 is read four times. Sensors stuck at 0x000 or 0xFFF are marked unavailable. The FSM auto-demotes to the most capable supported mode.

### 8.3 Modulators

Three modulators are selectable at runtime:

| Modulator | Switching freq | Bridges | Output | Status |
|---|---|---|---|---|
| `STAIR` | 500 Hz | Bridge 1 carries ±1 | 5-level staircase | Reliable, thermally unbalanced (legacy) |
| `STAIR_ALT` | 500 Hz | ±1 ownership alternates | 5-level staircase | Reliable, thermally balanced |
| `PSC` | 5 kHz default | Both bridges modulated | True 5-level PWM | **Default in v4** — project deliverable |

Switching is via the UART `MOD STAIR|PSC|STAIR_ALT` command or the dashboard's modulator dropdown.

The boot-default modulator is set by the `PWM_DEFAULT_MODULATOR` macro in `Core/Inc/pwm_config.h`.

### 8.4 Auto-Start

If no UART byte is received within 3 seconds of boot, the firmware issues its own START using the configured defaults. Any UART byte cancels auto-start permanently. The dashboard exploits this by sending `STATUS` on connect (and on every detected `$A,BOOT_SELF_TEST_DONE` line for post-reset cancellation), so a connected dashboard always retains full operator control.

This auto-start mechanism enables standalone deployment — the inverter runs from defaults with USB power only, no PC required.

### 8.5 Interrupt Hierarchy

| IRQ | Priority | Purpose |
|---|---|---|
| TIM1_UP (PWM update) | 0 (highest) | Per-period modulator dispatch, CCR write |
| TIM6 (sense tick) | 2 | 1 kHz flag-set only; SPI read happens in main loop |
| USART2 | 3 | Per-byte RX, TX buffer drain |
| SysTick | 15 (lowest) | ms counter |

This priority ordering guarantees PWM timing is never delayed by sensing or communication.

### 8.6 Telemetry Format

Telemetry emits at 20 Hz over USART2 in NMEA-style ASCII lines with XOR checksums:

```
$T,<ms>,<state>,<mode>,<fault>,<vdc1>,<vdc2>,<iout>,<level>*<chk>
```

Example: `$T,12345,RUN,FULL,0x00,49.87,50.02,3.41,1*7B`

Other line prefixes:

| Prefix | Type | Example |
|---|---|---|
| `$A,` | Acknowledgment | `$A,START` |
| `$E,` | Error | `$E,MODE_SENSOR_UNAVAILABLE` |
| `$F,` | Fault report | `$F,0x09,UV\|IMBAL` |
| `$H,` | Help text | `$H,START STOP CLEAR ...` |
| `$S,` | Status snapshot | `$S,ms=42,state=IDLE,mode=FULL,fault=0x00,...` |
| `$C,` | PWM config | `$C,mod=PSC,fsw=5000,bridge=BOTH,ffund=50.00,mi=0.95,cntoff=3199,lock=OK` |
| `$P,` | Protection config | `$P,vnom=50.00,uv=40.00,ov=58.00,oc=15.00,imbal=10.00` |
| `$R,` | Raw ADC diagnostic | `$R,dc1=2017,dc2=2018,cur=1862` |

### 8.7 UART Command Reference

| Command | Allowed states | Action |
|---|---|---|
| `START` | IDLE | Enable MOE, enter PRECHARGE then RUN |
| `STOP` | PRECHARGE, RUN | Disable MOE, return to IDLE |
| `CLEAR` | FAULT | Clear latched fault if active condition is gone |
| `MODE <0..5>` | IDLE, FAULT | Select sensing mode |
| `STATUS` | Any | Print one `$S` status line |
| `HELP` | Any | Print full command list |
| `MI <0.0..0.95>` | IDLE | Set modulation index |
| `RESCAN` | IDLE, FAULT | Re-run ADC self-test, re-mark sensors |
| `MOD STAIR\|PSC\|STAIR_ALT` | IDLE | Select modulator |
| `FSW <hz>` | IDLE | Set switching frequency (100–20 000 Hz) |
| `BRIDGE BOTH\|B1\|B2` | IDLE | Single-bridge test mode |
| `FFUND <hz>` | IDLE | Set fundamental frequency (10–400 Hz) |
| `VNOM <v>` | IDLE, FAULT | Set nominal bus voltage (derives UV/OV/IMBAL) |
| `OC <a>` | IDLE, FAULT | Set overcurrent threshold (0.5–20 A) |
| `SPIINV <0..7>` | IDLE, FAULT | Set MCP3201 SPI line-inversion mask + auto-rescan |
| `ADCRAW` | Any | One-shot raw MCP3201 read for diagnostics |
| `TRIP` | IDLE, PRECHARGE, RUN | Operator-forced fault — for demo purposes |
| `CONFIG` | Any | Print `$C` and `$P` config lines |

### 8.8 SPIINV — The 6N137 Polarity Switch

Each MCP3201 SPI line crosses a 6N137 optocoupler, which inverts. The firmware can be told to drive/read each line inverted to cancel the optocoupler:

| Bit | Line | When to set |
|---|---|---|
| 0 (0x01) | SCK | Wired through one 6N137 (standard) |
| 1 (0x02) | CS | Wired through one 6N137 (standard) |
| 2 (0x04) | MISO | Wired through one 6N137 (standard) |

For the standard wiring (one 6N137 per line), set `SPIINV 7`. For direct (non-isolated) test wiring, `SPIINV 0`. Other values handle mixed topologies during diagnostic work.

Setting SPIINV also automatically re-runs the ADC self-test so the operator immediately sees whether sensors come alive at the new polarity.

The boot default is set by `SPI_DEFAULT_INVERT_MASK` in `Core/Inc/spi_mcp3201.h`.

---

## 9. PSC-PWM Modulation Explained

### 9.1 Principle

In phase-shifted carrier PWM (PSC), each H-bridge cell modulates the same reference sine against its own triangular carrier, with the carriers offset in phase between cells. For N cascaded cells the carriers are spaced 360°/N apart (or equivalently 180°/N for natural cancellation).

For this two-cell system (N = 2), the carriers are 90° apart. The cascaded output waveform exhibits:
- Switching ripple at 2 × F_sw (10 kHz here), naturally cancelling at the cascade tap
- 5 distinct voltage levels (+2Vdc, +Vdc, 0, −Vdc, −2Vdc) over each sine peak region
- Balanced switching load between bridges (each switches at F_sw)

The 5-level output is intrinsic to PSC with 90° carrier shift; no quantization logic in software is required.

### 9.2 Unipolar Switching per Bridge

Within each H-bridge, the two legs are driven complementarily with opposite phase modulating signals:
- Leg A: duty = 0.5 + 0.5 × ref (where `ref` is the sine reference in range [−1, +1])
- Leg B: duty = 0.5 − 0.5 × ref

This produces a unipolar PWM output between the leg outputs, with effective switching frequency at the bridge output of 2 × F_sw. Combined with the 90° carrier shift between bridges, the cascaded output ripple is at 4 × F_sw.

### 9.3 STM32 Implementation

Both TIM1 (Bridge 1) and TIM8 (Bridge 2) are advanced-control timers configured for center-aligned PWM with complementary outputs and 3 µs dead-time. They share the APB2 timer clock at 64 MHz.

At a 5 kHz target switching frequency, the timer ARR is:
```
ARR = TIMER_CLK / (F_sw × 2) − 1 = 64 000 000 / (5 000 × 2) − 1 = 6 399
```

(The factor of 2 accounts for center-aligned mode, where one PWM period equals 2 × ARR counter ticks.)

The 90° phase shift between TIM8 and TIM1 is implemented by preloading TIM8's counter to `ARR / 2 = 3 199` ticks ahead of TIM1, immediately after both timers' CEN bits are set:

```c
TIM1->CR1 |= TIM_CR1_CEN;
TIM8->CR1 |= TIM_CR1_CEN;
if (g_pwm_modulator == MODULATOR_PSC) {
    TIM8->CNT = g_pwm_period / 2u;  // 90° offset for N=2
}
```

Because both timers share the same clock domain, once the offset is established it remains locked indefinitely. No master-slave timer linkage is required.

### 9.4 Phase-Lock Diagnostic

After applying a new PSC configuration the firmware reads both counters back, computes the measured offset, and reports it in the `$C` config line:

```
$C,mod=PSC,fsw=5000,bridge=BOTH,ffund=50.00,mi=0.95,cntoff=3200,lock=OK
```

`cntoff` is the measured TIM8 − TIM1 counter offset in clock ticks. `lock=OK` if the measured value is within 5 % of the expected ARR/2; `lock=BAD` otherwise. The operator (or dashboard) sees instantly whether the 90° shift took effect — without needing to scope two timers simultaneously.

### 9.5 Sine Look-Up Table

The reference sine is generated from a 256-entry pre-computed LUT. At each PWM update interrupt the phase accumulator is advanced by:

```
phase_increment = (F_fundamental / F_sw) × 256_samples
```

At 50 Hz fundamental and 5 kHz switching: 25.6 samples per PWM period. The accumulator is a `float` for sub-sample precision; the integer index into the LUT truncates the fractional part.

---

## 10. Protection System

The firmware implements seven fault conditions, all with software response. Hardware fuses provide the last line of defense.

### 10.1 Fault Categories

| Fault | Detection | Default threshold (VNOM=50 V) | Response |
|---|---|---|---|
| Undervoltage (UV) | DC bus < 0.80 × VNOM | 40 V | Latch, drop MOE |
| Overvoltage (OV) | DC bus > 1.16 × VNOM | 58 V | Latch, drop MOE |
| Overcurrent (OC) | \|I_out\| > OC threshold | 15 A | Latch, drop MOE |
| Imbalance | \|V_DC1 − V_DC2\| > 0.20 × VNOM | 10 V | Latch, drop MOE |
| Sensor lost | 5 consecutive 0x000 or 0xFFF reads | — | Latch, drop MOE |
| Manual TRIP | Operator command | — | Latch, drop MOE |
| Hardware short circuit | 15 A blade fuse | — | Physical disconnect |

### 10.2 Debounce

Each voltage/current fault uses a 3-sample N-of-M debounce at the 1 kHz sense rate. The fault must be observed in 3 consecutive scans before it trips. Single-sample noise is rejected; legitimate faults trip within ~3 ms.

### 10.3 FAULT_OUT Hardware Pin

PB5 is configured as a push-pull GPIO output, active-low. When the FSM latches any fault, FAULT_OUT is driven LOW; on return to IDLE it returns HIGH. This pin is intended to drive an external interlock relay or status LED. It corresponds to v3.1 header pin 16.

### 10.4 Clearing Faults

The `CLEAR` command is accepted only in FAULT state and only if the underlying condition has cleared. The firmware re-evaluates protection at the moment of CLEAR; if any fault bit is still active, CLEAR is rejected with `$E,FAULT_STILL_ACTIVE`. This prevents the operator from inadvertently re-enabling power into a still-failed condition.

---

## 11. Dashboard & Operator Workflow

The PC dashboard is the primary operator interface. It runs on Windows, Linux, and macOS, requires no firmware modification, and exposes every UART command through tappable controls.

### 11.1 Architecture

```
┌─────────────────────────┐         ┌──────────────────────────┐
│  STM32F303RE Nucleo     │         │   PySide6 Dashboard      │
│  ┌────────────────────┐ │   USB   │  ┌─────────────────────┐ │
│  │  Firmware FSM      │ │   VCP   │  │  Source Adapter     │ │
│  │  + PSC modulator   │ │ ─────── │  │  (Serial / Sim /    │ │
│  │  + Sensing         │ │ 115200  │  │   Replay)           │ │
│  │  + Protection      │ │   8N1   │  └─────────────────────┘ │
│  │  + USART2 telem    │ │         │  ┌─────────────────────┐ │
│  └────────────────────┘ │         │  │  NMEA Parser        │ │
└─────────────────────────┘         │  └─────────────────────┘ │
                                    │  ┌─────────────────────┐ │
                                    │  │  Live plots + FSM   │ │
                                    │  │  + Fault badge      │ │
                                    │  │  + Modulation viz   │ │
                                    │  └─────────────────────┘ │
                                    │  ┌─────────────────────┐ │
                                    │  │  Command controls   │ │
                                    │  └─────────────────────┘ │
                                    └──────────────────────────┘
```

Built on PySide6 + pyqtgraph + pyserial. The simulator is a pure-Python state-machine mirror of the firmware that requires no hardware — used for fault-condition demos, training, and offline development.

### 11.2 Installation

```powershell
py -3 -m venv dashboard\.venv
dashboard\.venv\Scripts\python -m pip install --upgrade pip
dashboard\.venv\Scripts\python -m pip install -r dashboard\requirements.txt
dashboard\.venv\Scripts\python dashboard\run_dashboard.py
```

### 11.3 Operator Workflow (Bench Session)

1. **Connect first.** Plug the Nucleo's ST-LINK USB before opening the dashboard. Note the assigned COM port (Windows: Device Manager → Ports).
2. **Open dashboard, connect to COM port.** The dashboard sends `STATUS` immediately on connect, cancelling the firmware's 3 s auto-start window.
3. **Flash firmware.** From STM32CubeIDE or `STM32_Programmer_CLI`. The dashboard re-cancels auto-start the moment it sees the post-flash boot message.
4. **Configure VNOM** for the actual bench bus voltage. At low test voltages (e.g. 10 V), set `VNOM 10` to scale protection thresholds appropriately.
5. **Configure modulator.** `MOD PSC` for the 5-level deliverable; `MOD STAIR` for the legacy fallback; `MOD STAIR_ALT` for thermally-balanced staircase without PSC's hardware demands.
6. **Apply DC bus voltage** to both bridges with output limits set conservatively.
7. **START.** Watch the dashboard for `$A,START`, then `$A,RUN` after ~6 ms pre-charge.
8. **Monitor.** Live plots of V_DC1, V_DC2, I_out, the modulation visualization, and the FSM state badge.
9. **STOP.** Cleanly disables MOE and returns to IDLE.

### 11.4 Safety Boundaries

- `START` over live serial is gated behind an "Arm live START" checkbox. The user must explicitly enable the gate before each session.
- Scenario fault buttons (UV, OV, OC, IMBAL, Sensor Lost, etc.) only run against the simulator. They never inject fake sensor values into the firmware. This means a fault-demonstration button cannot accidentally trip a real power stage.
- The dashboard refuses to send `START` over live serial without arming. Other commands (`STATUS`, `STOP`, `MODE`, `CLEAR`, `MI`, etc.) are always available.

---

## 12. Bring-Up & Test

Full bring-up procedures live in the firmware repository:

- **`FIRST_BENCH_SESSION.md`** — recommended first-session walkthrough. Goes from `git pull` to confirmed 5-level PSC output in one continuous procedure, with explicit pass/fail criteria and TLP250 protection checks at every step.
- **`HARDWARE_BRINGUP.md`** — comprehensive phase-by-phase reference. Covers every test phase from continuity to full-voltage PSC sustained run, with troubleshooting trees for every common failure mode.

### 12.1 Condensed Phase Checklist

| Phase | Activity | Pass criterion |
|---|---|---|
| 0 | Firmware sanity (no power) | Boot messages, `$C` config, telemetry @ 20 Hz |
| 1 | Continuity (no power) | No unexpected shorts, all diodes oriented correctly |
| 2 | Gate drive with external 15 V (no DC bus) | Clean Vgs on all 8 MOSFETs, dead-time visible |
| 3 | B0515S supply test | 13–16 V on +15V_Drive under load |
| 4 | Sensing decode (5 V into bus terminal) | `vdc` reads 4.7–5.3 V; SPIINV set correctly |
| 5 | Low-voltage power (10 V bus, STAIR) | 5-level staircase at ±20 V output |
| 6 | Single-bridge isolation | Each bridge in B1/B2 mode produces 3-level output |
| 7 | Full voltage (50 V bus, STAIR) | ±100 V staircase, THD < 5 % |
| 7b | Safe PSC bring-up (5 V, ramping) | 5 levels confirmed at low voltage before raising |
| 8 | PSC at full voltage | 5 distinct levels at ±100 V, bridges thermally balanced |
| 9 | Frequency sweep (optional) | Stable across 1–10 kHz F_sw |
| 10 | Fault injection | All seven fault types trip within 3–4 ms |

### 12.2 Bench-Validated Results (Demo)

At the project demonstration:
- ✅ 5-level PSC output verified on oscilloscope at the cascaded AC output
- ✅ Bridges thermally balanced — Bridge 1 and Bridge 2 MOSFET case temperatures within ~3 °C at sustained 50 V / ~700 W operation
- ✅ `$C,...,lock=OK,cntoff≈3199` reported by firmware (PSC phase-shift confirmed)
- ✅ Full protection system exercised (UV, OV, OC, IMBAL, sensor-lost, manual TRIP)
- ✅ Grounding architecture verified clean (the 5V_GND ↔ 50V_GND issue identified in late iteration was resolved on the populated boards)

---

## 13. V3.1 Errata

The following points in v3.1 are corrected by v4.

### 13.1 Pin-Map Errors (Critical)

**v3.1 listed (incorrect):**
- PWM_1L: PA10 (TIM1_CH2N) → PA10 has *no* TIM1_CH2N alternate function on the STM32F303RE
- PWM_3H/PWM_3L/PWM_4H/PWM_4L on PC6/PC7/PC8/PC9 → only PC6 maps to TIM8_CH1; PC7/PC8/PC9 map to TIM8_CH2/CH3/CH4 respectively, not the complementary outputs

**v4 corrects to:**
- PWM_1L: PA12 (TIM1_CH2N, AF6) ✓
- TIM8 channels: PB6/PB3/PB8/PB0 (CH1/CH1N/CH2/CH2N) ✓ — these are the valid complementary-pair pins for TIM8 on the F303RE package

### 13.2 MOSFET Selection

**v3.1:** IRFZ44N (55 V V_DSS) — insufficient margin against the 1.5KE62A's 84.5 V clamp.
**v4:** IRFB4110 (100 V V_DSS, 4.5 mΩ R_DS(on)) — comfortable margin, lower conduction losses.

### 13.3 Sensing Topology

**v3.1:** Three independent isolated MISO returns, three 6N137 per system.
**v4:** Two isolated MISO returns — DC2 and CUR ADCs wire-share PC3 on the upper-bridge island. Sequential one-CS-at-a-time read in firmware.

### 13.4 Modulation Strategy

**v3.1:** In-Phase Disposition Level-Shifted PWM (IPD LS-PWM) at 5 kHz, no fallback.
**v4:** Three modulators runtime-switchable. PSC-PWM at 5 kHz is the bench-validated deliverable; STAIR (500 Hz quantize) and STAIR_ALT (bridge-balanced quantize) are fallbacks. The active modulator is selectable from the dashboard.

### 13.5 Protection Thresholds

**v3.1:** Fixed thresholds (UV=40 V, OV=58 V, IMBAL=10 V, OC=15 A).
**v4:** Voltage thresholds runtime-configurable via VNOM, scaling all three by fixed ratios. OC remains independent. This enables bench testing at any bus voltage from 5 V to 60 V.

### 13.6 System Clock

**v3.1:** 72 MHz from external 8 MHz crystal (HSE) through PLL.
**v4:** 64 MHz from internal HSI through PLL — no crystal required. All timer arithmetic is derived from the actual clock, so register values differ from v3.1's tables.

### 13.7 Dead-Time

**v3.1:** 500 ns – 1 µs target (sized for IRFZ44N).
**v4:** 3 µs (sized for IRFB4110's ~150 nC gate charge with the same 22 Ω gate resistor).

### 13.8 Maximum Duty Cycle Clamp

**v3.1:** Specified 95 % but indicated 99 % was used.
**v4:** Hard 95 % enforced in firmware, with the OLD 99 % clamp tightened to comply with v3.1 §7.4. Output amplitude impact: ~4 % at MI = 0.95.

### 13.9 Auto-Start

**v3.1:** Not specified.
**v4:** 3-second auto-start fallback if no UART activity received. Standalone deployment supported; dashboard auto-cancels.

### 13.10 Dashboard

**v3.1:** Not present in the design scope.
**v4:** First-class operator interface (PySide6 + pyqtgraph + pyserial) with live plots, simulator-backed scenario playback, and full command coverage.

---

## 14. Safety

Power-stage operation involves voltages and currents capable of causing fire, injury, or fatal electric shock. Observe the following at all times:

- **DC link capacitors store energy for ~8 minutes after power-off.** The 100 kΩ / 2 W bleeders provide passive discharge but verify with a multimeter before touching the bus.
- **The 1.5KE62A TVS will fail short on sustained overvoltage** — protection of last resort, not an operating-point limit.
- **Bridge 2's negative terminal is not at system ground.** Differential probes are required for any measurement spanning the two bridges.
- **Always have an emergency-stop reachable** during operation. The bench supply Output Enable button is sufficient if directly accessible.
- **Heatsinks must be attached to all 8 MOSFETs before applying any DC bus voltage.** No exceptions.
- **Safety glasses** during initial power-up and any voltage ramp. Failed DC link capacitors can vent explosively.
- **No `START` over live serial without explicitly arming the dashboard's safety checkbox.**
- **OPEN mode disables all protection.** Use only for demos with isolated low-voltage supplies.

The firmware enforces:
- Maximum duty cycle 95 %
- Modulation index range 0.0–0.95
- VNOM range 5–60 V
- OC range 0.5–20 A
- Fault latching with operator-acknowledged CLEAR
- MOE driven low in IDLE, BOOT, and FAULT (via `BDTR.OSSI = 1`, all gates forced inactive)

The hardware enforces:
- 15 A blade fuse on each DC input
- 1N5408 reverse-polarity diode
- 1.5KE62A TVS clamp
- 100 kΩ bleeder for capacitor discharge

---

## 15. Future Work

The following items are tracked as roadmap items in the project repository's `roadmap/` directory:

### 15.1 Hardware

- **LC output filter design.** Sized for 5 kHz PSC switching with the 4× ripple-frequency advantage, targeting <2 % output THD into resistive load.
- **Thermal management and enclosure.** Current bench operation uses TO-220 clip-on heatsinks. A purpose-built enclosure with forced-air or aluminum-substrate cooling would enable sustained operation at the 700 W rating.
- **Higher switching frequency exploration.** At F_sw = 10–15 kHz the LC filter shrinks significantly. The IRFB4110 + TLP250 + 22 Ω gate path supports this with no BOM changes; switching losses become the limit. Frequency sweep characterization is the gating test.

### 15.2 Firmware

- **Closed-loop voltage regulation.** Currently MI is set manually. Adding a PI loop on output RMS voltage would compensate for load variations and DC bus droop.
- **Grid-tie phase-lock.** A software PLL on a measured grid voltage would enable grid-following operation. Requires an additional voltage sensor on the AC output.
- **CAN or RS-485 interface.** USART2/VCP is convenient for bench but a galvanically isolated industrial bus is appropriate for any deployed product.

### 15.3 Experimental Tracks (Repository: `experimental/`)

The repository's `experimental/` directory houses untested or research-only work. These tracks are not validated on the project hardware and are gated behind a clear "NOT VALIDATED" banner. They do not appear in the main report but are preserved for future development:

- **RISC-V SoC and hardware PWM accelerator.** A custom RV32IM core with a dedicated zero-jitter PWM peripheral, synthesized to GDSII on the SkyWater 130 nm PDK. Layout complete; no silicon. Provides a future high-performance control path with hardware-enforced dead-time and synchronized carriers.
- **FPGA controller emulation.** Verilog RTL paths for prototyping the RISC-V design on a development FPGA before any silicon commitment.

### 15.4 Product Path

To take this beyond a graduation project requires:
- Safety certification scope (IEC 62109 for inverters, regional variants)
- EMC compliance testing
- Conformal coating and ingress protection
- Production-grade BOM with lifecycle commitment from suppliers
- Manufacturing test fixtures (in-circuit test, programming, calibration)
- A safety case for the closed-loop control firmware

These items are out of scope for the graduation project but are tracked in `roadmap/product-path.md` for future reference.

---

## Appendix A — Quick Reference Card

| Operation | Command |
|---|---|
| Bench test at 12 V bus | `VNOM 12`, then `START` |
| Switch to PSC at full voltage | `MOD PSC`, `FSW 5000`, `VNOM 50`, `START` |
| Single-bridge fault diagnostic | `BRIDGE B1`, `START`, then `BRIDGE B2`, `START` |
| Operator-forced fault demo | `TRIP` from RUN — drops MOE, drives FAULT_OUT low |
| Diagnose dead sensor | `ADCRAW` to see raw counts, then `SPIINV 7` to flip polarity |
| Set conservative current limit | `OC 5` (5 A trip during initial bring-up) |
| Live config snapshot | `CONFIG` emits `$C` and `$P` lines |
| Recover from sensor loss without reboot | `RESCAN` |

## Appendix B — Key Files in the Firmware Repository

| Path | Role |
|---|---|
| `Core/Src/main.c` | System init, clock, GPIO, NVIC, FSM_Init kickoff |
| `Core/Src/pwm_modulator.c` | TIM1+TIM8 setup, STAIR/STAIR_ALT/PSC modulators |
| `Core/Inc/pwm_config.h` | Runtime PWM defaults and bounds |
| `Core/Src/fsm.c` | State machine, command dispatch, auto-start |
| `Core/Src/sensing.c` | 1 kHz sensor scan, IIR filtering, mode logic |
| `Core/Src/spi_mcp3201.c` | Bit-banged SPI driver, SPIINV polarity handling |
| `Core/Src/protection.c` | Threshold checking, debounce, latching |
| `Core/Src/uart_telem.c` | NMEA emit/parse, command tokenizer |
| `dashboard/visual_twin_dashboard/` | PySide6 desktop application |
| `dashboard/visual_twin_dashboard/sim.py` | PC-only simulator mirror of firmware |

---

*End of Build Guide v4.0 — May 2026*
