import subprocess
import time

# --- CONFIGURATION ---
HOTSPOT_SSID = "RPi_IoT_Provisioning" 
HOTSPOT_IP = "10.42.0.1"

def run_command(command, ignore_fail=False):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return True
    except subprocess.CalledProcessError as e:
        if not ignore_fail:
            print(f"CMD Error: {command}\n{e.stderr.strip()}")
        return False

def get_wifi_list():
    """
    Scans for available networks to show in the UI.
    """
    try:
        print("[*] Scanning for networks...")
        # Get SSIDs, remove duplicates, sort them
        cmd = "nmcli -t -f SSID dev wifi list"
        result = subprocess.check_output(cmd, shell=True, text=True)
        
        # Filter empty lines and remove duplicates
        ssids = sorted(list(set([line.strip() for line in result.split('\n') if line.strip()])))
        return ssids
    except:
        return []

def start_hotspot():
    print("-" * 30)
    print(f"[*] Starting Provisioning Hotspot: {HOTSPOT_SSID}")
    
    # 1. Clean Slate
    run_command("nmcli device disconnect wlan0", ignore_fail=True)
    run_command(f"nmcli connection delete '{HOTSPOT_SSID}'", ignore_fail=True)

    # 2. Create OPEN Hotspot (Using your working settings)
    cmd_create = (
        f"nmcli con add type wifi ifname wlan0 con-name '{HOTSPOT_SSID}' "
        f"autoconnect yes ssid '{HOTSPOT_SSID}'"
    )
    run_command(cmd_create)

    cmd_config = (
        f"nmcli con modify '{HOTSPOT_SSID}' "
        "802-11-wireless.mode ap "
        "802-11-wireless.band bg "
        "802-11-wireless.channel 6 "
        "ipv4.method shared"
    )
    run_command(cmd_config)

    # 3. Activate
    print("[*] Activating AP...")
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
    print("-" * 30)
    print(f"[*] PROVISIONING: Attempting to connect to '{ssid}'...")

    # 1. Prepare Connection Profile
    run_command(f"nmcli connection delete '{ssid}'", ignore_fail=True)
    run_command(f"nmcli con add type wifi ifname wlan0 con-name '{ssid}' ssid '{ssid}'")
    run_command(f"nmcli con modify '{ssid}' wifi-sec.key-mgmt wpa-psk wifi-sec.psk '{password}'")

    # 2. The Critical Switch (With Timeout Protection logic in mind)
    print("[*] Switching networks...")
    
    # We add a longer timeout (20s) for the command itself
    try:
        # We use check_output here to force a wait, but we rely on nmcli's internal timeout
        subprocess.check_call(f"nmcli con up '{ssid}'", shell=True, timeout=25)
        print(f"[SUCCESS] Connected to {ssid}!")
        return True
    except subprocess.TimeoutExpired:
        print(f"[FAIL] Connection timed out (Wrong password or weak signal).")
        return False
    except subprocess.CalledProcessError:
        print(f"[FAIL] Connection refused or failed.")
        return False