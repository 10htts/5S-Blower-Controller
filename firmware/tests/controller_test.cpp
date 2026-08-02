#include <cassert>
#include <cmath>
#include <limits>

#include "controller.h"

namespace {

Inputs nominal(bool trigger = true) {
    return Inputs{trigger, 18.0f, 0.0f, 25.0f};
}

void reach_run(Controller& controller) {
    const Inputs inputs = nominal();
    controller.step(inputs, 0.0f);
    assert(controller.state == State::ARMING);
    controller.step(inputs, 0.0f);
    assert(controller.state == State::SOFT_START);

    float previous = controller.duty;
    for (int i = 0; i < 10; ++i) {
        controller.step(inputs, 0.15f);
        assert(controller.duty >= previous);
        assert(controller.duty >= 0.0f && controller.duty <= 1.0f);
        previous = controller.duty;
    }
    assert(controller.state == State::RUN);
    assert(std::abs(controller.duty - 1.0f) < 1e-6f);
}

}  // namespace

int main() {
    {
        Controller controller;
        reach_run(controller);
    }
    {
        Controller controller;
        reach_run(controller);
        Inputs inputs = nominal();
        inputs.voltage = 14.9f;
        controller.step(inputs, 0.01f);
        assert(controller.state == State::FAULT_LATCHED);
        assert(controller.fault_reason == State::UNDERVOLTAGE);
        assert(controller.duty == 0.0f);

        controller.step(inputs, 0.01f);
        assert(controller.state == State::FAULT_LATCHED);
        inputs.trigger = false;
        controller.step(inputs, 0.01f);
        assert(controller.state == State::FAULT_LATCHED);
        inputs.voltage = 16.5f;
        controller.step(inputs, 0.01f);
        assert(controller.state == State::OFF);
    }
    {
        Controller controller;
        reach_run(controller);
        Inputs inputs = nominal();
        inputs.current = 40.0f;
        controller.step(inputs, 0.01f);
        assert(controller.state == State::FAULT_LATCHED);
        assert(controller.fault_reason == State::OVERCURRENT);
        inputs.trigger = false;
        inputs.current = 0.0f;
        controller.step(inputs, 0.01f);
        assert(controller.state == State::OFF);
    }
    {
        Controller controller;
        Inputs inputs = nominal();
        inputs.voltage = std::numeric_limits<float>::quiet_NaN();
        controller.step(inputs, 0.01f);
        assert(controller.state == State::FAULT_LATCHED);
        assert(controller.fault_reason == State::INPUT_FAULT);
        inputs.trigger = false;
        controller.step(inputs, 0.01f);
        assert(controller.state == State::FAULT_LATCHED);
        inputs.voltage = 18.0f;
        controller.step(inputs, 0.01f);
        assert(controller.state == State::OFF);
    }
    {
        Controller controller;
        controller.step(nominal(), -0.01f);
        assert(controller.state == State::FAULT_LATCHED);
        assert(controller.duty == 0.0f);
    }
    {
        Controller controller;
        reach_run(controller);
        controller.step(nominal(false), 0.01f);
        assert(controller.state == State::OFF);
        assert(controller.duty == 0.0f);
    }
}
