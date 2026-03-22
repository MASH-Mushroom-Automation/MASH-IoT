# M.A.S.H. IoT Device
## User Manual

---

**Device Name:** M.A.S.H. IoT Device (Mushroom Automation w/ Smart Hydro-Environment)
**Firmware Version:** v2.8.0 — "Actuator Event Logging & Analytics"
**Hardware Platform:** Raspberry Pi + Arduino Uno R3
**Target Display:** 1024 × 600 (Raspberry Pi Official 7" Touchscreen)
**Document Date:** March 3, 2026
**Developed by:** Mushroom Automation w/ Smart Hydro-Environment (M.A.S.H.)

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Hardware Overview](#2-hardware-overview)
3. [First Power-On](#3-first-power-on)
4. [WiFi Provisioning (First-Time Setup)](#4-wifi-provisioning-first-time-setup)
5. [Accessing the Web Interface](#5-accessing-the-web-interface)
6. [Dashboard](#6-dashboard)
7. [Controls](#7-controls)
8. [Alerts](#8-alerts)
9. [AI Insights](#9-ai-insights)
10. [Settings](#10-settings)
11. [Pairing with the Mobile App](#11-pairing-with-the-mobile-app)
12. [MASHAuto Automation Reference](#12-mashauto-automation-reference)
13. [Firmware Updates (OTA)](#13-firmware-updates-ota)
- [Appendix A — Troubleshooting](#appendix-a--troubleshooting)
- [Appendix B — Environmental Thresholds Reference](#appendix-b--environmental-thresholds-reference)
- [Appendix C — Actuator Reference](#appendix-c--actuator-reference)

---

## 1. Introduction

The M.A.S.H. IoT Device is the on-site hardware gateway of the Mushroom Automation w/ Smart Hydro-Environment (M.A.S.H.) platform. It is permanently installed alongside the mushroom cultivation chambers and performs continuous environmental monitoring, closed-loop automation, and cloud synchronization — without requiring manual intervention during normal operation.

### System Architecture

The device is built on a **two-layer architecture**:

| Layer              | Hardware       | Responsibility                                                 |
| ------------------ | -------------- | -------------------------------------------------------------- |
| **Hardware Layer** | Arduino Uno R3 | Reads sensors, drives relay outputs, enforces safety watchdog  |
| **Control Layer**  | Raspberry Pi   | Runs automation logic, web interface, cloud sync, and database |

The two layers communicate over a **USB serial connection at 9,600 baud**. The Arduino sends JSON sensor readings every 5 seconds. The Raspberry Pi sends JSON relay-control commands in response. If the serial connection is lost for more than 60 seconds, the Arduino's hardware watchdog automatically turns off all relays — preventing any actuator from remaining stuck in an active state.

### Access Methods

The device can be accessed and monitored through three pathways:

| Method                             | Where                             | Use Case                                        |
| ---------------------------------- | --------------------------------- | ----------------------------------------------- |
| **Web Interface**                  | Browser on the same Wi-Fi network | Primary on-site monitoring and control          |
| **MASH Grower Mobile App**         | Android smartphone                | Remote monitoring, actuator control, analytics  |
| **Cloud (Firebase + Backend API)** | Internet                          | Off-site real-time monitoring, command delivery |

---

## 2. Hardware Overview

### Physical Components

| Component                        | Description                                                           |
| -------------------------------- | --------------------------------------------------------------------- |
| **Raspberry Pi** (3B or 4B)      | Main controller running the MASH gateway software                     |
| **Arduino Uno R3**               | Reads sensors and drives relay outputs via USB serial                 |
| **7" Touchscreen (1024×600)**    | Displays the MASH web interface in kiosk mode                         |
| **8-Channel Relay Module**       | Switches 220V AC loads (fans, mist maker, LED lights)                 |
| **SCD41 Sensor — Fruiting Room** | Measures CO₂, Temperature, and Humidity via hardware I2C (pins A4/A5) |
| **SCD41 Sensor — Spawning Room** | Same measurement, via software I2C (pins D10/D11)                     |

> **Note:** Both SCD41 sensors share the I2C address `0x62`. They are differentiated by the I2C bus they are connected to — not by their address. This is a critical implementation detail that prevents sensor cross-reading.

### Relay Actuator Mapping

| Relay   | Arduino Pin | Actuator Name          | Room             | Function                           |
| ------- | ----------- | ---------------------- | ---------------- | ---------------------------------- |
| Relay 1 | Pin 2       | Spawning Exhaust Fan   | Spawning         | CO₂ and temperature ventilation    |
| Relay 2 | Pin 3       | Fruiting Exhaust Fan   | Fruiting         | Removes CO₂-rich air               |
| Relay 3 | Pin 4       | Fruiting Intake Blower | Fruiting         | Draws fresh air in                 |
| Relay 4 | Pin 5       | Humidifier Fan         | Fruiting         | Circulates mist through chamber    |
| Relay 5 | Pin 6       | Mist Maker             | Fruiting         | Generates ultrasonic humidity mist |
| Relay 6 | Pin 7       | LED Grow Lights        | Fruiting         | 12-hour light cycle (08:00–20:00)  |
| Relay 7 | Pin 8       | Device Exhaust Fan     | Device enclosure | Removes heat from electronics      |

> **Active Low Logic:** The relay module uses **active-low** triggering. Writing `LOW` to a pin activates the relay (turns the connected device ON). On every startup, the Arduino initializes all relay pins to `HIGH` (all OFF). This ensures no actuator is accidentally powered during boot.

### Indicator LEDs

| LED           | Location           | Meaning                                                    |
| ------------- | ------------------ | ---------------------------------------------------------- |
| Power LED     | Raspberry Pi board | RPi is receiving power                                     |
| Activity LED  | Raspberry Pi board | Disk/CPU activity (solid during boot, flickers during use) |
| TX/RX LEDs    | Arduino board      | Serial communication with Raspberry Pi is active           |
| Arduino Power | Arduino board      | Arduino is powered via USB from RPi                        |

---

## 3. First Power-On

### Boot Sequence

When the device is powered on, the following startup sequence occurs automatically:

**Step 1 — Hardware power-up (0–10 seconds)**
The Raspberry Pi begins booting Linux. The touchscreen may show a rainbow splash or remain dark during this phase.

**Step 2 — Service initialization (10–30 seconds)**
The MASH gateway service starts. The web interface becomes available once Flask binds to port 5000.

**Step 3 — Sensor warmup (30 seconds)**
After the first sensor data arrives from the Arduino, a **30-second warmup period** begins. During this period, sensor readings are logged to the database but the automation engine does not yet act on them. This prevents false actuator triggers caused by unstabilized sensor readings immediately after power-on.

**Step 4 — Network check**
On startup, the system checks for an active Wi-Fi connection:
- If a known Wi-Fi network is available → connects automatically.
- If no Wi-Fi is available → **starts the provisioning hotspot** (`MASH-Device`) automatically.

**Step 5 — Normal operation begins**
Once warmup completes and network is established, the automation engine activates (if `auto_mode` is enabled in configuration), Firebase sync begins, and the web dashboard becomes fully operational.

### Expected Boot Time

| Phase                            | Duration           |
| -------------------------------- | ------------------ |
| Linux boot to service start      | ~15–25 seconds     |
| MASH service initialization      | ~5–10 seconds      |
| Sensor warmup                    | 30 seconds         |
| **Total time to full operation** | **~50–65 seconds** |

---

## 4. WiFi Provisioning (First-Time Setup)

On first boot — or whenever the device does not have a saved Wi-Fi connection — it automatically activates a provisioning hotspot to allow Wi-Fi configuration through a web browser.

### Step 1 — Connect to the Device Hotspot

Using a smartphone, laptop, or any Wi-Fi-capable device:

1. Open your device's Wi-Fi settings.
2. Locate and connect to the network named **`MASH-Device`**.
3. This is an **open network** — no password is required.
4. Your device will be assigned an IP address in the `10.42.0.x` range.

> **Note:** Internet access will not be available while connected to the `MASH-Device` hotspot. This is expected.

### Step 2 — Open the WiFi Setup Page

Open a web browser and navigate to:

```
http://10.42.0.1:5000/wifi-setup
```

The WiFi Setup page will load. Depending on the current device state, one of the following banners will appear at the top:

| Banner              | Color  | Meaning                                          |
| ------------------- | ------ | ------------------------------------------------ |
| "Connected"         | Green  | Device is already on a Wi-Fi network             |
| "Provisioning Mode" | Blue   | Device hotspot is active, awaiting configuration |
| "Not Connected"     | Orange | No Wi-Fi and hotspot was not yet fully ready     |

### Step 3 — Select Your Wi-Fi Network

1. The **Network** dropdown lists all 2.4 GHz Wi-Fi networks detected nearby. Select your home or facility network from the list.
2. If your network does not appear in the list, select **"Enter Manually…"** and type the SSID in the text field that appears.
3. Enter the network **Password** in the password field. Tap the eye icon to reveal the password and verify it before proceeding.

> **Important:** The MASH Device uses the **2.4 GHz Wi-Fi band only**. If your router operates on 5 GHz only, the network will not appear in the scan results. Ensure your router has 2.4 GHz enabled.

### Step 4 — Connect to the Network

Tap **Connect to Network**. The button will disable itself after the first tap to prevent duplicate submissions.

The browser will redirect to the **"Applying Settings…"** page, which shows an animated spinner, the target network SSID, and instructions explaining what happens next.

### Step 5 — Reconnect Your Device

The MASH IoT Device is now switching from hotspot mode to client mode and joining your Wi-Fi network. This process takes **30–60 seconds**.

During this time:
- The `MASH-Device` hotspot will disappear.
- Your phone or laptop will lose connection to the setup page.
- The MASH Device will obtain a new IP address from your router.

**To resume access after the switch:**
1. Reconnect your phone or laptop to your regular Wi-Fi network.
2. Find the device's new IP address from your router's admin panel, or check the IP displayed on the MASH Device's touchscreen.
3. Navigate to `http://<device-ip>:5000` in a browser.

> **Failsafe:** If the device fails to connect to the specified network within 30 seconds, it will **automatically restart the `MASH-Device` hotspot**, allowing you to try again.

---

## 5. Accessing the Web Interface

The MASH Device hosts a full-featured web interface accessible from any device on the same local network.

### Access Methods

| Method                   | Address                   | Notes                                                      |
| ------------------------ | ------------------------- | ---------------------------------------------------------- |
| **By IP address**        | `http://<device-ip>:5000` | Most reliable; find IP from your router's device list      |
| **Friendly domain**      | `http://mash.lan`         | May work on some network configurations                    |
| **Provisioning hotspot** | `http://10.42.0.1:5000`   | Only available when device is in hotspot/provisioning mode |

### Recommended Browsers

Any modern browser is compatible: Google Chrome, Mozilla Firefox, Microsoft Edge, or Safari. The interface is optimized for the Raspberry Pi's **1024 × 600** touchscreen display but is also usable on standard laptop and desktop resolutions.

### Navigation

All pages share a common **left sidebar navigation** with the following links:

| Icon | Label       | Page                                           |
| ---- | ----------- | ---------------------------------------------- |
| 🏠    | Dashboard   | Live sensor monitoring (default page)          |
| 🎚    | Controls    | Manual and automatic actuator control          |
| 🔔    | Alerts      | Active and historical system alerts            |
| 🧠    | AI Insights | Machine learning model status                  |
| ⚙️    | Settings    | WiFi, cloud sync, power, and firmware settings |

---

## 6. Dashboard

The **Dashboard** is the default page and the real-time monitoring hub for both cultivation rooms. It updates automatically every **3 seconds** without requiring a page refresh.

### Room Toggle

At the top of the page, two buttons allow switching the displayed room:

- **Fruiting Room** — Shows sensor data and actuator status for the fruiting chamber.
- **Spawning Room** — Shows sensor data and actuator status for the spawning chamber.

Tap either button to switch the active view.

### System Status Bar

A status strip below the room toggle shows four live indicators:

| Indicator   | Icon           | Meaning                                                                   |
| ----------- | -------------- | ------------------------------------------------------------------------- |
| **Sensors** | Microchip icon | Arduino serial connection status — "Connected" (green) or "Offline" (red) |
| **WiFi**    | Wi-Fi icon     | Current connected network SSID, or "Disconnected"                         |
| **Sync**    | Cloud icon     | Firebase cloud sync status — "Active" (green) or "Inactive" (grey)        |
| **Uptime**  | Clock icon     | Time elapsed since the MASH service last started                          |

### Provisioning Banner

When the device is in hotspot/provisioning mode, an **orange banner** appears below the status bar reading "Device is in Provisioning Mode." Tapping this banner opens a two-step modal:

- **Step 1:** Connect your phone or laptop to the `MASH-Device` hotspot (no password).
- **Step 2:** Scan the WiFi setup QR code or visit `http://mash.lan/wifi-setup` to configure the network.

### Sensor Cards

Each room displays three sensor cards:

| Card            | Unit                    | Description                          |
| --------------- | ----------------------- | ------------------------------------ |
| **CO₂ Level**   | ppm (parts per million) | Current carbon dioxide concentration |
| **Temperature** | °C (Celsius)            | Current air temperature              |
| **Humidity**    | % (relative humidity)   | Current relative humidity            |

Each card shows the live reading in large text, the target value for that room, and a **Room Condition badge**:

| Badge        | Color  | Meaning                                            |
| ------------ | ------ | -------------------------------------------------- |
| **Optimal**  | Green  | All sensors are within target tolerance            |
| **Warning**  | Yellow | At least one sensor is approaching its limit       |
| **Critical** | Red    | At least one sensor has exceeded its limit         |
| **Waiting**  | Grey   | Sensor data not yet received (e.g., during warmup) |

### Actuator Status Icons

Below the sensor cards, a row of small icons represents the current on/off state of each actuator in that room. Lit icons (colored) indicate the actuator is currently active (ON). Dim icons indicate the actuator is inactive (OFF). This is a **read-only status display** — to control actuators, use the [Controls page](#7-controls).

### Floating QR Code Button

A floating circular button in the bottom-right corner of the Dashboard opens the **Device Connection QR Code** modal. This QR code allows the MASH Grower Mobile app to pair with this device without manually entering the MASH ID or IP address.

See [Chapter 11](#11-pairing-with-the-mobile-app) for mobile pairing instructions.

---

## 7. Controls

The **Controls** page provides direct manual control over all actuators and allows switching between Automatic and Manual operation modes.

### Auto / Manual Mode Toggle

At the top of the page, a prominent toggle switch controls the overall operation mode:

| Mode                  | Toggle State | Behavior                                                                          |
| --------------------- | ------------ | --------------------------------------------------------------------------------- |
| **Automatic Control** | ON (green)   | MASHAuto AI runs the automation. Actuator cards are dimmed and cannot be clicked. |
| **Manual Control**    | OFF (grey)   | All actuator cards are interactive. The user has full direct control.             |

> **Important:** Switching from Automatic to Manual mode stops the automation engine from issuing new commands. Actuators retain their last state — they are **not reset to OFF** when switching modes. Similarly, switching back to Automatic mode re-engages the automation engine from the current sensor conditions.

### Fruiting Room Actuators

| Card               | Badge | Function                                                      |
| ------------------ | ----- | ------------------------------------------------------------- |
| **Mist Maker**     | AUTO  | Generates ultrasonic humidity mist to raise relative humidity |
| **Humidifier Fan** | AUTO  | Distributes mist throughout the fruiting chamber              |
| **Exhaust Fan**    | AUTO  | Expels CO₂-rich or warm air from the chamber                  |
| **Intake Blower**  | AUTO  | Draws fresh air into the chamber                              |
| **LED Lights**     | TIMED | Grow lights on a fixed 12-hour schedule (08:00–20:00)         |

### Spawning Room Actuators

| Card            | Badge           | Function                                                                     |
| --------------- | --------------- | ---------------------------------------------------------------------------- |
| **Exhaust Fan** | PASSIVE / FLUSH | Passive cycle ventilation; switches to Flush mode when CO₂ exceeds 2,000 ppm |

### Device Room Actuators

| Card            | Badge | Function                                                           |
| --------------- | ----- | ------------------------------------------------------------------ |
| **Exhaust Fan** | TIMED | Ventilates heat from the electronics enclosure on a fixed schedule |

### Toggling an Actuator (Manual Mode)

**Step 1.** Ensure the Auto/Manual toggle at the top shows **Manual Control** (toggle OFF / grey).

**Step 2.** Tap any actuator card. The card will update immediately to reflect the new state:
- **ON** — Card shows a colored (active) background and "ON" label.
- **OFF** — Card shows a grey (inactive) background and "OFF" label.

**Step 3.** The command is sent to the Arduino via serial and the relay physically switches within 1–2 seconds.

> **Cooldown:** After toggling any actuator, a **5-second cooldown** applies to that card. This prevents rapid toggling that could damage relay hardware.

> **Error Recovery:** If the command fails to reach the Arduino, the card automatically reverts to its previous state and displays an error notification.

### Mode Badges Explained

| Badge       | Meaning                                                                       |
| ----------- | ----------------------------------------------------------------------------- |
| **AUTO**    | Actuator is managed by the MASHAuto decision engine in Automatic mode         |
| **TIMED**   | Actuator follows a fixed clock-based on/off schedule                          |
| **PASSIVE** | Actuator runs on a periodic interval cycle (e.g., 2 minutes every 30 minutes) |
| **FLUSH**   | Override mode — actuator runs continuously until the trigger condition clears |

---

## 8. Alerts

The **Alerts** page displays automatically generated environmental alerts and allows acknowledging resolved issues.

### Alerts Overview

At the top of the page, three summary cards show:
- **Active Issues** — Total number of unacknowledged alerts (blue border)
- **Critical** — Number of critical-severity alerts (red border)
- **Warnings** — Number of warning-severity alerts (yellow border)

### Active Alerts Table

The Active Alerts table lists all current unacknowledged alerts with the following columns:

| Column          | Description                                                      |
| --------------- | ---------------------------------------------------------------- |
| **Room**        | Which cultivation room triggered the alert (Fruiting / Spawning) |
| **Severity**    | Alert level: Critical (red), Warning (yellow), or Info (blue)    |
| **Message**     | Human-readable description of the condition                      |
| **Detected At** | Timestamp when the alert was first triggered                     |
| **Action**      | Acknowledge button                                               |

**To acknowledge an alert:**
1. Once the condition that caused the alert has been resolved, tap the **Acknowledge** button on that row.
2. The row will fade out and the alert count will decrease.
3. The alert moves to the Alert History table below.

### Alert History Table

The Alert History table lists all previously acknowledged alerts, showing the same columns without an Action button. Up to the **50 most recent** alerts are shown.

### What Triggers Each Alert

| Condition                       | Alert Level | Threshold                                      |
| ------------------------------- | ----------- | ---------------------------------------------- |
| CO₂ exceeds critical level      | Critical    | > 1,500 ppm (Fruiting), > 2,000 ppm (Spawning) |
| Temperature too high            | Critical    | > 30.0 °C                                      |
| Temperature too low             | Critical    | < 18.0 °C                                      |
| Humidity too low                | Critical    | < 70 %                                         |
| CO₂ approaching limit           | Warning     | Sensor trending toward CO₂ max threshold       |
| Temperature out of target range | Warning     | Outside ±2 °C of room target                   |
| Humidity out of target range    | Warning     | Outside ±10 % of room target                   |

> **No Active Alerts State:** When all alerts have been acknowledged and no new conditions are detected, the page displays a green illustration and the message "No Active Alerts — All systems operating normally."

---

## 9. AI Insights

The **AI Insights** page shows the status of the machine learning subsystem embedded in the MASH Device. This page is **informational only** — it does not provide controls. Automation is enabled or disabled from the [Controls page](#7-controls).

### ML System Status

A top-level card shows whether the `scikit-learn` Python library is installed and whether ML features are enabled in the device configuration:

| Status                       | Meaning                                                  |
| ---------------------------- | -------------------------------------------------------- |
| scikit-learn installed     | The ML runtime is available                              |
| ML features enabled        | `ml_enabled: true` is set in `config/config.yaml`        |
| scikit-learn not installed | ML cannot run; the page will display the install command |
| ⚠️ ML features disabled       | Library is present but ML is turned off in configuration |

### Model Status Cards

**Anomaly Detection Model (Isolation Forest)**

This model continuously evaluates incoming sensor readings for statistical anomalies — such as sudden temperature spikes or sensor hardware faults. When an anomaly is detected, the system substitutes the last known valid reading rather than discarding the data cycle, ensuring automation continuity.

- Status: **Model Active** (green) or **Not Loaded** (orange if model file is missing)

**Actuation Model (Decision Tree)**

This model determines which actuators to activate or deactivate based on current temperature, humidity, CO₂ levels, and the time of day. It outputs relay state recommendations for the automation engine.

- Status: **Model Active** (green) or **Not Loaded** (orange if model file is missing)

### AI Feature Summary

| Feature                     | Description                                                   |
| --------------------------- | ------------------------------------------------------------- |
| Real-time Anomaly Detection | Flags sensor readings outside statistical norms               |
| Predictive Maintenance      | Identifies patterns that may indicate equipment degradation   |
| Smart Automation            | Determines optimal actuator states for current conditions     |
| Learning from Data          | Models are retrained weekly on locally stored historical data |

### Enabling or Disabling ML

To enable or disable the ML subsystem, edit the device configuration file at `config/config.yaml` and set:

```yaml
system:
  ml_enabled: true   # Set to false to disable ML
```

A device reboot is required after changing this setting.

---

## 10. Settings

The **Settings** page provides device configuration, network management, cloud synchronization control, power functions, and firmware management. It is organized into **five tabs** accessible via the left sidebar within the page.

### Tab 1 — General

| Item              | Description                                                       |
| ----------------- | ----------------------------------------------------------------- |
| **Current Time**  | Displays the current local system time, updated live every second |
| **System Uptime** | Time elapsed since the MASH gateway service last started          |

### Tab 2 — WiFi Connection

| Item                                   | Description                                                                                                                                           |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Connection Status**                  | Shows the currently connected network SSID and the device's local IP address                                                                          |
| **Disconnect and Enable Provisioning** | Disconnects from the current Wi-Fi network and restarts the provisioning hotspot (`MASH-Device`). Use this to reconfigure the device's Wi-Fi network. |

> **Warning:** Selecting "Disconnect and Enable Provisioning" will immediately terminate the Wi-Fi connection. Any active monitoring sessions and cloud sync will be interrupted until a new network is configured.

### Tab 3 — Cloud Sync

| Item                       | Description                                                       |
| -------------------------- | ----------------------------------------------------------------- |
| **Firebase Realtime Sync** | Toggle switch to enable or disable Firebase cloud synchronization |
| **Sync Status**            | Current state — "Active" (green) or "Inactive" (grey)             |

When Firebase Sync is **enabled**, all sensor readings and actuator state changes are pushed to the MASH Firebase Realtime Database in real time. This enables remote monitoring via the MASH Grower Mobile app (Cloud Mode), historical data access from anywhere with internet access, and real-time alert delivery to connected mobile apps.

When Firebase Sync is **disabled**, all data continues to be saved locally to the device's SQLite database, but no cloud data is transmitted.

### Tab 4 — Power Controls

> **Warning:** Both actions on this tab will temporarily interrupt all environment monitoring. Ensure cultivation conditions are stable before proceeding.

| Button              | Action                                                                                          | Recovery                                            |
| ------------------- | ----------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **Reboot Device**   | Restarts the Raspberry Pi. All monitoring resumes automatically after ~60 seconds.              | Automatic restart and service resumption            |
| **Shutdown Device** | Fully powers down the Raspberry Pi. The device will not restart unless physically power-cycled. | Requires manual power-cycle via the power connector |

Both actions display a confirmation dialog before executing.

### Tab 5 — About System

| Item                  | Description                                                   |
| --------------------- | ------------------------------------------------------------- |
| **Product Name**      | M.A.S.H. IoT Gateway                                          |
| **Firmware Version**  | Current installed firmware version (e.g., v2.8.0)             |
| **Hardware**          | Raspberry Pi                                                  |
| **OS Environment**    | Linux (Debian)                                                |
| **Update Status**     | "Up to Date" (green) or "Update Available" (orange/red badge) |
| **Check for Updates** | Queries GitHub Releases for new firmware versions             |
| **History**           | Opens the Changelog modal showing all release notes           |

See [Chapter 13](#13-firmware-updates-ota) for full update instructions.

---

## 11. Pairing with the Mobile App

The MASH Grower Mobile app (Android) can connect to this device for remote monitoring and control. There are two pairing methods.

### Method A — MASH ID

The MASH ID is the unique identifier for this device. It is always visible in two locations:
- **Printed on the label** on the side of the device enclosure.
- **Displayed on the device's touchscreen** under Settings → About System (e.g., `MASH-B2-CAL26-CE637C`).

**To pair using MASH ID:**
1. Open the MASH Grower Mobile app and navigate to the device connection screen.
2. Tap the MASH ID entry field and enter the full identifier in the format `MASH-##-#####-######`.
3. Tap **Connect**. The app will locate the device on the local network or via cloud.

### Method B — QR Code Scan

**Step 1 — Display the QR Code on the device:**
On the MASH Device's touchscreen, navigate to the **Dashboard** and tap the floating circular QR button in the bottom-right corner. A QR code modal will appear on screen.

**Step 2 — Scan with the mobile app:**
In the MASH Grower Mobile app, navigate to the device connection screen and tap **Scan QR Code**. Point the phone camera at the QR code displayed on the device screen.

### Connection Modes

After pairing, the mobile app connects in one of two modes:

| Mode              | Condition                              | Data Updates           | Commands                      |
| ----------------- | -------------------------------------- | ---------------------- | ----------------------------- |
| **Local (Wi-Fi)** | Phone and device on same Wi-Fi network | HTTP polling every 10s | < 1 second via HTTP           |
| **Cloud**         | Remote access via internet             | Real-time via Firebase | 1–5 seconds via MQTT/Firebase |

---

## 12. MASHAuto Automation Reference

MASHAuto is the MASH Device's embedded intelligent control engine. When the Auto/Manual toggle on the Controls page is set to **Automatic Control**, MASHAuto continuously reads sensor data every 5 seconds and autonomously controls all actuators to maintain optimal growing conditions.

### How MASHAuto Decides

MASHAuto operates as a two-stage pipeline:

**Stage 1 — Anomaly Detection (Isolation Forest)**
Each incoming sensor reading is first evaluated for statistical validity. If a reading is flagged as anomalous (e.g., a CO₂ spike to 9,999 ppm caused by a sensor glitch), the system substitutes the last known valid reading to prevent false actuation.

**Stage 2 — Actuation Decision (Decision Tree)**
The validated readings — temperature, humidity, CO₂ concentration, and current time of day — are passed to the Decision Tree model. The model outputs a recommended state (ON or OFF) for each actuator based on patterns learned from historical sensor data.

### Fruiting Room Logic

| Trigger                 | Condition                     | Action                                                    |
| ----------------------- | ----------------------------- | --------------------------------------------------------- |
| Low humidity            | Humidity < 85 %               | Start **Humidifier Cycle** (Mist Maker + Fan alternation) |
| Humidity overshoot risk | Humidity trending toward 95 % | Stop humidifier cycle early                               |
| High CO₂                | CO₂ > 1,000 ppm               | Turn **Exhaust Fan ON**                                   |
| CO₂ recovered           | CO₂ drops below 900 ppm       | Turn Exhaust Fan OFF                                      |
| High temperature        | Temp > 26.0 °C                | Turn **Exhaust Fan ON**                                   |
| LED schedule            | Clock: 08:00                  | Turn **LED Grow Lights ON**                               |
| LED schedule            | Clock: 20:00                  | Turn **LED Grow Lights OFF**                              |

#### Humidifier Cycle (HumidifierCycleManager)

When humidity falls below 85 %, the system starts an alternating mist/fan cycle. The cycle continues until humidity reaches the 90 % target.

| Phase                | Duration   | Mist Maker | Humidifier Fan |
| -------------------- | ---------- | ---------- | -------------- |
| Phase 1 — Mist       | 10 seconds | ON         | OFF            |
| Phase 2 — Distribute | 30 seconds | OFF        | ON             |

### Spawning Room Logic

| Trigger                    | Condition        | Action                                                      |
| -------------------------- | ---------------- | ----------------------------------------------------------- |
| High CO₂ (flush trigger)   | CO₂ > 2,000 ppm  | Switch Exhaust Fan to **Flush Mode** (5 minutes continuous) |
| Normal intervals (passive) | Every 30 minutes | Run Exhaust Fan for **2 minutes** (passive cycle)           |
| Temperature high           | Temp > 27.0 °C   | Turn **Exhaust Fan ON**                                     |

### Device Room Logic

| Schedule          | Time                       | Action                                   |
| ----------------- | -------------------------- | ---------------------------------------- |
| Ventilation cycle | 08:00, 12:00, 16:00, 20:00 | Run Device Exhaust Fan for **3 minutes** |

### Manual Override Behavior

When a user manually controls an actuator from the Controls page or the mobile app while in Automatic mode:

1. A **manual override** is recorded for that actuator.
2. The automation engine **will not re-issue commands** for overridden actuators during the current override window.
3. Overrides **expire automatically after 5 minutes**, after which the automation engine resumes control.
4. All overrides are cleared immediately when the mode is switched back to Automatic.

### Automation Startup Delay

After powering on, MASHAuto will not begin issuing commands until the **30-second sensor warmup period** has completed.

---

## 13. Firmware Updates (OTA)

The MASH Device supports **Over-the-Air (OTA) firmware updates** delivered from the MASH GitHub Releases repository. Updates are applied without requiring physical access to the device.

### Checking for Updates

1. Navigate to **Settings → About System** tab.
2. Tap **Check for Updates**. The device will query the GitHub Releases API.
3. The **Update Status** badge will change to "Update Available" if a newer version exists.

### Update Priority Levels

| Badge Color | Level                  | Recommended Action                                                  |
| ----------- | ---------------------- | ------------------------------------------------------------------- |
| 🔴 Red       | **Critical Update**    | Install immediately — contains a critical bug fix or security patch |
| 🟠 Orange    | **Recommended Update** | Install soon — important stability or feature improvements          |
| 🔵 Blue      | **Standard Update**    | Optional — new features or minor improvements                       |

### Installing an Update

1. When an update is available, a modal appears with the new version number, release name, and changelog.
2. A warning is shown: **"The device will restart automatically after the update."**
3. Tap **Update Now** to begin. A progress bar will display the download progress.
4. Once downloaded, the new firmware is applied and the device **restarts automatically**. All monitoring resumes within ~60 seconds.

> **Rollback Safety:** The update system uses an A/B rollback mechanism. If the new firmware fails to boot successfully, the device automatically rolls back to the previous stable version.

---

## Appendix A — Troubleshooting

---

**1. The device is not connecting to my Wi-Fi network.**

- Verify that the network name (SSID) was entered correctly, including capitalization.
- Confirm the password is correct by connecting another device to the same network.
- Ensure the target network is **2.4 GHz** — the MASH Device does not support 5 GHz Wi-Fi.
- If using manual SSID entry, confirm there are no leading or trailing spaces.
- Move the device physically closer to the router and try again.
- If the hotspot does not automatically restart after a failed attempt, reboot the device (Settings → Power Controls → Reboot).

---

**2. The web interface is not loading in my browser.**

- Confirm your phone or laptop is on the **same Wi-Fi network** as the MASH Device.
- Verify the device is fully booted (allow 60 seconds after power-on).
- Confirm you are accessing port **5000**: `http://<ip>:5000`.
- Try obtaining the device IP from your router's admin panel.
- If no IP is found, the device may be in hotspot mode — connect to `MASH-Device` and access `http://10.42.0.1:5000/wifi-setup` to reconfigure.

---

**3. Sensor readings on the dashboard show 0 or "—".**

- Check that the Arduino Uno is powered and connected to the Raspberry Pi via USB.
- Verify the USB cable is seated firmly in both the Arduino and the RPi.
- Reboot the device (Settings → Power Controls → Reboot). The serial auto-detect will attempt reconnection on startup.
- If the problem persists after reboot, try a different USB cable.

---

**4. Actuators are not responding to manual toggle commands.**

- Confirm the Auto/Manual toggle is set to **Manual Control** (toggle OFF / grey). In Automatic mode, cards cannot be clicked.
- Wait for the **5-second cooldown** to expire if the actuator was toggled recently.
- Verify the Arduino is connected (sensor readings should be updating on the Dashboard).
- Check that the relay module is powered.

---

**5. MASHAuto automation does not appear to be running.**

- Open the Controls page and confirm the toggle reads **Automatic Control** (green/ON).
- Wait 30–60 seconds after switching to Auto mode for the warmup period to complete.
- Verify that ML is enabled (`ml_enabled: true` in `config/config.yaml`). Check the AI Insights page to confirm both model status cards show "Model Active."
- Confirm sensor readings are live (non-zero, updating in Dashboard).

---

**6. The QR code on the dashboard is not scannable from the mobile app.**

- Ensure the mobile device camera is within **15–30 cm** of the touchscreen with the QR code fully centered in the viewfinder.
- Clean the touchscreen surface — fingerprints or smudges can distort the QR pattern.
- Reduce ambient glare on the screen.
- As an alternative, use the **MASH ID manual entry** method (Settings → About System).

---

**7. Cannot connect the mobile app to the device.**

- For **Local Mode**: ensure the mobile device and the MASH Device are on the same Wi-Fi network.
- For **Cloud Mode**: ensure both devices have active internet connections.
- Verify the device's Firebase cloud sync is enabled (Settings → Cloud Sync → toggle ON).
- Confirm the MASH ID entered in the mobile app exactly matches the serial number in Settings → About System.

---

**8. Firebase cloud sync is not working.**

- Navigate to Settings → Cloud Sync and confirm the Firebase Realtime Sync toggle is **ON**.
- Confirm the MASH Device has an active internet connection (check the Wi-Fi indicator in the status bar).

---

**9. The device is not rebooting after selecting "Reboot Device."**

- The device web interface will become unreachable for ~60 seconds during a reboot; this is normal. Wait at least 90 seconds before assuming the reboot failed.
- After the reboot completes, refresh the browser or re-enter the device IP address.
- If the device does not come back online after 2 minutes, perform a manual power cycle.

---

**10. A firmware OTA update failed.**

- The device's A/B rollback mechanism should automatically restore the previous firmware version if the new version fails to boot.
- The failed version will be marked as "unstable" and will not be offered as an update again automatically.
- If the device is completely unresponsive after an update attempt, a manual power cycle will trigger the rollback. Allow 90 seconds for the rollback boot.

---

## Appendix B — Environmental Thresholds Reference

### Fruiting Room

| Parameter         | Target      | Min     | Max       | Alert Tolerance               |
| ----------------- | ----------- | ------- | --------- | ----------------------------- |
| Temperature       | 24.0 °C     | 22.0 °C | 26.0 °C   | ±2.0 °C                       |
| Relative Humidity | 90.0 %      | 85.0 %  | 95.0 %    | ±10 %                         |
| CO₂ Concentration | < 1,000 ppm | —       | 1,000 ppm | Exhaust Fan ON at > 1,000 ppm |

**Critical Alert Thresholds (Fruiting):**

| Condition                   | Threshold   |
| --------------------------- | ----------- |
| Critical CO₂                | > 1,500 ppm |
| Critical Temperature (High) | > 30.0 °C   |
| Critical Temperature (Low)  | < 18.0 °C   |
| Critical Humidity (Low)     | < 70 %      |

### Spawning Room

| Parameter         | Target      | Min     | Max       | Alert Tolerance                  |
| ----------------- | ----------- | ------- | --------- | -------------------------------- |
| Temperature       | 25.0 °C     | 23.0 °C | 27.0 °C   | ±2.0 °C                          |
| Relative Humidity | 95.0 %      | 90.0 %  | 98.0 %    | ±5 %                             |
| CO₂ Concentration | < 2,000 ppm | —       | 2,000 ppm | Exhaust Fan Flush at > 2,000 ppm |

### Passive Ventilation Schedules

| Fan                  | Normal Cycle                               | Flush / Override Trigger                       |
| -------------------- | ------------------------------------------ | ---------------------------------------------- |
| Spawning Exhaust Fan | 2 minutes ON every 30 minutes              | Continuous 5-minute flush when CO₂ > 2,000 ppm |
| Device Exhaust Fan   | 3 minutes ON at 08:00, 12:00, 16:00, 20:00 | No override trigger                            |

---

## Appendix C — Actuator Reference

| Actuator Name           | Room             | Arduino Pin | Relay # | Function                                               |
| ----------------------- | ---------------- | ----------- | ------- | ------------------------------------------------------ |
| Fruiting Exhaust Fan    | Fruiting         | 3           | 2       | Removes CO₂-rich or warm air from the fruiting chamber |
| Fruiting Intake Blower  | Fruiting         | 4           | 3       | Draws fresh air into the fruiting chamber              |
| Humidifier Fan          | Fruiting         | 5           | 4       | Distributes mist throughout the chamber                |
| Mist Maker (Humidifier) | Fruiting         | 6           | 5       | Generates ultrasonic mist to raise relative humidity   |
| LED Grow Lights         | Fruiting         | 7           | 6       | Provides grow lighting; 08:00–20:00 schedule           |
| Spawning Exhaust Fan    | Spawning         | 2           | 1       | Passive ventilation and CO₂ flush for spawning chamber |
| Device Exhaust Fan      | Device enclosure | 8           | 7       | Removes heat from the electronics enclosure            |

### Serial Command Format

The Raspberry Pi sends actuator commands to the Arduino in the following JSON format over USB serial at 9,600 baud:

```json
{"actuator": "MIST_MAKER", "state": "ON"}
{"actuator": "FRUITING_EXHAUST_FAN", "state": "OFF"}
{"actuator": "SPAWNING_EXHAUST_FAN", "state": "ON"}
```

On device shutdown or serial disconnect, the Raspberry Pi sends the special command `ALL_OFF` to ensure all relays are returned to the inactive state.

---

*This document applies to M.A.S.H. IoT Device firmware v2.8.0 and subsequent releases unless otherwise noted.*
*Technical support contact: mash.mushroom.automation@gmail.com*
*© 2026 Mushroom Automation w/ Smart Hydro-Environment (M.A.S.H.). All rights reserved.*
