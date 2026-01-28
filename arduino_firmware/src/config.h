// M.A.S.H. IoT - Arduino Configuration
// Hardware pin definitions and constants

#ifndef CONFIG_H
#define CONFIG_H

// ==================== SERIAL COMMUNICATION ====================
#define SERIAL_BAUD 9600
#define JSON_BUFFER_SIZE 256

// ==================== SENSOR CONFIGURATION ====================
// SCD41 Sensor 1 (Fruiting Room) - Hardware I2C
#define SENSOR1_SDA_PIN A4  // Hardware I2C (via Grove Hub)
#define SENSOR1_SCL_PIN A5  // Hardware I2C
#define SENSOR1_ROOM "fruiting"

// SCD41 Sensor 2 (Spawning Room) - Software I2C
#define SENSOR2_SDA_PIN 10  // Digital pin for Software I2C
#define SENSOR2_SCL_PIN 11  // Digital pin for Software I2C
#define SENSOR2_ROOM "spawning"

// Sensor timing
#define SENSOR_READ_INTERVAL 5000  // Read every 5 seconds
#define SENSOR_WARMUP_TIME 2000    // Wait 2s for sensor initialization

// ==================== RELAY CONFIGURATION ====================
// Relay Module: 8-Channel, Active LOW (write LOW to activate)
#define RELAY_FRUITING_FAN 2
#define RELAY_FRUITING_MIST 3
#define RELAY_FRUITING_LIGHT 4
#define RELAY_SPAWNING_FAN 5
#define RELAY_SPAWNING_MIST 6
#define RELAY_SPAWNING_LIGHT 7
#define RELAY_SPARE_1 8
#define RELAY_SPARE_2 9

// Relay states (Active LOW configuration)
#define RELAY_ON LOW
#define RELAY_OFF HIGH

// ==================== WATCHDOG CONFIGURATION ====================
#define WATCHDOG_TIMEOUT 10000  // 10 seconds without serial = shutdown
#define WATCHDOG_CHECK_INTERVAL 1000  // Check every 1 second

// ==================== ANOMALY FILTERING ====================
#define TEMP_MIN -10.0    // Minimum valid temperature (°C)
#define TEMP_MAX 60.0     // Maximum valid temperature (°C)
#define HUMIDITY_MIN 0.0  // Minimum valid humidity (%)
#define HUMIDITY_MAX 100.0 // Maximum valid humidity (%)
#define CO2_MIN 400       // Minimum valid CO2 (ppm)
#define CO2_MAX 5000      // Maximum valid CO2 (ppm)

// Moving average filter size
#define FILTER_SIZE 5

// Pin Definitions
// -----------------

// Spawning Room
#define SPAWNING_EXHAUST_FAN_PIN 2

// Fruiting Room
#define FRUITING_EXHAUST_FAN_PIN 3
#define FRUITING_BLOWER_FAN_PIN 4
#define HUMIDIFIER_FAN_PIN 5
#define HUMIDIFIER_PIN 6
#define FRUITING_LED_PIN 7

// I2C Pins for SoftWire
#define SDA_PIN A4
#define SCL_PIN A5

#endif // CONFIG_H
