# M.A.S.H. IoT Project Setup Guide

This guide provides step-by-step instructions for setting up the M.A.S.H. IoT system on a Raspberry Pi and programming the Arduino microcontroller.

## Table of Contents
1.  [Prerequisites](#1-prerequisites)
2.  [Raspberry Pi Gateway Setup](#2-raspberry-pi-gateway-setup)
3.  [Arduino Firmware Setup](#3-arduino-firmware-setup)
4.  [Kiosk Mode Configuration](#4-kiosk-mode-configuration)
5.  [System Verification](#5-system-verification)
6.  [Updating the Application](#6-updating-the-application)
7.  [Troubleshooting](#7-troubleshooting)

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

These steps configure the main control application on the Raspberry Pi. Since the repository is private and the organization disables Deploy Keys, you must use a **Personal Access Token (PAT)** to grant the Raspberry Pi secure access.

#### 2.1. Set Up GitHub Access (Personal Access Token)

This is a **one-time setup** to grant the Raspberry Pi access to the private repository.

1.  **Generate a Personal Access Token on GitHub**
    *   Log in to your GitHub account.
    *   Go to **Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
    *   Click **Generate new token** and select **Generate new token (classic)**.
    *   In the **Note** field, give your token a descriptive name, like `MASH IoT RPi Access`.
    *   Set an **Expiration** date for the token (e.g., 30 or 90 days).
    *   Under **Select scopes**, check the box next to **`repo`**. This will grant the token permission to access your private repository.
    *   Scroll down and click **Generate token**.

2.  **Copy Your New Token**
    *   **CRITICAL:** GitHub will show you the token only once. Copy the token string immediately and save it in a secure place temporarily. You will need it for the next step.

#### 2.2. Clone the Repository and Install Dependencies

1.  **Clone the Repository via HTTPS**
    Open a terminal on your Raspberry Pi and run the standard clone command:
    ```bash
    git clone https://github.com/MASH-Mushroom-Automation/MASH-IoT.git
    cd MASH-IoT
    ```

2.  **Authenticate When Prompted**
    *   When the terminal prompts you for a **Username**, enter your GitHub username and press Enter.
    *   When it prompts you for a **Password**, **paste the Personal Access Token** you just created. Do not enter your normal GitHub password.

    Git will now clone the repository. It should also automatically cache your token, so you won't need to enter it again for future updates.

3.  **Navigate to the Gateway Directory**
    ```bash
    cd rpi_gateway
    ```

4.  **Create a Python Virtual Environment**
    ```bash
    python3 -m venv venv
    ```

5.  **Activate the Virtual Environment**
    ```bash
    source venv/bin/activate
    ```

6.  **Upgrade Build Tools**
    ```bash
    pip install --upgrade pip setuptools wheel
    ```

7.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

8.  **Run the Application**
    ```bash
    python -m app.main
    ```
    The server should start on `http://127.0.0.1:5000`. You can now stop it with `Ctrl+C`.

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

### 6. Updating the Application

Because you authenticated with a Personal Access Token when you cloned, the `update.sh` script will work without any changes.

1.  **Navigate to the Scripts Directory**
    ```bash
    cd ~/MASH-IoT/scripts
    ```

2.  **Make the Update Script Executable** (if you haven't already)
    ```bash
    chmod +x update.sh
    ```

3.  **Run the Script**
    This command will fetch the latest code, update dependencies, and restart the app.
    ```bash
    ./update.sh
    ```

---

### 7. Troubleshooting

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

#### Kiosk Mode Browser Does Not Start

If you reboot and the Raspberry Pi goes to the desktop instead of launching the full-screen browser, the autostart configuration may be incorrect.

**Solution: Check the `autostart` file**

1.  Open a terminal on the Raspberry Pi.
2.  View the contents of the LXDE autostart file:
    ```bash
    cat ~/.config/lxsession/LXDE-pi/autostart
    ```
3.  Ensure that a line similar to the following exists in the file. It starts with `@` and points to `chromium-browser`:
    ```bash
    @/usr/bin/chromium-browser --password-store=basic --kiosk ... http://localhost:5000
    ```
4.  If that line is missing, the setup script may have failed. You can try running it again:
    ```bash
    cd ~/MASH-IoT/scripts
    ./setup_kiosk.sh
    ```
    Then reboot the Raspberry Pi.
