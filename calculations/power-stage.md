# Power-stage comparison

## A: MCU low-side PWM (selected reference architecture)

An MCU drives a TC4422A gate driver from a nominal 9.98 V rail and two parallel IPT015N10N5 100 V N-channel MOSFETs. A Kelvin-connected 2 mΩ shunt provides current feedback; an SMDJ33A TVS, local bulk ceramic/electrolytic capacitance, and an STPS41H100C recirculation diode manage supply and switching energy. This architecture supports filtered UV, current, thermal, watchdog, and trigger-release behavior in one testable state machine.

## B: analog controller (rejected for the reference)

An oscillator, ramp comparator, current-limit comparator, and UV/thermal shutdown can reduce firmware cost, but threshold interaction, restart latching, and diagnostic coverage become less transparent. It is only attractive after measured current and thermal requirements justify a simpler fixed-function design.

## Loss screening

The selected MOSFET is specified at a maximum 1.5 mΩ at 10 V gate drive and 25 °C. Two ideal, equally sharing devices therefore have a screening resistance of 0.75 mΩ. DC conduction-only estimates are:

| Total current | Ideal pair loss |
|---:|---:|
| 10 A | 0.075 W |
| 20 A | 0.300 W |
| 25 A | 0.469 W |
| 30 A | 0.675 W |
| 40 A | 1.200 W |

These figures are not thermal predictions. They exclude hot `RDS(on)`, current-sharing error, switching overlap, diode loss, gate-drive loss, shunt loss, copper loss, and motor ripple. Recalculate with measured waveforms and datasheet worst cases, and verify VDS/VGS transients and SOA before release.
