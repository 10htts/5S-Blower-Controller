# Current sensing

RS1 is a 2 mΩ, 3 W metal-strip shunt with split-pad Kelvin routing to an INA180A2 nominal-gain-50 amplifier. Ideal values are:

| Current | Shunt voltage | Shunt power | Ideal amplifier output |
|---:|---:|---:|---:|
| 25 A | 50 mV | 1.25 W | 2.5 V |
| 30 A | 60 mV | 1.80 W | 3.0 V |
| 40 A | 80 mV | 3.20 W | 4.0 V |

At 40 A the ideal shunt dissipation exceeds its 3 W nominal rating, so the firmware's provisional 40 A trip cannot be treated as a continuous-current rating. Validate shunt pulse energy, tolerance, temperature coefficient, amplifier offset/gain error and output swing, ADC reference/scaling, filtering delay, and trip latency from measured motor waveforms. Firmware limiting never replaces the external fuse.
