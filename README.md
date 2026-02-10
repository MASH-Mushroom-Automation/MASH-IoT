
# M.A.S.H. IoT Repository

## 🚀 Quick Start

**First time setup on Raspberry Pi?** Follow our complete guide:
👉 **[Raspberry Pi Setup Guide](docs/RASPBERRY_PI_SETUP.md)**

**Need to fix script permissions?**
```bash
bash scripts/fix_permissions.sh
```

**Find your Arduino:**
```bash
python3 scripts/find_arduino.py
```

**Test connection:**
```bash
python3 scripts/test_arduino.py
```

---

## Repository Overview

**Repository Name:** MASH-IoT

**Tech Stack:**

- **Microcontroller (Arduino):** C++ (Hardware Interface)
- **Gateway (Raspberry Pi):** Python 3.9+
- **GUI:** Flask Web App (running locally in Chromium Kiosk Mode)
- **Database:** SQLite (Local) + Firebase (Cloud)

---

## Final Folder Structure

This structure integrates your old `utils` into a cleaner layout and reflects your tested WiFi provisioning modules.

```text
MASH-IoT/
├── arduino_firmware/           # THE HANDS
│   ├── src/
│   │   ├── main.cpp            # Loops: 1. Read Sensors 2. Listen for Serial cmds
│   │   ├── sensors.cpp         # SCD41 Logic (SoftWire + Wire)
│   │   ├── actuators.cpp       # Relay control (Fan, Mist, Light)
│   │   └── safety.cpp          # Watchdog: Turn off all relays if Serial disconnects
│   └── platformio.ini
│
├── rpi_gateway/                # THE BRAIN
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # Orchestrator: Starts Web Server + Serial Loop
│   │   │
│   │   ├── core/               # Core Logic
│   │   │   ├── serial_comm.py  # Talks to Arduino (sends commands, gets data)
│   │   │   ├── logic_engine.py # The "Brain": If Temp > 30 -> Fan ON
│   │   │   └── screen.py       # Turns HDMI on/off (Energy Saving)
│   │   │
│   │   ├── cloud/              # Connectivity
│   │   │   ├── firebase.py     # *Migrated from old repo*
│   │   │   └── sync.py         # Offline -> Online syncing logic
│   │   │
│   │   ├── database/
│   │   │   ├── db_manager.py   # *Migrated from old repo*
│   │   │   └── models.py       # SQL Alchemy or raw SQL schemas
│   │   │
│   │   ├── utils/              # *Heavily Migrated from old repo*
│   │   │   ├── wifi_manager.py # *NEW: Combined Hotspot + Connection logic (Tested)*
│   │   │   └── identity.py     # Device ID generation
│   │   │
│   │   └── web/                # The New GUI
│   │       ├── routes.py       # Flask Endpoints (Integrates logic from tested app.py)
│   │       ├── templates/      # HTML Files (Jinja2 Templates)
│   │       │   ├── dashboard.html
│   │       │   ├── settings.html
│   │       │   └── wifi_setup.html # *Use HTML_TEMPLATE from app.py here*
│   │       └── static/         # STATIC ASSETS (Served by Flask)
│   │           ├── css/        # Stylesheets (Tailwind output or custom.css)
│   │           ├── js/         # Client-side JavaScript
│   │           └── assets/     # Images, Icons, Fonts
│   │               ├── icons/  # SVG/PNG Icons (Fan, Temp, etc.)
│   │               ├── images/ # Logos, QR Code placeholder
│   │               └── fonts/  # Custom fonts (if offline)
│   │
│   ├── config/
│   │   ├── config.yaml         # Thresholds (Temp targets, etc.)
│   │   └── .env                # Secrets
│   │
│   └── requirements.txt
│
├── scripts/                    # Setup/Install scripts
│   ├── install_dependencies.sh
│   └── setup_kiosk.sh          # Auto-configures Chromium boot
│
└── README.md
```

---

## Detailed Functional Scopes

### A. Arduino (Microcontroller)

- **Calibration:**
	- Able to calibrate SCD41 sensors to standard (using `performForcedRecalibration` or autoCalibration).

- **Dual Sensor Reading:**
	- Able to read data from two SCD41 sensors simultaneously.
	- Implementation: 1 via Hardware I2C (Grove Hub), 1 via Software I2C (Pins 10/11).
	- Differentiation: Tag data as room: "fruiting" vs room: "spawning".

- **Anomaly Filtering (Edge Processing):**
	- Able to filter out anomalies in data gathering.
	- Logic: Filter sudden significant changes (spikes) that last only a short time (e.g., Temp 70+ for 1 sec then back to 23).
	- Method: Moving Average Buffer (size 10) or Median Filter.

- **Data Transmission:**
	- Able to send JSON-formatted data string to Raspberry Pi 3 Model B via USB Serial.

### B. Raspberry Pi (Gateway & Controller)

- **Data Ingestion:**
	- Able to receive and parse JSON data from Arduino Uno R3.

- **Local Storage (Offline Capability):**
	- Able to save every reading to a local SQLite database immediately.
	- Data must persist even if power is lost or internet is down.

- **Cloud Synchronization:**
	- Able to send aggregated sensor data to record in Cloud (Firebase).
	- Logic: Check for internet -> If connected, upload unsynced rows from SQLite -> Mark as synced.

- **Actuation Logic (The "Brain")**
	- Able to compare sensor readings against `config.yaml` thresholds.
	- Able to send command strings (e.g., `FAN_ON`) back to Arduino.

- **GUI Hosting:**
	- Able to host a local Web Server (Flask) accessible via `localhost:5000` (Kiosk) and `http://mash-device.local` (Network).

### C. GUI (Web Interface)

- **Flow:**
	- Onboarding: If no WiFi, show Hotspot setup screen.
	- WiFi Connection: User selects SSID and enters password.
	- QR Page: Display generated QR code for Mobile App pairing.
	- Dashboard: Live view of Fruiting vs. Spawning status.

---

## Development Phases (The "Repair" Job)

### Phase 1: The Hardware Foundation (Arduino)
- **Goal:** Arduino reads 2x SCD41s (using the Software I2C hack) and accepts Relay commands.
- **Test:** Open Serial Monitor. You should see: `{ "fruiting": { "co2": 800 }, "spawning": { "co2": 2000 } }`.
- **Test:** Type `FAN_ON` in Serial Monitor -> Relay clicks.

### Phase 2: The Gateway Core (RPi Python)
- **Goal:** Python script reads that Serial JSON and saves it to SQLite.
- **Migration:** Adapt `database_manager.py` to specifically store this JSON structure.

### Phase 3: The New Face (Web GUI)
- **Goal:** A Flask page shows the live data.
- **Task:** Create `dashboard.html` using Tailwind CSS (CDN or local).
- **Task:** Use HTMX or simple JS polling (`setInterval`) to fetch data from Python every 2 seconds. No complex WebSockets needed yet.

### Phase 4: Connectivity (The "Smart" Part)
- **Goal:** Connect to WiFi via GUI.
- **Migration:** Hook up `wifi_setup.html` forms to your existing `wifi.py` functions.
- **Goal:** Sync to Firebase.


---

## 5. Hardware Specifications & Bill of Materials

### A. Core Processing

| Component         | Model/Type                | Role                                      | Voltage      | Notes                                                                 |
|-------------------|---------------------------|--------------------------------------------|--------------|-----------------------------------------------------------------------|
| Gateway           | Raspberry Pi 3 Model B    | Master Controller, Web Server, DB Host     | 5V (Micro USB) | Logic Level: 3.3V (needs shifter for 5V sensors, but routed via Arduino). WiFi 2.4GHz, Bluetooth 4.1 |
| Microcontroller   | Arduino Uno R3            | Hardware Interface (Sensors/Relays), Safety Watchdog | 5V (USB/DC) | Communication: USB Serial (to RPi)                                    |

### B. Sensors (Environmental)

| Sensor           | Model/Type         | Qty | Protocol | Voltage      | Range (CO2) | Range (Temp) | Range (RH) | Wiring Strategy                                  |
|------------------|-------------------|-----|----------|--------------|-------------|--------------|------------|--------------------------------------------------|
| CO2/Temp/Humidity| Sensirion SCD41   | 2   | I2C (0x62)| 3.3V - 5V    | 400-5000 ppm| -10°C to 60°C| 0% to 100% | 1: HW I2C (A4/A5) via Grove Hub; 2: SW I2C (D10/D11) |

### C. Actuators (Control)

| Device           | Model/Type                | Role                        | Trigger      | Load Capacity      |
|------------------|--------------------------|-----------------------------|--------------|-------------------|
| Relay Module     | 8-Channel 5V Relay Module| Switch High Voltage AC Loads| Logic Low/High| 10A @ 250VAC      |
| Exhaust Fans     | 12V DC                   | Airflow                     | -            | -                 |
| Intake Fans      | 12V DC                   | Airflow                     | -            | -                 |
| Humidifier Fan   | 24V DC                   | Humidity Control            | -            | -                 |
| Humidifier       | 45V Mist Maker           | Humidity Control            | -            | -                 |
| Grow Lights      | 5V LED Strips            | Lighting                    | -            | -                 |

### D. Power & Connectivity Modules

- Grove I2C Hub: Passive Splitter (used for Sensor 1)
- Power Supplies:
		- 5V 2.5A+ Adapter for Raspberry Pi
		- 12V Adapter for Fans/Lights (if DC)
		- 12V 3A Adapter for Relay Power Supply
		- 9V for USB for Arduino
		- 48V Power supply for Mist

---

## 6. Cloud & Connectivity Configuration

### A. Firebase Configuration

- **Location:** `rpi_gateway/config/firebase_config.json`

### B. MQTT Configuration (HiveMQ)

- **Location:** `rpi_gateway/config/.env`
- Used for low-latency command/control if HTTP polling is too slow.

| Parameter         | Value                                                        |
|-------------------|--------------------------------------------------------------|
| Broker URL        | 290691cd2bcb4d7faf979db077890beb.s1.eu.hivemq.cloud          |
| TCP Port (TLS)    | 8883                                                         |
| Websocket Port    | 8884                                                         |
| Username          | mash_zen                                                     |
| Password          | zenGarden125                                                 |
| Permissions       | PUBLISH_SUBSCRIBE                                            |

**Connection Strings:**

- TLS MQTT: `tls://290691cd2bcb4d7faf979db077890beb.s1.eu.hivemq.cloud:8883`
- TLS Websocket: `wss://290691cd2bcb4d7faf979db077890beb.s1.eu.hivemq.cloud:8884/mqtt`