# Firmware

Host-testable reference state machine. Build with a C++17 compiler when targeting hardware; constants are centralized in `src/config.h`. The controller retains soft-start progress across calls, latches protection trips until trigger release, applies the configured undervoltage restart hysteresis, and fails safe on invalid engineering inputs.

`Inputs::trigger` is normalized active-high. The board input is electrically active-low, so the target-specific hardware layer must debounce and invert the pin before calling `Controller::step`. That layer must also configure PWM safe-off at reset, the ATtiny1616 watchdog and brown-out detector, ADC scaling/filtering, periodic scheduling, and gate-output shutdown on missed deadlines. Those target-specific pieces and the final thresholds remain release blockers; this portable code does not claim a verified MCU image or pinout.

`firmware/tests/controller_test.cpp` exercises the compiled state machine when a C++ compiler is available. The Python test suite skips that executable test on hosts without a compiler; CI and release validation must run it with warnings treated as errors.
