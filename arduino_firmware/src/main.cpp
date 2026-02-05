// M.A.S.H. IoT - Arduino Main
// Two-layer architecture: Arduino reads sensors, RPi makes decisions
// Communication: JSON over USB Serial (9600 baud)

#include <Arduino.h>
#include <ArduinoJson.h>
#include "config.h"
#include "sensors.h"
#include "actuators.h"
#include "safety.h"

// ==================== GLOBAL OBJECTS ====================
SensorManager sensors;
ActuatorManager actuators;
SafetyWatchdog watchdog(WATCHDOG_TIMEOUT);

// ==================== JSON & SERIAL ====================
JsonDocument jsonSensorDoc;
JsonDocument jsonCommandDoc;

// ==================== FUNCTION PROTOTYPES ====================
void handleSerialCommands();
ActuatorType stringToActuatorType(const char* str);
ActuatorState stringToActuatorState(const char* str);


// ==================== TIMING ====================
unsigned long lastSensorRead = 0;
unsigned long lastWatchdogCheck = 0;

// ==================== SERIAL BUFFER ====================
char serialBuffer[128];
int bufferIndex = 0;

// ==================== SETUP ====================
void setup() {
    // Initialize serial communication
    Serial.begin(SERIAL_BAUD);
    while (!Serial) {
        ; // Wait for serial port to connect (needed for native USB)
    }
    
    Serial.println(F(""));
    Serial.println(F("========================================"));
    Serial.println(F("  M.A.S.H. IoT - Arduino Firmware v1.0"));
    Serial.println(F("  Mushroom Automation Smart Home"));
    Serial.println(F("========================================"));
    Serial.println(F(""));
    
    // Initialize actuators first (safety: all OFF)
    actuators.begin();
    
    // Initialize sensors
    Serial.println(F("[INIT] Initializing sensors..."));
    if (!sensors.begin()) {
        Serial.println(F("[ERROR] Sensor initialization failed!"));
        while (1) {
            delay(1000);
            Serial.println(F("[ERROR] Please check sensor wiring"));
        }
    }
    
    // Start watchdog
    watchdog.begin();
    
    Serial.println(F(""));
    Serial.println(F("[READY] System ready. Waiting for commands..."));
    Serial.println(F("[INFO] Send commands: FRUITING_FAN_ON, SPAWNING_MIST_OFF, etc."));
    Serial.println(F(""));
}

// ==================== MAIN LOOP ====================
void loop() {
    unsigned long currentMillis = millis();

    // ==================== TASK 1: HANDLE INCOMING COMMANDS ====================
    handleSerialCommands();
    
    // ==================== TASK 2: READ SENSORS & REPORT ====================
    if (currentMillis - lastSensorRead >= SENSOR_READ_INTERVAL) {
        lastSensorRead = currentMillis;
        
        // Read both sensors
        SensorReading fruiting = sensors.readSensor1();
        SensorReading spawning = sensors.readSensor2();
        
        // Create JSON output
        jsonSensorDoc.clear();
        
        // Fruiting room data
        JsonObject fruitingObj = jsonSensorDoc["fruiting"].to<JsonObject>();
        if (fruiting.isValid) {
            fruitingObj["temp"] = round(fruiting.temperature * 10) / 10.0;
            fruitingObj["humidity"] = round(fruiting.humidity * 10) / 10.0;
            fruitingObj["co2"] = fruiting.co2;
        } else {
            fruitingObj["error"] = "invalid_reading";
        }
        
        // Spawning room data
        JsonObject spawningObj = jsonSensorDoc["spawning"].to<JsonObject>();
        if (spawning.isValid) {
            spawningObj["temp"] = round(spawning.temperature * 10) / 10.0;
            spawningObj["humidity"] = round(spawning.humidity * 10) / 10.0;
            spawningObj["co2"] = spawning.co2;
        } else {
            spawningObj["error"] = "invalid_reading";
        }
        
        // Send JSON to RPi
        serializeJson(jsonSensorDoc, Serial);
        Serial.println();  // End with newline
    }
    
    // ==================== TASK 3: CHECK WATCHDOG ====================
    if (currentMillis - lastWatchdogCheck >= 1000) {
        lastWatchdogCheck = currentMillis;
        if (watchdog.checkTimeout()) {
            actuators.shutdownAll();
        }
    }
}

// ==================== COMMAND HANDLING ====================

void handleSerialCommands() {
    static int bufferPos = 0;

    while (Serial.available() > 0) {
        char incomingChar = Serial.read();
        
        // Update watchdog heartbeat on ANY serial data received
        watchdog.heartbeat();

        if (incomingChar == '\n' || incomingChar == '\r') {
            if (bufferPos > 0) {
                serialBuffer[bufferPos] = '\0'; // Null-terminate the string

                DeserializationError error = deserializeJson(jsonCommandDoc, serialBuffer);

                if (error) {
                    Serial.print(F("[ERROR] deserializeJson() failed: "));
                    Serial.println(error.c_str());
                } else {
                    // Check for keepalive/heartbeat messages (no actuator field)
                    if (jsonCommandDoc.containsKey("keepalive")) {
                        // Silently acknowledge keepalive (watchdog already updated by heartbeat())
                        // Serial.println(F("[KEEPALIVE] ACK")); // Uncomment for debugging
                    } else {
                        const char* actuatorStr = jsonCommandDoc["actuator"];
                        const char* stateStr = jsonCommandDoc["state"];

                        if (actuatorStr && stateStr) {
                            ActuatorType type = stringToActuatorType(actuatorStr);
                            ActuatorState state = stringToActuatorState(stateStr);

                            if (type != (ActuatorType)-1) {
                                actuators.set(type, state);
                                Serial.print(F("[CMD] Set "));
                                Serial.print(actuatorStr);
                                Serial.print(F(" to "));
                                Serial.println(stateStr);
                            } else {
                                Serial.print(F("[ERROR] Unknown actuator: "));
                                Serial.println(actuatorStr);
                            }
                        } else {
                            Serial.println(F("[ERROR] Invalid JSON command format. Missing 'actuator' or 'state'."));
                        }
                    }
                }
                
                // Clear the buffer for the next command
                bufferPos = 0; 
            }
        } else {
            if ((size_t)bufferPos < sizeof(serialBuffer) - 1) {
                serialBuffer[bufferPos++] = incomingChar;
            }
        }
    }
}

ActuatorType stringToActuatorType(const char* str) {
    if (strcmp(str, "MIST_MAKER") == 0) return MIST_MAKER;
    if (strcmp(str, "HUMIDIFIER_FAN") == 0) return HUMIDIFIER_FAN;
    if (strcmp(str, "FRUITING_EXHAUST_FAN") == 0) return FRUITING_EXHAUST_FAN;
    if (strcmp(str, "FRUITING_INTAKE_FAN") == 0) return FRUITING_INTAKE_FAN;
    if (strcmp(str, "SPAWNING_EXHAUST_FAN") == 0) return SPAWNING_EXHAUST_FAN;
    if (strcmp(str, "DEVICE_EXHAUST_FAN") == 0) return DEVICE_EXHAUST_FAN;
    if (strcmp(str, "FRUITING_LED") == 0) return FRUITING_LED;
    if (strcmp(str, "RESERVED") == 0) return RESERVED;
    return (ActuatorType)-1; // Invalid actuator
}

ActuatorState stringToActuatorState(const char* str) {
    if (strcmp(str, "ON") == 0) return STATE_ON;
    return STATE_OFF;
}

