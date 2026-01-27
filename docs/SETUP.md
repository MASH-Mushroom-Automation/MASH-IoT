# M.A.S.H. IoT Project Setup Guide

This guide provides step-by-step instructions for setting up the M.A.S.H. IoT system on a Raspberry Pi and programming the Arduino microcontroller.

## Table of Contents
1.  [Prerequisites](#1-prerequisites)
2.  [Raspberry Pi Gateway Setup](#2-raspberry-pi-gateway-setup)
3.  [Arduino Firmware Setup](#3-arduino-firmware-setup)
4.  [Kiosk Mode Configuration](#4-kiosk-mode-configuration)
5.  [System Verification](#5-system-verification)
6.  [Troubleshooting](#6-troubleshooting)

---

### 1. Prerequisites

#### Hardware
*   Raspberry Pi 3B or newer (with Raspberry Pi OS)
*   Arduino Uno R3 or compatible board
*   SCD41 CO2/Temp/Humidity Sensors (x2)
*   8-Channel Relay Module
*   All necessary wiring, power supplies, and mushroom cultivation actuators (fans, humidifier).
*   Raspberry Pi 7" Touchscreen Display (Recommended)

#### Software
*   [Git](https://git-scm.com/downloads)
*   [Python 3.8+](https://www.python.org/downloads/)
*   [Visual Studio Code](https://code.visualstudio.com/) with the following extensions:
    *   **PlatformIO IDE:** For compiling and uploading Arduino firmware.
    *   **Python:** For Raspberry Pi development.

---

### 2. Raspberry Pi Gateway Setup

These steps configure the main control application on the Raspberry Pi.

1.  **Clone the Repository**
    Open a terminal on your Raspberry Pi and clone the project:
    ```bash
    git clone https://github.com/MASH-Mushroom-Automation/MASH-IoT.git
    cd MASH-IoT
    ```

2.  **Navigate to the Gateway Directory**
    All commands for the gateway should be run from this directory.
    ```bash
    cd rpi_gateway
    ```

3.  **Create a Python Virtual Environment**
    This isolates the project's dependencies from the system's Python installation.
    ```bash
    python3 -m venv venv
    ```

4.  **Activate the Virtual Environment**
    You must activate the environment in every new terminal session before running the application.
    ```bash
    source venv/bin/activate
    ```
    *On Windows, the command is `venv\\Scripts\\activate`.*

5.  **Upgrade Build Tools**
    Before installing the dependencies, upgrade pip's core tools to prevent build errors, especially on Raspberry Pi.
    ```bash
    pip install --upgrade pip setuptools wheel
    ```

6.  **Install Dependencies**
    This command reads the `requirements.txt` file and installs all necessary Python libraries.
    ```bash
    pip install -r requirements.txt
    ```

7.  **Run the Application**
    To start the web server and the Arduino communication loop, run the main module:
    ```bash
    python -m app.main
    ```
    You should see output indicating that the server has started, typically on `http://127.0.0.1:5000`.

---

### 3. Arduino Firmware Setup

These steps use the PlatformIO IDE extension in VS Code to flash the firmware onto the Arduino.

1.  **Open the Project in VS Code**
    Open the root `MASH-IoT` folder in Visual Studio Code.

2.  **Open the PlatformIO CLI**
    In VS Code, open a new terminal and select "PlatformIO CLI" or use the standard terminal.

3.  **Navigate to the Firmware Directory**
    ```bash
    cd arduino_firmware
    ```

4.  **Build the Firmware**
    This command compiles the C++ code to ensure there are no errors.
    ```bash
    pio run
    ```

5.  **Upload the Firmware**
    Connect the Arduino to your computer via USB and run the upload command. PlatformIO will automatically detect the port.
    ```bash
    pio run -t upload
    ```

6.  **Monitor Serial Output (Optional)**
    To see the JSON data being sent from the Arduino, use the serial monitor.
    ```bash
    pio device monitor
    ```
    The baud rate should be set to 9600.

---

### 4. Kiosk Mode Configuration

This step makes the Raspberry Pi automatically launch the dashboard in a full-screen browser on boot, which is ideal for a dedicated control panel.

1.  **Navigate to the Scripts Directory**
    From the project's root directory:
    ```bash
    cd scripts
    ```

2.  **Make the Script Executable**
    Give the script permission to be executed.
    ```bash
    chmod +x setup_kiosk.sh
    ```

3.  **Run the Setup Script**
    Execute the script. It will create a systemd service to run the backend and configure the Chromium browser to auto-start.
    ```bash
    ./setup_kiosk.sh
    ```

4.  **Reboot the Raspberry Pi**
    The changes will take effect after a reboot.
    ```bash
    sudo reboot
    ```
    After rebooting, the Raspberry Pi should automatically start the M.A.S.H. backend and open the dashboard in a full-screen browser.

---

### 5. System Verification

1.  **Check the Backend Service**
    After running the kiosk script and rebooting, you can check the status of the backend service with:
    ```bash
    sudo systemctl status mash-iot
    ```

2.  **View the Dashboard**
    On the Raspberry Pi's desktop (or any device on the same network), open a web browser and navigate to `http://<Your_RPi_IP_Address>:5000`. If you are on the Pi itself, you can use `http://127.0.0.1:5000` or `http://localhost:5000`.

---

### 6. Troubleshooting

#### `scikit-learn` Installation Fails on Raspberry Pi

If you encounter an error while `pip` is trying to install `scikit-learn`, it's likely because it cannot find a pre-compiled version for your Raspberry Pi and is failing to build it from the source code.

**Solution 1: Use a compatible version (Recommended)**

The `requirements.txt` file in this project is configured to let `pip` choose the best compatible version. If you have modified it, ensure the line for `scikit-learn` does not have a version pin, like this:
```
scikit-learn
```

**Solution 2: Install System Build Dependencies**

If the installation continues to fail, you may be missing system-level libraries needed for compilation. You can install them with the following commands:
```bash
sudo apt-get update
sudo apt-get install build-essential python3-dev libatlas-base-dev
```
After installing these, delete the `venv` folder, create a new one, activate it, and try running `pip install -r requirements.txt` again.
