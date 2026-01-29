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

// Actuator types - matches relay module IN1-IN8
enum ActuatorType {
    MIST_MAKER,            // IN1: Fruiting room humidifier
    HUMIDIFIER_FAN,        // IN2: Fruiting room humidifier fan
    FRUITING_EXHAUST_FAN,  // IN3: Fruiting room exhaust
    FRUITING_INTAKE_FAN,   // IN4: Fruiting room intake blower
    SPAWNING_EXHAUST_FAN,  // IN5: Spawning room exhaust
    DEVICE_EXHAUST_FAN,    // IN6: Device room exhaust
    FRUITING_LED,          // IN7: Fruiting room LED lights
    RESERVED               // IN8: Reserved for future use
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
