# Manufacturing

The repository includes a KiCad 10 export script. It updates Gerbers, Excellon drills, PCB/schematic PDFs, reports, and the ZIP package only after DRC with schematic parity, ERC, and required fabrication-layer checks pass. On failure it writes fresh reports and a blocked status, but leaves older output directories and archives untouched.

Run from the repository root:

```powershell
python scripts/export_manufacturing.py --kicad-cli "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
```

The current Rev C CAD export passes DRC and ERC. Its current review artifacts are:

- `hardware/outputs/revC/`
- `manufacturing/pcbway-review-revC.zip`

The ZIP may be uploaded to PCBWay's viewer or quotation workflow for an independent file review. It is **not approved for ordering**: exact mechanical fit, motor current and inductive transients, fuse coordination, enclosure thermal performance, and first-article tests are still missing. PCBWay assembly is additionally blocked by incomplete procurement data in the BOM. See `manufacturing/pcbway/README.md` and `docs/revision-status.md`.

Older `revA` outputs are superseded and must not be used for a new quote or order.
