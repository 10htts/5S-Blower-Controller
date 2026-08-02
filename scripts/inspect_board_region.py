"""Print pads, tracks, and vias intersecting a rectangular board region."""

from __future__ import annotations

import argparse

import pcbnew


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("board")
    parser.add_argument("left", type=float)
    parser.add_argument("top", type=float)
    parser.add_argument("right", type=float)
    parser.add_argument("bottom", type=float)
    args = parser.parse_args()
    bounds = (args.left, args.top, args.right, args.bottom)

    def inside(x: float, y: float) -> bool:
        return bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]

    board = pcbnew.LoadBoard(args.board)
    print("PADS")
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            at = pad.GetPosition()
            x, y = mm(at.x), mm(at.y)
            if inside(x, y):
                copper = [
                    board.GetLayerName(layer)
                    for layer in pad.GetLayerSet().Seq()
                    if board.GetLayerName(layer).endswith(".Cu")
                ]
                print(
                    f"{footprint.GetReference()}.{pad.GetNumber()} "
                    f"net={pad.GetNetname()} at=({x:.4f},{y:.4f}) "
                    f"size={mm(pad.GetSizeX()):.4f}x{mm(pad.GetSizeY()):.4f} "
                    f"layers={copper}"
                )

    print("TRACKS_AND_VIAS")
    for item in board.GetTracks():
        if item.GetClass() == "PCB_VIA":
            at = item.GetPosition()
            x, y = mm(at.x), mm(at.y)
            if inside(x, y):
                print(
                    f"VIA net={item.GetNetname()} at=({x:.4f},{y:.4f}) "
                    f"diameter={mm(item.GetWidth(pcbnew.F_Cu)):.4f} "
                    f"drill={mm(item.GetDrillValue()):.4f}"
                )
            continue
        start, end = item.GetStart(), item.GetEnd()
        sx, sy = mm(start.x), mm(start.y)
        ex, ey = mm(end.x), mm(end.y)
        if inside(sx, sy) or inside(ex, ey):
            print(
                f"TRACK net={item.GetNetname()} layer={board.GetLayerName(item.GetLayer())} "
                f"({sx:.4f},{sy:.4f})->({ex:.4f},{ey:.4f}) "
                f"width={mm(item.GetWidth()):.4f}"
            )


if __name__ == "__main__":
    main()
