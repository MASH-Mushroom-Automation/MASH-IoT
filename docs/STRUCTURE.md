MASH-IoT Final Folder Structure Guide

```
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
│   │       ├── templates/      # HTML Files
│   │       │   ├── dashboard.html
│   │       │   ├── settings.html
│   │       │   └── wifi_setup.html # *Use HTML_TEMPLATE from app.py here*
│   │       └── static/         # CSS/JS
│   │           ├── css/
│   │           └── js/
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