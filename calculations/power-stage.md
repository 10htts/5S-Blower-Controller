# Power-stage comparison

## A: MCU low-side PWM (selected reference architecture)

An MCU drives a dedicated gate driver and two parallel 60/75 V N-channel MOSFETs. A Kelvin shunt provides current feedback; a TVS, local bulk ceramic/electrolytic capacitance, and a recirculation diode handle switching energy. This architecture supports filtered UV, current, thermal, watchdog, and trigger-release behavior in one testable state machine.

## B: analog controller (rejected for the reference)

An oscillator, ramp comparator, current-limit comparator, and UV/thermal shutdown can reduce firmware cost, but threshold interaction, restart latching, and diagnostic coverage become less transparent. It is only attractive after measured current and thermal requirements justify a simpler fixed-function design.

## Loss screening

For a candidate effective MOSFET resistance `Rds_on`, conduction loss is `I²R`: at 10/20/25/30 A it is `100/400/625/900 × Rds_on` W. Switching and diode losses are not included because gate charge, switching time, inductance, and motor waveform are not yet measured. Select parts with at least 60 V rating and verify SOA and hot resistance from the manufacturer datasheet before release.
