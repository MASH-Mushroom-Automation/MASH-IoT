import subprocess
import time
import os

# --- CONFIGURATION ---
HOTSPOT_SSID = "MASH-Device" 
HOTSPOT_IP = "10.42.0.1"

def run_command(command, ignore_fail=False):
    """Executes a shell command and returns True if successful."""
    try:
        # We capture output to check for success/failure text if needed
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return True
    except subprocess.CalledProcessError as e:
        if not ignore_fail:
            print(f"CMD Error: {command}\n{e.stderr.strip()}")
        return False

def get_wifi_list():
    """
    Scans for available WiFi networks and returns a sorted list of unique SSIDs.
    Used to populate the dropdown in the UI.
    """
    try:
        print("[*] Utils: Scanning for networks...")
        # Get list of SSIDs (-t for tabular, -f for field)
        cmd = "nmcli -t -f SSID dev wifi list"
        result = subprocess.check_output(cmd, shell=True, text=True)
        
        # Filter empty lines, remove duplicates, and sort
        ssids = sorted(list(set([line.strip() for line in result.split('\n') if line.strip()])))
        return ssids
    except Exception as e:
        print(f"[!] Scan Error: {e}")
        return []

def start_hotspot():
    """
    Creates and starts the Provisioning Hotspot (OPEN/No Password).
    Includes the fix for RPi 3B PMF issues.
    """
    print("-" * 30)
    print(f"[*] Utils: Starting Provisioning Hotspot: {HOTSPOT_SSID}")
    
    # 1. Clean Slate: Disconnect wlan0 and delete old profile
    run_command("nmcli device disconnect wlan0", ignore_fail=True)
    run_command(f"nmcli connection delete '{HOTSPOT_SSID}'", ignore_fail=True)

    # 2. Create OPEN Hotspot (No Password)
    cmd_create = (
        f"nmcli con add type wifi ifname wlan0 con-name '{HOTSPOT_SSID}' "
        f"autoconnect yes ssid '{HOTSPOT_SSID}'"
    )
    run_command(cmd_create)

    # 3. Apply Compatibility Settings (Band BG, Shared IP)
    cmd_config = (
        f"nmcli con modify '{HOTSPOT_SSID}' "
        "802-11-wireless.mode ap "
        "802-11-wireless.band bg "
        "802-11-wireless.channel 6 "
        "ipv4.method shared"
    )
    run_command(cmd_config)

    # 4. Reset Radio & Activate
    print("[*] Utils: Activating AP...")
    run_command("nmcli radio wifi off") 
    time.sleep(1)
    run_command("nmcli radio wifi on")
    time.sleep(2)
    
    if run_command(f"nmcli con up '{HOTSPOT_SSID}'"):
        print(f"[SUCCESS] Hotspot is UP. Connect to '{HOTSPOT_SSID}'")
        return True
    else:
        print("[FAIL] Could not start Hotspot.")
        return False

def connect_to_wifi(ssid, password):
    """
    Attempts to switch from Hotspot to a standard WiFi network.
    Includes timeout protection.
    """
    print("-" * 30)
    print(f"[*] Utils: Attempting to connect to '{ssid}'...")

    # 1. Clean up old connection with same name
    run_command(f"nmcli connection delete '{ssid}'", ignore_fail=True)

    # 2. Create the new Client connection profile
    run_command(f"nmcli con add type wifi ifname wlan0 con-name '{ssid}' ssid '{ssid}'")
    
    # 3. Apply Security
    run_command(f"nmcli con modify '{ssid}' wifi-sec.key-mgmt wpa-psk wifi-sec.psk '{password}'")

    # 4. The Critical Switch
    print("[*] Utils: Switching networks...")
    
    try:
        # 25s timeout: If nmcli hangs (common with wrong passwords), we kill it.
        subprocess.check_call(f"nmcli con up '{ssid}'", shell=True, timeout=25)
        print(f"[SUCCESS] Connected to {ssid}!")
        return True
    except subprocess.TimeoutExpired:
        print(f"[FAIL] Connection timed out (Possible wrong password).")
        return False
    except subprocess.CalledProcessError:
        print(f"[FAIL] Connection refused or failed.")
        return False