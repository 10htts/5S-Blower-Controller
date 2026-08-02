# Assumptions (reference revision)

| Item | Provisional value | Required evidence |
|---|---:|---|
| Battery | 15–21 V, 5S | pack measurement under load and charger-state review |
| Continuous current | 25 A | measured running current |
| Startup current | 40 A or more | current probe |
| PWM | 20 kHz | firmware configuration |
| UV trip/restart | 15.0/16.5 V | system test |
| Overcurrent trip | 40 A | measured trip latency, shunt pulse, and motor waveform |
| MOSFET shutdown | 90 °C sensor | sensor-to-junction correlation and enclosure thermal test |
| Copper | 2 oz target | fabricator stackup and measured temperature rise |
| Board envelope | 77 × 62 mm CAD outline | enclosure and adapter fit check |

Values are not production limits until measured.
