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
    pinMode(RELAY_FRUITING_FAN, OUTPUT);
    pinMode(RELAY_FRUITING_MIST, OUTPUT);
    pinMode(RELAY_FRUITING_LIGHT, OUTPUT);
    pinMode(RELAY_SPAWNING_FAN, OUTPUT);
    pinMode(RELAY_SPAWNING_MIST, OUTPUT);
    pinMode(RELAY_SPAWNING_LIGHT, OUTPUT);
    pinMode(RELAY_SPARE_1, OUTPUT);
    pinMode(RELAY_SPARE_2, OUTPUT);
    
    // Turn all relays OFF (write HIGH for active-low)
    shutdownAll();
    
    Serial.println(F("[OK] Actuators initialized (all OFF)"));
}

int ActuatorManager::getPin(ActuatorType type) {
    switch (type) {
        case FRUITING_FAN: return RELAY_FRUITING_FAN;
        case FRUITING_MIST: return RELAY_FRUITING_MIST;
        case FRUITING_LIGHT: return RELAY_FRUITING_LIGHT;
        case SPAWNING_FAN: return RELAY_SPAWNING_FAN;
        case SPAWNING_MIST: return RELAY_SPAWNING_MIST;
        case SPAWNING_LIGHT: return RELAY_SPAWNING_LIGHT;
        default: return -1;
    }
}

void ActuatorManager::set(ActuatorType type, ActuatorState state) {
    int pin = getPin(type);
    if (pin == -1) return;
    
    // Active LOW: write LOW to turn ON
    digitalWrite(pin, (state == STATE_ON) ? RELAY_ON : RELAY_OFF);
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
    digitalWrite(RELAY_FRUITING_FAN, RELAY_OFF);
    digitalWrite(RELAY_FRUITING_MIST, RELAY_OFF);
    digitalWrite(RELAY_FRUITING_LIGHT, RELAY_OFF);
    digitalWrite(RELAY_SPAWNING_FAN, RELAY_OFF);
    digitalWrite(RELAY_SPAWNING_MIST, RELAY_OFF);
    digitalWrite(RELAY_SPAWNING_LIGHT, RELAY_OFF);
    digitalWrite(RELAY_SPARE_1, RELAY_OFF);
    digitalWrite(RELAY_SPARE_2, RELAY_OFF);
    
    // Update state tracking
    for (int i = 0; i < 8; i++) {
        states[i] = false;
    }
    
    Serial.println(F("[SAFETY] All actuators OFF"));
}

bool ActuatorManager::executeCommand(const char* command) {
    // Command format: "FRUITING_FAN_ON", "SPAWNING_MIST_OFF", etc.
    
    if (strcmp(command, "FRUITING_FAN_ON") == 0) {
        turnOn(FRUITING_FAN);
        Serial.println(F("[CMD] Fruiting Fan ON"));
        return true;
    }
    else if (strcmp(command, "FRUITING_FAN_OFF") == 0) {
        turnOff(FRUITING_FAN);
        Serial.println(F("[CMD] Fruiting Fan OFF"));
        return true;
    }
    else if (strcmp(command, "FRUITING_MIST_ON") == 0) {
        turnOn(FRUITING_MIST);
        Serial.println(F("[CMD] Fruiting Mist ON"));
        return true;
    }
    else if (strcmp(command, "FRUITING_MIST_OFF") == 0) {
        turnOff(FRUITING_MIST);
        Serial.println(F("[CMD] Fruiting Mist OFF"));
        return true;
    }
    else if (strcmp(command, "FRUITING_LIGHT_ON") == 0) {
        turnOn(FRUITING_LIGHT);
        Serial.println(F("[CMD] Fruiting Light ON"));
        return true;
    }
    else if (strcmp(command, "FRUITING_LIGHT_OFF") == 0) {
        turnOff(FRUITING_LIGHT);
        Serial.println(F("[CMD] Fruiting Light OFF"));
        return true;
    }
    else if (strcmp(command, "SPAWNING_FAN_ON") == 0) {
        turnOn(SPAWNING_FAN);
        Serial.println(F("[CMD] Spawning Fan ON"));
        return true;
    }
    else if (strcmp(command, "SPAWNING_FAN_OFF") == 0) {
        turnOff(SPAWNING_FAN);
        Serial.println(F("[CMD] Spawning Fan OFF"));
        return true;
    }
    else if (strcmp(command, "SPAWNING_MIST_ON") == 0) {
        turnOn(SPAWNING_MIST);
        Serial.println(F("[CMD] Spawning Mist ON"));
        return true;
    }
    else if (strcmp(command, "SPAWNING_MIST_OFF") == 0) {
        turnOff(SPAWNING_MIST);
        Serial.println(F("[CMD] Spawning Mist OFF"));
        return true;
    }
    else if (strcmp(command, "SPAWNING_LIGHT_ON") == 0) {
        turnOn(SPAWNING_LIGHT);
        Serial.println(F("[CMD] Spawning Light ON"));
        return true;
    }
    else if (strcmp(command, "SPAWNING_LIGHT_OFF") == 0) {
        turnOff(SPAWNING_LIGHT);
        Serial.println(F("[CMD] Spawning Light OFF"));
        return true;
    }
    else if (strcmp(command, "ALL_OFF") == 0) {
        shutdownAll();
        return true;
    }
    
    // Unknown command
    Serial.print(F("[ERROR] Unknown command: "));
    Serial.println(command);
    return false;
}
