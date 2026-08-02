# Validation plan

Record the board serial/revision, test date, operator, equipment model, probe arrangement, instrument settings, supply limits, ambient temperature, firmware version, raw captures, and pass/fail decision for every test. Agree on numerical acceptance limits before testing; do not derive a limit after seeing the result.

## Before a fabrication order

1. Independently review the schematic, PCB, DRC/ERC reports, Gerbers, drill file, and footprint/polarity mapping.
2. Measure the battery adapter and enclosure. Confirm the 77 × 62 mm outline, holes, terminals, polarity, component heights, insulation, creepage around exposed conductors, airflow, and service access.
3. Characterize the exact motor at 15, 18, and 21 V: steady running current, start waveform, restrained/locked-rotor current with a safe current limit, lead resistance, and inductance.
4. Select the exact external fuse, connector, and wire. Review voltage/current ratings and coordinate fuse time-current and I²t behavior with the TVS, shunt, MOSFETs, diode, copper, and worst credible fault.
5. Recalculate hot MOSFET conduction/switching loss, shunt pulse/steady loss, diode loss, copper/via rise, bulk-capacitor ripple, and transient margin using the measured motor data.

## First-article electrical tests

1. Follow `docs/bring-up.md` from a current-limited bench supply with the motor disconnected, then with a fused and restrained motor.
2. Verify battery and logic rails, reset gate-off state, PWM frequency/dead behavior, gate amplitude, ADC scaling, trigger polarity, soft-start monotonicity, and trigger-release restart.
3. Capture B+, MOSFET VDS, both VGS waveforms, switch node, shunt current, and regulator rails during connection, start, stop, stall/fault, and fuse interruption. Compare every peak with component absolute maximums plus an approved engineering margin.
4. Verify undervoltage trip/restart under slow ramps and battery sag, overcurrent response, overtemperature response, invalid-sensor fail-safe behavior, watchdog reset, brownout reset, and repeated power cycling.

## Thermal, endurance, and integration tests

1. Measure MOSFET, shunt, diode, TVS, connectors, wires, capacitors, regulators, and PCB temperatures in the final enclosure at the approved duty cycle and worst ambient condition.
2. Run repeated starts, stops, stalls/faults, UV events, and long-duration operation while checking for drift, nuisance trips, damaged copper, connector heating, or uncontrolled restart.
3. Check conducted and radiated noise in the final wiring/enclosure configuration and verify that switching does not corrupt trigger, ADC, or programming interfaces.
4. Inspect the first article after testing and archive photographs, waveforms, temperatures, firmware, and a signed release checklist.

No board is order-approved until every applicable item has objective evidence and an approved pass criterion.
