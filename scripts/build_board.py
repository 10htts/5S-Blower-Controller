"""Single source of truth for the 5S blower controller reference revision (Rev C).

Generates BOTH hardware/blower-controller.kicad_sch and .kicad_pcb from one
connectivity table.  Manual edits to the KiCad files are NOT the workflow;
edit this script and regenerate.  Deterministic (fixed uuid5 seeds).

Run with KiCad's bundled interpreter:
    "C:/Program Files/KiCad/10.0/bin/python.exe" scripts/build_board.py

The default build reproduces the accepted route by generating the validated
power-stage base, importing ``hardware/routing/revC-freerouting.ses``, and
applying the explicit post-route repairs in
``scripts/repair_freeroute_candidate.py``.  ``--legacy-full-routing`` retains
the earlier hand-authored full-route table only for comparison.

Verified component data (datasheet review 2026-08-01/02):
- Q1/Q2  IPT015N10N5ATMA1  100V 1.5mOhm max @10Vgs, Qg typ 169nC, TOLL,
         pin1=G pins2-8=S tab=D (KiCad fp pads 1=G 2=S 3=D). LCSC C108964.
- D2     STPS41H100CG-TR   100V 2x20A Schottky, D2PAK, 1=A 2/tab=K 3=A.
- D1     SMDJ33A           33V standoff, Vc 53.3V @56.3A, 3000W, SMC, unidir.
- U2     TC4422AVOA        4.5-18V (abs 20V), 10A pk, SOIC-8:
         1=VDD 2=IN 3=NC 4=GND 5=GND 6=OUT 7=OUT 8=VDD. LCSC C37183.
- U3     TPS7A4001DGNR     7-100V in, 50mA, FB=1.173V typ, MSOP-8 PowerPAD:
         1=OUT 2=FB 3=NC 4=GND 5=EN 6=NC 7=NC 8=IN, EP=GND. LCSC C55006.
- U4     MCP1703A-5002E/DB 16V in, 250mA, SOT-223: 1=VIN 2=GND(tab) 3=VOUT.
- U1     ATTINY1616-SNR    SOIC-20: 1=VDD 20=GND 16=UPDI 11=PB0(TCA0 WO0)
         10=PB1 2=PA4/AIN4 3=PA5/AIN5 4=PA6/AIN6 5=PA7/AIN7. LCSC C614136.
- U5     INA180A2IDBVR     gain 50, CM -0.2..26V, SOT-23-5:
         1=OUT 2=GND 3=IN+ 4=IN- 5=VS. LCSC C192764.
- RS1    WSR32L000FEA      2mOhm 1% 3W metal strip, Kelvin by split-pad layout.
- C1/C2  UPW1J471MHD       470uF 63V 12.5x25mm P5 low-Z, 1.72A @100kHz.
- C3-C5  C3225X7S2A475K200AE  4.7uF 100V X7S 1210.
- TH1    NCP18XH103F03RB   NTC 10k B3380 0603. LCSC C13564.
- D3     PESD5V0S1BA       bidirectional ESD, SOD-323. LCSC C19224.
- D4     S1M (onsemi)      1000V 1A SMA. LCSC C232826.
- LED1   19-217/GHC-YR1S2/3T green 0603. LCSC C72043 (/6T C2986059 stocked).

VDRV = 10V from TPS7A4001: Vout = 1.173*(1+R14/R15), R14=97.6k R15=13.0k
       -> 9.98V nominal.  Gate driver return is Kelvin-tied to the MOSFET
       source bus (ISNS) so gate current does not cross the shunt.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import kicadlib  # noqa: E402
import kicad_sch_writer as sw  # noqa: E402

SYMDIR = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
FPDIR = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
OUT_SCH = ROOT / "hardware" / "blower-controller.kicad_sch"
OUT_PCB = ROOT / "hardware" / "blower-controller.kicad_pcb"
OUT_PRO = ROOT / "hardware" / "blower-controller.kicad_pro"
PROJ_SYM = ROOT / "hardware" / "symbols" / "blower_project.kicad_sym"
ROUTING_SESSION = ROOT / "hardware" / "routing" / "revC-freerouting.ses"


def enforce_release_drc_severities():
    """Keep manufacturing-relevant placement/routing checks enabled.

    pcbnew can rewrite the project file with KiCad's default ignored severities
    while saving a generated board.  Reinstate the release policy immediately
    before the command-line DRC so reproducibility cannot hide these checks.
    """
    project = OUT_PRO.read_text(encoding="utf-8")
    replacements = {
        '"missing_courtyard": "ignore"': '"missing_courtyard": "error"',
        '"track_not_centered_on_via": "ignore"': (
            '"track_not_centered_on_via": "error"'
        ),
    }
    for old, new in replacements.items():
        project = project.replace(old, new)
    OUT_PRO.write_text(project, encoding="utf-8")

# --------------------------------------------------------------- nets
# Every net used by more than one pin.
NETS = [
    "VBAT", "GND", "SW", "ISNS", "GATE", "G_Q1", "G_Q2", "PWM",
    "VREG_IN", "VDRV", "VFB", "+5V", "VSNS", "TRIG_PAD", "TRIG",
    "CUR", "CUR_ADC", "NTC", "UPDI", "LED_A", "LED_CTL", "SNUB",
]

# --------------------------------------------------------------- parts
# ref: (symlib, symname, footprint "Lib:Name", value, MPN, LCSC,
#       {pin: net}, [nc pins], dnp)
D = dict
PARTS = {
    # power stage
    "Q1": D(sym=("Transistor_FET", "IPT015N10N5"),
            fp="Package_TO_SOT_SMD:Infineon_PG-HSOF-8-1",
            value="IPT015N10N5", mpn="IPT015N10N5ATMA1", lcsc="C108964",
            nets={"1": "G_Q1", "2": "ISNS", "3": "SW"}),
    "Q2": D(sym=("Transistor_FET", "IPT015N10N5"),
            fp="Package_TO_SOT_SMD:Infineon_PG-HSOF-8-1",
            value="IPT015N10N5", mpn="IPT015N10N5ATMA1", lcsc="C108964",
            nets={"1": "G_Q2", "2": "ISNS", "3": "SW"}),
    "D2": D(sym=("Device", "D_Schottky_Dual_CommonCathode_AKA"),
            fp="Package_TO_SOT_SMD:TO-263-3_TabPin2",
            value="STPS41H100CG", mpn="STPS41H100CG-TR", lcsc="",
            nets={"1": "SW", "2": "VBAT", "3": "SW"}),
    "D1": D(sym=("Device", "D_Zener"), fp="Diode_SMD:D_SMC",
            value="SMDJ33A", mpn="SMDJ33A", lcsc="",
            nets={"1": "VBAT", "2": "GND"}),
    "RS1": D(sym=("Device", "R"),
             fp="Resistor_SMD:R_Shunt_Vishay_WSR2_WSR3_KelvinConnection",
             value="2m0 3W", mpn="WSR32L000FEA", lcsc="",
             nets={"1": "ISNS", "2": "GND"}),
    "C1": D(sym=("Device", "C_Polarized"),
            fp="Capacitor_THT:CP_Radial_D12.5mm_P5.00mm",
            value="470u 63V", mpn="UPW1J471MHD", lcsc="",
            nets={"1": "VBAT", "2": "GND"}),
    "C2": D(sym=("Device", "C_Polarized"),
            fp="Capacitor_THT:CP_Radial_D12.5mm_P5.00mm",
            value="470u 63V", mpn="UPW1J471MHD", lcsc="",
            nets={"1": "VBAT", "2": "GND"}),
    "C3": D(sym=("Device", "C"), fp="Capacitor_SMD:C_1210_3225Metric",
            value="4u7 100V X7S", mpn="C3225X7S2A475K200AE", lcsc="",
            nets={"1": "VBAT", "2": "GND"}),
    "C4": D(sym=("Device", "C"), fp="Capacitor_SMD:C_1210_3225Metric",
            value="4u7 100V X7S", mpn="C3225X7S2A475K200AE", lcsc="",
            nets={"1": "VBAT", "2": "GND"}),
    "C5": D(sym=("Device", "C"), fp="Capacitor_SMD:C_1210_3225Metric",
            value="4u7 100V X7S", mpn="C3225X7S2A475K200AE", lcsc="",
            nets={"1": "VBAT", "2": "GND"}),
    "C6": D(sym=("Device", "C"), fp="Capacitor_SMD:C_0603_1608Metric",
            value="100n 100V", mpn="", lcsc="",
            nets={"1": "VBAT", "2": "GND"}),
    # snubber provision (DNP until transient waveform measured)
    "R16": D(sym=("Device", "R"), fp="Resistor_SMD:R_2512_6332Metric",
             value="DNP-snubber", mpn="", lcsc="",
             nets={"1": "SW", "2": "SNUB"}, dnp=True),
    "C20": D(sym=("Device", "C"), fp="Capacitor_SMD:C_1210_3225Metric",
             value="DNP-snubber", mpn="", lcsc="",
             nets={"1": "SNUB", "2": "GND"}, dnp=True),
    # gate drive (return referenced to ISNS source bus)
    "U2": D(sym=("Driver_FET", "TC4422"),
            fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
            value="TC4422AVOA", mpn="TC4422AVOA", lcsc="C37183",
            nets={"1": "VDRV", "2": "PWM", "4": "ISNS", "5": "ISNS",
                  "6": "GATE", "7": "GATE", "8": "VDRV"}, nc=["3"]),
    "R3": D(sym=("Device", "R"), fp="Resistor_SMD:R_0805_2012Metric",
            value="4R7", mpn="", lcsc="", nets={"1": "GATE", "2": "G_Q1"}),
    "R4": D(sym=("Device", "R"), fp="Resistor_SMD:R_0805_2012Metric",
            value="4R7", mpn="", lcsc="", nets={"1": "GATE", "2": "G_Q2"}),
    "R12": D(sym=("Device", "R"), fp="Resistor_SMD:R_0603_1608Metric",
             value="100k", mpn="", lcsc="", nets={"1": "G_Q1", "2": "ISNS"}),
    "R13": D(sym=("Device", "R"), fp="Resistor_SMD:R_0603_1608Metric",
             value="100k", mpn="", lcsc="", nets={"1": "G_Q2", "2": "ISNS"}),
    "R6": D(sym=("Device", "R"), fp="Resistor_SMD:R_0603_1608Metric",
            value="100k", mpn="", lcsc="", nets={"1": "PWM", "2": "GND"}),
    "C7": D(sym=("Device", "C"), fp="Capacitor_SMD:C_1206_3216Metric",
            value="4u7 25V X7R", mpn="", lcsc="",
            nets={"1": "VDRV", "2": "ISNS"}),
    "C8": D(sym=("Device", "C"), fp="Capacitor_SMD:C_0603_1608Metric",
            value="100n 25V", mpn="", lcsc="",
            nets={"1": "VDRV", "2": "ISNS"}),
    # regulators
    "D4": D(sym=("Device", "D"), fp="Diode_SMD:D_SMA",
            value="S1M", mpn="S1M (onsemi)", lcsc="C232826",
            nets={"1": "VREG_IN", "2": "VBAT"}),
    "U3": D(sym=("blower_project", "TPS7A4001"),
            fp="Package_SO:MSOP-8-1EP_3x3mm_P0.65mm_EP1.68x1.88mm",
            value="TPS7A4001", mpn="TPS7A4001DGNR", lcsc="C55006",
            nets={"1": "VDRV", "2": "VFB", "4": "GND", "5": "VREG_IN",
                  "8": "VREG_IN", "9": "GND"}, nc=["3", "6", "7"]),
    "R14": D(sym=("Device", "R"), fp="Resistor_SMD:R_0603_1608Metric",
             value="97k6 1%", mpn="", lcsc="", nets={"1": "VDRV", "2": "VFB"}),
    "R15": D(sym=("Device", "R"), fp="Resistor_SMD:R_0603_1608Metric",
             value="13k0 1%", mpn="", lcsc="", nets={"1": "VFB", "2": "GND"}),
    "C9": D(sym=("Device", "C"), fp="Capacitor_SMD:C_1210_3225Metric",
            value="1u 100V X7S", mpn="", lcsc="",
            nets={"1": "VREG_IN", "2": "GND"}),
    "C10": D(sym=("Device", "C"), fp="Capacitor_SMD:C_1206_3216Metric",
             value="4u7 25V X7R", mpn="", lcsc="",
             nets={"1": "VDRV", "2": "GND"}),
    "U4": D(sym=("Regulator_Linear", "MCP1703Ax-500xxDB"),
            fp="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
            value="MCP1703A-5002E/DB", mpn="MCP1703A-5002E/DB", lcsc="",
            nets={"1": "VDRV", "2": "GND", "3": "+5V"}),
    "C11": D(sym=("Device", "C"), fp="Capacitor_SMD:C_0603_1608Metric",
             value="1u 25V", mpn="", lcsc="", nets={"1": "VDRV", "2": "GND"}),
    "C12": D(sym=("Device", "C"), fp="Capacitor_SMD:C_0603_1608Metric",
             value="1u 25V", mpn="", lcsc="", nets={"1": "+5V", "2": "GND"}),
    # MCU
    "U1": D(sym=("MCU_Microchip_ATtiny", "ATtiny1616-S"),
            fp="Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm",
            value="ATtiny1616", mpn="ATTINY1616-SNR", lcsc="C614136",
            nets={"1": "+5V", "2": "VSNS", "3": "CUR_ADC", "4": "NTC",
                  "5": "TRIG", "10": "LED_CTL", "11": "PWM", "16": "UPDI",
                  "20": "GND"},
            nc=["6", "7", "8", "9", "12", "13", "14", "15", "17", "18", "19"]),
    "C13": D(sym=("Device", "C"), fp="Capacitor_SMD:C_0603_1608Metric",
             value="100n 25V", mpn="", lcsc="", nets={"1": "+5V", "2": "GND"}),
    "C14": D(sym=("Device", "C"), fp="Capacitor_SMD:C_0603_1608Metric",
             value="1u 25V", mpn="", lcsc="", nets={"1": "+5V", "2": "GND"}),
    # current sense
    "U5": D(sym=("Amplifier_Current", "INA180A2"),
            fp="Package_TO_SOT_SMD:SOT-23-5",
            value="INA180A2", mpn="INA180A2IDBVR", lcsc="C192764",
            nets={"1": "CUR", "2": "GND", "3": "ISNS", "4": "GND",
                  "5": "+5V"}),
    "C19": D(sym=("Device", "C"), fp="Capacitor_SMD:C_0603_1608Metric",
             value="100n 25V", mpn="", lcsc="", nets={"1": "+5V", "2": "GND"}),
    "R10": D(sym=("Device", "R"), fp="Resistor_SMD:R_0603_1608Metric",
             value="100R", mpn="", lcsc="", nets={"1": "CUR", "2": "CUR_ADC"}),
    "C18": D(sym=("Device", "C"), fp="Capacitor_SMD:C_0603_1608Metric",
             value="1n 50V C0G", mpn="", lcsc="",
             nets={"1": "CUR_ADC", "2": "GND"}),
    # bus voltage divider (5V at ADC = 32.8V bus)
    "R1": D(sym=("Device", "R"), fp="Resistor_SMD:R_0603_1608Metric",
            value="100k 1%", mpn="", lcsc="", nets={"1": "VBAT", "2": "VSNS"}),
    "R2": D(sym=("Device", "R"), fp="Resistor_SMD:R_0603_1608Metric",
            value="18k 1%", mpn="", lcsc="", nets={"1": "VSNS", "2": "GND"}),
    "C16": D(sym=("Device", "C"), fp="Capacitor_SMD:C_0603_1608Metric",
             value="100n 25V", mpn="", lcsc="", nets={"1": "VSNS", "2": "GND"}),
    # NTC near MOSFETs
    "TH1": D(sym=("Device", "Thermistor_NTC"),
             fp="Resistor_SMD:R_0603_1608Metric",
             value="NTC 10k B3380", mpn="NCP18XH103F03RB", lcsc="C13564",
             nets={"1": "NTC", "2": "GND"}),
    "R9": D(sym=("Device", "R"), fp="Resistor_SMD:R_0603_1608Metric",
            value="10k 1%", mpn="", lcsc="", nets={"1": "+5V", "2": "NTC"}),
    "C17": D(sym=("Device", "C"), fp="Capacitor_SMD:C_0603_1608Metric",
             value="100n 25V", mpn="", lcsc="", nets={"1": "NTC", "2": "GND"}),
    # trigger input
    "R8": D(sym=("Device", "R"), fp="Resistor_SMD:R_0603_1608Metric",
            value="10k", mpn="", lcsc="", nets={"1": "TRIG_PAD", "2": "TRIG"}),
    "R7": D(sym=("Device", "R"), fp="Resistor_SMD:R_0603_1608Metric",
            value="10k", mpn="", lcsc="", nets={"1": "TRIG", "2": "+5V"}),
    "C15": D(sym=("Device", "C"), fp="Capacitor_SMD:C_0603_1608Metric",
             value="100n 25V", mpn="", lcsc="", nets={"1": "TRIG", "2": "GND"}),
    "D3": D(sym=("Device", "D_TVS"), fp="Diode_SMD:D_SOD-323",
            value="PESD5V0S1BA", mpn="PESD5V0S1BA,115", lcsc="C19224",
            nets={"1": "TRIG_PAD", "2": "GND"}),
    # status LED
    "R11": D(sym=("Device", "R"), fp="Resistor_SMD:R_0603_1608Metric",
             value="1k", mpn="", lcsc="", nets={"1": "LED_CTL", "2": "LED_A"}),
    "LED1": D(sym=("Device", "LED"), fp="LED_SMD:LED_0603_1608Metric",
              value="GREEN", mpn="19-217/GHC-YR1S2/3T", lcsc="C72043",
              nets={"1": "GND", "2": "LED_A"}),
    # connectors / wire pads (external fuse required in B+ lead)
    "J1": D(sym=("Connector_Generic", "Conn_01x01"),
            fp="Connector_Wire:SolderWire-4sqmm_1x01_D3mm_OD6mm",
            value="B+ (via ext fuse)", mpn="", lcsc="", nets={"1": "VBAT"},
            in_bom=False),
    "J2": D(sym=("Connector_Generic", "Conn_01x01"),
            fp="Connector_Wire:SolderWire-4sqmm_1x01_D3mm_OD6mm",
            value="B-", mpn="", lcsc="", nets={"1": "GND"}, in_bom=False),
    "J3": D(sym=("Connector_Generic", "Conn_01x01"),
            fp="Connector_Wire:SolderWire-4sqmm_1x01_D3mm_OD6mm",
            value="M+", mpn="", lcsc="", nets={"1": "VBAT"}, in_bom=False),
    "J4": D(sym=("Connector_Generic", "Conn_01x01"),
            fp="Connector_Wire:SolderWire-4sqmm_1x01_D3mm_OD6mm",
            value="M-", mpn="", lcsc="", nets={"1": "SW"}, in_bom=False),
    "J5": D(sym=("Connector_Generic", "Conn_01x01"),
            fp="Connector_Wire:SolderWire-0.5sqmm_1x01_D0.9mm_OD2.1mm",
            value="TRIGGER", mpn="", lcsc="", nets={"1": "TRIG_PAD"},
            in_bom=False),
    "J7": D(sym=("Connector_Generic", "Conn_01x01"),
            fp="Connector_Wire:SolderWire-0.5sqmm_1x01_D0.9mm_OD2.1mm",
            value="TRIG_RET", mpn="", lcsc="", nets={"1": "GND"},
            in_bom=False),
    "J6": D(sym=("Connector_Generic", "Conn_01x03"),
            fp="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
            value="UPDI", mpn="", lcsc="",
            nets={"1": "+5V", "2": "UPDI", "3": "GND"}),
    # test points
    "TP1": D(sym=("Connector", "TestPoint"), fp="TestPoint:TestPoint_Pad_D1.5mm",
             value="+5V", mpn="", lcsc="", nets={"1": "+5V"}),
    "TP2": D(sym=("Connector", "TestPoint"), fp="TestPoint:TestPoint_Pad_D1.5mm",
             value="VDRV", mpn="", lcsc="", nets={"1": "VDRV"}),
    "TP3": D(sym=("Connector", "TestPoint"), fp="TestPoint:TestPoint_Pad_D1.5mm",
             value="PWM", mpn="", lcsc="", nets={"1": "PWM"}),
    "TP4": D(sym=("Connector", "TestPoint"), fp="TestPoint:TestPoint_Pad_D1.5mm",
             value="GATE", mpn="", lcsc="", nets={"1": "GATE"}),
    "TP5": D(sym=("Connector", "TestPoint"), fp="TestPoint:TestPoint_Pad_D1.5mm",
             value="CUR", mpn="", lcsc="", nets={"1": "CUR"}),
    "TP6": D(sym=("Connector", "TestPoint"), fp="TestPoint:TestPoint_Pad_D1.5mm",
             value="VSNS", mpn="", lcsc="", nets={"1": "VSNS"}),
    "TP7": D(sym=("Connector", "TestPoint"), fp="TestPoint:TestPoint_Pad_D1.5mm",
             value="GND", mpn="", lcsc="", nets={"1": "GND"}),
    "TP8": D(sym=("Connector", "TestPoint"), fp="TestPoint:TestPoint_Pad_D1.5mm",
             value="SW", mpn="", lcsc="", nets={"1": "SW"}),
    # mechanics: 4x M2.5 mount, 2x M3 zip-tie strain relief
    "H1": D(sym=("Mechanical", "MountingHole"),
            fp="MountingHole:MountingHole_2.7mm_M2.5", value="M2.5",
            mpn="", lcsc="", nets={}),
    "H2": D(sym=("Mechanical", "MountingHole"),
            fp="MountingHole:MountingHole_2.7mm_M2.5", value="M2.5",
            mpn="", lcsc="", nets={}),
    "H3": D(sym=("Mechanical", "MountingHole"),
            fp="MountingHole:MountingHole_2.7mm_M2.5", value="M2.5",
            mpn="", lcsc="", nets={}),
    "H4": D(sym=("Mechanical", "MountingHole"),
            fp="MountingHole:MountingHole_2.7mm_M2.5", value="M2.5",
            mpn="", lcsc="", nets={}),
    "H5": D(sym=("Mechanical", "MountingHole"),
            fp="MountingHole:MountingHole_3.2mm_M3", value="ziptie",
            mpn="", lcsc="", nets={}),
    "H6": D(sym=("Mechanical", "MountingHole"),
            fp="MountingHole:MountingHole_3.2mm_M3", value="ziptie",
            mpn="", lcsc="", nets={}),
}

# PWR_FLAG placements: nets whose only sources are passive/connector pins.
POWER_FLAGS = ["GND", "VBAT", "ISNS", "VREG_IN"]

# ------------------------------------------------- schematic placement
# ref -> (x, y, rot).  A3 sheet is 420x297.  Grouped by function.
SCH_POS = {
    # battery entry / protection (top left)
    "J1": (40, 45, 180), "J2": (40, 105, 180),
    "D1": (60, 75, 90), "C1": (75, 75, 0), "C2": (90, 75, 0),
    "C3": (105, 75, 0), "C4": (120, 75, 0), "C5": (135, 75, 0),
    "C6": (150, 75, 0),
    # power stage (top middle)
    "J3": (185, 45, 180), "J4": (185, 95, 180),
    "D2": (210, 60, 0),
    "Q1": (235, 110, 0), "Q2": (270, 110, 0),
    "R12": (247, 125, 0), "R13": (282, 125, 0),
    "RS1": (255, 150, 0),
    "R16": (305, 110, 0), "C20": (305, 130, 0),
    "TP8": (200, 88, 0),
    # gate drive (middle left of stage)
    "U2": (165, 145, 0),
    "R3": (200, 132, 90), "R4": (200, 152, 90),
    "R6": (140, 160, 0), "C7": (150, 170, 0), "C8": (163, 170, 0),
    "TP4": (190, 125, 0), "TP3": (137, 140, 0),
    # regulators (bottom left)
    "D4": (45, 190, 180), "U3": (75, 195, 0),
    "C9": (55, 205, 0), "R14": (100, 195, 0), "R15": (100, 215, 0),
    "C10": (115, 205, 0), "TP2": (120, 188, 0),
    "U4": (150, 195, 0), "C11": (130, 205, 0), "C12": (175, 205, 0),
    "TP1": (180, 188, 0),
    # MCU (bottom middle)
    "U1": (240, 220, 0), "C13": (215, 250, 0), "C14": (225, 250, 0),
    # current sense (right of stage)
    "U5": (330, 150, 0), "C19": (350, 140, 0),
    "R10": (350, 155, 90), "C18": (365, 165, 0), "TP5": (345, 145, 0),
    # dividers / NTC / trigger (right)
    "R1": (320, 55, 0), "R2": (320, 75, 0), "C16": (335, 75, 0),
    "TP6": (330, 63, 0),
    "R9": (355, 55, 0), "TH1": (355, 75, 0), "C17": (370, 75, 0),
    "J5": (310, 195, 180), "R8": (325, 200, 90), "R7": (335, 185, 0),
    "C15": (340, 205, 0), "D3": (318, 210, 90), "J7": (310, 220, 180),
    # LED / UPDI / mech (bottom right)
    "R11": (300, 240, 90), "LED1": (312, 240, 0),
    "J6": (355, 235, 0), "TP7": (370, 220, 0),
    "H1": (35, 250, 0), "H2": (45, 250, 0), "H3": (55, 250, 0),
    "H4": (65, 250, 0), "H5": (75, 250, 0), "H6": (85, 250, 0),
}
FLAG_POS = {"GND": (30, 130), "VBAT": (30, 120), "ISNS": (255, 165),
            "VREG_IN": (55, 180)}

SCH_NOTES = [
    ("5S BLOWER CONTROLLER - REV C REFERENCE - NOT APPROVED TO ORDER", 145, 20, 3.0),
    ("External fuse REQUIRED in B+ battery lead; select after measured current and I2t review.", 100, 27, 1.5),
    ("Gate driver GND returns to ISNS source bus (Kelvin, below shunt current path).", 165, 178, 1.5),
    ("R16/C20 snubber DNP until switch-node transient is measured.", 305, 95, 1.5),
    ("Trigger input: closing external switch to GND pulls TRIG low (active-low).", 330, 172, 1.5),
    ("VDRV = 1.173V x (1 + R14/R15) = 10.0V nominal.", 75, 225, 1.5),
]

# Project symbol library: TPS7A4001 (pinout from TI SBVS162B, verified).
TPS7A4001_SYM = """(kicad_symbol_lib (version 20231120) (generator blower_generate_design)
  (symbol "TPS7A4001" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)
    (property "Reference" "U" (at -7.62 11.43 0) (effects (font (size 1.27 1.27))))
    (property "Value" "TPS7A4001" (at 0 11.43 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at 0 -13.97 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Datasheet" "https://www.ti.com/lit/ds/symlink/tps7a4001.pdf" (at 0 -16.51 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (symbol "TPS7A4001_0_1"
      (rectangle (start -10.16 10.16) (end 10.16 -10.16)
        (stroke (width 0.254) (type default)) (fill (type background))))
    (symbol "TPS7A4001_1_1"
      (pin power_out line (at 15.24 7.62 180) (length 5.08)
        (name "OUT" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      (pin input line (at 15.24 0 180) (length 5.08)
        (name "FB" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      (pin no_connect line (at 15.24 -5.08 180) (length 5.08)
        (name "NC" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
      (pin power_in line (at 0 -15.24 90) (length 5.08)
        (name "GND" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      (pin input line (at -15.24 0 0) (length 5.08)
        (name "EN" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
      (pin no_connect line (at 15.24 -7.62 180) (length 5.08)
        (name "NC" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
      (pin no_connect line (at 15.24 -2.54 180) (length 5.08)
        (name "NC" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))
      (pin power_in line (at -15.24 7.62 0) (length 5.08)
        (name "IN" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 0 -15.24 90) (length 5.08) hide
        (name "EP" (effects (font (size 1.27 1.27)))) (number "9" (effects (font (size 1.27 1.27))))))))
"""


def snap(v, grid=1.27):
    return round(round(v / grid) * grid, 4)


def build_schematic():
    PROJ_SYM.parent.mkdir(parents=True, exist_ok=True)
    PROJ_SYM.write_text(TPS7A4001_SYM, encoding="utf-8")
    (ROOT / "hardware" / "sym-lib-table").write_text(
        '(sym_lib_table\n  (version 7)\n'
        '  (lib (name "blower_project")(type "KiCad")'
        '(uri "${KIPRJMOD}/symbols/blower_project.kicad_sym")'
        '(options "")(descr "project symbols"))\n)\n', encoding="utf-8")
    store = sw.SymbolStore(SYMDIR, project_libs={"blower_project": PROJ_SYM})
    sch = sw.Schematic(store, title="5S Blower Controller (reference)",
                       rev="C", company="open hardware - CERN-OHL-S-2.0",
                       date="2026-08-02")
    missing = [r for r in PARTS if r not in SCH_POS and not r.startswith("#")]
    assert not missing, f"no schematic position for {missing}"
    for ref in sorted(PARTS):
        p = PARTS[ref]
        x, y, rot = SCH_POS[ref]
        x, y = snap(x), snap(y)
        sch.place(ref, p["sym"][0], p["sym"][1], p["value"], x, y, rot,
                  pin_nets=p.get("nets", {}), nc_pins=p.get("nc", []),
                  footprint=p["fp"], mpn=p.get("mpn", ""),
                  lcsc=p.get("lcsc", ""), dnp=p.get("dnp", False),
                  in_bom=p.get("in_bom"))
    for i, net in enumerate(POWER_FLAGS, 1):
        x, y = FLAG_POS[net]
        sch.power_flag(i, net, snap(x), snap(y))
    for text, x, y, size in SCH_NOTES:
        sch.text(text, x, y, size)
    sch.write(OUT_SCH)
    print(f"wrote {OUT_SCH}")
    return sch


def expected_connectivity():
    """net -> set of (ref, pin) from the table, including stacked twins."""
    exp = {}
    for ref, p in PARTS.items():
        for pin, net in p.get("nets", {}).items():
            exp.setdefault(net, set()).add((ref, pin))
    # note: #FLG power symbols never appear in exported netlists
    return exp


def verify_netlist():
    net_file = ROOT / "hardware" / "outputs" / "netlist-check.net"
    net_file.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format",
                    "kicadsexpr", "-o", str(net_file), str(OUT_SCH)],
                   check=True)
    root = kicadlib.parse_file(net_file)
    nets_node = root.find("nets")
    actual = {}
    nc_pins = []
    nc_net_by_pin = {}
    for net in nets_node.find_all("net"):
        name = net.find("name").atom(1)
        members = {(n.find("ref").atom(1), n.find("pin").atom(1))
                   for n in net.find_all("node")}
        if name.startswith("unconnected-"):
            nc_pins.extend(members)
            for member in members:
                nc_net_by_pin[member] = name
            continue
        actual[name] = members
    exp = expected_connectivity()
    errors = []
    for net, mem in sorted(exp.items()):
        got = actual.get(net, set())
        if not mem <= got:
            errors.append(f"net {net}: missing {sorted(mem - got)} (got {sorted(got)})")
    for net, mem in sorted(actual.items()):
        extra = mem - exp.get(net, set())
        # stacked hidden pins (TC4422 5/7/8, hidden EP twins) are acceptable extras
        allowed = {("U2", "5"), ("U2", "7"), ("U2", "8")}
        extra -= allowed
        if extra and net not in exp:
            errors.append(f"unexpected net {net}: {sorted(mem)}")
        elif extra:
            errors.append(f"net {net}: unexpected members {sorted(extra)}")
    declared_nc = {(r, pin) for r, p in PARTS.items() for pin in p.get("nc", [])}
    bad_nc = {p for p in nc_pins if p not in declared_nc and p[1] != "3"}
    if bad_nc:
        errors.append(f"undeclared unconnected pins: {sorted(bad_nc)}")
    if errors:
        for e in errors:
            print("NETLIST ERROR:", e)
        raise SystemExit(1)
    print(f"netlist verified: {len(exp)} nets, {len(nc_pins)} declared no-connects")
    return actual, nc_net_by_pin


# ==================================================================== PCB
BOARD_W, BOARD_H = 77.0, 62.0

# ref -> (x, y, rot)
PCB_POS = {
    # power stage
    "Q1": (24, 21, 90), "Q2": (49, 21, 90), "D2": (36.5, 10.5, 90),
    "RS1": (36.5, 35.5, 0), "D1": (61.5, 17, 0),
    "C1": (60.3, 29.5, 0), "C2": (60.3, 44, 0),
    "C3": (53.5, 30, 0), "C4": (53.5, 34, 0), "C5": (53.5, 38, 0),
    "C6": (53.5, 40.5, 0),
    "R16": (46, 33, 90), "C20": (47.5, 39, 0),  # DNP snubber SW->SNUB->GND
    # wire pads
    "J4": (17, 4.5, 0), "J3": (25, 4.5, 0), "J1": (50.5, 4.5, 0),
    "J2": (48, 48, 0), "J5": (2.6, 15.5, 0), "J7": (2.6, 11, 0),
    # gate drive
    "U2": (24.5, 34, 0),
    "R3": (18.8, 29, 180), "R4": (42, 26.3, 0),
    "R12": (18.5, 30.9, 0), "R13": (42, 29.2, 180),
    "C7": (24, 39.5, 0), "C8": (28, 38, 0), "R6": (8.5, 53, 0),
    # regulators
    "D4": (13.5, 15.5, 0), "C9": (8.5, 19.8, 90), "U3": (13.5, 20.5, 0),
    "R14": (17.4, 21, 90), "R15": (12.3, 24, 90), "C10": (14.5, 25.5, 90),
    "U4": (7, 26.5, 0), "C11": (13.5, 28.8, 0), "C12": (5.5, 31.8, 90),
    # MCU
    "U1": (13.2, 40, 0), "C13": (15, 31.5, 0), "C14": (11.5, 31.5, 0),
    # current sense
    "U5": (36.5, 42, 0), "C19": (40.5, 42, 0), "R10": (32, 42, 0),
    "C18": (28.5, 42, 0),
    # dividers / NTC / trigger
    "R1": (14, 10.5, 0), "R2": (3.5, 32, 90), "C16": (8, 31.5, 0),
    "TH1": (18.5, 12.5, 0), "R9": (5, 42, 0), "C17": (5, 44, 0),
    "D3": (6, 15.5, 90), "R8": (8.5, 15.5, 90), "R7": (3.8, 35, 90),
    "C15": (3.8, 38.5, 90),
    # LED / UPDI
    "R11": (13, 48.5, 0), "LED1": (17, 48.5, 0), "J6": (25, 48, 90),
    # test points
    "TP1": (29, 51.5, 0), "TP2": (5.5, 20, 0), "TP3": (21.2, 44, 0),
    "TP4": (30.6, 29.5, 0), "TP5": (44, 42, 0), "TP6": (9, 10, 0),
    "TP7": (54, 48, 0), "TP8": (20, 10.5, 0),
    # mechanics
    "H1": (4, 4, 0), "H2": (4, 48, 0), "H3": (35, 48, 0),
    "H4": (72.5, 25, 0), "H5": (62, 4.5, 0), "H6": (70, 4.5, 0),
}

# Power-stage-only copper.  Low-current control/ADC/trigger/UPDI nets are
# intentionally absent from these tables until a later routed milestone.
# zones: (net, layer, priority, clearance, min_width, connection, polygon)
POWER_STAGE_ZONES = []
for _layer in ("F", "B"):
    POWER_STAGE_ZONES.extend([
        ("VBAT", _layer, 3, 0.4, 0.25, "full",
         [(21.5, 1.2), (58.0, 1.2), (58.0, 14.0), (21.5, 14.0)]),
        ("VBAT", _layer, 3, 0.4, 0.25, "full",
         [(56.0, 15.0), (63.0, 15.0), (63.0, 50.0), (56.0, 50.0),
          (56.0, 42.0), (50.5, 42.0), (50.5, 28.5), (53.5, 28.5),
          (53.5, 23.0), (56.0, 23.0)]),
        ("SW", _layer, 3, 0.4, 0.25, "full",
         [(13.5, 1.2), (20.5, 1.2), (20.5, 14.8), (52.0, 14.8),
          (52.0, 22.8), (15.5, 22.8), (15.5, 8.0), (13.5, 8.0)]),
        ("ISNS", _layer, 3, 0.4, 0.25, "full",
         [(20.4, 24.4), (53.8, 24.4), (53.8, 28.0), (43.8, 28.0),
          (43.8, 30.5), (34.0, 30.5), (34.0, 39.0), (29.5, 39.0),
          (29.5, 30.5), (20.4, 30.5)]),
        ("GND", _layer, 0, 0.3, 0.25, "full",
         [(1.2, 1.2), (75.8, 1.2), (75.8, 60.8), (1.2, 60.8)]),
    ])

# explicit tracks: (net, layer, width, [point,...]); point = "REF.PAD" or (x,y)
POWER_STAGE_TRACKS = [
    # D2 common-cathode lead to its tab and top VBAT plane; input TVS/caps
    # connect by the adjacent full-connect VBAT/GND planes.
    ("VBAT", "F", 1.2, ["D2.LEAD2", "D2.TAB2"]),
    ("VBAT", "F", 3.0, [(57.0, 13.0), "D1.1"]),
    ("GND", "F", 1.0, ["C6.2", "C5.2"]),
    ("SW", "B", 2.0,
     ["J4.1", (17.0, 9.0), (17.0, 20.5), (31.0, 21.5),
      (36.5, 22.0), (41.5, 21.5)]),

    # True shunt Kelvin pair.  These touch only the WSR3 sense fingers and
    # the INA180 inputs; load copper uses the large RS1 pads/zones instead.
    ("ISNS", "F", 0.3,
     ["RS1.SENSE1", (30.2, 40.0), (34.0, 40.0), (34.0, 42.95), "U5.3"]),
    ("GND", "F", 0.3,
     ["RS1.SENSE2", (42.79, 43.8), (39.0, 43.8), "U5.4"]),

    # Driver supply decoupling: both VDD pins share the local VDRV node;
    # C8 is the closest HF capacitor and C7 is the local bulk capacitor.
    # The U2.8-to-C8 leg is routed on B.Cu (via drop just south of U2's
    # body, via rise just north of C8) because the direct F.Cu path at
    # x=27.8 runs through the GATE pad column and the ISNS pads/zone.
    ("VDRV", "F", 0.6, ["U2.1", "U2.8"]),
    ("VDRV", "B", 0.5, [(27.8, 32.095), (27.8, 36.9)]),
    ("VDRV", "F", 0.5, [(27.8, 36.9), (27.8, 37.7), "C8.1"]),
    ("VDRV", "F", 0.6,
     ["C8.1", (27.2, 37.7), (22.5, 37.3), "C7.1"]),
    # U3.1 to R14.1 stays entirely on F.Cu, routed around the north/east/
    # south perimeter of U3 (x=18.4 corridor, clear of Q1's large SW pad to
    # the east and of R14.2/VFB to the west) so it never touches B.Cu in
    # this pocket -- VREG_IN's B.Cu run (U3.8/D4/C9) passes underneath it.
    ("VDRV", "F", 0.5,
     ["U3.1", (11.35, 17.6), (18.4, 17.6), (18.4, 23.0), (17.4, 23.0),
      "R14.1"]),
    ("VDRV", "F", 0.5, ["C10.1", "C11.1", (12.7, 30.3), (13.0, 30.3)]),
    ("VDRV", "B", 0.5, [(17.4, 23.0), (13.0, 30.3)]),
    ("VDRV", "B", 0.5, [(13.0, 30.3), (17.5, 28.0)]),
    # Detour below y=31 (south of the ISNS zone/via/diagonal Kelvin return
    # at x=20-27) before turning east to the U2.8 via, instead of cutting
    # diagonally through that quiet-ground/Kelvin territory.
    ("VDRV", "B", 0.5,
     [(17.5, 28.0), (17.5, 31.6), (27.8, 31.6), (27.8, 32.095)]),

    # TC4422 Kelvin return to ISNS and both local bypass returns.
    ("ISNS", "F", 0.6, ["U2.4", "U2.5"]),
    ("ISNS", "F", 0.6,
     ["U2.5", (29.0, 35.905), "C8.2", (28.8, 36.0), "RS1.1"]),
    ("ISNS", "F", 0.6,
     ["C7.2", (25.5, 41.0), (28.8, 41.0), "C8.2"]),

    # Common driver output splits to individual gate resistors.
    ("GATE", "F", 0.8, ["U2.7", (29.0, 33.365), (29.0, 31.0)]),
    ("GATE", "F", 0.8, ["U2.6", (29.0, 34.635), (29.0, 31.0)]),
    ("GATE", "F", 0.8,
     [(29.0, 31.0), (22.0, 29.0), "R3.1"]),
    ("GATE", "F", 0.8,
     [(29.0, 31.0), (30.5, 29.0), (39.0, 29.0), (39.0, 26.3), "R4.1"]),

    # Individual gate resistors and gate-source pull-downs.
    ("G_Q1", "F", 0.8,
     ["R3.2", (16.5, 29.0), (16.5, 26.25), "Q1.1"]),
    ("G_Q1", "F", 0.4,
     ["R12.1", (17.675, 30.2), (16.5, 30.2), (16.5, 29.0)]),
    ("G_Q2", "F", 0.8, ["R4.2", "Q2.1"]),
    ("G_Q2", "F", 0.4, ["R13.1", (44.0, 29.2), "Q2.1"]),
    ("ISNS", "F", 0.4, ["R12.2", (21.0, 30.5)]),
    ("ISNS", "F", 0.4, ["R13.2", (41.0, 30.5)]),
    ("ISNS", "F", 2.0, [(33.5, 32.0), "RS1.1"]),
    ("ISNS", "B", 3.0, [(27.0, 26.5), (33.5, 32.0)]),
    ("ISNS", "B", 3.0,
     [(52.0, 26.5), (46.0, 29.0), (41.0, 30.5), (33.5, 32.0)]),
    ("ISNS", "B", 0.4, [(21.0, 30.5), (27.0, 26.5)]),
]

# Explicit, deterministic inter-layer stitching; all drills remain >= 0.5 mm.
POWER_STAGE_VIAS = [
    ("VBAT", 29.0, 9.0, 0.5, 1.0), ("VBAT", 44.5, 9.0, 0.5, 1.0),
    ("VBAT", 59.5, 18.0, 0.5, 1.0), ("VBAT", 59.5, 25.0, 0.5, 1.0),
    ("VBAT", 59.5, 35.0, 0.5, 1.0), ("VBAT", 59.5, 48.0, 0.5, 1.0),
    ("VBAT", 51.5, 32.0, 0.5, 1.0), ("VBAT", 51.5, 36.0, 0.5, 1.0),
    ("VBAT", 51.5, 40.0, 0.5, 1.0),
    ("SW", 17.0, 9.0, 0.5, 1.0), ("SW", 31.0, 21.5, 0.5, 1.0),
    ("SW", 36.5, 22.0, 0.5, 1.0), ("SW", 41.5, 21.5, 0.5, 1.0),
    ("ISNS", 27.0, 26.5, 0.5, 1.0), ("ISNS", 52.0, 26.5, 0.5, 1.0),
    ("ISNS", 33.5, 32.0, 0.5, 1.0), ("ISNS", 41.0, 30.5, 0.5, 1.0),
    ("VDRV", 17.4, 23.0, 0.4, 0.8),
    ("VDRV", 13.0, 30.3, 0.4, 0.8),
    ("VDRV", 27.8, 32.095, 0.4, 0.8), ("VDRV", 27.8, 36.9, 0.4, 0.8),
    ("ISNS", 21.0, 30.5, 0.4, 0.8),
    ("GND", 43.5, 40.5, 0.5, 1.0), ("GND", 45.0, 44.5, 0.5, 1.0),
    ("GND", 52.5, 46.0, 0.5, 1.0), ("GND", 63.8, 17.0, 0.5, 1.0),
    ("GND", 66.5, 17.0, 0.5, 1.0), ("GND", 64.0, 29.5, 0.5, 1.0),
    ("GND", 66.6, 29.5, 0.5, 1.0), ("GND", 64.0, 44.0, 0.5, 1.0),
    ("GND", 66.6, 44.0, 0.5, 1.0),
]

POWER_STAGE_STITCH_GRIDS = []

# Remaining low-current/control routing.  This table is intentionally omitted
# by --power-stage-only so that the accepted power-stage milestone remains
# independently reproducible.  The default generator emits the complete board.
FULL_BOARD_TRACKS = [
    # High-voltage regulator feed and feedback divider.  The VBAT feed crosses
    # the switch region only at its quiet left boundary, then remains in the
    # regulator area.
    ("VBAT", "F", 0.5,
     ["R1.1", (13.175, 13.0), (14.5, 13.6), "D4.2"]),
    ("VBAT", "F", 0.5,
     [(14.5, 13.6), (21.8, 13.5)]),
    # VREG_IN: D4.1/U3.8/C9.1 are wired on B.Cu (dropping straight through
    # vias at each pad) so this whole branch passes underneath the F.Cu
    # VDRV perimeter route without touching it.  U3.5 (the other east-side
    # VREG_IN pin) is picked up separately by a short F.Cu lane just below
    # U3's body (y=22.2, between the EP/GND row and the R14/R15/C10 stack)
    # that lands on C9.1, tying the whole net together.
    ("VREG_IN", "F", 0.4, ["U3.8", (15.65, 18.8), (15.0, 18.8)]),
    ("VREG_IN", "B", 0.4, ["D4.1", (15.0, 18.8)]),
    ("VREG_IN", "B", 0.4, ["D4.1", "C9.1"]),
    # U3.5 escapes south (clear of the tight MSOP-8 pitch) then drops to
    # B.Cu so the whole run to C9.1 passes underneath VFB's F.Cu crossing
    # below, instead of blocking it with a long F.Cu lane.
    ("VREG_IN", "F", 0.4, ["U3.5", (15.65, 22.2)]),
    ("VREG_IN", "B", 0.4, [(15.65, 22.2), "C9.1"]),
    # VFB (U3.2) stays on F.Cu the whole way: west first (clear of U3's own
    # pin pitch), south past the VREG_IN B.Cu run (different layer, so no
    # conflict), then to R15.1.
    ("VFB", "F", 0.3,
     ["U3.2", (10.2, 20.175), (10.2, 23.2), "R15.1"]),
    ("VFB", "F", 0.3,
     ["R14.2", (18.7, 20.175), (18.7, 24.0), (13.5, 24.0), "R15.1"]),
    # Explicit GND stitches: U3's GND pin/EP and R15/C10's GND pads sit in a
    # pocket now boxed in by the VFB/VREG_IN routing above, so tie them
    # directly rather than relying on the pour alone to reach every pad.
    ("GND", "F", 0.3, ["U3.4", (11.35, 21.7), (13.5, 21.7), "U3.9"]),
    ("GND", "F", 0.3, ["R15.2", "C10.2"]),

    # Remaining VDRV branches from the already-routed regulator/driver rail.
    ("VDRV", "F", 0.4, ["TP2.1", (6.5, 20.0)]),
    ("VDRV", "F", 0.4, ["U4.1", (6.5, 23.2)]),
    ("VDRV", "B", 0.4,
     [(6.5, 20.0), (6.5, 23.2)]),
    ("VDRV", "B", 0.4,
     [(6.5, 20.0), (8.0, 17.6), (11.35, 17.6)]),

    # 5 V local fan-out.  Short front-layer stubs reach a back-layer logic
    # trunk; the INA180 branch stays below the Kelvin input pair.
    ("+5V", "F", 0.3, ["U4.3", (3.2, 28.8)]),
    ("+5V", "F", 0.3, ["C12.1", (7.2, 32.575)]),
    ("+5V", "F", 0.3, ["R7.2", (7.2, 34.175)]),
    ("+5V", "F", 0.3, ["U1.1", (7.2, 34.285)]),
    ("+5V", "F", 0.3, ["C14.1", (10.725, 33.0)]),
    ("+5V", "F", 0.3, ["C13.1", (14.225, 33.0)]),
    ("+5V", "F", 0.3, ["R9.1", (3.2, 42.0)]),
    ("+5V", "B", 0.3,
     [(3.2, 28.8), (4.5, 30.0), (7.2, 32.575), (7.2, 34.285)]),
    ("+5V", "B", 0.3,
     [(7.2, 34.285), (10.725, 33.0), (14.225, 33.0)]),
    ("+5V", "B", 0.3,
     [(7.2, 34.285), (3.2, 42.0), (6.2, 47.0), "J6.1"]),
    ("+5V", "F", 0.3,
     ["J6.1", (23.0, 48.0), (23.0, 51.5), "TP1.1"]),
    ("+5V", "B", 0.3,
     ["J6.1", (22.0, 44.5), (31.0, 44.5), (37.6, 44.8)]),
    ("+5V", "F", 0.3,
     [(37.6, 44.8), (36.2, 44.8), (36.2, 41.05), "U5.5"]),
    ("+5V", "F", 0.3,
     ["U5.5", (39.0, 40.5), "C19.1"]),

    # PWM command and pull-down/test branch, kept away from current-sense
    # inputs and from the switch copper.
    ("PWM", "F", 0.3,
     ["U2.2", (20.5, 33.365), (20.5, 42.5), "TP3.1", "U1.11"]),
    ("PWM", "F", 0.3,
     ["U1.11", (19.5, 47.0), (19.5, 51.5), (9.0, 51.5), "R6.1"]),

    # Current amplifier output and ADC RC filter.  CUR is local; CUR_ADC uses
    # the back layer to pass the MCU without entering the Kelvin pair area.
    ("CUR", "F", 0.3, ["U5.1", "R10.1"]),
    ("CUR", "F", 0.3,
     ["U5.1", (36.0, 39.8), (42.5, 39.8), "TP5.1"]),
    ("CUR_ADC", "F", 0.3, ["R10.2", "C18.1", (26.5, 42.0)]),
    ("CUR_ADC", "F", 0.3, ["U1.3", (7.0, 36.825)]),
    ("CUR_ADC", "B", 0.3,
     [(7.0, 36.825), (8.0, 40.5), (24.5, 40.5), (26.5, 42.0)]),

    # Quiet battery-voltage divider route down the left edge, outside SW.
    ("VSNS", "F", 0.3,
     ["R1.2", (14.825, 9.2), (9.0, 9.2), "TP6.1"]),
    ("VSNS", "F", 0.3, ["TP6.1", (9.0, 11.5)]),
    ("VSNS", "B", 0.3,
     [(9.0, 11.5), (10.5, 24.0), (9.5, 29.5), (7.2, 30.0)]),
    ("VSNS", "F", 0.3,
     [(7.2, 30.0), "C16.1", "R2.1", (6.5, 35.555), "U1.2"]),

    # NTC divider/filter.  The short thermistor escape crosses the left edge
    # of the SW pour, then the long analog run threads the regulator/control
    # pocket (VDRV/VFB/VREG_IN/GND/VSNS copper around D4/C9/U4/C16) with two
    # F<->B layer swaps at points individually checked for both track and via
    # hole clearance against the built board.  The route stays off SW/GATE
    # copper throughout and keeps a short final F.Cu stub into U1.4 clear of
    # U1's other pads.
    ("NTC", "F", 0.3,
     ["TH1.1", (12.5, 12.5), (13.2, 13.8), (13.2, 16.5), (13.0, 16.8),
      (10.3, 16.8), (10.3, 19.0), (9.7, 19.3), (7.7, 19.3), (7.7, 20.0)]),
    ("NTC", "B", 0.3,
     [(7.7, 20.0), (7.7, 21.6), (8.0, 21.9), (8.7, 22.1), (8.7, 28.9)]),
    ("NTC", "F", 0.3,
     [(8.7, 28.9), (9.9, 29.1), (9.9, 33.2), (10.0, 33.7), (10.0, 37.2),
      (9.7, 37.5), (9.0, 37.5), (9.0, 38.0), "U1.4"]),
    # U1.4's stub to the R9/C17 divider/filter drops to B.Cu immediately so
    # it clears U1.5 (TRIG) and then the TRIG/+5V F.Cu runs it would
    # otherwise cross near y=39.3, rejoining F.Cu only at R9.2's pad.
    ("NTC", "F", 0.3, ["U1.4", (8.6, 38.1), (5.9, 38.5)]),
    ("NTC", "B", 0.3, [(5.9, 38.5), (5.8, 41.8)]),
    ("NTC", "F", 0.3, [(5.8, 41.8), "R9.2", "C17.1"]),

    # Active-low trigger: connector/ESD resistor loop is local; the filtered
    # logic-side signal follows the board edge, away from SW and analog ADCs.
    ("TRIG_PAD", "F", 0.3, ["J5.1", "D3.1", "R8.1"]),
    ("TRIG", "F", 0.3, ["R8.2", (10.0, 14.675)]),
    ("TRIG", "B", 0.3,
     [(10.0, 14.675), (2.2, 18.0), (2.2, 35.825)]),
    ("TRIG", "F", 0.3,
     [(2.2, 35.825), "R7.1", "C15.1", "U1.5"]),

    # Programming and indicator routes.
    ("UPDI", "F", 0.3, ["U1.16", (19.0, 39.365)]),
    ("UPDI", "B", 0.3,
     [(19.0, 39.365), (18.5, 43.0), (23.0, 46.0), "J6.2"]),
    ("LED_CTL", "F", 0.3, ["U1.10", "R11.1"]),
    ("LED_A", "F", 0.3, ["R11.2", "LED1.2"]),

    # DNP RC snubber provision.  It is completely connected but remains
    # excluded from BOM/placement until measured values are selected.
    ("SW", "F", 0.5, ["R16.1", (56.8, 35.9625)]),
    ("SW", "B", 0.5,
     [(56.8, 35.9625), (56.8, 23.0), (50.0, 22.0)]),
    ("SNUB", "F", 0.4,
     ["R16.2", (44.0, 30.0375), (44.0, 37.5), "C20.1"]),

    # The thermistor return exits the SW pour before joining the solid quiet
    # ground plane.  Other low-current returns connect directly to that plane.
    ("GND", "F", 0.3, ["TH1.2", (21.0, 12.5)]),

    # GND bridges: reconnect B.Cu plane regions separated by the low-current
    # signal corridors, pairing a front-plane tie with a stitch via each.
    ("GND", "F", 0.3, ["U5.2", (35.3625, 44.0)]),
    ("GND", "F", 0.4, [(5.0, 15.5), (5.0, 16.5)]),
    ("GND", "F", 0.4, [(4.8, 26.0), (4.8, 27.0)]),
    ("GND", "F", 0.4, [(4.8, 45.0), (4.8, 46.0)]),
    ("GND", "F", 0.4, [(11.0, 45.5), (11.0, 46.5)]),
    ("GND", "F", 0.4, [(16.5, 41.5), (16.5, 42.5)]),
    ("GND", "F", 0.4, [(30.5, 49.5), (31.5, 49.5)]),
    ("GND", "F", 0.4, [(33.0, 43.0), (33.0, 44.0)]),
]

FULL_BOARD_VIAS = [
    ("NTC", 7.7, 20.0, 0.4, 0.8),
    ("NTC", 8.7, 28.9, 0.4, 0.8),
    ("NTC", 5.9, 38.5, 0.4, 0.8),
    ("NTC", 5.8, 41.8, 0.4, 0.8),
    ("VDRV", 6.5, 20.0, 0.4, 0.8),
    ("VDRV", 6.5, 23.2, 0.4, 0.8),
    ("VDRV", 11.35, 17.6, 0.4, 0.8),
    ("VREG_IN", 11.5, 15.5, 0.4, 0.8), ("VREG_IN", 15.0, 18.8, 0.4, 0.8),
    ("VREG_IN", 8.5, 21.275, 0.4, 0.8), ("VREG_IN", 15.65, 22.2, 0.4, 0.8),
    ("+5V", 3.2, 28.8, 0.4, 0.8),
    ("+5V", 7.2, 32.575, 0.4, 0.8),
    ("+5V", 7.2, 34.285, 0.4, 0.8),
    ("+5V", 10.725, 33.0, 0.4, 0.8),
    ("+5V", 14.225, 33.0, 0.4, 0.8),
    ("+5V", 3.2, 42.0, 0.4, 0.8),
    ("+5V", 37.6, 44.8, 0.4, 0.8),
    ("CUR_ADC", 7.0, 36.825, 0.4, 0.8),
    ("CUR_ADC", 26.5, 42.0, 0.4, 0.8),
    ("VSNS", 9.0, 11.5, 0.4, 0.8),
    ("VSNS", 7.2, 30.0, 0.4, 0.8),
    ("TRIG", 10.0, 14.675, 0.4, 0.8),
    ("TRIG", 2.2, 35.825, 0.4, 0.8),
    ("UPDI", 19.0, 39.365, 0.4, 0.8),
    ("GND", 5.0, 16.0, 0.5, 1.0),
    ("GND", 4.8, 26.5, 0.5, 1.0),
    ("GND", 4.8, 45.5, 0.5, 1.0),
    ("GND", 11.0, 46.0, 0.5, 1.0),
    ("GND", 16.5, 42.0, 0.5, 1.0),
    ("GND", 31.0, 49.5, 0.5, 1.0),
    ("GND", 33.0, 43.5, 0.5, 1.0),
    ("SW", 56.8, 35.9625, 0.5, 1.0),
]

SILK = [
    ("BLOWER CTRL 5S REV C - REFERENCE ONLY", 38.5, 55.0, 1.0, 0.15),
    ("NOT APPROVED TO ORDER - EXTERNAL FUSE REQUIRED IN B+ LEAD",
     38.5, 58.5, 0.85, 0.13),
    ("M-", 17, 10.5, 1.2, 0.2), ("M+", 27, 10.5, 1.2, 0.2),
    ("B+", 50.5, 10.5, 1.2, 0.2), ("B-", 48, 43.0, 1.2, 0.2),
    ("TRIG", 3.0, 19.0, 0.8, 0.12), ("RET", 3.0, 8.5, 0.8, 0.12),
    ("5V UPDI GND", 27.5, 44.0, 0.8, 0.12),
    ("ZIP TIE", 66.0, 10.5, 0.8, 0.12),
]


def build_pcb(sch, nc_net_by_pin, placement_only=False,
              power_stage_only=False):
    import pcbnew
    from pcbnew import VECTOR2I, FromMM

    def mm(x, y):
        return VECTOR2I(FromMM(x), FromMM(y))

    board = pcbnew.BOARD()
    nets = {}
    board_net_names = list(NETS) + sorted(set(nc_net_by_pin.values()))
    for name in board_net_names:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni

    bds = board.GetDesignSettings()
    bds.m_MinClearance = FromMM(0.15)
    bds.m_TrackMinWidth = FromMM(0.25)
    bds.m_ViasMinSize = FromMM(0.5)
    bds.m_MinThroughDrill = FromMM(0.3)
    bds.m_CopperEdgeClearance = FromMM(0.3)
    bds.SetBoardThickness(FromMM(1.6))

    pads = {}          # (ref, padnum) -> list of PAD
    pad_boxes = []     # (netcode, x0, y0, x1, y1, has_hole)
    for ref in sorted(PARTS):
        part = PARTS[ref]
        lib, fpname = part["fp"].split(":")
        fp = pcbnew.FootprintLoad(str(FPDIR / f"{lib}.pretty"), fpname)
        assert fp is not None, f"footprint not found: {part['fp']}"
        board.Add(fp)
        x, y, rot = PCB_POS[ref]
        fp.SetPosition(mm(x, y))
        fp.SetOrientationDegrees(rot)
        fp.SetReference(ref)
        fp.SetValue(part["value"])
        fp.SetFPIDAsString(part["fp"])
        fp.SetPath(pcbnew.KIID_PATH(f"/{sw.uid(f'sym/{ref}')}"))
        if part.get("mpn"):
            fp.SetField("MPN", part["mpn"])
        fp.SetField("LCSC", part.get("lcsc") or "UNVERIFIED")
        for field_name in ("MPN", "LCSC"):
            if fp.HasField(field_name):
                field = fp.GetField(field_name)
                field.SetLayer(pcbnew.F_Fab)
                field.SetVisible(False)
        if part.get("dnp"):
            fp.SetAttributes(fp.GetAttributes()
                             | pcbnew.FP_EXCLUDE_FROM_BOM
                             | pcbnew.FP_DNP
                             | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        if ref.startswith(("TP", "H")):
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM)
        for pad in fp.Pads():
            num = pad.GetNumber()
            net = part.get("nets", {}).get(num) or nc_net_by_pin.get((ref, num))
            if net:
                pad.SetNet(nets[net])
                is_rs1_sense_finger = (ref == "RS1"
                                       and pcbnew.ToMM(pad.GetBoundingBox().GetWidth()) < 1.0)
                is_ina_kelvin_input = ref == "U5" and num in {"3", "4"}
                pad.SetLocalZoneConnection(
                    pcbnew.ZONE_CONNECTION_NONE
                    if is_rs1_sense_finger or is_ina_kelvin_input
                    else pcbnew.ZONE_CONNECTION_FULL)
            pads.setdefault((ref, num), []).append(pad)
        r = fp.Reference()
        r.SetLayer(pcbnew.F_Fab)
        r.SetTextSize(mm(0.6, 0.6))
        r.SetTextThickness(FromMM(0.1))
        r.SetTextAngleDegrees(0)
        fp.Value().SetLayer(pcbnew.F_Fab)
        fp.Value().SetVisible(False)
        declared = set(part.get("nets", {}))
        have = {n for (rr, n) in pads if rr == ref}
        missing = declared - have
        assert not missing, f"{ref}: pads {missing} not in footprint {part['fp']}"

    def pad_pos(spec):
        if spec == "RS1.SENSE1":   # small Kelvin sense finger of pad 1
            cands = pads[("RS1", "1")]
        elif spec == "RS1.SENSE2":
            cands = pads[("RS1", "2")]
        elif spec in {"D2.LEAD2", "D2.TAB2"}:
            cands = pads[("D2", "2")]
        else:
            ref, num = spec.rstrip("x").split(".")
            cands = pads[(ref, num)]
        if spec.startswith("RS1.SENSE"):
            pad = min(cands, key=lambda p: p.GetBoundingBox().GetWidth())
        elif spec == "D2.LEAD2":
            pad = min(cands, key=lambda p: (p.GetBoundingBox().GetWidth()
                                            * p.GetBoundingBox().GetHeight()))
        elif spec == "D2.TAB2":
            pad = max(cands, key=lambda p: (p.GetBoundingBox().GetWidth()
                                            * p.GetBoundingBox().GetHeight()))
        else:
            pad = max(cands, key=lambda p: p.GetBoundingBox().GetWidth())
        p = pad.GetPosition()
        return (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))

    layer_map = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}
    tracks_to_place = ([] if placement_only else
                       POWER_STAGE_TRACKS if power_stage_only else
                       POWER_STAGE_TRACKS + FULL_BOARD_TRACKS)
    vias_to_place = ([] if placement_only else
                     POWER_STAGE_VIAS if power_stage_only else
                     POWER_STAGE_VIAS + FULL_BOARD_VIAS)
    zones_to_place = [] if placement_only else POWER_STAGE_ZONES
    stitch_grids_to_place = [] if placement_only else POWER_STAGE_STITCH_GRIDS
    if placement_only:
        print("placement-only mode: skipping tracks, vias, and zones")
    elif power_stage_only:
        print("power-stage-only mode: high-current, gate, driver, and Kelvin copper")
    else:
        print("full-routing mode: power stage plus all control and support nets")

    for net, layer, width, pts in tracks_to_place:
        coords = [pad_pos(p) if isinstance(p, str) else p for p in pts]
        for a, b in zip(coords, coords[1:]):
            if a == b:
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(mm(*a))
            t.SetEnd(mm(*b))
            t.SetWidth(FromMM(width))
            t.SetLayer(layer_map[layer])
            t.SetNet(nets[net])
            board.Add(t)

    def add_via(net, x, y, drill, dia):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(mm(x, y))
        v.SetDrill(FromMM(drill))
        v.SetWidth(FromMM(dia))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(nets[net])
        board.Add(v)

    for net, x, y, drill, dia in vias_to_place:
        add_via(net, x, y, drill, dia)

    # zones first (needed for stitch point-in-poly test)
    conn_map = {"full": pcbnew.ZONE_CONNECTION_FULL,
                "thermal": pcbnew.ZONE_CONNECTION_THERMAL}
    zone_polys = {}
    for net, layer, prio, clr, minw, conn, poly in zones_to_place:
        z = pcbnew.ZONE(board)
        z.SetLayer(layer_map[layer])
        z.SetNet(nets[net])
        z.SetAssignedPriority(prio)
        z.SetLocalClearance(FromMM(clr))
        z.SetMinThickness(FromMM(minw))
        z.SetPadConnection(conn_map[conn])
        z.SetThermalReliefGap(FromMM(0.5))
        z.SetThermalReliefSpokeWidth(FromMM(1.0))
        z.SetIslandRemovalMode(
            pcbnew.ISLAND_REMOVAL_MODE_ALWAYS
            if net in {"GND", "SW"} or layer == "F"
            else pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        z.Outline().NewOutline()
        for x, y in poly:
            z.Outline().Append(FromMM(x), FromMM(y))
        board.Add(z)
        zone_polys.setdefault((net, layer), []).append(poly)

    def in_poly(x, y, poly):
        inside = False
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                xt = x1 + (y - y1) / (y2 - y1) * (x2 - x1)
                if x < xt:
                    inside = not inside
        return inside

    # collect keep-away boxes: every pad of a different net, every hole
    obstacles = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            obstacles.append((pad.GetNetCode(),
                              pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                              pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()),
                              pad.HasHole()))
    track_pts = []
    for t in board.GetTracks():
        if t.GetClass() == "PCB_TRACK":
            track_pts.append((t.GetNetCode(),
                              pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y),
                              pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y),
                              t.GetLayer()))
    placed_vias = [(v[0], v[1], v[2]) for v in vias_to_place]

    def stitch_ok(net, x, y):
        netcode = nets[net].GetNetCode()
        fpoly = zone_polys.get((net, "F"), [])
        bpoly = zone_polys.get((net, "B"), [])
        if net == "GND":
            fok = bok = True   # GND zones cover the whole board
        else:
            fok = any(in_poly(x, y, p) for p in fpoly)
            bok = any(in_poly(x, y, p) for p in bpoly)
        if not (fok and bok):
            return False
        for oc, x0, y0, x1, y1, hole in obstacles:
            margin = 0.8 if (hole or oc != netcode) else 0.35
            if x0 - margin < x < x1 + margin and y0 - margin < y < y1 + margin:
                return False
        for nc, tx0, ty0, tx1, ty1, _ in track_pts:
            if nc == netcode:
                continue
            # distance point-to-segment
            dx, dy = tx1 - tx0, ty1 - ty0
            ln = dx * dx + dy * dy
            t = 0 if ln == 0 else max(0, min(1, ((x - tx0) * dx + (y - ty0) * dy) / ln))
            px, py = tx0 + t * dx, ty0 + t * dy
            if (x - px) ** 2 + (y - py) ** 2 < 1.1 ** 2:
                return False
        for _, vx, vy in placed_vias:
            if (x - vx) ** 2 + (y - vy) ** 2 < 1.4 ** 2:
                return False
        return True

    stitched = 0
    for net, x0, y0, x1, y1, pitch in stitch_grids_to_place:
        y = y0
        row = 0
        while y <= y1 + 1e-6:
            x = x0 + (pitch / 2 if row % 2 else 0)
            while x <= x1 + 1e-6:
                if stitch_ok(net, x, y):
                    add_via(net, x, y, 0.5, 1.0)
                    placed_vias.append((net, x, y))
                    stitched += 1
                x += pitch
            y += pitch
            row += 1
    print(f"stitching vias placed: {stitched}")

    # board outline (rounded rect r=2)
    W, H, R = BOARD_W, BOARD_H, 2.0

    def seg(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(mm(x1, y1)); s.SetEnd(mm(x2, y2))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FromMM(0.1))
        board.Add(s)

    def arc(sx, sy, mx, my, ex, ey):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(mm(sx, sy), mm(mx, my), mm(ex, ey))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FromMM(0.1))
        board.Add(s)

    k = R * 0.29289321
    seg(R, 0, W - R, 0); seg(W, R, W, H - R)
    seg(W - R, H, R, H); seg(0, H - R, 0, R)
    arc(0, R, k, k, R, 0)
    arc(W - R, 0, W - k, k, W, R)
    arc(W, H - R, W - k, H - k, W - R, H)
    arc(R, H, k, H - k, 0, H - R)

    for text, x, y, size, th in SILK:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(mm(x, y))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(mm(size, size))
        t.SetTextThickness(FromMM(th))
        board.Add(t)

    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(str(OUT_PCB), board)
    print(f"wrote {OUT_PCB}: {len(board.GetFootprints())} footprints")


def main():
    sch = build_schematic()
    _, nc_net_by_pin = verify_netlist()
    if "--sch-only" in sys.argv:
        return

    placement_only = "--placement-only" in sys.argv
    power_stage_only = "--power-stage-only" in sys.argv
    legacy_full_routing = "--legacy-full-routing" in sys.argv
    if placement_only or power_stage_only or legacy_full_routing:
        build_pcb(
            sch,
            nc_net_by_pin,
            placement_only=placement_only,
            power_stage_only=power_stage_only,
        )
        return

    # The accepted Freerouting session was generated from the independently
    # validated power-stage-only base.  Import it, apply the small deterministic
    # repairs, and make KiCad itself refill and strictly check the saved board.
    build_pcb(sch, nc_net_by_pin, power_stage_only=True)
    if not ROUTING_SESSION.is_file():
        raise FileNotFoundError(f"routing session not found: {ROUTING_SESSION}")

    import pcbnew
    from repair_freeroute_candidate import repair

    board = pcbnew.LoadBoard(str(OUT_PCB))
    if not pcbnew.ImportSpecctraSES(board, str(ROUTING_SESSION)):
        raise RuntimeError(f"failed to import routing session: {ROUTING_SESSION}")
    repair(board)
    pcbnew.SaveBoard(str(OUT_PCB), board)
    enforce_release_drc_severities()

    build_report = ROOT / "hardware" / "outputs" / "release-route-build-drc.rpt"
    build_report.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            KICAD_CLI,
            "pcb",
            "drc",
            "--severity-all",
            "--schematic-parity",
            "--all-track-errors",
            "--refill-zones",
            "--save-board",
            "--exit-code-violations",
            "-o",
            str(build_report),
            str(OUT_PCB),
        ],
        check=True,
    )
    print(f"release routing reproduced; strict DRC report: {build_report}")


if __name__ == "__main__":
    main()
