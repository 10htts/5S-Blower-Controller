"""Minimal KiCad s-expression parsing utilities for the board/schematic generator.

Parses official KiCad 10 symbol libraries and footprints so the generator can
embed unmodified library symbols, compute absolute pin positions, and verify
pad numbering against the connectivity table.  Deterministic, stdlib-only.
"""
from __future__ import annotations

import math
import re
from pathlib import Path


class S(list):
    """S-expression node: first element is the tag, rest are atoms or S nodes."""

    @property
    def tag(self):
        return self[0] if self else None

    def find(self, tag):
        for item in self[1:]:
            if isinstance(item, S) and item.tag == tag:
                return item
        return None

    def find_all(self, tag):
        return [i for i in self[1:] if isinstance(i, S) and i.tag == tag]

    def atom(self, index=1, default=None):
        try:
            value = self[index]
        except IndexError:
            return default
        return value


_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()"]+')


class QStr(str):
    """String that was quoted in the source and must be re-quoted on dump."""


def parse(text: str) -> S:
    tokens = _TOKEN.findall(text)
    pos = 0

    def read():
        nonlocal pos
        token = tokens[pos]
        pos += 1
        if token == "(":
            node = S()
            while tokens[pos] != ")":
                node.append(read())
            pos += 1
            return node
        if token.startswith('"'):
            return QStr(token[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        return token

    return read()


def parse_file(path) -> S:
    return parse(Path(path).read_text(encoding="utf-8"))


def dump(node, indent=0) -> str:
    """Serialize an S node back to KiCad-style text."""
    if not isinstance(node, S):
        return atom_text(node)
    pad = "  " * indent
    parts = [str(node.tag)]
    complex_children = any(isinstance(i, S) for i in node[1:])
    if not complex_children:
        parts += [atom_text(i) for i in node[1:]]
        return f"({' '.join(parts)})"
    out = [f"({node.tag}"]
    line = out[0]
    body = []
    for item in node[1:]:
        if isinstance(item, S):
            body.append(dump(item, indent + 1))
        else:
            line += " " + atom_text(item)
    out[0] = line
    inner = "\n".join("  " * (indent + 1) + chunk for chunk in body)
    return out[0] + "\n" + inner + "\n" + pad + ")"


_BARE = re.compile(r"^[A-Za-z0-9_.\-+*/:%~${}\[\]<>|&^!?=#@']+$")


def atom_text(value) -> str:
    text = str(value)
    if isinstance(value, QStr) or (
            isinstance(value, str) and (text == "" or not _BARE.match(text))):
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(value, float):
        return format_num(value)
    return text


def format_num(value: float) -> str:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text if text not in ("-0", "") else "0"


class SymbolLib:
    """Loads (symbol ...) definitions from one or more .kicad_sym files."""

    def __init__(self, base_dir):
        self.base = Path(base_dir)
        self._cache = {}

    def _load_lib(self, lib):
        if lib not in self._cache:
            root = parse_file(self.base / f"{lib}.kicad_sym")
            self._cache[lib] = {
                s.atom(1): s for s in root.find_all("symbol")
            }
        return self._cache[lib]

    def raw_symbol(self, lib, name) -> S:
        table = self._load_lib(lib)
        if name not in table:
            raise KeyError(f"symbol {lib}:{name} not found")
        return table[name]

    def resolve(self, lib, name):
        """Return (chain, merged pins) resolving `extends` parents."""
        chain = [self.raw_symbol(lib, name)]
        node = chain[0]
        while True:
            ext = node.find("extends")
            if ext is None:
                break
            node = self.raw_symbol(lib, ext.atom(1))
            chain.append(node)
        return chain

    def pins(self, lib, name):
        """All pins of a symbol (resolving extends): list of dicts."""
        chain = self.resolve(lib, name)
        # Pins are drawn in the deepest parent that defines sub-symbols.
        for node in chain:
            result = []
            for unit in node.find_all("symbol"):
                for pin in unit.find_all("pin"):
                    at = pin.find("at")
                    result.append({
                        "etype": pin.atom(1),
                        "shape": pin.atom(2),
                        "x": float(at.atom(1)),
                        "y": float(at.atom(2)),
                        "rot": float(at.atom(3, 0)),
                        "len": float(pin.find("length").atom(1)),
                        "name": pin.find("name").atom(1),
                        "number": pin.find("number").atom(1),
                        "unit": unit.atom(1),
                        "hide": pin.find("hide") is not None
                                or "hide" in [a for a in pin if isinstance(a, str)],
                    })
            if result:
                return result
        return []

    def property_value(self, lib, name, prop):
        for node in self.resolve(lib, name):
            for p in node.find_all("property"):
                if p.atom(1) == prop:
                    return p.atom(2)
        return None


def footprint_pads(path):
    """Return pad list [(number, x, y, shape, size, attrs)] for a .kicad_mod."""
    root = parse_file(path)
    pads = []
    for pad in root.find_all("pad"):
        at = pad.find("at")
        size = pad.find("size")
        drill = pad.find("drill")
        pads.append({
            "number": pad.atom(1),
            "type": pad.atom(2),
            "shape": pad.atom(3),
            "x": float(at.atom(1)),
            "y": float(at.atom(2)),
            "rot": float(at.atom(3, 0)),
            "sx": float(size.atom(1)),
            "sy": float(size.atom(2)),
            "drill": float(drill.atom(1)) if drill is not None and not isinstance(drill.atom(1), S) else None,
        })
    return root, pads


def pin_endpoint(pin, sym_x, sym_y, sym_rot, mirror=None):
    """Absolute schematic position of a pin's connection point.

    Symbol-editor Y axis points up; schematic Y axis points down.  The pin
    'at' is the connection endpoint (tip), rotation gives direction toward
    the body.
    """
    px, py = pin["x"], pin["y"]
    if mirror == "x":
        py = -py
    elif mirror == "y":
        px = -px
    rad = math.radians(sym_rot)
    cos_r, sin_r = round(math.cos(rad)), round(math.sin(rad))
    rx = px * cos_r - py * sin_r
    ry = px * sin_r + py * cos_r
    return (sym_x + rx, sym_y - ry)
