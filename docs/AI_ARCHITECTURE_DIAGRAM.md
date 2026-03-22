# 🏗️ AI System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MASH IoT - AI Control System                         │
│                     Intelligent Humidity Management                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            SENSOR LAYER                                     │
└─────────────────────────────────────────────────────────────────────────────┘

          ┌────────────┐      ┌────────────┐      ┌────────────┐
          │  SCD41     │      │  SCD41     │      │  SCD41     │
          │  Sensor    │      │  Sensor    │      │  Sensor    │
          └──────┬─────┘      └──────┬─────┘      └──────┬─────┘
                 │                   │                   │
                 └───────────────────┴───────────────────┘
                                     │
                         ┌───────────▼───────────┐
                         │   Arduino Uno R3      │
                         │   (Serial: 9600 baud) │
                         └───────────┬───────────┘
                                     │ USB
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RASPBERRY PI GATEWAY                                │
└─────────────────────────────────────────────────────────────────────────────┘

                         ┌───────────────────────┐
                         │   serial_comm.py      │
                         │   (JSON Parser)       │
                         └───────────┬───────────┘
                                     │
                         ┌───────────▼───────────┐
                         │   orchestrator.py     │
                         │   (Main Loop: 5s)     │
                         └───────────┬───────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI DECISION ENGINE                                  │
│                        (logic_engine.py)                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐         ┌──────────────────────────┐
│   STAGE 1: FILTERING     │         │   STAGE 2: CONTROL       │
│   Isolation Forest       │────────▶│   Decision Tree + Rules  │
└────────┬─────────────────┘         └─────────┬────────────────┘
         │                                     │
         │ IF anomaly detected                 │ IF data valid
         │ (humidity >100%, etc)               │ (normal readings)
         │                                     │
         ▼                                     ▼
  ┌──────────────┐                    ┌──────────────────────┐
  │   SKIP       │                    │  HumidifierCycle     │
  │  Actuation   │                    │  Manager             │
  └──────────────┘                    └──────────┬───────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────┐
                    │                             │                     │
              ┌─────▼─────┐             ┌─────────▼────────┐    ┌──────▼──────┐
              │  Trend    │             │  Overshoot       │    │   Phase     │
              │  Analysis │             │  Prediction      │    │  Manager    │
              └─────┬─────┘             └─────────┬────────┘    └──────┬──────┘
                    │                             │                     │
                    │  Track last 3 readings      │  15s lookahead      │
                    │  Calculate %/second         │  Safety margin      │
                    │                             │                     │
                    └─────────────────────────────┴─────────────────────┘
                                                  │
                                        ┌─────────▼─────────┐
                                        │  DECISION LOGIC   │
                                        └─────────┬─────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────┐
                    │                             │                     │
        ┌───────────▼──────────┐      ┌───────────▼─────────┐  ┌───────▼──────────┐
        │  START CYCLE?        │      │  CONTINUE CYCLE?    │  │  STOP CYCLE?     │
        │                      │      │                     │  │                  │
        │  humidity < 85%      │      │  humidity < 90%     │  │  humidity ≥ 90%  │
        │  AND not active      │      │  AND not overshoot  │  │  OR will overshoot│
        └───────────┬──────────┘      └───────────┬─────────┘  └───────┬──────────┘
                    │                             │                     │
                    │                             │                     │
                    └─────────────────┬───────────┴─────────────────────┘
                                      │
                            ┌─────────▼─────────┐
                            │   STATE MACHINE   │
                            │                   │
                            │  ┌──────────┐     │
                            │  │   IDLE   │     │
                            │  └────┬─────┘     │
                            │       │           │
                            │       ▼           │
                            │  ┌──────────┐     │
                            │  │   MIST   │     │
                            │  │  (5 sec) │     │
                            │  └────┬─────┘     │
                            │       │           │
                            │       ▼           │
                            │  ┌──────────┐     │
                            │  │   FAN    │     │
                            │  │  (10 sec)│     │
                            │  └────┬─────┘     │
                            │       │           │
                            │       └───────┐   │
                            └───────────────┼───┘
                                            │
                          ┌─────────────────┴──────────────────┐
                          │                                    │
                  ┌───────▼──────────┐              ┌──────────▼─────────┐
                  │  MIST MAKER      │              │  HUMIDIFIER FAN    │
                  │  ON (5s)         │              │  ON (10s)          │
                  │  OFF (10s)       │              │  OFF (5s)          │
                  └───────┬──────────┘              └──────────┬─────────┘
                          │                                    │
                          └─────────────────┬──────────────────┘
                                            │
                                ┌───────────▼───────────┐
                                │  routes.py            │
                                │  /api/control_actuator│
                                └───────────┬───────────┘
                                            │
                                ┌───────────▼───────────┐
                                │  serial_comm.py       │
                                │  send_json_command()  │
                                └───────────┬───────────┘
                                            │ USB Serial
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ACTUATOR LAYER                                   │
└─────────────────────────────────────────────────────────────────────────────┘

                         ┌───────────────────────┐
                         │   Arduino Uno R3      │
                         │   Relay Controller    │
                         └───────────┬───────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
          ┌─────────▼─────────┐          ┌──────────▼──────────┐
          │  8-Channel Relay   │          │  8-Channel Relay    │
          │  Module (Ch1-4)    │          │  Module (Ch5-8)     │
          └─────────┬──────────┘          └──────────┬──────────┘
                    │                                 │
       ┌────────────┼────────────┐       ┌───────────┼──────────┐
       │            │            │       │           │          │
  ┌────▼────┐  ┌───▼────┐  ┌───▼───┐ ┌─▼─────┐ ┌──▼────┐ ┌───▼────┐
  │  Mist   │  │ Humid. │  │ Exh.  │ │ HEPA  │ │ Light │ │  UV    │
  │  Maker  │  │  Fan   │  │  Fan  │ │  Fan  │ │       │ │ Steril │
  └─────────┘  └────────┘  └───────┘ └───────┘ └───────┘ └────────┘
  120V/60Hz    120V/60Hz   120V/60Hz 120V/60Hz 120V/60Hz 240V/60Hz

┌─────────────────────────────────────────────────────────────────────────────┐
│                         MONITORING LAYER                                    │
└─────────────────────────────────────────────────────────────────────────────┘

                         ┌───────────────────────┐
                         │   Flask Web Server    │
                         │   (Port 5000)         │
                         └───────────┬───────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
  ┌───────▼────────┐       ┌─────────▼────────┐      ┌─────────▼────────┐
  │   Dashboard    │       │   Controls UI    │      │   WiFi Setup     │
  │   /dashboard   │       │   /controls      │      │   /wifi_setup    │
  └────────────────┘       └──────────────────┘      └──────────────────┘
          │                          │                          │
          ▼                          ▼                          ▼
  ┌────────────────────────────────────────────────────────────────┐
  │                    Browser (Chrome/Firefox)                   │
  │                   http://raspberrypi.local:5000               │
  └────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════

KEY COMPONENTS:

🔹 Isolation Forest - ML anomaly detector (filters sensor faults)
🔹 Decision Tree - ML actuation model (optimal relay states)
🔹 HumidifierCycleManager - State machine (mist/fan cycle)
🔹 Trend Analysis - Rate calculator (humidity %/second)
🔹 Overshoot Prediction - Future humidity estimator (15s ahead)

═══════════════════════════════════════════════════════════════════════════════

DATA FLOW EXAMPLE:

1. SCD41 Sensor → Arduino → RPi
   Reading: {temp: 22.5°C, humidity: 83%, co2: 950ppm}

2. Isolation Forest (Stage 1)
   Input: [22.5, 83, 950]
   Output: prediction = 1 (NORMAL, not anomaly)
   Data valid, proceed to Stage 2

3. Trend Analysis
   Last 3 readings: [82%, 82.8%, 83%]
   Rate: (83-82)/10s = 0.1%/s

4. Decision Logic
   Current: 83% < 85% (target min)
   Cycle: not active
   START CYCLE

5. State Machine → MIST Phase
   Command: {"actuator": "mist_maker", "state": "ON"}
   Duration: 5 seconds

6. After 5s → FAN Phase
   Command: {"actuator": "mist_maker", "state": "OFF"}
   Command: {"actuator": "humidifier_fan", "state": "ON"}
   Duration: 10 seconds

7. Continue cycle until...
   Humidity: 90.2%, Rate: 0.28%/s
   Predicted: 90.2 + (0.28 × 15) = 94.4%
   Safety: 94.4% > (95% max)
   STOP CYCLE (prevent overshoot)

8. Result
   Final humidity: 91.0% (in 85-95% range)
   Overshoot: PREVENTED ✅

═══════════════════════════════════════════════════════════════════════════════

TIMING DIAGRAM:

Time │ Phase    │ Mist  │ Fan   │ Humidity │ Decision
─────┼──────────┼───────┼───────┼──────────┼────────────────────────
 0s  │ IDLE     │ OFF   │ OFF   │  83.0%   │ < 85%, start cycle
 0s  │ MIST     │ ON    │ OFF   │  83.2%   │ Misting...
 5s  │ FAN      │ OFF   │ ON    │  84.5%   │ Distributing...
15s  │ MIST     │ ON    │ OFF   │  86.8%   │ Misting...
20s  │ FAN      │ OFF   │ ON    │  88.2%   │ Distributing...
30s  │ MIST     │ ON    │ OFF   │  89.5%   │ Misting...
35s  │ FAN      │ OFF   │ ON    │  90.2%   │ Rate=0.28%/s, predict 94.4%
36s  │ IDLE     │ OFF   │ OFF   │  90.4%   │ Stopped, will overshoot
45s  │ IDLE     │ OFF   │ OFF   │  91.0%   │ Stable in range

═══════════════════════════════════════════════════════════════════════════════
```

**Legend:**

- `┌─┐` Boxes = Components
- `│` Vertical = Data flow
- `▼` Arrows = Process direction
- `═` Double line = Section separator
- `✅` Check = Success/validation
- `🔹` Diamond = Key component

**Color Coding (when printed):**

- **Blue** - Sensors & data collection
- **Green** - AI/ML decision making
- **Orange** - Actuator control
- **Purple** - Web interface

---

**File:** [docs/AI_ARCHITECTURE_DIAGRAM.md](AI_ARCHITECTURE_DIAGRAM.md)  
**Created:** 2024-01-20  
**System:** MASH IoT v1.0
