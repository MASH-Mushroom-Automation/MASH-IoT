# Operational Manual for the M.A.S.H. IoT Environmental Control Gateway

## Academic Reference Edition

---

**System Designation:** Mushroom Automation w/ Smart Hydro-Environment (M.A.S.H.) — IoT Environmental Control Gateway
**Firmware Revision:** v2.8.0 — "Actuator Event Logging and Analytics"
**Hardware Platform:** Raspberry Pi Single-Board Computer with Arduino Uno R3 Co-Processor
**Document Classification:** System Operations and User Procedures Reference
**Publication Date:** March 3, 2026
**Prepared by:** Mushroom Automation w/ Smart Hydro-Environment Research and Development Team

---

## Abstract

This document constitutes the operational reference manual for the Mushroom Automation w/ Smart Hydro-Environment (M.A.S.H.) IoT Environmental Control Gateway, a two-layer embedded computing system designed for the autonomous monitoring and regulation of environmental conditions within controlled mushroom cultivation facilities. The system integrates a Raspberry Pi single-board computer serving as the primary control layer with an Arduino Uno R3 co-processor serving as the hardware interface layer. These two components communicate via USB serial data exchange to achieve continuous sensor acquisition, machine-learning-driven actuation logic, cloud data synchronization, and an HTTP-based web user interface. This manual provides a comprehensive procedural description of all system components, user interfaces, operational modes, automation behaviors, configuration parameters, and maintenance procedures necessary for the deployment and ongoing operation of the system within a research or agricultural production context.

---

## Table of Contents

1. [System Overview and Architecture](#1-system-overview-and-architecture)
2. [Hardware Subsystem Description](#2-hardware-subsystem-description)
3. [System Initialization and Boot Procedure](#3-system-initialization-and-boot-procedure)
4. [Network Provisioning and Configuration](#4-network-provisioning-and-configuration)
5. [Web Interface Access and Navigation](#5-web-interface-access-and-navigation)
6. [Environmental Monitoring Dashboard](#6-environmental-monitoring-dashboard)
7. [Actuator Control Interface](#7-actuator-control-interface)
8. [Environmental Alert System](#8-environmental-alert-system)
9. [Machine Learning Subsystem Status Interface](#9-machine-learning-subsystem-status-interface)
10. [System Configuration Interface](#10-system-configuration-interface)
11. [Mobile Application Integration](#11-mobile-application-integration)
12. [MASHAuto Automation Engine — Operational Reference](#12-mashauto-automation-engine--operational-reference)
13. [Firmware Update Procedures](#13-firmware-update-procedures)
- [Appendix A — Diagnostic Procedures and Error Resolution](#appendix-a--diagnostic-procedures-and-error-resolution)
- [Appendix B — Environmental Threshold Parameters Reference](#appendix-b--environmental-threshold-parameters-reference)
- [Appendix C — Actuator Hardware Reference](#appendix-c--actuator-hardware-reference)

---

## 1. System Overview and Architecture

### 1.1 System Purpose and Scope

The M.A.S.H. IoT Environmental Control Gateway is a purpose-built embedded computing platform deployed in mushroom cultivation facilities to perform continuous closed-loop environmental management. The system addresses the precision environmental control requirements of fungal cultivation, wherein deviations in temperature, relative humidity, or carbon dioxide concentration beyond established tolerance thresholds can materially impair mycelial development, fruiting body formation, and yield quality.

The system integrates local sensor acquisition, threshold-driven and machine-learning-driven actuation, persistent local data storage, multi-channel cloud synchronization, and a locally-hosted web user interface accessible from any networked computing device within the deployment environment. The architecture is designed to maintain continuous autonomous operation independently of cloud service availability, with all critical automation functions executing locally.

### 1.2 Two-Layer Hardware Architecture

The M.A.S.H. Gateway operates through a deliberate two-layer hardware separation. The hardware abstraction layer is implemented on an Arduino Uno R3 microcontroller, which is solely responsible for sensor data acquisition via the I2C bus, relay actuator output management via digital GPIO pins, and a hardware-level safety watchdog mechanism. The control and intelligence layer is implemented on a Raspberry Pi single-board computer running a Linux-based operating system, which hosts the Flask web server, the SQLite persistent data store, the scikit-learn machine learning inference pipeline, the Firebase Realtime Database synchronization client, the MQTT publish/subscribe client, and the NetworkManager-based Wi-Fi provisioning subsystem.

These two layers communicate exclusively through a USB serial data channel operating at 9,600 bits per second with 8 data bits, no parity bit, and one stop bit (8N1 framing). The Arduino transmits JSON-serialized environmental sensor readings to the Raspberry Pi every five seconds. The Raspberry Pi transmits JSON-serialized relay control commands to the Arduino in response to automation decisions or user-initiated control actions.

### 1.3 Connectivity and Data Access Architecture

The system provides environmental monitoring data and control access through four independent pathways. The primary pathway is the locally-hosted Flask web application accessible via HTTP at port 5000, serving clients on the local area network through direct IP address or optionally through mDNS hostname resolution. The secondary pathway is the MASH Grower mobile application, which communicates with the gateway either through direct local HTTP polling when the mobile client is connected to the same local area network, or through Firebase Realtime Database subscription when remote access is required. The tertiary pathway is the Firebase Realtime Database, which receives real-time sensor telemetry via the Firebase Admin SDK as data is acquired. The quaternary pathway is the HiveMQ cloud MQTT broker, which enables low-latency command delivery from remote clients.

The system implements an offline-first data persistence strategy: all incoming sensor readings are committed to the local SQLite database as the primary write operation, after which cloud synchronization is attempted as a non-blocking secondary operation. This architecture guarantees data continuity during network interruptions.

---

## 2. Hardware Subsystem Description

### 2.1 Computational Components

The primary computational platform is a Raspberry Pi single-board computer (Models 3B or 4B), operating under a Debian Linux distribution. This platform executes the MASH gateway software stack, which includes the Python-based Flask web application, the scikit-learn inference runtime, the SQLite database engine, the Firebase Admin SDK, the Paho MQTT client library, and the NetworkManager Python binding. The secondary computational component is an Arduino Uno R3 microcontroller, which operates independently of the Raspberry Pi for its critical safety functions. The Arduino is physically connected to the Raspberry Pi via USB, through which it both receives power and maintains the serial communication channel.

### 2.2 Environmental Sensing

Environmental measurements are acquired from two Sensirion SCD41 sensor modules, one positioned within the fruiting cultivation chamber and one within the spawning cultivation chamber. Each SCD41 module is capable of simultaneous carbon dioxide concentration measurement (photoacoustic NDIR method), temperature measurement, and relative humidity measurement. The two sensor modules share the I2C address 0x62; disambiguation is achieved through the use of separate I2C buses. The fruiting chamber sensor communicates via the Arduino's hardware I2C interface (analog pins A4 and A5 serving as SDA and SCL respectively), implemented through the Arduino Wire library. The spawning chamber sensor communicates via a software-emulated I2C interface (digital pins D10 and D11 serving as SDA and SCL respectively), implemented through the SoftWire library. This bus-based differentiation strategy eliminates the requirement for hardware address reconfiguration.

### 2.3 Relay Actuation Hardware

Physical load switching is performed by an eight-channel relay module connected to the Arduino's digital output GPIO pins and operating under active-low logic. In this configuration, a GPIO low-voltage output (logic level 0) energizes the relay coil and closes the normally-open contact, thereby connecting the load to the AC supply. A GPIO high-voltage output (logic level 1) de-energizes the relay coil and opens the contact. On every power-on cycle, the Arduino firmware initializes all relay control pins to the high logic state, ensuring that all controlled loads are in the de-energized (inactive) condition at system startup. The relay module switches 220V AC loads including ventilation fans, an ultrasonic mist maker, and LED grow lights.

### 2.4 Safety Watchdog Mechanism

The Arduino firmware implements a hardware-level safety watchdog independent of the Raspberry Pi control layer. The watchdog monitors the elapsed time since the most recent serial command received from the Raspberry Pi. If this interval exceeds sixty seconds, the watchdog logic unconditionally forces all relay control pins to the high logic state, thereby de-energizing all connected loads. This mechanism ensures that all actuators are returned to the inactive state in the event of Raspberry Pi failure, serial link interruption, or gateway software crash, preventing any load from remaining in an unattended active condition.

---

## 3. System Initialization and Boot Procedure

### 3.1 Boot Sequence

Upon application of power, the Raspberry Pi initiates the Linux boot process, which includes filesystem checks, system service initialization, and the deferred launch of the MASH gateway systemd service. The MASH gateway service startup follows a deterministic initialization sequence. The sequence begins with the loading of user preferences from persistent storage, followed by the parsing of the primary configuration file (`config/config.yaml`) and the application of any environment variable overrides sourced from the `.env` secrets file. The firmware version string is injected into the runtime configuration at this stage.

Following configuration loading, the Flask web application instance is created, Cross-Origin Resource Sharing (CORS) headers are configured, and the route blueprint is registered. A network connectivity assessment is then performed: if the system identifies an active network interface with internet reachability, normal operation proceeds; otherwise, the NetworkManager hotspot provisioning interface (`MASH-Device`) is activated to enable first-time network configuration. The subsequent initialization phase proceeds in order through SQLite database initialization, backend REST API client construction, Firebase Admin SDK initialization, MQTT client connection establishment, Arduino serial port detection and connection, and machine learning model loading.

### 3.2 Sensor Warmup Period

Immediately upon receipt of the first valid sensor data frame from the Arduino, the system enters a thirty-second sensor warmup state, indicated by the runtime flag `sensor_warmup_complete = False`. During this interval, incoming sensor data is recorded to the database and forwarded to the cloud synchronization pipeline, but the MASHAuto automation engine is inhibited from issuing actuation commands. This delay is implemented to prevent false actuator activations arising from transient sensor readings that may occur immediately after the SCD41 sensors are powered and before their measurement outputs have stabilized. On the expiry of the thirty-second interval, the warmup flag transitions to `True`, and the automation engine becomes active.

### 3.3 Expected Initialization Duration

The total elapsed time from power application to full system operational status, encompassing Linux boot, service initialization, and sensor warmup, is typically in the range of fifty to sixty-five seconds under normal operating conditions on a Raspberry Pi 3B or 4B.

---

## 4. Network Provisioning and Configuration

### 4.1 Provisioning Mechanism

Network configuration is managed through the NetworkManager subsystem via its command-line interface (`nmcli`). On first deployment, or whenever the system cannot associate with a previously configured wireless network, the gateway activates a Wi-Fi hotspot using the NetworkManager AP connection profile. This hotspot presents under the service set identifier `MASH-Device`, operates on the 2.4 GHz band with open authentication (no pre-shared key), and assigns connected clients IP addresses within the `10.42.0.0/24` subnet. The gateway itself is reachable at `10.42.0.1` on port 5000 while in this provisioning state.

### 4.2 Provisioning Web Interface

The provisioning interface is served at the path `/wifi-setup` on the gateway's Flask web server. This interface enumerates available wireless networks detected by the NetworkManager scan subsystem and presents them to the user via an HTML form. The user selects the target SSID from the enumerated list or enters a custom SSID, and provides the corresponding pre-shared key. Submission of this form initiates the following sequence on the gateway: the NetworkManager AP connection profile is deactivated, a new NetworkManager station connection profile is created with the supplied SSID and credentials, and NetworkManager is instructed to activate this new profile.

### 4.3 Post-Provisioning Transition

Upon successful association with the specified wireless network, the provisioning hotspot connection is deactivated, the gateway's network interface is reassigned a DHCP-issued address from the infrastructure router, and normal operation resumes. The transition process typically completes within thirty seconds. A failsafe mechanism is implemented: if association with the specified network has not been confirmed within thirty seconds of provisioning form submission, NetworkManager is instructed to re-activate the hotspot, allowing the operator to reattempt configuration. The provisioning transition page at `/wifi-connecting` presents this status to the operator during the transition interval.

---

## 5. Web Interface Access and Navigation

### 5.1 Access Endpoints

The web application is accessible through multiple addressing schemes depending on network configuration. The primary access method during provisioning is through the fixed IP address `10.42.0.1` at port 5000. Following network configuration and DHCP address assignment, the primary access method is through the dynamically assigned IP address at port 5000, which the operator may obtain from the network router's device table. If the optional Avahi mDNS daemon is active on the gateway, the friendly hostname `mash.lan` may be used as an alternative address for compatible clients. All access methods use the HTTP protocol on port 5000; the application does not implement HTTPS or TLS termination in the local deployment configuration.

### 5.2 Navigation Structure

The web application is structured as a multi-page Flask application with a persistent left-column navigation sidebar rendered through a shared Jinja2 base template. The sidebar provides navigation links to the five primary interface sections: Dashboard (`/dashboard`), Controls (`/controls`), Alerts (`/alerts`), AI Insights (`/ai_insights`), and Settings (`/settings`). The dashboard is the designated default landing page. The WiFi provisioning interfaces at `/wifi-setup` and `/wifi-connecting` are rendered without the shared navigation sidebar, as they are designed for access exclusively in the provisioning state.

---

## 6. Environmental Monitoring Dashboard

### 6.1 Overview and Update Behavior

The Dashboard page (`/dashboard`) provides the primary real-time environmental monitoring interface. The page implements client-side periodic data polling, retrieving current sensor data and system status from the gateway's REST API at a three-second interval using asynchronous JavaScript requests. This polling architecture enables continuous display updates without full page reloads.

### 6.2 Room Selection Interface

A binary selection control at the top of the page allows the operator to select between the Fruiting Room and Spawning Room data views. The selection determines which room's sensor data is displayed in the sensor metric cards and which room's actuator assignments are represented in the actuator status icons.

### 6.3 System Status Indicators

A status strip displays four system-level indicators derived from the gateway's runtime state. The first indicator reports the Arduino serial connection status, presenting as "Connected" when the serial data pipe is active and as "Offline" when serial communication has been interrupted or lost. The second indicator reports the current wireless network association, displaying the associated SSID when connected or a disconnection state indicator. The third indicator reports Firebase Realtime Database synchronization activity, reflecting the current state of the cloud data push pipeline. The fourth indicator reports the elapsed uptime of the MASH gateway service since the most recent process start.

### 6.4 Environmental Status Classification

Each room's environmental data is accompanied by a composite condition badge that communicates the overall environmental status. The badge classification logic applies the following rules against the room's configured threshold parameters: the "Optimal" classification is assigned when all three measured parameters (temperature, relative humidity, and carbon dioxide concentration) are within their configured nominal ranges; "Warning" when at least one parameter is approaching but has not exceeded its threshold limit; "Critical" when at least one parameter has exceeded its configured threshold limit; and "Waiting" when no valid sensor data has yet been received.

### 6.5 Actuator Status Representation

The lower section of the Dashboard displays read-only status icons for all actuators assigned to the selected room. These icons reflect the most recently reported actuation state for each device and are updated with each polling cycle. This component provides passive monitoring visibility only; actuator control interactions are reserved for the Controls interface.

---

## 7. Actuator Control Interface

### 7.1 Operation Mode Selection

The Controls page (`/controls`) presents actuator management through a two-mode framework governed by a primary toggle control at the top of the page. In the Automatic Control mode (toggle active), the MASHAuto automation engine retains exclusive authority over all actuation commands, and the individual actuator control cards are rendered in an interaction-disabled state. In the Manual Control mode (toggle inactive), the automation engine suspends command issuance, and all actuator control cards respond to operator interaction. Transitioning between modes does not reset any actuator to a default state; each actuator retains its current state at the moment of mode change until explicitly modified.

### 7.2 Actuator Control Cards

Each managed actuator is represented by a dedicated control card displaying the actuator name, its operational role badge (indicating whether it operates under automated threshold logic, a fixed time schedule, periodic interval cycling, or adaptive flush behavior), and its current binary state. In Manual Control mode, the operator may interact with any card to toggle its associated relay. Each toggle interaction transmits a JSON-serialized command to the Arduino co-processor via the serial interface, and the relay responds within approximately one to two seconds. A five-second command cooldown is enforced per actuator following each toggle interaction to protect relay hardware from rapid command cycling.

### 7.3 Actuator Classification Badges

The operational role badges displayed on actuation cards communicate the governance model under which each actuator operates. The "AUTO" badge designates actuators governed in real time by the MASHAuto threshold and machine-learning decision pipeline. The "TIMED" badge designates actuators that follow a deterministic clock-based on/off schedule. The "PASSIVE" badge designates actuators that execute a recurring interval cycle regardless of sensor conditions. The "FLUSH" badge designates actuators capable of entering an emergency continuous-run state triggered by a sensor threshold exceedance, overriding the normal passive cycle.

---

## 8. Environmental Alert System

### 8.1 Alert Generation

The alert subsystem continuously evaluates incoming sensor data against a set of configurable threshold parameters. When a measurement crosses a configured threshold, the system generates an alert record and persists it to the SQLite `alerts` table. Alert records are classified by severity into three tiers: Critical (indicating conditions that pose an immediate risk to crop viability), Warning (indicating conditions trending toward a threshold breach or already outside the nominal range), and Informational (indicating non-urgent condition notifications).

### 8.2 Alert Interface

The Alerts page (`/alerts`) presents all current unacknowledged alert records in a tabular format, with each record displaying the affected room identifier, alert severity classification, a human-readable condition description, and the timestamp of initial detection. An acknowledge action control is associated with each active alert record. When the operator acknowledges an alert, the record is marked as acknowledged in the database and removed from the active alerts display. Acknowledged records are transferred to the Alert History table, which retains a rolling collection of the fifty most recently acknowledged records. A summary card group at the top of the page presents aggregate counts of active issues, critical alerts, and warning alerts.

### 8.3 Threshold Parameters for Alert Generation

Critical alerts are generated when carbon dioxide concentration in the fruiting room exceeds 1,500 parts per million, when carbon dioxide concentration in the spawning room exceeds 2,000 parts per million, when temperature in either room exceeds 30.0 degrees Celsius, when temperature in either room falls below 18.0 degrees Celsius, or when relative humidity in either room falls below 70 percent. Warning alerts are generated when parameter values exceed the per-room configured nominal maximum or minimum limits but remain below the critical thresholds.

---

## 9. Machine Learning Subsystem Status Interface

### 9.1 AI Insights Interface Overview

The AI Insights page (`/ai_insights`) presents a read-only status dashboard for the embedded machine learning inference subsystem. This interface does not provide operator controls; its purpose is to communicate the operational status of the two ML model components that underpin the MASHAuto automation engine to support transparency and diagnostic oversight.

### 9.2 ML Runtime Status

The page evaluates and displays the availability of the scikit-learn Python library on the gateway host, which constitutes the required inference runtime for both deployed models. It further evaluates the `ml_enabled` configuration flag in `config/config.yaml` to determine whether the ML subsystem is enabled at the application level. Both conditions must be satisfied for the automation engine to function under ML-governed decision-making.

### 9.3 Model Component Status

The two model components — the Isolation Forest anomaly detection model (`data/models/isolation_forest.pkl`) and the Decision Tree actuation classifier (`data/models/decision_tree.pkl`) — are each presented with an individual status indicator reflecting whether the serialized model artifact has been successfully loaded into memory. A status of "Model Active" indicates successful deserialization and inference readiness. A status of "Not Loaded" indicates that the model file is absent or could not be deserialized, which will cause the automation engine to fall back to a rule-based actuation mode for the affected function.

---

## 10. System Configuration Interface

### 10.1 Settings Interface Structure

The Settings page (`/settings`) is organized as a five-tab interface providing access to general system information, network configuration, cloud synchronization controls, power management operations, and firmware version management.

### 10.2 General Tab

The General tab presents the current system time retrieved from the gateway operating system clock, updated at one-second intervals, and the elapsed service uptime since the most recent MASH gateway process start. These values are informational and not configurable through the interface.

### 10.3 WiFi Configuration Tab

The WiFi tab displays the current network association status, including the connected SSID and the DHCP-assigned local IP address. This tab also provides a "Disconnect and Enable Provisioning" control, which instructs NetworkManager to deactivate the current station connection and activate the provisioning hotspot. This control is used to initiate network reconfiguration, such as when migrating the device to a new physical location with a different wireless infrastructure. Execution of this control immediately terminates cloud synchronization, mobile application Cloud Mode connectivity, and MQTT broker connectivity.

### 10.4 Cloud Synchronization Tab

The Cloud Sync tab provides a toggle control governing the Firebase Realtime Database synchronization pipeline. When the toggle is in the active state, all incoming sensor data and actuation state change events are transmitted to the configured Firebase project in real time via the Firebase Admin SDK push operations. When the toggle is in the inactive state, the Firebase synchronization pipeline is suspended, and data continues to be persisted exclusively to the local SQLite database. The toggle state is persisted to the application's user preferences store and survives service restarts.

### 10.5 Power Controls Tab

The Power Controls tab exposes two system state transition operations. The reboot operation initiates a controlled restart of the Raspberry Pi, after which the MASH gateway service resumes automatically, restoring full environmental monitoring within approximately sixty seconds. The shutdown operation initiates a graceful system halt, after which restoration of service requires physical removal and reapplication of power. Both operations are gated by a confirmation dialog.

### 10.6 About System and Firmware Management Tab

The About System tab displays product identification information including the installed firmware version string, the hardware platform designation, the operating system environment, and an update status badge reflecting the most recently retrieved comparison between the installed version and the latest release available on the gateway's configured GitHub Releases endpoint. A "Check for Updates" control initiates a synchronous API query to the GitHub Releases API to refresh the update status badge. A "History" control opens a modal presenting the complete version changelog registry maintained within the firmware, covering all previous releases.

---

## 11. Mobile Application Integration

### 11.1 Device Pairing

The MASH Grower mobile application (Android) supports two device pairing modalities. The first modality is manual MASH ID entry, in which the operator inputs the device's unique serial identifier (formatted as `MASH-##-#####-######`, as printed on the device enclosure label and reproducible from the About System tab) into the application's device connection interface. The second modality is QR code scanning, in which the operator activates the QR code display modal on the gateway Dashboard (via the floating action button in the lower right corner) and presents the rendered QR code symbol to the mobile application's integrated camera scanner. The QR code payload encodes the MASH ID, device display name, local IP address, and port number, enabling the application to populate all connection parameters without manual operator entry.

### 11.2 Connection Mode Selection

Following pairing, the mobile application establishes a connection to the gateway in one of two modes, selected automatically based on network topology. In the Local mode, applicable when the mobile client is associated with the same wireless local-area network as the gateway, the application communicates directly with the gateway's Flask HTTP API on port 5000, polling for sensor data at ten-second intervals and delivering actuator control commands via HTTP POST requests. This mode achieves command delivery latency under one second. In the Cloud mode, applicable when the mobile client is on a different network than the gateway, the application consumes sensor data from Firebase Realtime Database subscription events and delivers actuator control commands via the MQTT broker or Firebase-mediated command delivery, achieving typical command latency of one to five seconds.

---

## 12. MASHAuto Automation Engine — Operational Reference

### 12.1 Engine Architecture

The MASHAuto automation engine, implemented in `app/core/logic_engine.py`, operates as a continuously executing evaluation loop driven by incoming serial sensor data frames. The engine implements a two-stage decision pipeline. In the first stage, each incoming sensor data frame is evaluated by the Isolation Forest anomaly detection model to identify statistically anomalous readings. Readings identified as anomalous are replaced by the most recently accepted valid reading for the affected parameter, ensuring that subsequent actuation decisions are based on plausible environmental data. In the second stage, the validated, anomaly-corrected sensor readings — augmented by the current wall-clock hour as a time-of-day feature — are passed as an input feature vector to the Decision Tree actuation classifier. The classifier outputs a binary actuation state recommendation for each managed actuator based on patterns learned from historical labeled environmental data collected within the facility.

### 12.2 Fruiting Room Automation Logic

The fruiting room automation logic governs six actuators: the exhaust fan, the intake blower fan, the humidifier fan, the Mist Maker ultrasonic atomizer, and the LED grow lights. When the measured relative humidity in the fruiting room falls below 85 percent, the HumidifierCycleManager component initiates a recurring two-phase humidification cycle. Phase one activates the Mist Maker for a duration of ten seconds while maintaining the humidifier fan in the inactive state; phase two deactivates the Mist Maker and activates the humidifier fan for thirty seconds to distribute the generated aerosol throughout the chamber volume. This two-phase cycle repeats until the measured humidity returns to the 90 percent target value. The cycle manager additionally implements a predictive termination mechanism: if the rate of humidity increase observed across the three most recent readings indicates that the humidity is trending rapidly toward 95 percent, the cycle is terminated preemptively to prevent overshoot. When measured carbon dioxide concentration in the fruiting room exceeds 1,000 parts per million, the exhaust fan is activated. The exhaust fan is deactivated when the concentration subsequently falls below a hysteresis threshold of 900 parts per million. When measured temperature in the fruiting room exceeds 26.0 degrees Celsius, the exhaust fan is activated independently of the CO₂ level. The LED grow lights are governed by a fixed clock schedule, activating at 08:00 hours and deactivating at 20:00 hours.

### 12.3 Spawning Room Automation Logic

The spawning room automation logic governs a single actuator: the spawning room exhaust fan. The fan operates under a passive interval cycling mode as its baseline behavior, activating for two minutes at thirty-minute intervals regardless of sensor conditions. This passive cycling provides a minimum ventilation rate for carbon dioxide removal and temperature regulation. In addition to passive cycling, the fan is subject to a flush override trigger: when measured carbon dioxide concentration exceeds 2,000 parts per million, the fan transitions to Flush mode, operating continuously for five minutes to rapidly reduce the elevated CO₂ concentration. The fan additionally activates when measured temperature exceeds 27.0 degrees Celsius.

### 12.4 Device Room Ventilation

A dedicated device enclosure exhaust fan is managed by a fixed clock schedule, activating for three minutes at each of four daily time points: 08:00, 12:00, 16:00, and 20:00 hours. This scheduled ventilation prevents heat accumulation within the electronics enclosure.

### 12.5 Manual Override Handling

When an operator issues a manual actuation command through the web interface or mobile application while the automation engine is in Automatic Control mode, the engine records a manual override for the affected actuator and refrains from issuing further commands for that actuator for a five-minute override window. This mechanism allows temporary operator intervention without requiring a full mode switch. Override records are cleared when the override window expires, at which point the automation engine resumes autonomous management of the actuator. All outstanding overrides are cleared immediately upon any explicit transition from Manual Control mode to Automatic Control mode.

---

## 13. Firmware Update Procedures

### 13.1 Update Availability Assessment

The gateway continuously assesses update availability by polling the GitHub Releases API endpoint for the MASH-IoT repository. The installed firmware version string is compared against the version tag of the most recent GitHub release. The update status badge in the Settings About System tab reflects the outcome of this comparison, categorizing pending updates by priority: Critical (red badge), indicating mandatory updates containing security patches or critical defect corrections; Recommended (orange badge), indicating significant stability or feature updates; and Standard (blue badge), indicating incremental or feature-enhancement releases.

### 13.2 Update Application Procedure

When an update is identified, the operator may initiate installation by interacting with the update action control presented in the About System tab or in the update notification modal. The gateway retrieves the firmware archive from the GitHub release asset endpoint, verifies the download, and applies the update in place. Upon successful application, the gateway initiates an automatic service restart to load the updated firmware. Full service restoration following the restart is expected within sixty seconds.

### 13.3 Rollback Safety Mechanism

The update system implements an A/B partition-based rollback mechanism to protect against failed updates. The previous firmware version is preserved in a designated rollback partition prior to the application of each update. If the newly installed firmware fails to achieve a successful boot state — as determined by a boot verification check executed during the service initialization sequence — the system automatically restores the previous firmware version from the rollback partition and marks the failed firmware version as incompatible in the update registry. The failed version will not be offered for installation in subsequent update cycles.

---

## Appendix A — Diagnostic Procedures and Error Resolution

### A.1 Serial Data Acquisition Failure

If the Dashboard displays null or zero sensor readings and the Sensors status indicator in the status strip shows a disconnected state, the probable cause is a loss of the USB serial data channel between the Raspberry Pi and the Arduino co-processor. The operator should verify that the USB cable connecting the two devices is fully seated at both terminations. A service restart via the Settings Power Controls Reboot function will cause the gateway software to re-execute the serial port auto-detection routine, which scans available serial interfaces in order of priority (`/dev/ttyACM0` first on Linux). If the failure persists following reboot, the USB cable should be replaced with a known-good cable.

### A.2 Wi-Fi Association Failure During Provisioning

If the gateway does not successfully associate with the specified wireless network following the submission of the WiFi provisioning form, and the provisioning hotspot subsequently reactivates, the operator should verify the accuracy of the SSID and pre-shared key entered during provisioning, with particular attention to case sensitivity, character substitution, and leading or trailing whitespace. The operator should also confirm that the target network operates on the 2.4 GHz frequency band, as the gateway wireless interface does not support 5 GHz operation. Physical proximity to the access point should be maximized to eliminate signal margin as a contributing factor.

### A.3 Web Interface Inaccessibility

If a browser client is unable to connect to the gateway web interface by IP address, the operator should confirm that the client device is associated with the same wireless local-area network as the gateway, that the gateway has completed its boot sequence (minimum sixty seconds should be allowed), and that the connection attempt targets port 5000 using the HTTP scheme. The gateway's IP address may be verified through the network router's DHCP client table or, if the gateway touchscreen is operative, through direct observation of the displayed dashboard which includes the IP in the WiFi status indicator.

### A.4 Automation Engine Not Responding

If actuators are not activating in response to environmental conditions while the Controls page mode toggle indicates Automatic Control, the operator should first allow a minimum of sixty seconds following any mode transitions or service restarts, as the sensor warmup inhibitor suppresses automation during this interval. The AI Insights page should be consulted to confirm that both machine learning models report Active status. The operator should also verify that sensor readings displayed on the Dashboard are non-zero and updating, as the automation engine requires valid sensor input to make actuation decisions.

### A.5 Mobile Application Connection Failure

If the MASH Grower mobile application cannot establish a connection to the gateway, the operator should verify that the MASH ID entered in the application corresponds exactly to the device serial identifier displayed in the Settings About System tab. For Local mode connectivity, the mobile device must be associated to the same wireless network as the gateway. For Cloud mode connectivity, both the gateway and mobile device require functional internet access, and the Firebase Realtime Sync setting in the gateway Settings Cloud Sync tab must be in the enabled state.

### A.6 Firmware Update Failure

In the event that a firmware update cannot be applied successfully, the gateway's rollback mechanism will restore the prior firmware version automatically. If the gateway is completely non-responsive following an update attempt, a power cycle should be performed. The rollback restoration process completes within approximately ninety seconds of power application. Following rollback restoration, the failed firmware version will not be presented as an update candidate in subsequent update checks.

---

## Appendix B — Environmental Threshold Parameters Reference

### B.1 Fruiting Room Parameters

The fruiting room environmental control targets and alert thresholds are configured as follows. The nominal temperature target is 24.0 degrees Celsius, with a permissible operating range of 22.0 to 26.0 degrees Celsius. Warning alerts are generated when temperature falls outside this range; critical alerts are generated when temperature falls below 18.0 degrees Celsius or exceeds 30.0 degrees Celsius. The nominal relative humidity target is 90.0 percent, with a permissible operating range of 85.0 to 95.0 percent. Critical alerts are generated when relative humidity falls below 70.0 percent. The maximum permissible carbon dioxide concentration is 1,000 parts per million; the exhaust fan is activated at this threshold and deactivated at a hysteresis value of 900 parts per million. Critical CO₂ alerts are generated when concentration exceeds 1,500 parts per million.

### B.2 Spawning Room Parameters

The spawning room environmental control targets and alert thresholds are configured as follows. The nominal temperature target is 25.0 degrees Celsius, with a permissible operating range of 23.0 to 27.0 degrees Celsius. The nominal relative humidity target is 95.0 percent, with a permissible operating range of 90.0 to 98.0 percent. The maximum permissible carbon dioxide concentration is 2,000 parts per million, at which point the exhaust fan flush override is activated.

### B.3 Ventilation Schedules

The spawning room exhaust fan passive interval cycle operates with a two-minute active period at a thirty-minute recurrence interval. The device room exhaust fan scheduled cycle operates with a three-minute active period at the time points 08:00, 12:00, 16:00, and 20:00 hours daily.

---

## Appendix C — Actuator Hardware Reference

### C.1 Actuator Assignments

The system manages seven actuators through the eight-channel relay module. The fruiting room is served by five actuators: a fruiting exhaust fan (Arduino digital pin 3, relay channel 2) responsible for carbon dioxide and temperature removal; a fruiting intake blower fan (Arduino digital pin 4, relay channel 3) responsible for fresh air introduction; a humidifier fan (Arduino digital pin 5, relay channel 4) responsible for aerosol distribution; a Mist Maker ultrasonic atomizer (Arduino digital pin 6, relay channel 5) responsible for humidity generation; and LED grow lights (Arduino digital pin 7, relay channel 6) operating under a fixed photoperiod schedule. The spawning room is served by one actuator: a spawning exhaust fan (Arduino digital pin 2, relay channel 1) operating in passive interval and flush override modes. The device electronics enclosure is served by one actuator: a device exhaust fan (Arduino digital pin 8, relay channel 7) operating under a fixed clock ventilation schedule.

### C.2 Serial Command Protocol

The Raspberry Pi transmits actuation commands to the Arduino co-processor as JSON objects over the USB serial interface at 9,600 baud. Each command object contains two fields: the key `actuator` carrying the firmware-designated actuator name string, and the key `state` carrying the desired state string ("ON" or "OFF"). Representative command examples follow:

```json
{"actuator": "FRUITING_EXHAUST_FAN", "state": "ON"}
{"actuator": "MIST_MAKER", "state": "OFF"}
{"actuator": "SPAWNING_EXHAUST_FAN", "state": "ON"}
```

On gateway service shutdown or following detection of serial link loss, the gateway transmits an `ALL_OFF` sentinel command to the Arduino, instructing the co-processor to de-energize all relay channels regardless of their current state. The hardware safety watchdog augments this software-level safety command by independently enforcing all-relays-off behavior in the event that the `ALL_OFF` command is not received within sixty seconds.

---

*This document constitutes the complete operational reference for firmware revision v2.8.0 of the M.A.S.H. IoT Environmental Control Gateway. All specifications, thresholds, and behavioral descriptions reflect the configuration defined in `config/config.yaml` version corresponding to firmware v2.8.0.*

*Technical support: mash.mushroom.automation@gmail.com*
*© 2026 Mushroom Automation w/ Smart Hydro-Environment (M.A.S.H.). All rights reserved.*
