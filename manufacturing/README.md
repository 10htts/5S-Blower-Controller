# Manufacturing

The repository now includes a KiCad 10 export script. It creates Gerbers, Excellon drills, PCB PDF, schematic PDF, DRC report, and a ZIP package. The script records the DRC result in the archive and refuses to label a failing board as orderable.

Run from the repository root:

```powershell
python scripts/export_manufacturing.py --kicad-cli "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
```

The current reference board is intentionally blocked: it is a layout draft with unresolved DRC violations and is not suitable for upload to PCBWay. `manufacturing/pcbway/README.md` contains the release checklist.
