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
// Pin mappings match physical relay module IN1-IN8
#define RELAY_MIST_MAKER_PIN 2        // IN1: Mist Maker (Humidifier) 45V - Fruiting
#define RELAY_HUMIDIFIER_FAN_PIN 3    // IN2: Humidifier Fan 12V - Fruiting
#define RELAY_FRUITING_EXHAUST_PIN 4  // IN3: Exhaust Fan 24V - Fruiting
#define RELAY_FRUITING_INTAKE_PIN 5   // IN4: In-take Fan 12V - Fruiting
#define RELAY_SPAWNING_EXHAUST_PIN 6  // IN5: Exhaust Fan 12V - Spawning
#define RELAY_DEVICE_EXHAUST_PIN 7    // IN6: Exhaust Fan 12V - Device
#define RELAY_LED_LIGHTS_PIN 8        // IN7: LED Lights 5V - Fruiting
#define RELAY_RESERVED_PIN 9          // IN8: Reserved

// Relay states (Active LOW configuration)
#define RELAY_ON LOW
#define RELAY_OFF HIGH

// ==================== WATCHDOG CONFIGURATION ====================
#define WATCHDOG_TIMEOUT 600000  // 10 minutes (600 seconds) without serial = shutdown
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

// ==================== I2C CONFIGURATION ====================
// Hardware I2C pins (built-in Wire library)
#define HARDWARE_SDA_PIN A4
#define HARDWARE_SCL_PIN A5

// Software I2C pins (SoftWire library for second sensor)
#define SOFTWARE_SDA_PIN 10
#define SOFTWARE_SCL_PIN 11

#endif // CONFIG_H
