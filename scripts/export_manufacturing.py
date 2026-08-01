"""Export and package KiCad manufacturing outputs.

The package is deliberately marked preliminary when DRC has violations. This
prevents a syntactically valid Gerber archive from being mistaken for a safe
orderable design.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import shutil
import subprocess
import sys

ROOT = Path(__file__).parents[1]
PCB = ROOT / "hardware" / "blower-controller.kicad_pcb"
SCH = ROOT / "hardware" / "blower-controller.kicad_sch"
OUT = ROOT / "hardware" / "outputs" / "revA"
ARCHIVE = ROOT / "manufacturing" / "release-revA.zip"

parser = argparse.ArgumentParser()
parser.add_argument("--kicad-cli", default=shutil.which("kicad-cli"))
args = parser.parse_args()
if not args.kicad_cli:
    raise SystemExit("kicad-cli not found; install KiCad or pass --kicad-cli")
if not PCB.exists() or not SCH.exists():
    raise SystemExit("missing KiCad source files")

OUT.mkdir(parents=True, exist_ok=True)
def run(*parts, check=True):
    return subprocess.run([args.kicad_cli, *parts], cwd=ROOT, check=check)

drc = OUT / "revA-drc.rpt"
result = run("pcb", "drc", "--exit-code-violations", "--output", str(drc), str(PCB), check=False)
status = "PASS: KiCad DRC returned no violations" if result.returncode == 0 else "BLOCKED: KiCad DRC returned violations"

run("pcb", "export", "gerbers", "--output", str(OUT), "--layers", "F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts", str(PCB))
run("pcb", "export", "drill", "--output", str(OUT), "--format", "excellon", "--generate-map", "--map-format", "pdf", str(PCB))
run("pcb", "export", "pdf", "--output", str(OUT / "pcb.pdf"), "--layers", "F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts", str(PCB))
run("sch", "export", "pdf", "--output", str(OUT / "schematic.pdf"), str(SCH))
run("pcb", "export", "pos", "--output", str(OUT / "placement.csv"), "--format", "csv", "--units", "mm", "--side", "both", str(PCB))

(OUT / "MANUFACTURING-STATUS.txt").write_text(
    f"{status}\nREFERENCE REVISION ONLY. Do not order until DRC, electrical review, thermal testing, and mechanical fit are complete.\n",
    encoding="utf-8",
)
(OUT / "BOM.csv").write_text(
    "Reference,Value,Manufacturer part number,Assembly status\n"
    "F1,30A fuse,VERIFY AFTER CURRENT MEASUREMENT,UNVERIFIED\n"
    "Q1 Q2,100V MOSFET,IPT015N10NM5,VERIFY DATASHEET AND FOOTPRINT\n"
    "D1,SMBJ33A TVS,SMBJ33A,VERIFY CLAMPING AND PULSE ENERGY\n",
    encoding="utf-8",
)

with ZipFile(ARCHIVE, "w", ZIP_DEFLATED) as archive:
    for file in OUT.rglob("*"):
        if file.is_file():
            archive.write(file, file.relative_to(ROOT).as_posix())
print(f"{status}\n{ARCHIVE}")
sys.exit(result.returncode)
