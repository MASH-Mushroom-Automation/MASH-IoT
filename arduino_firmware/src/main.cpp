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
    
    // ==================== TASK 1: READ SENSORS ====================
    if (currentMillis - lastSensorRead >= SENSOR_READ_INTERVAL) {
        lastSensorRead = currentMillis;
        
        // Read both sensors
        SensorReading fruiting = sensors.readSensor1();
        SensorReading spawning = sensors.readSensor2();
        
        // Create JSON output
        StaticJsonDocument<JSON_BUFFER_SIZE> doc;
        
        // Fruiting room data
        JsonObject fruitingObj = doc.createNestedObject("fruiting");
        if (fruiting.isValid) {
            fruitingObj["temp"] = round(fruiting.temperature * 10) / 10.0;
            fruitingObj["humidity"] = round(fruiting.humidity * 10) / 10.0;
            fruitingObj["co2"] = fruiting.co2;
        } else {
            fruitingObj["error"] = "invalid_reading";
        }
        
        // Spawning room data
        JsonObject spawningObj = doc.createNestedObject("spawning");
        if (spawning.isValid) {
            spawningObj["temp"] = round(spawning.temperature * 10) / 10.0;
            spawningObj["humidity"] = round(spawning.humidity * 10) / 10.0;
            spawningObj["co2"] = spawning.co2;
        } else {
            spawningObj["error"] = "invalid_reading";
        }
        
        // Send JSON to RPi
        serializeJson(doc, Serial);
        Serial.println();  // End with newline
    }
    
    // ==================== TASK 2: LISTEN FOR COMMANDS ====================
    while (Serial.available() > 0) {
        char c = Serial.read();
        
        // Update watchdog (received data = RPi is alive)
        watchdog.heartbeat();
        
        if (c == '\n' || c == '\r') {
            // End of command
            if (bufferIndex > 0) {
                serialBuffer[bufferIndex] = '\0';  // Null terminate
                actuators.executeCommand(serialBuffer);
                bufferIndex = 0;  // Reset buffer
            }
        } else if (bufferIndex < 127) {
            serialBuffer[bufferIndex++] = c;
        }
    }
    
    // ==================== TASK 3: WATCHDOG CHECK ====================
    if (currentMillis - lastWatchdogCheck >= WATCHDOG_CHECK_INTERVAL) {
        lastWatchdogCheck = currentMillis;
        
        if (watchdog.checkTimeout()) {
            // SAFETY TRIGGERED: No serial communication
            actuators.shutdownAll();
            Serial.println(F("[EMERGENCY] Watchdog triggered - All systems OFF"));
        }
    }
}

