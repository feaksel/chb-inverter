---
title: Thermal enclosure
---

# Thermal enclosure

The bench validation confirmed both bridges thermally matched under sustained load with **the boards on an open bench** — clip-on TO-220 heatsinks per MOSFET, free convection. The bridge case-temperature delta was ≈ 3 °C in the demo session, well within safe operating range for the IRFB4110.

This roadmap item is the path to **enclosed deployment** — a chassis that the inverter can ship inside, with the thermal performance maintained.

## What changes when you put the boards in a box

Free convection on an open bench dissipates 5–10 W per device pretty easily. Inside an enclosed chassis with no airflow, the same 5–10 W can take the junction temperature past spec within minutes. Three things change:

1. **Convection path is broken.** Hot air collects above the boards; ambient temperature inside the box drifts up; thermal margin shrinks every minute.
2. **The transformer / LC filter** (if added per [LC filter](lc-filter.md)) adds its own losses inside the same enclosure.
3. **EMI** that radiated freely on the open bench now has to be contained — the chassis itself becomes part of the EMI strategy.

## Enclosure dimensions

A starting envelope based on the as-built component footprint:

| Component | Approx dimensions |
|---|---|
| 2× single-bridge v4 PCB (≈ 150 × 100 mm each, end-to-end) | 320 × 100 × 30 mm |
| STM32 Nucleo-F303RE + standoffs | 90 × 70 × 20 mm |
| 2× isolated bench supplies (in production, integrated power-supply board) | 200 × 100 × 40 mm |
| LC filter board (planned) | 150 × 80 × 60 mm (the 15 mH toroid is the bulky part) |
| Cable strain-relief + terminal blocks | 50 mm depth allowance |

Rough enclosure: **300 × 250 × 150 mm**. Wall-mount or DIN-rail mounting bracket.

## Forced air vs. larger heatsinks

| Approach | Pros | Cons |
|---|---|---|
| **Forced air** (axial fan, 60 mm or 80 mm, 12 V) | Cheap (50–100 TL per fan), proven, scales with the load | Audible noise; fan is a failure point — needs a `FAN_FAULT` bit in firmware; ingress protection (dust filter) needed |
| **Larger heatsinks** (vertical extruded with fins) | Silent, no moving parts, no extra failure mode | Significantly more BOM cost (200–400 TL per heatsink); takes up enclosure height; only works up to ≈ 5–10 W per device of dissipation |
| **Combined** (smaller heatsinks + slow fan) | Best of both — fan runs only when temperature climbs | Adds a temperature sensor + thermostat circuit + control logic to firmware |

For the project's ≈ 400 W power-stage load with ≈ 2.4 W of MOSFET dissipation total, **larger heatsinks alone** should be sufficient. Add a fan if production load could scale higher.

## Forced-air supervision (if a fan is added)

The firmware should add a `FAN_FAULT` bit to the protection chain:

- Tach input from the fan → GPIO → simple interrupt-driven pulse counter → expected RPM range.
- If RPM falls outside range for > 2 s, latch `FAULT_FAN` and proceed through the normal FAULT path (MOE off, FAULT_OUT pulled LOW, telemetry frame emits `$F,0x40,...`).
- The existing FSM + protection infrastructure already supports adding fault bits — `protection.h` defines the bitmask.

## Mechanical isolation

The four-layer ground-separation design ([grounding fix](../design-notes/grounding-fix.md)) must survive the chassis integration:

- **PCB standoffs** must be **insulating** (nylon, not metal) so the bridge-side ground islands don't bond to the chassis through the mounting screws.
- **Chassis ground** bonds to the controller's 5V_GND **only** — never to any bridge-side ground.
- **Cable shields** that enter the enclosure must terminate to chassis ground at the entry point, not run inside to a board ground.

Failing any of these defeats the isolation architecture that the entire design depends on.

## EMI containment

Enclosed switching power stages need filtering on the DC input and AC output, plus chassis-bonded shielding:

| Filter | Where | Purpose |
|---|---|---|
| Common-mode choke + Y caps on DC input | Per bridge | Reject conducted EMI back to the supply |
| Common-mode choke on AC output | After the LC filter | Reject conducted EMI to the load |
| Chassis bonding via low-impedance straps | At each PCB | Bleed off radiated EMI before it escapes |

Standard EMI filter modules from Direnc.net or Motorobit cover the conducted-EMI requirements at this power level.

## Effort estimate

| Sub-item | Engineer-time |
|---|---|
| Enclosure CAD (Inventor / Fusion 360) + sheet-metal fab | 2 weeks |
| Thermal characterisation in the enclosure (with + without fan) | 1 week |
| EMI filtering + chassis bonding | 1 week |
| Fan + supervision firmware | 3 days |

Total: **≈ 2 engineer-months** including the enclosure fab turn.

## Where this fits in the sequence

After [LC filter](lc-filter.md) (because the filter has to be inside the same enclosure) and after [closed-loop control](closed-loop-control.md) (because the control loop needs to be stable across the enclosure's thermal regime). Before [grid tie](grid-tie.md) (because a grid-tied unit must be enclosed for safety).
