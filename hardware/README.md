# Hardware

KiCad sources, gerbers, BOM, and photos for the as-built hardware.

| Path | Status |
|---|---|
| [`single-bridge-v4/`](single-bridge-v4/) | The board that was fabricated, populated, and demonstrated. Two identical modules cascaded. |
| [`legacy/`](legacy/) | Earlier design iterations preserved for the iteration-history narrative. Not for fabrication. |

The canonical engineering reference for everything in this directory is **[Build Guide v4.0](../docs/hardware/build-guide-v4.md)**.

## Conventions

- BOMs are CSV with these columns: `Reference`, `Quantity`, `Value`, `Footprint`, `MPN`, `Supplier`, `Supplier Part Number`, `Supplier URL`, `Unit Cost TL`.
- Suppliers are restricted to Turkish domestic vendors: Motorobit, Direnc.net, Robotistan, Komponentci.net.
- Passives default to through-hole (THT) for hand-assembly. Documented exceptions: ACS712 (SOIC-8), MCP3201 (DIP-8).
- Photos in `photos/` are tracked via Git LFS (see [`.gitattributes`](../.gitattributes)).
