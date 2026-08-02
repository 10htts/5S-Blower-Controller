"""Export and package KiCad manufacturing outputs.

The release archive is updated only after KiCad DRC (including schematic
parity), ERC, and required fabrication-layer checks all pass. Passing these
machine checks does not change the reference revision's not-approved-to-order
status.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import csv
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).parents[1]
PCB = ROOT / "hardware" / "blower-controller.kicad_pcb"
SCH = ROOT / "hardware" / "blower-controller.kicad_sch"
REVISION = "revC"
OUT = ROOT / "hardware" / "outputs" / REVISION
ARCHIVE = ROOT / "manufacturing" / f"pcbway-review-{REVISION}.zip"
REQUIRED_GERBER_SUFFIXES = {
    ".gtl", ".gbl", ".gts", ".gbs", ".gtp", ".gbp", ".gto", ".gbo", ".gm1"
}

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

drc = OUT / f"{REVISION}-drc.rpt"
erc = OUT / f"{REVISION}-erc.rpt"
drc_result = run(
    "pcb", "drc", "--severity-all", "--schematic-parity",
    "--all-track-errors", "--exit-code-violations", "--output", str(drc),
    str(PCB), check=False,
)
erc_result = run(
    "sch", "erc", "--severity-all", "--exit-code-violations",
    "--output", str(erc), str(SCH), check=False,
)

if drc_result.returncode != 0 or erc_result.returncode != 0:
    status = (
        "BLOCKED: KiCad preflight failed "
        f"(DRC exit {drc_result.returncode}, ERC exit {erc_result.returncode})."
    )
    (OUT / "MANUFACTURING-STATUS.txt").write_text(
        f"{status}\n"
        "REFERENCE REVISION ONLY. Do not order. Existing Gerbers or archives "
        "were not regenerated and must be treated as stale review artifacts.\n",
        encoding="utf-8",
    )
    print(status)
    print(f"DRC report: {drc}")
    print(f"ERC report: {erc}")
    sys.exit(drc_result.returncode or erc_result.returncode)

outputs_parent = ROOT / "hardware" / "outputs"
outputs_parent.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix=f"{REVISION}-export-", dir=outputs_parent) as temp_dir:
    stage = Path(temp_dir)
    shutil.copy2(drc, stage / drc.name)
    shutil.copy2(erc, stage / erc.name)

    run("pcb", "export", "gerbers", "--output", str(stage), "--layers", "F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.SilkS,B.SilkS,Edge.Cuts", str(PCB))
    run("pcb", "export", "drill", "--output", str(stage), "--format", "excellon", "--generate-map", "--map-format", "pdf", str(PCB))
    run("pcb", "export", "pdf", "--output", str(stage / "pcb.pdf"), "--layers", "F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts", str(PCB))
    run("sch", "export", "pdf", "--output", str(stage / "schematic.pdf"), str(SCH))
    run("pcb", "export", "pos", "--output", str(stage / "placement.csv"), "--format", "csv", "--units", "mm", "--side", "both", "--exclude-dnp", str(PCB))
    run(
        "sch", "export", "bom", "--output", str(stage / "BOM.csv"),
        "--fields", "Reference,Value,Footprint,MPN,LCSC,QUANTITY,DNP",
        "--labels", "References,Value,Footprint,Manufacturer Part Number,LCSC,Quantity,DNP",
        "--group-by", "Value,Footprint,MPN,LCSC,DNP", "--sort-field", "Reference",
        "--exclude-dnp", str(SCH),
    )
    run("pcb", "render", "--output", str(stage / "board-top.png"), "--side", "top", "--quality", "high", str(PCB))
    run("pcb", "render", "--output", str(stage / "board-bottom.png"), "--side", "bottom", "--quality", "high", str(PCB))

    kicad_python = Path(args.kicad_cli).with_name("python.exe")
    if not kicad_python.is_file():
        raise SystemExit(f"KiCad Python not found beside kicad-cli: {kicad_python}")
    via_in_pad_result = subprocess.run(
        [
            str(kicad_python),
            str(ROOT / "scripts" / "check_via_in_pad.py"),
            str(PCB),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    via_in_pad_report = via_in_pad_result.stdout
    (stage / "VIA-IN-PAD-REVIEW.txt").write_text(
        via_in_pad_report,
        encoding="utf-8",
    )
    via_in_pad_count = int(via_in_pad_report.splitlines()[0].split("=", 1)[1])

    generated_suffixes = {
        file.suffix.lower()
        for file in stage.iterdir()
        if file.is_file() and file.stat().st_size > 0
    }
    missing_gerbers = sorted(REQUIRED_GERBER_SUFFIXES - generated_suffixes)
    if missing_gerbers:
        raise SystemExit(
            "required Gerber layers were not generated: " + ", ".join(missing_gerbers)
        )
    if not any(
        file.suffix.lower() == ".drl" and file.stat().st_size > 0
        for file in stage.iterdir()
        if file.is_file()
    ):
        raise SystemExit("required Excellon drill file was not generated")

    with (stage / "BOM.csv").open(newline="", encoding="utf-8-sig") as bom_file:
        bom_rows = list(csv.DictReader(bom_file))
    incomplete_bom = [
        row["References"]
        for row in bom_rows
        if not row["Manufacturer Part Number"].strip()
        or not row["Footprint"].strip()
        or row["LCSC"].strip().upper() == "UNVERIFIED"
    ]

    status = (
        f"PASS: {REVISION} KiCad DRC/ERC returned no violations, "
        "including schematic parity"
    )
    assembly_status = (
        "BLOCKED: BOM/footprint procurement data is incomplete for "
        + ", ".join(incomplete_bom)
        if incomplete_bom
        else "PASS: every populated BOM row has a footprint and verified procurement identifier"
    )
    (stage / "MANUFACTURING-STATUS.txt").write_text(
        f"{status}\n"
        f"{assembly_status}\n"
        f"REVIEW REQUIRED: {via_in_pad_count} drilled via locations intersect "
        "SMD pad copper; approve dogbones or a filled/capped via-in-pad process "
        "before PCBA.\n"
        "REFERENCE REVISION ONLY. Do not order until electrical review, "
        "thermal testing, mechanical fit, and independent Gerber review are complete.\n",
        encoding="utf-8",
    )
    (stage / "FABRICATION-NOTES.txt").write_text(
        f"PCBWay {REVISION} fabrication review package generated by KiCad 10.\n"
        "Board stackup, copper weight, finish, material, controlled impedance, "
        "panelization, and finished thickness are NOT approved until the mechanical "
        "and current/thermal validation records are complete.\n"
        "Via-in-pad fill/cap/tenting is not specified; review "
        "VIA-IN-PAD-REVIEW.txt before PCBA.\n"
        "External fuse is mandatory. B+ and B- are the only battery connections; "
        "this board is not a charger or BMS.\n",
        encoding="utf-8",
    )

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(stage, OUT)

archive_temp = ARCHIVE.with_name(ARCHIVE.name + ".tmp")
if archive_temp.exists():
    archive_temp.unlink()
with ZipFile(archive_temp, "w", ZIP_DEFLATED) as archive:
    for file in OUT.rglob("*"):
        if file.is_file():
            archive.write(file, file.relative_to(OUT).as_posix())
archive_temp.replace(ARCHIVE)
print(f"{status}\n{ARCHIVE}")
