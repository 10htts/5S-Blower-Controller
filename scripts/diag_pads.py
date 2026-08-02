"""Diagnostic: dump exact pad centers/sizes/layers for named refs from the
generated board, using the KiCad pcbnew Python API.

Usage:
    "C:/Program Files/KiCad/10.0/bin/python.exe" scripts/diag_pads.py REF [REF...]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
PCB = ROOT / "hardware" / "blower-controller.kicad_pcb"

import pcbnew

board = pcbnew.LoadBoard(str(PCB))

refs = sys.argv[1:]
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if refs and ref not in refs:
        continue
    pos = fp.GetPosition()
    print(f"\n=== {ref} @ ({pcbnew.ToMM(pos.x):.4f}, {pcbnew.ToMM(pos.y):.4f}) "
          f"rot={fp.GetOrientationDegrees():.1f} layer={fp.GetLayerName()} ===")
    for pad in fp.Pads():
        p = pad.GetPosition()
        bb = pad.GetBoundingBox()
        net = pad.GetNetname()
        print(f"  pad {pad.GetNumber():>3} net={net!r:14} "
              f"@({pcbnew.ToMM(p.x):.4f}, {pcbnew.ToMM(p.y):.4f}) "
              f"size=({pcbnew.ToMM(bb.GetWidth()):.3f}x{pcbnew.ToMM(bb.GetHeight()):.3f}) "
              f"layer={pad.GetLayerName()} hole={pad.HasHole()}")
