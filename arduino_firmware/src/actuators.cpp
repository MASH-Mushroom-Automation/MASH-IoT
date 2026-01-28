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
    pinMode(SPAWNING_EXHAUST_FAN_PIN, OUTPUT);
    pinMode(FRUITING_EXHAUST_FAN_PIN, OUTPUT);
    pinMode(FRUITING_BLOWER_FAN_PIN, OUTPUT);
    pinMode(HUMIDIFIER_FAN_PIN, OUTPUT);
    pinMode(HUMIDIFIER_PIN, OUTPUT);
    pinMode(FRUITING_LED_PIN, OUTPUT);

    // Turn all relays OFF (write HIGH for active-low)
    shutdownAll();
    
    Serial.println(F("[OK] Actuators initialized (all OFF)"));
}

int ActuatorManager::getPin(ActuatorType type) {
    switch (type) {
        case SPAWNING_EXHAUST_FAN: return SPAWNING_EXHAUST_FAN_PIN;
        case FRUITING_EXHAUST_FAN: return FRUITING_EXHAUST_FAN_PIN;
        case FRUITING_BLOWER_FAN: return FRUITING_BLOWER_FAN_PIN;
        case HUMIDIFIER_FAN: return HUMIDIFIER_FAN_PIN;
        case HUMIDIFIER: return HUMIDIFIER_PIN;
        case FRUITING_LED: return FRUITING_LED_PIN;
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
    digitalWrite(SPAWNING_EXHAUST_FAN_PIN, HIGH);
    digitalWrite(FRUITING_EXHAUST_FAN_PIN, HIGH);
    digitalWrite(FRUITING_BLOWER_FAN_PIN, HIGH);
    digitalWrite(HUMIDIFIER_FAN_PIN, HIGH);
    digitalWrite(HUMIDIFIER_PIN, HIGH);
    digitalWrite(FRUITING_LED_PIN, HIGH);
    
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
