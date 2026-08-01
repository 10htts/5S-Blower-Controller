# Bring-up

1. Inspect polarity, shorts, solder bridges, MOSFET orientation, shunt Kelvin routing, and gate pull-down.
2. Power logic from a current-limited supply with the motor disconnected; verify reset leaves the gate off.
3. Verify ADC scaling and trigger release/fault behavior with simulated inputs.
4. Use a fused, current-limited supply and a restrained motor; begin with a low current limit and short duty cycle.
5. Increase load only while recording current, VBUS, gate waveform, MOSFET/shunt temperature, and fault response.
