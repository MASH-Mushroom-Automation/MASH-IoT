// M.A.S.H. IoT - Sensor Implementation
// Dual SCD41 sensor reading with anomaly filtering
// I2C timeout and bus recovery to prevent hangs

#include "sensors.h"
#include "config.h"

#include <Wire.h>
#include <SensirionI2CScd4x.h>

// ==================== SENSOR CONFIGURATION ====================
// USING TCA9548A I2C MULTIPLEXER FOR DUAL SENSORS
// - Single Hardware I2C bus with TCA9548A multiplexer
// - Configure multiplexer channels:
//   * Channel 0 (SD0): Fruiting SCD41
//   * Channel 1 (SD1): Spawning SCD41
//   * Channel 2-7: Available for expansion

#define USE_MULTIPLEXER
#define MUX_I2C_ADDRESS 0x70
#define MUX_CHANNEL_FRUITING 0
#define MUX_CHANNEL_SPAWNING 1

// Both sensors use Hardware I2C through multiplexer
SensirionI2CScd4x scd41_fruiting;
SensirionI2CScd4x scd41_spawning;

// Track consecutive I2C failures for recovery
static uint8_t i2cFailCount = 0;


// ==================== I2C BUS RECOVERY ====================

void recoverI2CBus() {
    /**
     * Attempt to recover a locked I2C bus by toggling SCL.
     * 
     * When SDA is stuck LOW (common with SCD41 sensors), the master
     * can clock SCL to force the slave to release the bus.
     * This is the standard I2C bus recovery procedure from the spec.
     */
    Serial.println(F("[I2C] Bus recovery: toggling SCL to release SDA"));
    
    // Disable Wire library temporarily
    Wire.end();
    
    // Configure SCL as output, SDA as input
    pinMode(HARDWARE_SCL_PIN, OUTPUT);
    pinMode(HARDWARE_SDA_PIN, INPUT_PULLUP);
    
    // Toggle SCL up to 9 times to unstick SDA
    for (int i = 0; i < 9; i++) {
        digitalWrite(HARDWARE_SCL_PIN, LOW);
        delayMicroseconds(5);
        digitalWrite(HARDWARE_SCL_PIN, HIGH);
        delayMicroseconds(5);
        
        // Check if SDA is released
        if (digitalRead(HARDWARE_SDA_PIN) == HIGH) {
            Serial.print(F("[I2C] SDA released after "));
            Serial.print(i + 1);
            Serial.println(F(" clock cycles"));
            break;
        }
    }
    
    // Generate STOP condition: SDA LOW->HIGH while SCL HIGH
    pinMode(HARDWARE_SDA_PIN, OUTPUT);
    digitalWrite(HARDWARE_SDA_PIN, LOW);
    delayMicroseconds(5);
    digitalWrite(HARDWARE_SCL_PIN, HIGH);
    delayMicroseconds(5);
    digitalWrite(HARDWARE_SDA_PIN, HIGH);
    delayMicroseconds(5);
    
    // Re-initialize Wire library
    Wire.begin();
    
    // Set I2C timeout again after re-init
#if defined(WIRE_HAS_TIMEOUT)
    Wire.setWireTimeout(I2C_TIMEOUT_MS * 1000, true);  // microseconds, reset on timeout
#endif
    
    delay(100);  // Allow bus to stabilize
    Serial.println(F("[I2C] Bus recovery complete"));
}


// ==================== MOVING AVERAGE FILTER ====================
MovingAverageFilter::MovingAverageFilter(int filterSize) {
    size = filterSize;
    buffer = new float[size];
    index = 0;
    count = 0;
    sum = 0.0;
    
    for (int i = 0; i < size; i++) {
        buffer[i] = 0.0;
    }
}

MovingAverageFilter::~MovingAverageFilter() {
    delete[] buffer;
}

float MovingAverageFilter::add(float value) {
    // Remove old value from sum
    sum -= buffer[index];
    
    // Add new value
    buffer[index] = value;
    sum += value;
    
    // Update circular buffer index
    index = (index + 1) % size;
    
    // Update count (until buffer is full)
    if (count < size) count++;
    
    return getAverage();
}

float MovingAverageFilter::getAverage() {
    if (count == 0) return 0.0;
    return sum / count;
}

void MovingAverageFilter::reset() {
    index = 0;
    count = 0;
    sum = 0.0;
    for (int i = 0; i < size; i++) {
        buffer[i] = 0.0;
    }
}

// ==================== SENSOR MANAGER ====================
SensorManager::SensorManager() {
    // Initialize filters for both sensors
    tempFilter1 = new MovingAverageFilter(FILTER_SIZE);
    humidityFilter1 = new MovingAverageFilter(FILTER_SIZE);
    tempFilter2 = new MovingAverageFilter(FILTER_SIZE);
    humidityFilter2 = new MovingAverageFilter(FILTER_SIZE);
    
    // Initialize last readings
    lastReading1 = {0, 0, 0, false, 0};
    lastReading2 = {0, 0, 0, false, 0};
}

SensorManager::~SensorManager() {
    delete tempFilter1;
    delete humidityFilter1;
    delete tempFilter2;
    delete humidityFilter2;
}

// ==================== MULTIPLEXER SUPPORT ====================
bool SensorManager::selectMuxChannel(uint8_t channel) {
    /**
     * Switch TCA9548A multiplexer to specified channel.
     * 
     * @param channel: Channel number (0-7)
     * @return true if successful, false if MUX not responding
     */
    if (channel > 7) return false;
    
    Wire.beginTransmission(MUX_I2C_ADDRESS);
    Wire.write(1 << channel);  // Set channel bit
    
    if (Wire.endTransmission() != 0) {
        Serial.println(F("[ERROR] Multiplexer not responding"));
        return false;
    }
    
    delay(5);  // Small delay for MUX switching
    return true;
}

bool SensorManager::detectMultiplexer() {
    /**
     * Check if TCA9548A multiplexer is present on I2C bus.
     * 
     * @return true if MUX detected
     */
    Wire.beginTransmission(MUX_I2C_ADDRESS);
    return (Wire.endTransmission() == 0);
}

bool SensorManager::begin() {

    Serial.println(F("[INIT] Checking for I2C multiplexer..."));
    
    Wire.begin();
    
    // Set I2C timeout to prevent bus lockup hangs
#if defined(WIRE_HAS_TIMEOUT)
    Wire.setWireTimeout(I2C_TIMEOUT_MS * 1000, true);  // microseconds, reset on timeout
    Serial.print(F("[I2C] Timeout set to "));
    Serial.print(I2C_TIMEOUT_MS);
    Serial.println(F("ms"));
#else
    Serial.println(F("[I2C] WARNING: Wire timeout not supported on this board"));
    Serial.println(F("[I2C] Hardware WDT will handle I2C lockup recovery"));
#endif
    
    if (detectMultiplexer()) {
        Serial.println(F("[OK] TCA9548A multiplexer detected!"));
        
        // Initialize Fruiting sensor on MUX channel 0
        if (!selectMuxChannel(MUX_CHANNEL_FRUITING)) {
            Serial.println(F("[ERROR] Failed to select MUX channel for Fruiting"));
            return false;
        }
        scd41_fruiting.begin(Wire);
        scd41_fruiting.stopPeriodicMeasurement();
        delay(100);
        uint16_t error1 = scd41_fruiting.startPeriodicMeasurement();
        
        // Initialize Spawning sensor (Channel 1)
        if (!selectMuxChannel(MUX_CHANNEL_SPAWNING)) {
            Serial.println(F("[ERROR] Failed to select MUX channel for Spawning"));
            return false;
        }
        scd41_spawning.begin(Wire);
        scd41_spawning.stopPeriodicMeasurement();
        delay(100);
        uint16_t error2 = scd41_spawning.startPeriodicMeasurement();
        
        if (error1 != 0 || error2 != 0) {
            Serial.println(F("[ERROR] Sensor initialization via MUX failed"));
            return false;
        }
        
        Serial.println(F("[OK] Both sensors initialized via multiplexer"));
        delay(SENSOR_WARMUP_TIME);
        return true;
    } else {
        Serial.println(F("[ERROR] TCA9548A multiplexer not detected!"));
        Serial.println(F("[ERROR] Check multiplexer wiring and address"));
        return false;
    }
}

bool SensorManager::validateReading(float temp, float humidity, uint16_t co2) {
    // Check if values are within valid ranges
    if (temp < TEMP_MIN || temp > TEMP_MAX) return false;
    if (humidity < HUMIDITY_MIN || humidity > HUMIDITY_MAX) return false;
    if (co2 < CO2_MIN || co2 > CO2_MAX) return false;
    
    return true;
}

SensorReading SensorManager::readSensor1() {
    SensorReading reading;
    reading.timestamp = millis();
    reading.isValid = false;
    
    // Select multiplexer channel for fruiting sensor
    if (!selectMuxChannel(MUX_CHANNEL_FRUITING)) {
        i2cFailCount++;
        if (i2cFailCount >= I2C_RECOVERY_RETRIES) {
            recoverI2CBus();
            i2cFailCount = 0;
        }
        return lastReading1;
    }
    
    uint16_t co2_raw;
    float temp_raw, humidity_raw;
    
    uint16_t error = scd41_fruiting.readMeasurement(co2_raw, temp_raw, humidity_raw);
    
    // Check for I2C timeout (Wire library returns error on timeout)
#if defined(WIRE_HAS_TIMEOUT)
    if (Wire.getWireTimeoutFlag()) {
        Wire.clearWireTimeoutFlag();
        Serial.println(F("[I2C] Timeout reading fruiting sensor"));
        i2cFailCount++;
        if (i2cFailCount >= I2C_RECOVERY_RETRIES) {
            recoverI2CBus();
            i2cFailCount = 0;
        }
        return lastReading1;
    }
#endif
    
    if (error != 0 || co2_raw == 0) {
        // Return last valid reading if current read fails
        return lastReading1;
    }
    
    // Validate raw reading
    if (!validateReading(temp_raw, humidity_raw, co2_raw)) {
        Serial.println(F("[WARNING] Fruiting sensor out of range"));
        return lastReading1;
    }
    
    // Successful read - reset failure counter
    i2cFailCount = 0;
    
    // Apply moving average filter
    reading.temperature = tempFilter1->add(temp_raw);
    reading.humidity = humidityFilter1->add(humidity_raw);
    reading.co2 = co2_raw;  // CO2 doesn't need as much filtering
    reading.isValid = true;
    
    // Update last valid reading
    lastReading1 = reading;
    
    return reading;
}

SensorReading SensorManager::readSensor2() {
    SensorReading reading;
    reading.timestamp = millis();
    reading.isValid = false;
    
    // Select multiplexer channel for spawning sensor
    if (!selectMuxChannel(MUX_CHANNEL_SPAWNING)) {
        i2cFailCount++;
        if (i2cFailCount >= I2C_RECOVERY_RETRIES) {
            recoverI2CBus();
            i2cFailCount = 0;
        }
        return lastReading2;
    }
    
    uint16_t co2_raw;
    float temp_raw, humidity_raw;
    
    uint16_t error = scd41_spawning.readMeasurement(co2_raw, temp_raw, humidity_raw);
    
    // Check for I2C timeout
#if defined(WIRE_HAS_TIMEOUT)
    if (Wire.getWireTimeoutFlag()) {
        Wire.clearWireTimeoutFlag();
        Serial.println(F("[I2C] Timeout reading spawning sensor"));
        i2cFailCount++;
        if (i2cFailCount >= I2C_RECOVERY_RETRIES) {
            recoverI2CBus();
            i2cFailCount = 0;
        }
        return lastReading2;
    }
#endif
    
    if (error != 0 || co2_raw == 0) {
        // Return last valid reading if current read fails
        return lastReading2;
    }
    
    // Validate raw reading
    if (!validateReading(temp_raw, humidity_raw, co2_raw)) {
        Serial.println(F("[WARNING] Spawning sensor out of range"));
        return lastReading2;
    }
    
    // Successful read - reset failure counter
    i2cFailCount = 0;
    
    // Apply moving average filter
    reading.temperature = tempFilter2->add(temp_raw);
    reading.humidity = humidityFilter2->add(humidity_raw);
    reading.co2 = co2_raw;
    reading.isValid = true;
    
    // Update last valid reading
    lastReading2 = reading;
    
    return reading;
}

void SensorManager::printReading(const char* room, SensorReading reading) {
    if (!reading.isValid) {
        Serial.print(F("["));
        Serial.print(room);
        Serial.println(F("] Invalid reading"));
        return;
    }
    
    Serial.print(F("["));
    Serial.print(room);
    Serial.print(F("] T:"));
    Serial.print(reading.temperature, 1);
    Serial.print(F(" H:"));
    Serial.print(reading.humidity, 1);
    Serial.print(F("% CO2:"));
    Serial.print(reading.co2);
    Serial.println(F("ppm"));
}