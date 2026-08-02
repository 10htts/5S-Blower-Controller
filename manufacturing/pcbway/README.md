# PCBWay review package

Use only `manufacturing/pcbway-review-revC.zip`. The archive is a **CAD-clean review package**, not an orderable release. Treat it as stale whenever the export command exits nonzero. The current source has a populated schematic and clean KiCad DRC/ERC reports, including schematic parity; remaining blocks are physical and procurement validation, not CAD connectivity.

The archive contains Gerbers for F.Cu/B.Cu, solder mask, silkscreen, paste, and Edge.Cuts; an Excellon drill file and drill map; BOM and XY placement CSV files; PCB and schematic PDFs; DRC/ERC reports; renders; and fabrication/status notes.

Before authorizing an order:

1. Confirm the 77 × 62 mm outline, mounting holes, connector locations, terminal polarity, component heights, and enclosure clearances against measured mechanical data.
2. Confirm the intended copper weight, thickness, finish, material, and any panelization with the fabricator.
3. Review every Gerber and drill layer in PCBWay's viewer and obtain an independent electrical/layout review.
4. Complete the motor, fuse, transient, thermal, EMI, and first-article gates in `docs/validation-plan.md`.
5. For assembly, resolve every part flagged in `MANUFACTURING-STATUS.txt`, review `VIA-IN-PAD-REVIEW.txt`, choose an approved dogbone or filled/capped via-in-pad process, and verify BOM/placement orientation against manufacturer datasheets.

The external fuse is mandatory. This board accepts only B+ and B− from the battery; it is not a charger or BMS.
