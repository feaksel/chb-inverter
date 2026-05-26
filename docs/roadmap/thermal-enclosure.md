# Thermal enclosure

!!! info "Phase 5 stub"
    The bench validation confirmed both bridges thermally matched under sustained load with **the boards on an open bench** — clip-on TO-220 heatsinks per MOSFET, free convection.

The roadmap item is the path to an enclosed deployment:

- **Enclosure** — the boards need a chassis. The current footprint is two 4-layer PCBs + STM32 Nucleo + dual isolated DC supplies + load wiring. A 250 × 200 × 100 mm enclosure with cable glands is a sensible first cut.
- **Forced air vs. larger heatsinks** — at the demonstrated load (≈ 400 W) the clip-on heatsinks were OK on a bench. In an enclosure the convection path is broken; either add a fan (cheap, noisy) or step up to a bigger heatsink with thermal pads (quiet, more BOM cost). The MOSFET case-temperature data from the bench validation is the input that decides.
- **Forced-air supervision** — if a fan is added, the firmware should add a `FAN_FAULT` bit (via a tach input or shoot-through-style supervision) and treat fan loss as a fault condition. The existing protection chain already supports adding new fault bits.
- **Mechanical isolation** — the bridge-side ground islands must stay isolated through the chassis. Standoffs need to keep the floating-island return from coupling to the chassis ground; chassis ground itself ties to the controller side.
- **EMI** — enclosed switching power stages need filtering on the DC input and AC output. Currently absent.

## Decision deferred

The team has not committed to an enclosure design. The graduation deliverable is the open-bench cascaded inverter, with the thermal balance argument backed by bench measurements. Enclosure is the natural next step if the project is taken toward a product, and is captured in the [product path](product-path.md).
