# Hardware

<figure markdown="span">
  ![Top-down KiCad render of the single-bridge v4 PCB](../../hardware/single-bridge-v4/renders/pcb-top-down-kicad.jpeg){ loading=lazy width=80% }
  <figcaption>Top-down KiCad render of the single-bridge v4 PCB. Two identical instances are cascaded to form the 5-level inverter.</figcaption>
</figure>

KiCad sources, gerbers, BOM, and photos for the **single-bridge v4** module — the board that was fabricated, populated, and demonstrated.

## Canonical reference

The authoritative engineering reference is **[Build Guide v4.0](build-guide-v4.md)** (May 2026). Everything in this section either summarizes the guide or links into it.

## Pages in this section

| Page | What it covers |
|---|---|
| [Architecture](architecture.md) | System block diagram, two-module cascade arithmetic, why each component was chosen. |
| [Build Guide v4.0](build-guide-v4.md) | As-built reference document — 15 sections covering hardware, firmware, bring-up, and known issues. |
| [BOM](bom.md) | Full bill of materials with Turkish supplier links — auto-rendered summary + link to `bom.csv`. |
| [Schematic](schematic.md) | KiCad hierarchical schematic — top + 7 subsheets (HS / LS / driver / 5V→15V / voltage-sense / current-sense). |
| [PCB layout](pcb-layout.md) | 4-layer stack-up details, 3D + top-down renders, gerber pack pointers. |
| [Populated photos](populated-photos.md) | Headline 100 V scope capture + demo-day photos + earlier bench-session gallery. |

## Conventions

- BOM has fixed columns: `Reference`, `Quantity`, `Value`, `Footprint`, `MPN`, `Supplier`, `Supplier Part Number`, `Supplier URL`, `Unit Cost TL`.
- Suppliers restricted to Turkish domestic vendors: Motorobit, Direnc.net, Robotistan, Komponentci.net.
- Passives default to through-hole (THT) for hand-assembly. Documented exceptions: ACS712 (SOIC-8), MCP3201 (DIP-8).
- Photos + KiCad PCB + gerbers + renders are tracked via Git LFS — see [`.gitattributes`](https://github.com/feaksel/chb-inverter/blob/main/.gitattributes). After `git clone`, run `git lfs install && git lfs pull`.
