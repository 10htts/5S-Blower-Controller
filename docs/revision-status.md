# Revision status — Rev C

**NOT YET APPROVED TO ORDER.** The CAD and export pipeline are complete and clean; the remaining blockers require real component, motor, mechanical, and first-article evidence.

| Release gate | Status | Evidence or remaining work |
|---|---|---|
| Deterministic schematic/PCB generation | PASS | `scripts/build_board.py` reproduces the canonical routed board from the accepted session plus reviewed repairs. |
| KiCad PCB checks | PASS | 0 DRC violations, 0 unconnected items, 0 schematic-parity issues with KiCad 10.0.5; missing-courtyard and off-center-via-track checks are enabled as errors. |
| KiCad schematic checks | PASS | 0 ERC errors and 0 warnings. |
| Repository and firmware host checks | PASS | Design checker and host unit tests pass. Target MCU integration remains a separate gate. |
| Fabrication plots and visual CAD review | PASS | Rev C Gerbers, drill, PDFs, renders, reports, BOM, and placement files generated and visually reviewed. |
| PCBWay quotation/viewer package | PASS | `manufacturing/pcbway-review-revC.zip` is suitable for independent file review. |
| PCBA procurement/process package | BLOCKED | BOM has unresolved MPN/supplier data; 15 drilled via locations intersect SMD pad copper and need an approved dogbone or filled/capped process; every footprint and placement orientation still needs assembly review. |
| Target firmware and fail-safe behavior | BLOCKED | Implement and verify HAL, active-low trigger inversion, ADC scaling/filtering, PWM-safe reset, watchdog, brownout, and scheduling on the selected MCU. |
| Motor and wiring characterization | BLOCKED | Measure running, starting, and stall current at 15/18/21 V, motor inductance, lead resistance/length, and wire/connector ratings. |
| Fuse and protection coordination | BLOCKED | Select the exact external fuse and prove time-current/I²t coordination with wiring, TVS, MOSFET, shunt, and motor faults. |
| Mechanical fit | BLOCKED | Confirm the 77 × 62 mm outline, holes, connector locations, polarity, terminal geometry, and component-height keepouts against the enclosure and battery adapter. |
| Transient, thermal, and EMI validation | BLOCKED | Measure switch-node, drain, gate, and supply transients; temperatures in the final enclosure; conducted/radiated noise; and repeated start/fault cycles. |
| First-article release | BLOCKED | Assemble and inspect a fused prototype, complete `docs/bring-up.md`, and record signed results for every validation gate. |

The clean DRC/ERC result is necessary but is not proof that the board can safely carry an unknown motor current or survive an unknown enclosure and fuse system.
