"""Developer probe: dump pin/pad numbering for symbols and footprints used by
the generator, so connectivity tables are grounded in the real libraries."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import kicadlib

SYMDIR = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
FPDIR = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")

SYMBOLS = [
    ("Transistor_FET", "IPT015N10N5"),
    ("Driver_FET", "TC4422"),
    ("Regulator_Linear", "MCP1703Ax-500xxDB"),
    ("MCU_Microchip_ATtiny", "ATtiny1616-S"),
    ("Amplifier_Current", "INA180A2"),
    ("Device", "R_Shunt"),
    ("Device", "R"),
    ("Device", "C"),
    ("Device", "C_Polarized"),
    ("Device", "D"),
    ("Device", "D_Zener"),
    ("Device", "D_TVS"),
    ("Device", "D_Schottky_Dual_CommonCathode_AKA"),
    ("Device", "Thermistor_NTC"),
    ("Device", "LED"),
    ("Connector", "TestPoint"),
    ("Connector_Generic", "Conn_01x01"),
    ("Connector_Generic", "Conn_01x03"),
    ("Mechanical", "MountingHole"),
    ("power", "PWR_FLAG"),
]

FOOTPRINTS = [
    "Package_TO_SOT_SMD.pretty/Infineon_PG-HSOF-8-1_ThermalVias.kicad_mod",
    "Package_TO_SOT_SMD.pretty/TO-263-3_TabPin2.kicad_mod",
    "Package_TO_SOT_SMD.pretty/SOT-223-3_TabPin2.kicad_mod",
    "Package_SO.pretty/SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod",
    "Package_SO.pretty/SOIC-20W_7.5x12.8mm_P1.27mm.kicad_mod",
    "Package_TO_SOT_SMD.pretty/SOT-23-5.kicad_mod",
    "Resistor_SMD.pretty/R_Shunt_Vishay_WSR2_WSR3_KelvinConnection.kicad_mod",
    "Diode_SMD.pretty/D_SMC.kicad_mod",
    "Connector_Wire.pretty/SolderWire-4sqmm_1x01_D3mm_OD6mm.kicad_mod",
    "Connector_Wire.pretty/SolderWire-0.5sqmm_1x01_D0.9mm_OD2.1mm.kicad_mod",
    "Capacitor_THT.pretty/CP_Radial_D12.5mm_P5.00mm.kicad_mod",
    "TestPoint.pretty/TestPoint_Pad_D1.5mm.kicad_mod",
]

lib = kicadlib.SymbolLib(SYMDIR)
for libname, sym in SYMBOLS:
    try:
        pins = lib.pins(libname, sym)
        fp = lib.property_value(libname, sym, "Footprint")
        chain = [c.atom(1) for c in lib.resolve(libname, sym)]
        print(f"== {libname}:{sym}  fp={fp!r}  chain={chain}")
        for p in sorted(pins, key=lambda q: (len(q['number']), q['number'])):
            print(f"   pin {p['number']:>3} {p['name']:<12} {p['etype']:<14} at=({p['x']},{p['y']}) rot={p['rot']} len={p['len']} unit={p['unit']} hide={p['hide']}")
    except Exception as exc:
        print(f"== {libname}:{sym}  ERROR {exc}")

for rel in FOOTPRINTS:
    try:
        root, pads = kicadlib.footprint_pads(FPDIR / rel)
        print(f"## {rel}: {len(pads)} pads")
        seen = set()
        for p in pads:
            key = p["number"]
            extra = "" if key not in seen else " (dup)"
            seen.add(key)
            print(f"   pad {p['number']:>3} {p['type']:<8} {p['shape']:<10} at=({p['x']},{p['y']}) size=({p['sx']}x{p['sy']}) drill={p['drill']}{extra}")
    except Exception as exc:
        print(f"## {rel}  ERROR {exc}")
