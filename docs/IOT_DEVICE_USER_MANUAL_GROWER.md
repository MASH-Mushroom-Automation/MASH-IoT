# M.A.S.H. Smart Growing Device
## Easy Guide for Growers

---

**Who is this guide for?**
This guide is written for farmers, mushroom growers, and anyone who wants to use the M.A.S.H. device without needing a technology background. You do not need to know anything about computers or electronics to follow this guide.

**What is the M.A.S.H. Device?**
The M.A.S.H. Device is a small box that sits near your mushroom growing area. It measures the air inside your growing rooms and automatically adjusts your fans, mist makers, and lights to keep conditions just right for your mushrooms — 24 hours a day, without you needing to do anything once it is set up.

---

## Table of Contents

1. [What the Device Does for You](#1-what-the-device-does-for-you)
2. [What Is Inside the Box](#2-what-is-inside-the-box)
3. [Turning On the Device for the First Time](#3-turning-on-the-device-for-the-first-time)
4. [Connecting the Device to Your Wi-Fi](#4-connecting-the-device-to-your-wi-fi)
5. [Viewing the Device on Your Screen](#5-viewing-the-device-on-your-screen)
6. [Reading the Dashboard (Main Screen)](#6-reading-the-dashboard-main-screen)
7. [Controlling Your Equipment](#7-controlling-your-equipment)
8. [Understanding Alerts and Warnings](#8-understanding-alerts-and-warnings)
9. [Using the MASH App on Your Phone](#9-using-the-mash-app-on-your-phone)
10. [What the Device Does Automatically](#10-what-the-device-does-automatically)
11. [Changing Settings](#11-changing-settings)
12. [When Something Goes Wrong](#12-when-something-goes-wrong)

---

## 1. What the Device Does for You

Once the M.A.S.H. Device is set up and turned on, it works non-stop in the background so you do not have to. Here is what it does every day:

**Watches the air in your growing rooms**
Every 5 seconds, the device checks the temperature, humidity (how moist the air is), and CO₂ level (how much old air is in the room) in both your Fruiting Room and Spawning Room.

**Keeps conditions in the ideal range**
If the air gets too dry, the mist maker turns on automatically. If there is too much CO₂, the exhaust fans turn on to bring in fresh air. If the temperature goes too high, ventilation activates. This all happens without you pressing any buttons.

**Warns you when something is wrong**
If a reading goes outside a safe range — for example, the temperature gets too high or the humidity drops dangerously low — the device sends an alert to the screen and to your phone so you can act quickly.

**Saves all your data**
Every reading is saved automatically, even when there is no internet. When the connection comes back, the data is uploaded to the cloud so you can look at it anytime from your phone.

**Works on its own all night**
You do not need to check on it during the night. The device runs its automatic routines around the clock, including turning the grow lights on in the morning and off in the evening.

---

## 2. What Is Inside the Box

You do not need to understand the electronics inside. Here is a simple description of what each part does in everyday terms:

| Part                                   | What It Does for You                                                                                            |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Main computer (Raspberry Pi)**       | The brain of the device. Runs all the automation and stores your data.                                          |
| **Sensor board (Arduino)**             | Reads the sensors and controls the physical switches for your equipment.                                        |
| **Small screen (7 inch)**              | Shows the live dashboard so you can see what is happening in your rooms at a glance.                            |
| **Relay switches**                     | The "switches" that turn your fans, mist maker, and lights on and off. Think of them like smart light switches. |
| **Air quality sensor — Fruiting Room** | Measures temperature, humidity, and CO₂ in your fruiting chamber.                                               |
| **Air quality sensor — Spawning Room** | Same measurements for your spawning chamber.                                                                    |

> **You do not need to touch or adjust any of the electronics inside.** Everything is controlled from the screen or your phone.

---

## 3. Turning On the Device for the First Time

### Powering On

Plug the device into a power outlet using the power cable provided. The small screen will turn on and display a loading screen. Wait about **60 seconds** for everything to start up fully.

### What Happens During the First Minute

**Seconds 0 – 30:** The device's built-in computer starts up. The screen may stay black briefly or show a startup logo.

**Seconds 30 – 60:** The device tests the air sensors to make sure they are giving stable readings. During this short warmup time, the fans and mist maker will not activate yet. This is normal — it prevents the equipment from switching on and off unnecessarily right after power-on.

**After 60 seconds:** You should see the main dashboard screen appear, showing live readings for your growing rooms.

### If You Are Setting Up for the First Time

The very first time you turn the device on, it will not be connected to your Wi-Fi yet. You will see an **orange bar** at the top of the screen. This means the device is waiting for you to connect it to your internet. Follow the steps in the next chapter to do this.

---

## 4. Connecting the Device to Your Wi-Fi

This only needs to be done once. After the device learns your Wi-Fi password, it will connect automatically every time you turn it on.

### Step 1 — Connect Your Phone to the Device's Temporary Network

When the device is not yet connected to your Wi-Fi, it creates its own temporary wireless network so you can set it up. Using your phone:

1. Go to your phone's **Wi-Fi settings**.
2. Look for a network called **`MASH-Device`**.
3. Tap it to connect. **There is no password** — just tap Connect.

Your phone's internet will stop working temporarily while you are connected to `MASH-Device`. This is normal and expected during setup.

### Step 2 — Open the Setup Page

Open the web browser on your phone (Chrome, Safari, or any browser) and type this address:

```
10.42.0.1:5000/wifi-setup
```

A simple setup page will appear on your phone screen.

### Step 3 — Choose Your Wi-Fi Network

On the setup page, you will see a dropdown list of nearby Wi-Fi networks. Tap the dropdown and select **your home or farm network** from the list.

> **Tip:** If your network does not appear, it may use a 5 GHz band. The M.A.S.H. Device works with **2.4 GHz Wi-Fi only**. Check your router settings or ask your internet provider if you are unsure.

If your network is not listed, you can type it in manually by selecting **"Enter Manually…"** from the dropdown.

### Step 4 — Enter Your Wi-Fi Password

Type your Wi-Fi password in the password box. You can tap the eye icon next to the box to see what you typed and double-check it.

### Step 5 — Tap "Connect to Network"

Tap the **Connect to Network** button. A spinning screen will appear saying the device is applying your settings.

### Step 6 — Reconnect Your Phone to Your Normal Wi-Fi

The device is now switching over to your Wi-Fi. This takes about **30 to 60 seconds**. During this time:
- The `MASH-Device` network will disappear from your phone's Wi-Fi list.
- Your phone will lose connection to the setup page.

Go back to your phone's Wi-Fi settings and reconnect to **your normal Wi-Fi network**. After a minute, the device's screen should show that it is connected.

> **If it does not connect:** The device will restart its setup network (`MASH-Device`) automatically after 30 seconds so you can try again. Double-check the password and try once more.

---

## 5. Viewing the Device on Your Screen

The device has a small built-in screen that always shows the dashboard. You can also view and control the device from **any web browser** on any phone, tablet, or laptop connected to your farm's Wi-Fi.

### Viewing from a Phone or Laptop

1. Make sure your device is on the **same Wi-Fi network** as the MASH Device.
2. Ask someone or check your router to find out the device's IP address (a number that looks like `192.168.1.xxx`).
3. Open a browser and type: `http://192.168.1.xxx:5000` (using the actual IP address).

The dashboard will appear on your screen just like it looks on the device's built-in display.

### The Five Sections of the Interface

Once you are viewing the device, there are five sections you can navigate to using the menu on the left side of the screen:

| Section         | What It Shows You                                          |
| --------------- | ---------------------------------------------------------- |
| **Dashboard**   | Live temperature, humidity, and CO₂ for both rooms         |
| **Controls**    | Turn equipment on/off manually or switch to automatic mode |
| **Alerts**      | Warnings and critical conditions that need your attention  |
| **AI Insights** | Whether the smart automation system is working             |
| **Settings**    | Wi-Fi, cloud backup, power options, and device updates     |

---

## 6. Reading the Dashboard (Main Screen)

The Dashboard is the first thing you see and the most important screen for day-to-day use. It tells you, at a glance, whether everything in your growing rooms is healthy.

### Switching Between Rooms

At the top of the screen you will see two buttons: **Fruiting Room** and **Spawning Room**. Tap either one to view that room's readings.

### The Status Strip

Just below the room buttons is a strip of four small indicators:

| Indicator      | Green Means                                             | Red / Orange Means                    |
| -------------- | ------------------------------------------------------- | ------------------------------------- |
| **Sensors**    | Sensors are connected and working                       | Sensor connection lost — check cables |
| **Wi-Fi**      | Device is connected to your network                     | Device has lost internet connection   |
| **Cloud Sync** | Data is being backed up online                          | Data is only being saved locally      |
| **Uptime**     | How long the device has been running without restarting | —                                     |

### The Three Readings

Each room shows three large cards showing the most important numbers:

**CO₂ Level (measured in ppm)**
CO₂ stands for carbon dioxide — the old, stale air that mushrooms breathe out. The higher this number, the more stale air is in the room. Your mushrooms do best when the CO₂ level is kept below the target shown on the card. If it gets too high, the device opens the exhaust fans automatically.

**Temperature (°C)**
The current air temperature inside the growing chamber. Mushrooms are sensitive to temperature — too hot or too cold slows their growth. The device will ventilate automatically if the temperature strays too far from the ideal.

**Humidity (%)**
How moist the air is. Mushrooms need high humidity to develop properly. If humidity drops, the device turns on the mist maker automatically to bring it back up.

### The Condition Badge

Next to each room name, you will see a colored badge telling you the overall health of the room:

| Badge Color    | What It Means                                         | What to Do                                           |
| -------------- | ----------------------------------------------------- | ---------------------------------------------------- |
| 🟢 **Optimal**  | All three readings are in the ideal range             | Nothing — the device is managing everything well     |
| 🟡 **Warning**  | One reading is close to going outside the safe range  | Keep an eye on it. The device is already responding. |
| 🔴 **Critical** | A reading has gone dangerously outside the safe range | Check the Alerts page immediately for details        |
| ⬜ **Waiting**  | The device just turned on and sensors are warming up  | Wait a minute — readings will appear shortly         |

### Equipment Status Icons

Below the readings, you will see small icons for each piece of equipment in that room. A **colored (bright) icon** means that piece of equipment is currently running. A **dim icon** means it is off. This is just for viewing — to actually turn things on or off, go to the Controls section.

---

## 7. Controlling Your Equipment

Go to the **Controls** section from the left menu to manually turn equipment on or off, or to switch between automatic and manual modes.

### Automatic Mode vs. Manual Mode

At the top of the Controls page is an important switch:

**When it shows "Automatic Control" (switch is ON, green):**
The device is managing everything for you. The equipment turns on and off automatically based on the current air readings. You do not need to do anything. The equipment cards are shown in grey and cannot be tapped — this is intentional to prevent accidental changes.

**When it shows "Manual Control" (switch is OFF, grey):**
You are in charge. You can tap any equipment card to turn it on or off manually. The device will not make any automatic changes until you switch back to Automatic.

> **Recommendation:** Leave the device in **Automatic Control** at all times during normal growing. Only switch to Manual if you need to test a specific piece of equipment or if instructed by your technician.

### Equipment in the Fruiting Room

| Equipment           | Normal Mode | What It Does                                        |
| ------------------- | ----------- | --------------------------------------------------- |
| **Mist Maker**      | Automatic   | Creates a fine mist to raise humidity               |
| **Humidifier Fan**  | Automatic   | Blows the mist evenly around the chamber            |
| **Exhaust Fan**     | Automatic   | Pushes out old, CO₂-rich air                        |
| **Intake Blower**   | Automatic   | Pulls fresh air into the chamber                    |
| **LED Grow Lights** | Scheduled   | Turns on at 8:00 AM, turns off at 8:00 PM every day |

### Equipment in the Spawning Room

| Equipment       | Normal Mode | What It Does                                                   |
| --------------- | ----------- | -------------------------------------------------------------- |
| **Exhaust Fan** | Automatic   | Provides regular air changes; runs longer if CO₂ gets too high |

### Turning Equipment On or Off Manually

1. Make sure the mode switch at the top is set to **Manual Control**.
2. Tap the card for the piece of equipment you want to control.
3. The card will change color and show **ON** or **OFF**.
4. The device sends the command to the equipment immediately — it will switch within 1–2 seconds.

> **Wait 5 seconds** before tapping the same card again. There is a short pause after each tap to protect the equipment from being switched on and off too quickly.

> **Switching back to Automatic:** Flip the switch at the top back to **Automatic Control**. The device will take over again immediately.

---

## 8. Understanding Alerts and Warnings

Go to the **Alerts** section from the left menu to see any warnings or emergencies that the device has detected.

### Types of Alerts

| Alert Type     | What It Means                                                                                                                                        |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🔴 **Critical** | A serious condition — for example, the temperature has gotten very high or humidity has dropped dangerously low. Check your growing room right away. |
| 🟡 **Warning**  | A condition is outside the normal range but not yet dangerous. The device is already responding automatically, but you should be aware.              |
| 🔵 **Info**     | General information — not urgent.                                                                                                                    |

### What to Do with an Alert

**Step 1 — Read the message.** Each alert tells you which room it is about and what the problem is, in plain language. For example: *"Fruiting Room CO₂ level exceeds safe limit."*

**Step 2 — Check your growing room.** Visit the room physically to confirm what is happening. For example, check that the exhaust fan is actually running and that air is moving.

**Step 3 — Once the issue is resolved, tap Acknowledge.** After you have confirmed the problem is fixed, tap the **Acknowledge** button next to that alert. It will move to the history list below.

### Common Alert Causes and What to Check

| Alert Message                          | Most Likely Cause                                  | What to Check                                                             |
| -------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------- |
| "CO₂ level exceeds critical threshold" | Exhaust fan not working, or door/window is blocked | Check that the exhaust fan is running and vents are not blocked           |
| "Temperature above critical limit"     | Cooling ventilation issue, or unusually hot day    | Check that exhaust fans are running; open a ventilation port if necessary |
| "Temperature below critical limit"     | Growing area is too cold                           | Check heating equipment or insulation                                     |
| "Humidity below critical level"        | Mist maker not functioning, or water tank is empty | Check mist maker power and water supply                                   |

---

## 9. Using the MASH App on Your Phone

The MASH Grower app lets you monitor and control the device from anywhere — even when you are not at the farm.

### Connecting the App to Your Device

There are two easy ways:

**Option A — Scan the QR Code (Easiest)**

1. On the device's touchscreen, go to the **Dashboard**.
2. Tap the round button in the bottom-right corner of the screen. A QR code will appear.
3. Open the MASH Grower app on your phone and tap **Scan QR Code**.
4. Point your phone camera at the QR code on the device screen.
5. The app will connect automatically — no typing required.

**Option B — Enter the Device Code Manually**

1. Every M.A.S.H. Device has a unique code printed on a label on the side of the box. It looks like: `MASH-B2-CAL26-CE637C`
2. Open the MASH Grower app and tap **Connect a Device**.
3. Type this code into the search box and tap **Connect**.

### Monitoring When You Are Away from the Farm

As long as the MASH Device has an internet connection, you can view your growing rooms from anywhere using the app. The data updates in real time.

If there is no internet at the farm, the device continues to save all readings locally. When the internet comes back, everything is uploaded automatically — you will not lose any data.

### Getting Notified of Problems

When an alert is triggered (for example, a temperature spike), the app will send a notification to your phone — even if the app is closed. Make sure to allow notifications for the MASH Grower app in your phone settings so you do not miss any urgent alerts.

---

## 10. What the Device Does Automatically

This chapter explains what your M.A.S.H. Device is doing on your behalf, so you know what to expect throughout the day and night.

### Humidity Management (Fruiting Room)

The device constantly watches the humidity level. When it drops below **85%**, the device starts a repeating mist cycle:

| Step                   | What Happens                                                                             |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| 1. Mist for 10 seconds | The mist maker turns on and creates a fine water vapor                                   |
| 2. Fan for 30 seconds  | The mist maker stops; the humidifier fan spreads the moisture evenly through the chamber |
| Repeat                 | This cycle repeats until humidity reaches 90%                                            |

Once humidity reaches **90%**, the cycle stops automatically. If humidity starts rising too fast toward 95%, the cycle stops early to prevent the room from getting too wet.

### CO₂ Management (Both Rooms)

**Fruiting Room:** When CO₂ rises above **1,000 ppm**, the exhaust fan turns on to flush out the stale air and bring in fresh air from outside. It turns off again once CO₂ drops below 900 ppm.

**Spawning Room:** The exhaust fan runs for **2 minutes every 30 minutes** as a regular air change, no matter what the CO₂ level is. If CO₂ gets very high (above 2,000 ppm), the fan runs continuously for **5 minutes** to flush out the stale air quickly.

### Temperature Management

If the temperature in the **Fruiting Room** rises above **26°C**, the exhaust fan turns on to bring cooler air in. In the **Spawning Room**, ventilation increases when temperature goes above **27°C**.

### Grow Lights (Fruiting Room)

The LED grow lights turn on automatically at **8:00 AM** and turn off at **8:00 PM** every day. You do not need to control these manually.

### Device Ventilation

The electronics box itself has an exhaust fan that runs for 3 minutes at 8:00 AM, 12:00 PM, 4:00 PM, and 8:00 PM every day. This prevents the electronics from overheating.

### Safety: Automatic Shutdown Protection

If the device's internal sensor connection is ever interrupted (for example, a cable comes loose), all equipment — fans, mist makers, everything — will automatically turn off within 60 seconds. This prevents any machine from accidentally being left on and running unsupervised.

---

## 11. Changing Settings

Go to the **Settings** section from the left menu. Settings are organized into five tabs.

### General

Shows the current time and how long the device has been running since it was last turned on. No changes can be made here.

### Wi-Fi

Shows which Wi-Fi network the device is currently connected to and the device's address on your network. If you want to connect the device to a different Wi-Fi network (for example, you changed your router or moved the device to a new location), tap **Disconnect and Enable Provisioning** and follow the setup steps again from [Chapter 4](#4-connecting-the-device-to-your-wi-fi).

> **Note:** Tapping this button will immediately disconnect the device from the internet. Cloud monitoring and the mobile app (Cloud Mode) will stop working until you reconnect.

### Cloud Sync

Shows whether the device is currently uploading data to the internet. There is a toggle switch:
- **ON (green):** Data is being backed up online. You can see it on your phone from anywhere.
- **OFF (grey):** Data is only saved on the device. The app can still work if your phone is on the same Wi-Fi network.

Leave this **ON** for normal use.

### Power Controls

| Option              | What It Does                                                                                                                                                            |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Reboot Device**   | Safely restarts the device. All monitoring resumes automatically after about 60 seconds. Use this if the device seems stuck or unresponsive.                            |
| **Shutdown Device** | Turns the device completely off. It will not turn back on unless you physically unplug it and plug it back in again. Use this only before moving or storing the device. |

Both options will ask you to confirm before doing anything.

### About (Device Information and Updates)

Shows the current software version installed on the device. If a software update is available, you will see a colored badge:

| Badge                  | What It Means                                | What to Do                                                        |
| ---------------------- | -------------------------------------------- | ----------------------------------------------------------------- |
| 🟢 **Up to Date**       | The device is running the latest software    | Nothing — you are good                                            |
| 🟠 **Update Available** | A new version is available with improvements | Tap **Update Now** when your growing cycle allows a brief restart |
| 🔴 **Critical Update**  | An important fix is available                | Install as soon as possible                                       |

To update: Tap **Check for Updates**, then tap **Update Now** when prompted. The device will download and install the update automatically and restart once it is finished. The whole process takes about 2–5 minutes.

---

## 12. When Something Goes Wrong

Use this section when you encounter a problem. If you cannot find your issue here, contact support.

---

**The device screen is black and does not turn on.**

- Make sure the power cable is firmly plugged into both the device and the wall socket.
- Try a different wall socket.
- Allow up to 2 minutes — it may still be starting up.

---

**The `MASH-Device` Wi-Fi network does not appear on my phone.**

- Wait 2 minutes after powering on the device — the hotspot may not be ready yet.
- Confirm that the device is powered (screen should be on or showing a startup screen).
- Move your phone closer to the device and refresh your Wi-Fi list.

---

**The setup page does not load when I type `10.42.0.1:5000`.**

- Make sure your phone is connected to `MASH-Device` and not still on your regular Wi-Fi.
- Try retyping the address carefully — there is a colon (`:`) before `5000`, not a dot.
- If it still does not load, try turning airplane mode on and then off on your phone, then reconnect to `MASH-Device`.

---

**The readings on the dashboard are not updating (showing 0 or dashes).**

- The sensors may still be warming up — wait up to 2 minutes after turning the device on.
- Check the **Sensors** indicator in the status strip. If it is red, the sensor cable inside the device has come loose.
- Try rebooting the device (Settings → Power Controls → Reboot).
- If readings are still missing after a reboot, contact your technician to check the internal cables.

---

**The equipment (fans, mist maker) is not turning on automatically.**

- Check the mode switch on the Controls page. It must be set to **Automatic Control** (green/ON) for the device to manage equipment on its own.
- Wait up to 1 minute after switching to Automatic mode for the device to assess conditions and respond.
- Check that the readings on the Dashboard are live (not showing 0 or dashes). The device only activates equipment when it has valid sensor data.
- Confirm the equipment is physically connected and powered.

---

**The mobile app cannot find the device.**

- Confirm your phone is on the same Wi-Fi network as the device.
- If using the code entry method, double-check the MASH ID printed on the device label — it is case-sensitive.
- If you are away from the farm (not on the same Wi-Fi), make sure Cloud Sync is turned ON in Settings.

---

**There is a red CRITICAL alert on the screen.**

Stay calm. Read the alert message carefully — it will tell you exactly which room and what the issue is.

1. Visit the affected growing room physically.
2. Check that the relevant equipment (fans, mist maker) is actually running.
3. Check for obvious physical problems: blocked vents, empty water tank, power cables unplugged.
4. Wait 5–10 minutes after resolving the issue for the readings to return to normal.
5. Once the issue is fixed, go to the Alerts page and tap **Acknowledge**.

If you cannot identify the cause or the alert keeps coming back, contact support.

---

**Support Contact**
Email: mash.mushroom.automation@gmail.com

---

*Thank you for using the M.A.S.H. Smart Growing Device.*
*We built it so you can focus on your mushrooms — not on technology.*

---

*Guide applies to M.A.S.H. Device firmware v2.8.0 and later.*
*© 2026 Mushroom Automation w/ Smart Hydro-Environment (M.A.S.H.). All rights reserved.*
