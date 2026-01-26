// M.A.S.H. IoT - Sensor Implementation
// Dual SCD41 sensor reading with anomaly filtering

#include "sensors.h"
#include "config.h"
#include <Wire.h>
#include <SoftWire.h>
#include <SensirionI2CScd4x.h>

// Hardware I2C sensor (Fruiting Room)
SensirionI2CScd4x scd41_hw;

// Software I2C sensor (Spawning Room)
SoftWire softWire(SENSOR2_SDA_PIN, SENSOR2_SCL_PIN);
SensirionI2CScd4x scd41_sw(softWire);

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

bool SensorManager::begin() {
    // Initialize Hardware I2C
    Wire.begin();
    scd41_hw.begin(Wire);
    
    // Initialize Software I2C
    softWire.begin();
    scd41_sw.begin(softWire);
    
    // Stop potentially running measurements
    scd41_hw.stopPeriodicMeasurement();
    scd41_sw.stopPeriodicMeasurement();
    
    delay(100);
    
    // Start periodic measurements
    uint16_t error1 = scd41_hw.startPeriodicMeasurement();
    uint16_t error2 = scd41_sw.startPeriodicMeasurement();
    
    if (error1 != 0) {
        Serial.println(F("[ERROR] Failed to start sensor 1 (fruiting)"));
        return false;
    }
    
    if (error2 != 0) {
        Serial.println(F("[ERROR] Failed to start sensor 2 (spawning)"));
        return false;
    }
    
    Serial.println(F("[OK] Both sensors initialized"));
    
    // Wait for sensors to warm up
    delay(SENSOR_WARMUP_TIME);
    
    return true;
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
    
    uint16_t co2_raw;
    float temp_raw, humidity_raw;
    
    uint16_t error = scd41_hw.readMeasurement(co2_raw, temp_raw, humidity_raw);
    
    if (error != 0 || co2_raw == 0) {
        // Return last valid reading if current read fails
        return lastReading1;
    }
    
    // Validate raw reading
    if (!validateReading(temp_raw, humidity_raw, co2_raw)) {
        Serial.println(F("[WARNING] Sensor 1 out of range"));
        return lastReading1;
    }
    
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
    
    uint16_t co2_raw;
    float temp_raw, humidity_raw;
    
    uint16_t error = scd41_sw.readMeasurement(co2_raw, temp_raw, humidity_raw);
    
    if (error != 0 || co2_raw == 0) {
        // Return last valid reading if current read fails
        return lastReading2;
    }
    
    // Validate raw reading
    if (!validateReading(temp_raw, humidity_raw, co2_raw)) {
        Serial.println(F("[WARNING] Sensor 2 out of range"));
        return lastReading2;
    }
    
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
    Serial.print(F("°C H:"));
    Serial.print(reading.humidity, 1);
    Serial.print(F("% CO2:"));
    Serial.print(reading.co2);
    Serial.println(F("ppm"));
}
