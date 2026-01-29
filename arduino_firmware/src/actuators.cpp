// M.A.S.H. IoT - Actuator Implementation
// Relay control with active-low logic

#include "actuators.h"
#include "config.h"
#include <string.h>

ActuatorManager::ActuatorManager() {
    // Initialize all states to OFF
    for (int i = 0; i < 8; i++) {
        states[i] = false;
    }
}

void ActuatorManager::begin() {
    // Configure all relay pins as OUTPUT
    pinMode(RELAY_MIST_MAKER_PIN, OUTPUT);
    pinMode(RELAY_HUMIDIFIER_FAN_PIN, OUTPUT);
    pinMode(RELAY_FRUITING_EXHAUST_PIN, OUTPUT);
    pinMode(RELAY_FRUITING_INTAKE_PIN, OUTPUT);
    pinMode(RELAY_SPAWNING_EXHAUST_PIN, OUTPUT);
    pinMode(RELAY_DEVICE_EXHAUST_PIN, OUTPUT);
    pinMode(RELAY_LED_LIGHTS_PIN, OUTPUT);
    pinMode(RELAY_RESERVED_PIN, OUTPUT);

    // Turn all relays OFF (write HIGH for active-low)
    shutdownAll();
    
    Serial.println(F("[OK] Actuators initialized (all OFF)"));
}

int ActuatorManager::getPin(ActuatorType type) {
    switch (type) {
        case MIST_MAKER: return RELAY_MIST_MAKER_PIN;
        case HUMIDIFIER_FAN: return RELAY_HUMIDIFIER_FAN_PIN;
        case FRUITING_EXHAUST_FAN: return RELAY_FRUITING_EXHAUST_PIN;
        case FRUITING_INTAKE_FAN: return RELAY_FRUITING_INTAKE_PIN;
        case SPAWNING_EXHAUST_FAN: return RELAY_SPAWNING_EXHAUST_PIN;
        case DEVICE_EXHAUST_FAN: return RELAY_DEVICE_EXHAUST_PIN;
        case FRUITING_LED: return RELAY_LED_LIGHTS_PIN;
        case RESERVED: return RELAY_RESERVED_PIN;
        default: return -1;
    }
}

void ActuatorManager::set(ActuatorType type, ActuatorState state) {
    int pin = getPin(type);
    if (pin == -1) return;
    
    // Active LOW: write LOW to turn ON
    digitalWrite(pin, (state == STATE_ON) ? LOW : HIGH);
    states[type] = (state == STATE_ON);
}

void ActuatorManager::turnOn(ActuatorType type) {
    set(type, STATE_ON);
}

void ActuatorManager::turnOff(ActuatorType type) {
    set(type, STATE_OFF);
}

void ActuatorManager::toggle(ActuatorType type) {
    bool currentState = getState(type);
    set(type, currentState ? STATE_OFF : STATE_ON);
}

bool ActuatorManager::getState(ActuatorType type) {
    return states[type];
}

void ActuatorManager::shutdownAll() {
    // Turn OFF all relays (write HIGH for active-low)
    digitalWrite(RELAY_MIST_MAKER_PIN, HIGH);
    digitalWrite(RELAY_HUMIDIFIER_FAN_PIN, HIGH);
    digitalWrite(RELAY_FRUITING_EXHAUST_PIN, HIGH);
    digitalWrite(RELAY_FRUITING_INTAKE_PIN, HIGH);
    digitalWrite(RELAY_SPAWNING_EXHAUST_PIN, HIGH);
    digitalWrite(RELAY_DEVICE_EXHAUST_PIN, HIGH);
    digitalWrite(RELAY_LED_LIGHTS_PIN, HIGH);
    digitalWrite(RELAY_RESERVED_PIN, HIGH);
    
    // Update state tracking
    for (int i = 0; i < 8; i++) {
        states[i] = false;
    }
    
    Serial.println(F("[SAFETY] All actuators OFF"));
}

bool ActuatorManager::executeCommand(const char* command) {
    // This function will be deprecated in favor of JSON commands in main.cpp
    // Keeping it for now to avoid breaking compilation.
    return false;
}
