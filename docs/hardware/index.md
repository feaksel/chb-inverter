# Hardware

KiCad sources, gerbers, BOM, and photos for the **single-bridge v4** module — the board that was fabricated, populated, and demonstrated. Two identical instances are cascaded to form the 5-level inverter.

## Canonical reference

The authoritative engineering reference is **[Build Guide v4.0](build-guide-v4.md)** (May 2026). Everything in this section either summarizes the guide or links into it.

## What's on this section

| Page | Purpose | Phase |
|---|---|---|
| [Build Guide v4.0](build-guide-v4.md) | The as-built reference document — 15 sections covering hardware, firmware, bring-up, and known issues. | ✅ in |
| Architecture | System block diagram, module breakdown, signal flow. | Phase 3 |
| BOM | Full bill of materials with Turkish supplier links, auto-rendered from `hardware/single-bridge-v4/bom.csv`. | Phase 3 |
| Schematic | Embedded PDF + ratsnest highlights from KiCad. | Phase 3 |
| PCB layout | Top, bottom, and isometric renders; layer stack-up. | Phase 3 |
| Populated photos | Gallery of the built modules and oscilloscope captures. | Phase 3 |

## Conventions

- BOM has fixed columns: `Reference`, `Quantity`, `Value`, `Footprint`, `MPN`, `Supplier`, `Supplier Part Number`, `Supplier URL`, `Unit Cost TL`.
- Suppliers restricted to Turkish domestic vendors: Motorobit, Direnc.net, Robotistan, Komponentci.net.
- Passives default to through-hole (THT) for hand-assembly. Documented exceptions: ACS712 (SOIC-8), MCP3201 (DIP-8).
- Photos are tracked via Git LFS — see [`.gitattributes`](https://github.com/feaksel/chb-inverter/blob/main/.gitattributes).
