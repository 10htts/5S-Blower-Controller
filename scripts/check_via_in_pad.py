"""Report through-via centers that intersect SMD pad copper.

This is an assembly-process review, not a KiCad DRC replacement.  A reported
via may be intentional, but it needs a documented dogbone, tent/fill/cap, or
other assembly decision before PCBA release.
"""
import argparse

import pcbnew


parser = argparse.ArgumentParser()
parser.add_argument("board")
args = parser.parse_args()

board = pcbnew.LoadBoard(args.board)
smd_pads = [
    (footprint.GetReference(), pad)
    for footprint in board.GetFootprints()
    for pad in footprint.Pads()
    if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
]

hits_by_via = {}
for item in board.Tracks():
    if item.GetClass() != "PCB_VIA":
        continue
    position = item.GetPosition()
    hits = []
    for reference, pad in smd_pads:
        if pad.HitTest(position):
            number = pad.GetNumber() or "unnumbered"
            hits.append(f"{reference}.{number}")
    if hits:
        key = (
            round(pcbnew.ToMM(position.x), 4),
            round(pcbnew.ToMM(position.y), 4),
            item.GetNetname(),
        )
        hits_by_via[key] = sorted(set(hits))

print(f"VIA_IN_PAD_COUNT={len(hits_by_via)}")
print(
    "Each entry is a drilled through-via whose center intersects SMD pad "
    "copper. Review dogbone routing or the required fill/cap/tenting process."
)
for (x_mm, y_mm, net), pad_names in sorted(hits_by_via.items()):
    print(
        f"x={x_mm:.4f} mm y={y_mm:.4f} mm net={net} "
        f"pads={','.join(pad_names)}"
    )
