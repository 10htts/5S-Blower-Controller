"""Generate the compact reference PCB source used for Rev A qualification.

The board envelope is provisional (100 x 60 mm); electrical and mechanical
measurements are still required before fitting it to an OEM housing.
"""
from pathlib import Path

OUT = Path(__file__).parents[1] / "hardware" / "blower-controller.kicad_pcb"

def esc(value: str) -> str:
    return value.replace('"', '\\"')

def fp(ref, value, x, y, pads, kind="thru_hole"):
    lines = [f'  (footprint "Custom:{ref}" (layer "F.Cu") (at {x} {y})',
             f'    (property "Reference" "{esc(ref)}" (at 0 -3 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
             f'    (property "Value" "{esc(value)}" (at 0 3 0) (layer "F.Fab") hide (effects (font (size 1 1) (thickness 0.15))))',
             '    (fp_rect (start -3 -2) (end 3 2) (stroke (width 0.25) (type default)) (fill none) (layer "F.SilkS"))']
    for number, px, py, net, shape in pads:
        if kind == "smd":
            lines.append(f'    (pad "{number}" smd {shape} (at {px} {py}) (size 2.2 2.2) (layers "F.Cu" "F.Paste" "F.Mask") (net {net[0]} "{net[1]}"))')
        else:
            lines.append(f'    (pad "{number}" thru_hole {shape} (at {px} {py}) (size 3.2 3.2) (drill 1.3) (layers "*.Cu" "*.Mask") (net {net[0]} "{net[1]}"))')
    lines.append('  )')
    return '\n'.join(lines)

def seg(x1, y1, x2, y2, width, layer, net):
    return f'  (segment (start {x1} {y1}) (end {x2} {y2}) (width {width}) (layer "{layer}") (net {net}))'

header = '''(kicad_pcb (version 20240108) (generator pcbnew)
  (general (thickness 1.6))
  (paper "A4")
  (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (36 "B.SilkS" user "b.silkscreen") (37 "F.SilkS" user "f.silkscreen") (44 "Edge.Cuts" user))
  (setup (pad_to_mask_clearance 0))
  (net 0 "")
  (net 1 "BATT+")
  (net 2 "GND")
  (net 3 "VIN_PROTECTED")
  (net 4 "MOTOR+")
  (net 5 "SW_NODE")
  (net 6 "GATE")
  (net 7 "SENSE")
  (net 8 "TRIGGER")
  (net 9 "+5V")
  (net 10 "NTC")
  (net 11 "CURRENT")
  (net 12 "V_SENSE")
  (net 13 "PWM")
'''

footprints = [
    fp("J1", "BATTERY", 25, 30, [("1", 0, 0, (1,"BATT+"), "rect"), ("2", 0, 7.62, (2,"GND"), "circle")]),
    fp("F1", "30A_FUSE", 35, 30, [("1", 0, 0, (1,"BATT+"), "rect"), ("2", 12, 0, (3,"VIN_PROTECTED"), "circle")]),
    fp("D1", "SMBJ33A_TVS", 53, 30, [("1", 0, 0, (3,"VIN_PROTECTED"), "rect"), ("2", 0, 7.62, (2,"GND"), "circle")]),
    fp("C1", "100uF_35V", 62, 30, [("1", 0, 0, (3,"VIN_PROTECTED"), "rect"), ("2", 0, 7.62, (2,"GND"), "circle")]),
    fp("J2", "MOTOR", 115, 34, [("1", 0, 0, (4,"MOTOR+"), "rect"), ("2", 0, 7.62, (5,"SW_NODE"), "circle")]),
    fp("D2", "STPS30L60CW", 98, 34, [("1", 0, 0, (4,"MOTOR+"), "rect"), ("2", 0, 7.62, (5,"SW_NODE"), "circle")]),
    fp("Q1", "IPT015N10NM5", 78, 50, [("1", -2.54, 0, (6,"GATE"), "rect"), ("2", 0, 0, (5,"SW_NODE"), "circle"), ("3", 2.54, 0, (2,"GND"), "circle")]),
    fp("Q2", "IPT015N10NM5", 78, 62, [("1", -2.54, 0, (6,"GATE"), "rect"), ("2", 0, 0, (5,"SW_NODE"), "circle"), ("3", 2.54, 0, (2,"GND"), "circle")]),
    fp("RS1", "2mR_3W_KELVIN", 86, 70, [("1", -3, 0, (5,"SW_NODE"), "rect"), ("2", 3, 0, (7,"SENSE"), "circle")], "smd"),
    fp("U1", "TC4420_GATE_DRIVER", 52, 52, [("1", -3, -2, (13,"PWM"), "rect"), ("2", -1, -2, (9,"+5V"), "circle"), ("3", 1, -2, (2,"GND"), "circle"), ("4", 3, -2, (6,"GATE"), "circle"), ("5", 3, 2, (6,"GATE"), "circle"), ("6", 1, 2, (2,"GND"), "circle"), ("7", -1, 2, (9,"+5V"), "circle"), ("8", -3, 2, (2,"GND"), "circle")], "smd"),
    fp("U2", "ATTINY1616", 36, 53, [("1", -3, -2, (9,"+5V"), "rect"), ("2", -1, -2, (2,"GND"), "circle"), ("3", 1, -2, (8,"TRIGGER"), "circle"), ("4", 3, -2, (11,"CURRENT"), "circle"), ("5", 3, 2, (10,"NTC"), "circle"), ("6", 1, 2, (12,"V_SENSE"), "circle"), ("7", -1, 2, (13,"PWM"), "circle"), ("8", -3, 2, (2,"GND"), "circle")], "smd"),
    fp("J3", "TRIGGER", 25, 70, [("1", 0, 0, (8,"TRIGGER"), "rect"), ("2", 0, 7.62, (2,"GND"), "circle")]),
    fp("R1", "100k_VDIV", 44, 38, [("1", -2, 0, (3,"VIN_PROTECTED"), "rect"), ("2", 2, 0, (12,"V_SENSE"), "circle")], "smd"),
    fp("R2", "27k_VDIV", 52, 38, [("1", -2, 0, (12,"V_SENSE"), "rect"), ("2", 2, 0, (2,"GND"), "circle")], "smd"),
    fp("R3", "10R_GATE", 61, 48, [("1", -2, 0, (6,"GATE"), "rect"), ("2", 2, 0, (6,"GATE"), "circle")], "smd"),
    fp("R4", "10k_NTC_PULLUP", 44, 44, [("1", -2, 0, (9,"+5V"), "rect"), ("2", 2, 0, (10,"NTC"), "circle")], "smd"),
    fp("TH1", "NTC_10K", 36, 70, [("1", 0, 0, (10,"NTC"), "rect"), ("2", 0, 7.62, (2,"GND"), "circle")]),
    fp("J4", "UPDI", 60, 70, [("1", 0, 0, (9,"+5V"), "rect"), ("2", 0, 2.54, (13,"PWM"), "circle"), ("3", 0, 5.08, (2,"GND"), "circle")]),
]

segments = [
    # high-current path
    seg(25,30,35,30,3,"F.Cu",1), seg(47,30,53,30,3,"F.Cu",3), seg(53,30,62,30,3,"F.Cu",3),
    seg(62,30,115,34,3,"F.Cu",4), seg(98,34,115,34,3,"F.Cu",4),
    seg(115,41.62,78,50,3,"B.Cu",5), seg(98,41.62,78,50,3,"B.Cu",5), seg(78,50,78,62,3,"B.Cu",5), seg(78,62,83,70,3,"B.Cu",5),
    seg(80.54,50,80.54,62,1,"F.Cu",2), seg(80.54,62,80.54,70,1,"F.Cu",2),
    # low-current routing
    seg(25,30,53,30,0.8,"B.Cu",1), seg(53,37.62,62,37.62,0.8,"B.Cu",2),
    seg(25,37.62,25,77.62,0.8,"B.Cu",2), seg(25,77.62,36,77.62,0.8,"B.Cu",2), seg(36,77.62,60,75.08,0.8,"B.Cu",2),
    seg(36,51,49,50,0.3,"F.Cu",13), seg(55,50,75.46,50,0.5,"F.Cu",6), seg(75.46,50,75.46,62,0.5,"F.Cu",6),
    seg(33,51,25,70,0.3,"F.Cu",8), seg(39,51,45,38,0.3,"F.Cu",11), seg(39,55,44,44,0.3,"F.Cu",10), seg(37,55,50,38,0.3,"F.Cu",12),
    seg(42,38,44,38,0.3,"F.Cu",3), seg(46,38,50,38,0.3,"F.Cu",12), seg(50,38,54,38,0.3,"F.Cu",12),
    seg(42,44,46,44,0.3,"F.Cu",10), seg(44,44,39,55,0.3,"F.Cu",10),
    seg(59,48,63,48,0.3,"F.Cu",6), seg(49,50,59,48,0.3,"F.Cu",13),
    seg(49,54,49,70,0.3,"F.Cu",2), seg(49,70,60,75.08,0.3,"F.Cu",2),
    seg(49,54,49,54,0.3,"F.Cu",9), seg(51,50,51,50,0.3,"F.Cu",9),
]

graphics = [
    '  (gr_rect (start 20 20) (end 120 80) (stroke (width 0.3) (type default)) (fill none) (layer "Edge.Cuts"))',
    '  (gr_text "5S BLOWER CTRL - REFERENCE REV A" (at 70 23) (layer "F.SilkS") (effects (font (size 1.5 1.5) (thickness 0.25))))',
    '  (gr_text "B+  B-   MOTOR   TRIGGER" (at 70 77) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
]

OUT.write_text(header + '\n'.join(footprints + graphics + segments) + '\n)\n', encoding='utf-8')
print(OUT)
