#pragma once

namespace config {

// Protection thresholds remain provisional until the validation plan has been
// completed with the intended battery, wiring, fuse, enclosure, and motor.
constexpr float UV_TRIP_V = 15.0f;
constexpr float UV_RESTART_V = 16.5f;
constexpr float OC_TRIP_A = 40.0f;
constexpr float OT_TRIP_C = 90.0f;
constexpr float SOFT_START_S = 1.5f;
constexpr float PWM_HZ = 20000.0f;

}  // namespace config
