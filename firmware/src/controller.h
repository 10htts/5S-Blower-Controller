#pragma once

enum class State {
    OFF,
    ARMING,
    SOFT_START,
    RUN,
    OVERCURRENT,
    UNDERVOLTAGE,
    OVERTEMPERATURE,
    INPUT_FAULT,
    FAULT_LATCHED,
};

struct Inputs {
    // Logical request after the HAL has debounced and inverted the board's
    // active-low TRIG pin. true always means "motor requested" here.
    bool trigger = false;
    float voltage = 0.0f;
    float current = 0.0f;
    float temperature = 0.0f;
};

class Controller {
  public:
    State state = State::OFF;
    State fault_reason = State::OFF;
    float duty = 0.0f;

    void reset();
    void step(const Inputs& inputs, float dt_seconds);

  private:
    void trip(State reason);
    bool can_clear_fault(const Inputs& inputs) const;
};
