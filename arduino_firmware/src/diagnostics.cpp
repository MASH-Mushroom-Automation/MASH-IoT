// M.A.S.H. IoT - Sensor Diagnostics
// Upload this sketch to debug sensor connection issues
// Open Serial Monitor at 9600 baud to see detailed diagnostics

#include <Arduino.h>
#include <Wire.h>
#include <SoftWire.h>
#include <SensirionI2CScd4x.h>

// Multiplexer address
#define MUX_I2C_ADDRESS 0x70

// Software I2C pins
#define SOFTWARE_SDA_PIN 10
#define SOFTWARE_SCL_PIN 11

SensirionI2CScd4x scd41_hw;  // Hardware I2C sensor
SoftWire softWire(SOFTWARE_SDA_PIN, SOFTWARE_SCL_PIN);
SensirionI2CScd4x scd41_sw;  // Software I2C sensor

void setup() {
    Serial.begin(9600);
    while (!Serial) {
        ; // Wait for serial port
    }
    
    Serial.println(F("\n\n"));
    Serial.println(F("========================================"));
    Serial.println(F("  M.A.S.H. IoT - Sensor Diagnostics"));
    Serial.println(F("========================================"));
    Serial.println(F(""));
    
    // Test 1: Check for multiplexer
    Serial.println(F("[TEST 1] Checking for TCA9548A multiplexer..."));
    Wire.begin();
    
    Wire.beginTransmission(MUX_I2C_ADDRESS);
    uint8_t mux_error = Wire.endTransmission();
    
    if (mux_error == 0) {
        Serial.println(F("  \u2713 MULTIPLEXER DETECTED at 0x70"));
        Serial.println(F("    Will use Hardware I2C for both sensors"));
        testWithMultiplexer();
    } else {
        Serial.print(F("  \u2717 MULTIPLEXER NOT FOUND (error code: "));
        Serial.print(mux_error);
        Serial.println(F(")"));
        Serial.println(F("    Falling back to SoftWire mode"));
        testWithoutMultiplexer();
    }
    
    Serial.println(F("\n========================================"));
    Serial.println(F("  Diagnostics Complete"));
    Serial.println(F("========================================"));
    Serial.println(F(""));
}

void loop() {
    // Keep running diagnostics every 10 seconds
    delay(10000);
    
    Serial.println(F("\n[RETEST] Running diagnostics again..."));
    
    Wire.beginTransmission(MUX_I2C_ADDRESS);
    if (Wire.endTransmission() == 0) {
        testWithMultiplexer();
    } else {
        testWithoutMultiplexer();
    }
}

void testWithMultiplexer() {
    Serial.println(F("\n[TEST 2] Testing sensors via multiplexer..."));
    
    // Test Fruiting sensor on Channel 0
    Serial.println(F("\n[TEST 2A] Fruiting Room Sensor (MUX Channel 0):"));
    selectMuxChannel(0);
    testSensorOnHardwareI2C("Fruiting");
    
    delay(1000);
    
    // Test Spawning sensor on Channel 1
    Serial.println(F("\n[TEST 2B] Spawning Room Sensor (MUX Channel 1):"));
    selectMuxChannel(1);
    testSensorOnHardwareI2C("Spawning");
}

void testWithoutMultiplexer() {
    Serial.println(F("\n[TEST 2] Testing sensors without multiplexer..."));
    
    // Test Hardware I2C
    Serial.println(F("\n[TEST 2A] Fruiting Room Sensor (Hardware I2C):"));
    testSensorOnHardwareI2C("Fruiting");
    
    delay(1000);
    
    // Test Software I2C
    Serial.println(F("\n[TEST 2B] Spawning Room Sensor (Software I2C):"));
    testSensorOnSoftwareI2C("Spawning");
}

void selectMuxChannel(uint8_t channel) {
    if (channel > 7) return;
    
    Wire.beginTransmission(MUX_I2C_ADDRESS);
    Wire.write(1 << channel);
    Wire.endTransmission();
    delay(5);
}

void testSensorOnHardwareI2C(const char* room) {
    scd41_hw.begin(Wire);
    
    // Stop any running measurement
    scd41_hw.stopPeriodicMeasurement();
    delay(500);
    
    // Start measurement
    uint16_t error = scd41_hw.startPeriodicMeasurement();
    
    if (error != 0) {
        Serial.print(F("  \u2717 START FAILED - Error: 0x"));
        Serial.println(error, HEX);
        return;
    }
    
    Serial.println(F("  \u2713 Sensor started, waiting 5 seconds for first reading..."));
    delay(5000);
    
    // Read measurement
    uint16_t co2;
    float temp, humidity;
    
    error = scd41_hw.readMeasurement(co2, temp, humidity);
    
    if (error != 0) {
        Serial.print(F("  \u2717 READ FAILED - Error: 0x"));
        Serial.println(error, HEX);
    } else if (co2 == 0) {
        Serial.println(F("  \u26a0 WARNING: CO2 = 0 (sensor still warming up)"));
    } else {
        Serial.println(F("  \u2713 SENSOR WORKING!"));
        Serial.print(F("    Temperature: "));
        Serial.print(temp, 1);
        Serial.println(F("\u00b0C"));
        
        Serial.print(F("    Humidity:    "));
        Serial.print(humidity, 1);
        Serial.println(F("%"));
        
        Serial.print(F("    CO2:         "));
        Serial.print(co2);
        Serial.println(F(" ppm"));
    }
}

void testSensorOnSoftwareI2C(const char* room) {
    softWire.begin();
    scd41_sw.begin(softWire);
    
    // Stop any running measurement
    scd41_sw.stopPeriodicMeasurement();
    delay(500);
    
    // Start measurement
    uint16_t error = scd41_sw.startPeriodicMeasurement();
    
    if (error != 0) {
        Serial.print(F("  \u2717 START FAILED - Error: 0x"));
        Serial.println(error, HEX);
        return;
    }
    
    Serial.println(F("  \u2713 Sensor started, waiting 5 seconds for first reading..."));
    delay(5000);
    
    // Read measurement
    uint16_t co2;
    float temp, humidity;
    
    error = scd41_sw.readMeasurement(co2, temp, humidity);
    
    if (error != 0) {
        Serial.print(F("  \u2717 READ FAILED - Error: 0x"));
        Serial.println(error, HEX);
    } else if (co2 == 0) {
        Serial.println(F("  \u26a0 WARNING: CO2 = 0 (sensor still warming up)"));
    } else {
        Serial.println(F("  \u2713 SENSOR WORKING!"));
        Serial.print(F("    Temperature: "));
        Serial.print(temp, 1);
        Serial.println(F("\u00b0C"));
        
        Serial.print(F("    Humidity:    "));
        Serial.print(humidity, 1);
        Serial.println(F("%"));
        
        Serial.print(F("    CO2:         "));
        Serial.print(co2);
        Serial.println(F(" ppm"));
    }
}
