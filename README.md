# 5S Blower Controller

Open-source reference controller for a two-wire brushed-DC blower powered by a removable 5-series lithium-ion battery (approximately 15–21 V). The design uses a protected low-side N-MOSFET PWM stage, soft start, trigger filtering, voltage/current/temperature protection, a physical fuse, and a latched fault requiring trigger release.

**Status: NOT YET APPROVED TO ORDER.** This is an unvalidated prototype/reference revision. The exact blower current, wiring, connector pinout, board envelope, and thermal environment are unknown. No regulatory certification is claimed.

See [architecture](docs/architecture.md), [wiring](docs/wiring.md), [safety](docs/safety.md), and [revision status](docs/revision-status.md). Firmware tests are host-side and do not replace hardware bring-up.

## Licensing

Hardware is licensed under CERN-OHL-S-2.0 (`LICENSE`). Firmware is GPLv3-or-later (`firmware/LICENSE`).

## Planned validation

Measure stall/start/run current, battery connector polarity, motor inductance, housing envelope, and thermal rise before selecting production thresholds or ordering PCBs.
