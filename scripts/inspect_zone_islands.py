"""Print filled-zone island bounds to support independent PCB review."""

from __future__ import annotations

import argparse

import pcbnew


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("board")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(args.board)
    for zone_index, zone in enumerate(board.Zones()):
        for layer in zone.GetLayerSet().Seq():
            fills = zone.GetFilledPolysList(layer)
            print(
                f"zone={zone_index} net={zone.GetNetname()} "
                f"layer={board.GetLayerName(layer)} outlines={fills.OutlineCount()}"
            )
            for outline_index in range(fills.OutlineCount()):
                outline = fills.Outline(outline_index)
                box = outline.BBox()
                print(
                    "  "
                    f"island={outline_index} "
                    f"left={mm(box.GetLeft()):.4f} top={mm(box.GetTop()):.4f} "
                    f"right={mm(box.GetRight()):.4f} bottom={mm(box.GetBottom()):.4f} "
                    f"w={mm(box.GetWidth()):.4f} h={mm(box.GetHeight()):.4f}"
                )


if __name__ == "__main__":
    main()
