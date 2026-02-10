MASH-IoT Final Folder Structure Guide

```
MASH-IoT/
├── .github/                    # GitHub-specific configurations and CI/CD
│   ├── appmod/                 # Application modernization tools
│   │   └── appcat/             # Application categorization
│   └── copilot-instructions.md # AI assistant guidelines
├── .gitignore                 # Git ignore rules
├── .vscode/                   # VS Code workspace settings
│   ├── c_cpp_properties.json  # C/C++ properties for Arduino
│   ├── launch.json            # Debug launch configurations
│   └── settings.json          # VS Code settings
├── app.py                     # Legacy Flask app (reference)
├── arduino_firmware/          # Arduino Uno firmware for hardware control
│   ├── .github/               # Firmware-specific GitHub configs
│   │   └── appmod/            # App mod tools for firmware
│   ├── .gitignore             # Firmware-specific ignore rules
│   ├── .pio/                  # PlatformIO build artifacts
│   │   ├── build/             # Compiled binaries
│   │   └── libdeps/           # Library dependencies
│   ├── .vscode/               # Firmware VS Code settings
│   │   ├── c_cpp_properties.json # C++ properties
│   │   ├── extensions.json    # Required extensions
│   │   ├── launch.json        # Debug configs
│   │   └── settings.json      # Settings
│   ├── FIRMWARE.md            # Firmware documentation
│   ├── PINOUT.md              # Hardware pin mappings
│   ├── platformio.ini         # PlatformIO configuration
│   ├── README.md              # Firmware readme
│   ├── REFACTOR_SUMMARY.md    # Refactoring notes
│   └── src/                   # Source code
│       ├── actuators.cpp      # Relay control logic
│       ├── actuators.h        # Actuator headers
│       ├── config.h           # Configuration constants
│       ├── main.cpp           # Main firmware loop
│       ├── safety.cpp         # Watchdog safety system
│       ├── safety.h           # Safety headers
│       ├── sensors.cpp        # SCD41 sensor reading
│       ├── sensors.h          # Sensor headers
│       └── version.h          # Version information
├── assets/                    # Static assets for branding
│   ├── logo-123x89.png        # Small logo
│   ├── logo-246x177.png       # Large logo
│   ├── mash-intro.mp4         # Intro video
│   └── splash.png             # Splash screen
├── docs/                      # Documentation files
│   ├── ACTUATOR_CONTROL_BUGFIX.md # Bug fixes for actuators
│   ├── ACTUATOR_STATE_FIX.md  # Actuator state fixes
│   ├── AI_ARCHITECTURE_DIAGRAM.md # AI system diagram
│   ├── AI_DEPLOYMENT_CHECKLIST.md # AI deployment steps
│   ├── AI_IMPLEMENTATION_GUIDE.md # AI implementation guide
│   ├── AI_IMPLEMENTATION_SUMMARY.md # AI summary
│   ├── AI_QUICK_REFERENCE.md  # AI quick ref
│   ├── API.md                 # API documentation
│   ├── ARDUINO_CONNECTION.md  # Arduino connection guide
│   ├── BUG_FIX_INTRO_ACTUATOR_STATES.md # Bug intro
│   ├── CLOUD_INTEGRATION.md   # Cloud integration
│   ├── CONNECTION_FIX_SUMMARY.md # Connection fixes
│   ├── DEPLOYMENT_CHECKLIST.md # Deployment checklist
│   ├── FIXES_FINAL.md         # Final fixes
│   ├── GUI_UPDATE.md          # GUI updates
│   ├── HUMIDIFIER_CYCLE_FIX.md # Humidifier fixes
│   ├── IMPROVEMENTS_SUMMARY.md # Improvements
│   ├── LOADING_SCREEN_TROUBLESHOOTING.md # Loading issues
│   ├── MACHINE_LEARNING.md    # ML documentation
│   ├── MDNS_SETUP_GUIDE.md    # mDNS setup
│   ├── OSK_VISUAL_INDICATORS_FIX.md # OSK fixes
│   ├── OTA_STRATEGY.md        # OTA updates
│   ├── PASSIVE_FAN_INTEGRATION.md # Fan integration
│   ├── PERMISSIONS_FIX.md     # Permission fixes
│   ├── QUICKSTART.md          # Quick start guide
│   ├── RASPBERRY_PI_SETUP.md  # RPi setup
│   ├── SCHEMA.md              # Database schema
│   ├── SENSOR_INTEGRATION_FIX.md # Sensor fixes
│   ├── SETUP.md               # Setup guide
│   ├── SMART_AUTO_CONTROL_WARMUP_FIX.md # Auto control fixes
│   ├── STRUCTURE.md           # This file
│   ├── SYSTEM_IMPROVEMENTS_SUMMARY_2.md # More improvements
│   ├── SYSTEM_IMPROVEMENTS_SUMMARY.md # Improvements
│   ├── SYSTEM_SETUP_GUIDE.md  # System setup
│   ├── SYSTEM_UPDATES_SUMMARY.md # Updates
│   ├── SYSTEM_UPDATES.md      # System updates
│   ├── UPDATES.md             # General updates
│   ├── VERSIONING_IMPLEMENTATION_SUMMARY.md # Versioning
│   ├── WIFI_PROVISIONING_COMPLETE_IMPLEMENTATION.md # WiFi provisioning
│   ├── WIFI_PROVISIONING_IMPLEMENTATION_PLAN.md # WiFi plan
│   └── WIFI_SWITCHING_FEATURE.md # WiFi switching
├── README.md                  # Project readme
├── rpi_gateway/               # Raspberry Pi gateway application
│   ├── app/                   # Main application code
│   │   ├── cloud/             # Cloud connectivity modules
│   │   │   ├── backend_api.py # Backend API client
│   │   │   ├── firebase.py    # Firebase integration
│   │   │   ├── mqtt_client.py # MQTT client
│   │   │   └── sync.py        # Data synchronization
│   │   ├── core/              # Core business logic
│   │   │   ├── logic_engine.py # Automation engine
│   │   │   ├── passive_fan_controller.py # Fan control
│   │   │   ├── serial_comm.py # Serial communication
│   │   │   └── version.py     # Version management
│   │   ├── database/          # Database layer
│   │   │   ├── db_manager.py  # Database operations
│   │   │   └── models.py      # Data models
│   │   ├── __init__.py        # Package init
│   │   ├── main.py            # Application entry point
│   │   ├── utils/             # Utility functions
│   │   │   ├── device_activation.py # Device activation
│   │   │   ├── identity.py    # Device identity
│   │   │   ├── mdns_advertiser.py # mDNS advertising
│   │   │   ├── screen.py      # Screen management
│   │   │   ├── user_preferences.py # User prefs
│   │   │   └── wifi_manager.py # WiFi management
│   │   └── web/               # Web interface
│   │       ├── routes.py      # Flask routes
│   │       ├── static/        # Static web assets
│   │       │   ├── css/       # Stylesheets
│   │       │   └── js/        # JavaScript
│   │       └── templates/     # HTML templates
│   │           ├── ai_insights.html # AI insights page
│   │           ├── alerts.html # Alerts page
│   │           ├── base.html   # Base template
│   │           ├── controls.html # Controls page
│   │           ├── dashboard.html # Dashboard
│   │           ├── index.html  # Home page
│   │           ├── settings.html # Settings
│   │           ├── wifi_connecting.html # WiFi connecting
│   │           └── wifi_setup.html # WiFi setup
│   ├── config/                # Configuration files
│   │   ├── .env               # Environment variables
│   │   ├── .env.example       # Example env vars
│   │   ├── config.yaml        # YAML configuration
│   │   └── firebase_config.json # Firebase config
│   ├── FIREBASE_CHECKLIST.md  # Firebase checklist
│   ├── FIREBASE_INTEGRATION_GUIDE.md # Firebase guide
│   ├── FIREBASE_QUICK_START.md # Firebase quick start
│   ├── QUICK_REFERENCE.md     # Quick reference
│   ├── requirements.txt       # Python dependencies
│   ├── rpi_gateway/           # Data directory
│   │   └── data/              # Persistent data
│   │       ├── models/        # ML models
│   │       └── sensor_data.db # SQLite database
│   ├── scripts/               # Gateway scripts
│   └── test_improvements.py   # Test improvements
├── scripts/                   # Setup and utility scripts
│   ├── check_display_config.sh # Display config check
│   ├── configure_osk.sh       # On-screen keyboard config
│   ├── diagnose_connection.py # Connection diagnostics
│   ├── diagnose_networkmanager.sh # NetworkManager diag
│   ├── disable_onscreen_keyboard.sh # Disable OSK
│   ├── find_arduino.py        # Find Arduino device
│   ├── fix_networkmanager_permissions.sh # Fix NM perms
│   ├── fix_permissions.sh     # Fix permissions
│   ├── install_dependencies.sh # Install deps
│   ├── launch_kiosk.sh        # Launch kiosk mode
│   ├── README.md              # Scripts readme
│   ├── run.txt                # Run instructions
│   ├── run_kiosk.sh           # Run kiosk
│   ├── run_kiosk.txt          # Kiosk run instructions
│   ├── setup_domain.sh        # Domain setup
│   ├── setup_kiosk.sh         # Kiosk setup
│   ├── setup_mdns.sh          # mDNS setup
│   ├── setup_os.sh            # OS setup
│   ├── setup_splash.sh        # Splash screen setup
│   ├── test_arduino.py        # Test Arduino
│   ├── test_mdns.py           # Test mDNS
│   ├── update.sh              # Update script
│   └── zen.sh                 # Zen script
└── wifi_manager.py            # Legacy WiFi manager (reference)
```