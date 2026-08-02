"""Deterministic KiCad schematic writer.

Builds a flat one-sheet .kicad_sch from a parts/net table:
- Embeds unmodified (flattened) official library symbols plus project symbols.
- Places symbol instances and attaches a global label at every connected pin.
- Adds no-connect markers, PWR_FLAGs, and text notes.

Determinism: all UUIDs are uuid5 of stable seed strings.
"""
from __future__ import annotations

import copy
import uuid
from pathlib import Path

import kicadlib
from kicadlib import S

NAMESPACE = uuid.UUID("9e2d7c3a-5b1f-4b0e-a6a3-2f0f5b7c1d10")
PROJECT = "blower-controller"
ROOT_UUID = str(uuid.uuid5(NAMESPACE, "root-sheet"))


def uid(seed: str) -> str:
    return str(uuid.uuid5(NAMESPACE, seed))


Q = kicadlib.QStr

# tags whose string arguments must be quoted in KiCad files
_QUOTED_TAGS = {"lib_id", "property", "reference", "value", "footprint",
                "pin", "global_label", "text", "title", "company", "date",
                "rev", "comment", "uuid", "generator", "project", "path",
                "name", "number", "page", "paper"}


def mk(tag, *items) -> S:
    node = S([tag])
    for it in items:
        if isinstance(it, str) and not isinstance(it, Q) and tag in _QUOTED_TAGS:
            it = Q(it)
        node.append(it)
    return node


def effects(size=1.27, hide=False, justify=None):
    e = mk("effects", mk("font", mk("size", size, size)))
    if justify:
        e.append(mk("justify", *justify))
    if hide:
        e.append(mk("hide", "yes"))
    return e


def prop(name, value, x, y, hide=True, size=1.27):
    return mk("property", name, value, mk("at", x, y, 0),
              effects(size=size, hide=hide))


class SymbolStore:
    """Flattens and caches library symbols for embedding."""

    def __init__(self, symdir, project_libs=None):
        self.lib = kicadlib.SymbolLib(symdir)
        self.project = {}
        for libname, path in (project_libs or {}).items():
            root = kicadlib.parse_file(path)
            self.project[libname] = {s.atom(1): s for s in root.find_all("symbol")}
        self.embedded = {}

    def _raw_chain(self, libname, name):
        if libname in self.project:
            table = self.project[libname]
            chain = [table[name]]
            while (ext := chain[-1].find("extends")) is not None:
                chain.append(table[ext.atom(1)])
            return chain
        return self.lib.resolve(libname, name)

    def flatten(self, libname, name) -> S:
        """Return embedded symbol named '<libname>:<name>' with extends resolved."""
        chain = self._raw_chain(libname, name)
        base = copy.deepcopy(chain[-1])
        base_name = base.atom(1)
        merged = base
        merged[1] = Q(f"{libname}:{name}")
        # rename inner units Base_X_Y -> Name_X_Y
        for unit in merged.find_all("symbol"):
            uname = unit.atom(1)
            if uname.startswith(base_name + "_"):
                unit[1] = Q(name + uname[len(base_name):])
        if len(chain) > 1:
            # merge properties from derived symbols (nearest wins)
            props = {p.atom(1): p for p in merged.find_all("property")}
            for node in reversed(chain[:-1]):
                for p in node.find_all("property"):
                    tgt = props.get(p.atom(1))
                    if tgt is not None:
                        tgt[2] = p.atom(2)
                    else:
                        np = copy.deepcopy(p)
                        merged.append(np)
                        props[p.atom(1)] = np
        return merged

    def embed(self, libname, name):
        key = f"{libname}:{name}"
        if key not in self.embedded:
            self.embedded[key] = self.flatten(libname, name)
        return key

    def pins(self, libname, name):
        if libname in self.project:
            chain = self._raw_chain(libname, name)
            for node in chain:
                result = []
                for unit in node.find_all("symbol"):
                    for pin in unit.find_all("pin"):
                        at = pin.find("at")
                        result.append({
                            "etype": pin.atom(1),
                            "x": float(at.atom(1)),
                            "y": float(at.atom(2)),
                            "rot": float(at.atom(3, 0)),
                            "name": pin.find("name").atom(1),
                            "number": pin.find("number").atom(1),
                        })
                if result:
                    return result
            return []
        return self.lib.pins(libname, name)


class Schematic:
    def __init__(self, store: SymbolStore, title, rev, company, date):
        self.store = store
        self.items = []
        self.title = title
        self.rev = rev
        self.company = company
        self.date = date
        self.pin_positions = {}  # (ref, pin_number) -> (x, y)
        self.refs = set()

    def place(self, ref, libname, name, value, x, y, rot=0, pin_nets=None,
              nc_pins=(), footprint="", mpn="", lcsc="", dnp=False,
              in_bom=None,
              value_offset=(0, 0), datasheet="~"):
        assert ref not in self.refs, f"duplicate ref {ref}"
        self.refs.add(ref)
        lib_id = self.store.embed(libname, name)
        u = uid(f"sym/{ref}")
        if in_bom is None:
            in_bom = not (ref.startswith(("#", "H", "TP")) or dnp)
        sym = mk("symbol",
                 mk("lib_id", lib_id),
                 mk("at", x, y, rot),
                 mk("unit", 1),
                 mk("exclude_from_sim", "no"),
                 mk("in_bom", "yes" if in_bom else "no"),
                 mk("on_board", "yes"),
                 mk("dnp", "yes" if dnp else "no"),
                 mk("uuid", u))
        show_val = not ref.startswith("#")
        sym.append(prop("Reference", ref, x, y - 2.54, hide=ref.startswith("#")))
        sym.append(prop("Value", value, x + value_offset[0],
                        y + 2.54 + value_offset[1], hide=not show_val))
        sym.append(prop("Footprint", footprint, x, y + 5.08, hide=True))
        sym.append(prop("Datasheet", datasheet, x, y + 7.62, hide=True))
        if mpn:
            sym.append(prop("MPN", mpn, x, y + 10.16, hide=True))
        sym.append(prop("LCSC", lcsc if lcsc else "UNVERIFIED", x, y + 12.7, hide=True))
        pins = self.store.pins(libname, name)
        assert pins or pin_nets in (None, {}), f"{ref}: no pins found"
        seen_numbers = set()
        for p in pins:
            px, py = kicadlib.pin_endpoint(p, x, y, rot)
            self.pin_positions[(ref, p["number"])] = (px, py)
            if p["number"] not in seen_numbers:
                sym.append(mk("pin", p["number"], mk("uuid", uid(f"pin/{ref}/{p['number']}"))))
                seen_numbers.add(p["number"])
        sym.append(mk("instances",
                      mk("project", PROJECT,
                         mk("path", f"/{ROOT_UUID}",
                            mk("reference", ref), mk("unit", 1)))))
        self.items.append(sym)
        # net labels / no-connects
        pin_nets = pin_nets or {}
        declared = set(pin_nets) | set(nc_pins)
        numbers = {p["number"] for p in pins}
        missing = declared - numbers
        assert not missing, f"{ref}: pins {missing} not in symbol {lib_id}"
        handled = set()
        for p in pins:
            n = p["number"]
            if n in handled:
                continue
            handled.add(n)
            px, py = self.pin_positions[(ref, n)]
            if n in pin_nets:
                self.add_label(pin_nets[n], px, py, seed=f"{ref}/{n}")
            elif n in nc_pins:
                self.items.append(mk("no_connect", mk("at", px, py),
                                     mk("uuid", uid(f"nc/{ref}/{n}"))))
            else:
                stacked = [q for q in pins if (q["x"], q["y"]) == (p["x"], p["y"])
                           and q["number"] != n]
                covered = any(q["number"] in pin_nets or q["number"] in nc_pins
                              for q in stacked)
                assert covered or p["etype"] in ("no_connect",), \
                    f"{ref} pin {n} has no net, NC flag, or stacked twin"
        unknown = set(pin_nets) - numbers
        assert not unknown, f"{ref}: nets on unknown pins {unknown}"

    def add_label(self, net, x, y, rot=0, seed=None):
        lbl = mk("global_label", net,
                 mk("shape", "passive"),
                 mk("at", x, y, rot),
                 mk("fields_autoplaced", "yes"),
                 effects(size=1.0),
                 mk("uuid", uid(f"label/{seed or (net, x, y)}")))
        lbl.append(prop("Intersheetrefs", "${INTERSHEET_REFS}", x, y, hide=True))
        self.items.append(lbl)

    def power_flag(self, index, net, x, y):
        self.place(f"#FLG{index:02d}", "power", "PWR_FLAG", "PWR_FLAG", x, y,
                   pin_nets={"1": net}, footprint="")

    def text(self, s, x, y, size=1.5):
        self.items.append(mk("text", s, mk("exclude_from_sim", "no"),
                             mk("at", x, y, 0), effects(size=size),
                             mk("uuid", uid(f"text/{x}/{y}/{s[:16]}"))))

    def write(self, path):
        root = mk("kicad_sch",
                  mk("version", 20231120),
                  mk("generator", "blower_generate_design"),
                  mk("uuid", ROOT_UUID),
                  mk("paper", "A3"),
                  mk("title_block",
                     mk("title", self.title),
                     mk("date", self.date),
                     mk("rev", self.rev),
                     mk("company", self.company),
                     mk("comment", 1, "REFERENCE REVISION - NOT APPROVED TO ORDER")))
        libs = mk("lib_symbols")
        for key in sorted(self.store.embedded):
            libs.append(self.store.embedded[key])
        root.append(libs)
        for item in self.items:
            root.append(item)
        root.append(mk("sheet_instances", mk("path", "/", mk("page", "1"))))
        Path(path).write_text(kicadlib.dump(root) + "\n", encoding="utf-8")
