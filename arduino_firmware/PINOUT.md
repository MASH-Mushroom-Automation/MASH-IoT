# Arduino Mega Pinout for M.A.S.H. IoT Firmware

This document lists the pin assignments for sensors and actuators used in the M.A.S.H. IoT Arduino Mega setup.

## Pin Assignments

| Device                | Arduino Mega Pin |
|-----------------------|------------------|
| SCD41 Sensor 1 (I2C, via Multiplexer)  | Multiplexer Channel 1 (SDA: 20, SCL: 21) |
| SCD41 Sensor 2 (I2C, via Multiplexer)  | Multiplexer Channel 2 (SDA: 20, SCL: 21) |
| Multiplexer Control   | S0: 30, S1: 31, S2: 32, S3: 33           |
| Relay 1 (Spawning Exhaust Fan)   | 22 |
| Relay 2 (Fruiting Exhaust Fan)   | 23 |
| Relay 3 (Fruiting Blower Fan)    | 24 |
| Relay 4 (Humidifier Fan)         | 25 |
| Relay 5 (Humidifier)             | 26 |
| Relay 6 (Fruiting LED)           | 27 |
| Relay 7 (Unused/Expansion)       | 28 |
| Relay 8 (Unused/Expansion)       | 29 |

- **I2C Sensors**: SCD41 sensors are connected via a multiplexer (e.g., TCA9548A) sharing the I2C bus (SDA: 20, SCL: 21).
- **Multiplexer Control Pins**: S0-S3 are used to select the active channel for each sensor.
- **Relays**: Each relay channel is connected to a dedicated digital pin.

## Notes
- Double-check wiring before powering the board.
- Unused relay channels can be repurposed for future expansion.
- If you change pin assignments in code, update this document accordingly.
