# Architecture

Battery B+ feeds an external fuse, reverse-polarity protection, TVS and bulk capacitance. The protected rail feeds the motor; the MOSFET low side switches motor current. A recirculation path is placed adjacent to the motor/MOSFET loop. A regulator powers the MCU and gate driver. The original low-current trigger is a filtered logic input with ESD protection.

The MCU architecture is selected provisionally because it makes protection and fault-latching behavior explicit and testable. Hardware gate pull-down/default-off, driver disable, watchdog, brownout, and a physical fuse provide independent protection layers.
