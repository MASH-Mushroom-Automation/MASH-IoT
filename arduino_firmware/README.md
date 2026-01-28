# M.A.S.H. IoT: Raspberry Pi Integration Guide

This guide provides instructions for setting up a Raspberry Pi to communicate with and control the M.A.S.H. IoT Arduino firmware.

## 1. System Architecture

The system uses a two-layer architecture:

-   **Raspberry Pi (The Brain)**: Responsible for all decision-making, logic, and timing. It reads sensor data from the Arduino and sends commands to control actuators.
-   **Arduino (The Muscle)**: Directly interfaces with sensors (SCD41) and actuators (relays). It continuously sends sensor data to the Pi and executes commands received over the serial port.

## 2. Prerequisites

Before you begin, ensure your Raspberry Pi is set up with:

-   Python 3
-   The `pyserial` library for serial communication.

You can install `pyserial` using pip:
```bash
pip3 install pyserial
```

## 3. Serial Communication Protocol

The Raspberry Pi and Arduino communicate over a USB serial connection.

-   **Port**: This will typically be `/dev/ttyACM0` or `/dev/ttyUSB0` on the Raspberry Pi.
-   **Baud Rate**: `9600`

### Sending Commands to Arduino

To control an actuator, send a JSON object to the Arduino with the following structure:

```json
{
  "actuator": "ACTUATOR_NAME",
  "state": "STATE"
}
```

-   `"actuator"`: The name of the device to control.
-   `"state"`: The desired state, either `"ON"` or `"OFF"`.

**Example:** To turn on the LED in the fruiting room, send the following JSON string, terminated by a newline character (`\\n`):

```json
{"actuator": "FRUITING_LED", "state": "ON"}\\n
```

### Receiving Data from Arduino

The Arduino will periodically send sensor data to the Raspberry Pi as a JSON object. The Pi should listen for this data, parse it, and use it for its control logic.

**Example Sensor Data:**

```json
{
  "fruiting": {
    "temp": 23.5,
    "humidity": 85.1,
    "co2": 850
  }
}
```
If a sensor reading is invalid, the JSON will indicate an error:
```json
{
  "fruiting": {
    "error": "invalid_reading"
  }
}
```

## 4. Actuator Reference

The following `"actuator"` names are supported:

| Chamber   | Actuator Name              | Description                                  |
| :-------- | :------------------------- | :------------------------------------------- |
| Spawning  | `SPAWNING_EXHAUST_FAN`     | Exhaust fan in the spawning room.            |
| Fruiting  | `FRUITING_EXHAUST_FAN`     | Main exhaust fan in the fruiting room.       |
| Fruiting  | `FRUITING_BLOWER_FAN`      | Blower fan for air circulation.              |
| Fruiting  | `HUMIDIFIER_FAN`           | Fan that pushes mist into the pipes.         |
| Fruiting  | `HUMIDIFIER`               | The ultrasonic mist maker itself.            |
| Fruiting  | `FRUITING_LED`             | LED lighting for the fruiting chamber.       |


## 5. Python Example Script

Here is a basic Python script to demonstrate sending a command and reading sensor data.

```python
import serial
import json
import time

# --- Configuration ---
# Check your device manager or run 'ls /dev/tty*' to find the correct port
ARDUINO_PORT = '/dev/ttyACM0' 
BAUD_RATE = 9600

# --- Establish Serial Connection ---
try:
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to Arduino on {ARDUINO_PORT}")
    # Allow time for Arduino to reset
    time.sleep(2) 
except serial.SerialException as e:
    print(f"Error: Could not open serial port {ARDUINO_PORT}. {e}")
    exit()

def send_command(actuator, state):
    """Sends a command to the Arduino."""
    if not ser.is_open:
        print("Error: Serial connection is not open.")
        return
        
    command = {"actuator": actuator, "state": state}
    json_command = json.dumps(command) + '\\n'
    
    try:
        ser.write(json_command.encode('utf-8'))
        print(f"Sent: {json_command.strip()}")
    except serial.SerialException as e:
        print(f"Error writing to serial port: {e}")

def read_sensor_data():
    """Reads and parses a line of sensor data from the Arduino."""
    if not ser.is_open or not ser.in_waiting:
        return None
        
    try:
        line = ser.readline().decode('utf-8').strip()
        if line:
            try:
                data = json.loads(line)
                return data
            except json.JSONDecodeError:
                print(f"Warning: Received non-JSON data: {line}")
                return None
    except Exception as e:
        print(f"Error reading from serial port: {e}")
    return None

# --- Main Execution ---
if __name__ == "__main__":
    try:
        # Example: Turn the fruiting room LED on for 5 seconds
        print("\\n--- Sending ON command ---")
        send_command("FRUITING_LED", "ON")
        time.sleep(5)
        
        print("\\n--- Sending OFF command ---")
        send_command("FRUITING_LED", "OFF")
        time.sleep(2)

        # Example: Continuously read sensor data
        print("\\n--- Listening for sensor data (Press Ctrl+C to stop) ---")
        while True:
            sensor_data = read_sensor_data()
            if sensor_data:
                print(f"Received data: {sensor_data}")
            time.sleep(1) # Don't flood the CPU

    except KeyboardInterrupt:
        print("\\nExiting program.")
    finally:
        if ser.is_open:
            ser.close()
            print("Serial port closed.")

```

This guide should provide a solid starting point for developing the control software on your Raspberry Pi.