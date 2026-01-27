// M.A.S.H. IoT - Sensor Interface
// Dual SCD41 sensor management with hardware and software I2C

#ifndef SENSORS_H
#define SENSORS_H

#include <Arduino.h>

// Sensor data structure
struct SensorReading {
    float temperature;
    float humidity;
    uint16_t co2;
    bool isValid;
    unsigned long timestamp;
};

// Moving average filter for anomaly detection
class MovingAverageFilter {
private:
    float* buffer;
    int size;
    int index;
    int count;
    float sum;

public:
    MovingAverageFilter(int filterSize);
    ~MovingAverageFilter();
    float add(float value);
    float getAverage();
    void reset();
};

// Sensor manager class
class SensorManager {
private:
    // Filters for anomaly detection
    MovingAverageFilter* tempFilter1;
    MovingAverageFilter* humidityFilter1;
    // MovingAverageFilter* tempFilter2;
    // MovingAverageFilter* humidityFilter2;
    
    // Last valid readings
    SensorReading lastReading1;
    // SensorReading lastReading2;
    
    // Validation helper
    bool validateReading(float temp, float humidity, uint16_t co2);

public:
    SensorManager();
    ~SensorManager();
    
    // Initialize sensors
    bool begin();
    
    // Read from sensors
    SensorReading readSensor1(); // Fruiting room (Hardware I2C)
    // SensorReading readSensor2(); // Spawning room (Software I2C)
    
    // Get filtered readings
    void printReading(const char* room, SensorReading reading);
};

#endif // SENSORS_H
