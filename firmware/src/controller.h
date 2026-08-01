#pragma once
enum class State { OFF, ARMING, SOFT_START, RUN, OVERCURRENT, UNDERVOLTAGE, OVERTEMPERATURE, FAULT_LATCHED };
struct Inputs { bool trigger=false; float voltage=0; float current=0; float temperature=0; };
class Controller { public: State state=State::OFF; float duty=0; void step(const Inputs& i, float dt); };
