# Thermal review

Measure MOSFET case and PCB temperature with thermocouples during steady operation and repeated starts at currents justified by the measured motor. Include hot `RDS(on)`, switching loss, current-sharing error, diode loss, copper/via spreading, capacitor ripple, connector and wire heating, enclosure airflow, and shunt heating.

The firmware's provisional 90 °C sensor trip is a protection target, not a demonstrated component-junction or touch-temperature limit. Correlate the sensor reading with the hottest MOSFET junction estimate and all nearby components in the final enclosure. Define allowable ambient temperature, duty cycle, cooldown behavior, and thermal margin before first-article testing.
