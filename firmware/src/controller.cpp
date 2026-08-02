#include "controller.h"

#include <algorithm>
#include <cmath>

#include "config.h"

namespace {

bool finite_inputs(const Inputs& inputs) {
    return std::isfinite(inputs.voltage) && std::isfinite(inputs.current) &&
           std::isfinite(inputs.temperature);
}

}  // namespace

void Controller::reset() {
    state = State::OFF;
    fault_reason = State::OFF;
    duty = 0.0f;
}

void Controller::trip(State reason) {
    duty = 0.0f;
    fault_reason = reason;
    state = State::FAULT_LATCHED;
}

bool Controller::can_clear_fault(const Inputs& inputs) const {
    if (!finite_inputs(inputs) || inputs.current < 0.0f ||
        inputs.temperature < -50.0f) {
        return false;
    }

    switch (fault_reason) {
        case State::UNDERVOLTAGE:
            return inputs.voltage >= config::UV_RESTART_V;
        case State::OVERCURRENT:
            return inputs.current < config::OC_TRIP_A;
        case State::OVERTEMPERATURE:
            return inputs.temperature < config::OT_TRIP_C;
        case State::INPUT_FAULT:
            return inputs.voltage >= config::UV_RESTART_V;
        default:
            return false;
    }
}

void Controller::step(const Inputs& inputs, float dt_seconds) {
    if (state == State::FAULT_LATCHED) {
        duty = 0.0f;
        // Every trip requires a physical trigger release. Undervoltage also
        // requires the configured restart threshold before re-arming.
        if (!inputs.trigger && can_clear_fault(inputs)) {
            reset();
        }
        return;
    }

    // Trigger release is the unconditional safe state. Faults that occur while
    // driving are latched below; an inactive request cannot start the output.
    if (!inputs.trigger) {
        reset();
        return;
    }

    if (!finite_inputs(inputs) || !std::isfinite(dt_seconds) ||
        dt_seconds < 0.0f || inputs.voltage < 0.0f || inputs.current < 0.0f ||
        inputs.temperature < -50.0f) {
        trip(State::INPUT_FAULT);
        return;
    }
    if (inputs.temperature >= config::OT_TRIP_C) {
        trip(State::OVERTEMPERATURE);
        return;
    }
    if (inputs.current >= config::OC_TRIP_A) {
        trip(State::OVERCURRENT);
        return;
    }
    if (inputs.voltage < config::UV_TRIP_V) {
        trip(State::UNDERVOLTAGE);
        return;
    }

    switch (state) {
        case State::OFF:
            duty = 0.0f;
            state = State::ARMING;
            return;
        case State::ARMING:
            duty = 0.0f;
            state = State::SOFT_START;
            return;
        case State::SOFT_START:
            duty = std::clamp(
                duty + dt_seconds / config::SOFT_START_S, 0.0f, 1.0f);
            if (duty >= 1.0f) {
                state = State::RUN;
            }
            return;
        case State::RUN:
            duty = 1.0f;
            return;
        default:
            trip(State::INPUT_FAULT);
            return;
    }
}
