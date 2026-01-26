// M.A.S.H. IoT - Actuator Control
// Relay module interface for fans, mist makers, and lights

#ifndef ACTUATORS_H
#define ACTUATORS_H

#include <Arduino.h>

// Actuator states
enum ActuatorState {
    STATE_OFF = 0,
    STATE_ON = 1
};

// Actuator types
enum ActuatorType {
    FRUITING_FAN,
    FRUITING_MIST,
    FRUITING_LIGHT,
    SPAWNING_FAN,
    SPAWNING_MIST,
    SPAWNING_LIGHT
};

class ActuatorManager {
private:
    // Current states
    bool states[8];
    
    // Helper to convert actuator type to pin
    int getPin(ActuatorType type);
    
public:
    ActuatorManager();
    
    // Initialize all relays
    void begin();
    
    // Control individual actuators
    void set(ActuatorType type, ActuatorState state);
    void turnOn(ActuatorType type);
    void turnOff(ActuatorType type);
    void toggle(ActuatorType type);
    
    // Get state
    bool getState(ActuatorType type);
    
    // Emergency shutdown
    void shutdownAll();
    
    // Parse and execute command from serial
    bool executeCommand(const char* command);
};

#endif // ACTUATORS_H
