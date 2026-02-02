import subprocess
import time
import os
import json
from pathlib import Path
import qrcode
from io import BytesIO
import base64

# --- CONFIGURATION ---
HOTSPOT_SSID = "MASH-Device" 
HOTSPOT_IP = "10.42.0.1"
WIFI_CREDENTIALS_FILE = "config/wifi_credentials.json"

def generate_wifi_qr_code(ssid: str, password: str = "", security: str = "nopass") -> str:
    """
    Generate WiFi QR code as base64 image
    
    QR Format: WIFI:T:<security>;S:<ssid>;P:<password>;;
    - T: Security type (nopass, WEP, WPA)
    - S: SSID (network name)
    - P: Password (empty for open networks)
    
    Returns base64-encoded PNG image string
    """
    if password:
        wifi_string = f"WIFI:T:WPA;S:{ssid};P:{password};;"
    else:
        wifi_string = f"WIFI:T:{security};S:{ssid};P:;;"
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(wifi_string)
    qr.make(fit=True)
    
    # Generate image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"

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

def get_current_network():
    """
    Returns the currently connected WiFi network SSID, or None if not connected.
    """
    try:
        cmd = "nmcli -t -f active,ssid dev wifi | grep '^yes'"
        result = subprocess.check_output(cmd, shell=True, text=True)
        # Format is "yes:SSID_NAME"
        if result:
            parts = result.strip().split(':')
            if len(parts) >= 2:
                return parts[1]
        return None
    except subprocess.CalledProcessError:
        # Not connected to any WiFi
        return None
    except Exception as e:
        print(f"[!] Error getting current network: {e}")
        return None

def save_wifi_credentials(ssid, password):
    """
    Save WiFi credentials to local storage for fallback.
    """
    try:
        credentials_path = Path(WIFI_CREDENTIALS_FILE)
        credentials_path.parent.mkdir(parents=True, exist_ok=True)
        
        credentials = {
            "last_known_ssid": ssid,
            "last_known_password": password,
            "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(credentials_path, 'w') as f:
            json.dump(credentials, f, indent=2)
        
        print(f"[*] Saved credentials for {ssid}")
        return True
    except Exception as e:
        print(f"[!] Failed to save credentials: {e}")
        return False

def load_wifi_credentials():
    """
    Load last known WiFi credentials from storage.
    Returns: (ssid, password) tuple or (None, None) if not found
    """
    try:
        credentials_path = Path(WIFI_CREDENTIALS_FILE)
        if not credentials_path.exists():
            return None, None
        
        with open(credentials_path, 'r') as f:
            credentials = json.load(f)
        
        ssid = credentials.get("last_known_ssid")
        password = credentials.get("last_known_password")
        
        return ssid, password
    except Exception as e:
        print(f"[!] Failed to load credentials: {e}")
        return None, None

def disconnect_wifi():
    """
    Disconnect from current WiFi network.
    Returns True only if disconnect actually succeeded.
    """
    print("[*] Disconnecting from WiFi...")
    try:
        # Get current connection
        current = get_current_network()
        if not current:
            print("[INFO] No active WiFi connection to disconnect")
            return True
        
        # Try to disconnect
        result = subprocess.run(
            f"nmcli connection down '{current}'",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Check if actually disconnected
        time.sleep(2)  # Wait for disconnect to take effect
        new_current = get_current_network()
        
        if new_current == current:
            print(f"[FAIL] Still connected to {current} - disconnect failed")
            print(f"[DEBUG] nmcli output: {result.stdout}")
            print(f"[DEBUG] nmcli error: {result.stderr}")
            return False
        else:
            print(f"[SUCCESS] Disconnected from {current}")
            return True
            
    except subprocess.TimeoutExpired:
        print("[!] Disconnect timeout")
        return False
    except Exception as e:
        print(f"[!] Error disconnecting: {e}")
        return False

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

def connect_to_wifi(ssid, password, save_credentials=True):
    """
    Attempts to connect to a WiFi network with automatic fallback.
    
    Flow:
    1. Save current network as backup (if connected)
    2. Disconnect from current network
    3. Try to connect to new network
    4. On failure, reconnect to previous network
    5. Save credentials on success
    
    Args:
        ssid: Target network SSID
        password: Network password
        save_credentials: Whether to save credentials for future fallback
    
    Returns:
        True if successful, False otherwise
    """
    print("-" * 50)
    print(f"[*] WiFi Manager: Switching to '{ssid}'...")
    
    # Step 1: Get current network for potential rollback
    current_network = get_current_network()
    backup_ssid, backup_password = None, None
    
    if current_network and current_network != ssid:
        print(f"[*] Currently connected to: {current_network}")
        # Load backup credentials in case we need to rollback
        backup_ssid, backup_password = load_wifi_credentials()
        
        # Disconnect from current network
        print("[*] Disconnecting from current network...")
        disconnect_wifi()
        time.sleep(2)
    
    # Step 2: Clean up any existing connection profile with same name
    run_command(f"nmcli connection delete '{ssid}'", ignore_fail=True)

    # Step 3: Create the new connection profile
    print(f"[*] Creating connection profile for '{ssid}'...")
    if not run_command(f"nmcli con add type wifi ifname wlan0 con-name '{ssid}' ssid '{ssid}'"):
        print("[!] Failed to create connection profile")
        return _rollback_connection(backup_ssid, backup_password, current_network)
    
    # Step 4: Apply WPA2-PSK security
    if not run_command(f"nmcli con modify '{ssid}' wifi-sec.key-mgmt wpa-psk wifi-sec.psk '{password}'"):
        print("[!] Failed to configure security")
        return _rollback_connection(backup_ssid, backup_password, current_network)

    # Step 5: Attempt connection with timeout
    print("[*] Connecting to network...")
    try:
        subprocess.check_call(f"nmcli con up '{ssid}'", shell=True, timeout=25)
        print(f"[SUCCESS] Connected to {ssid}!")
        
        # Save credentials for future fallback
        if save_credentials:
            save_wifi_credentials(ssid, password)
        
        return True
        
    except subprocess.TimeoutExpired:
        print(f"[FAIL] Connection timed out (wrong password or weak signal)")
        return _rollback_connection(backup_ssid, backup_password, current_network)
        
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Connection failed: {e}")
        return _rollback_connection(backup_ssid, backup_password, current_network)

def _rollback_connection(backup_ssid, backup_password, original_network):
    """
    Internal helper to rollback to previous network on connection failure.
    """
    if backup_ssid and backup_password:
        print("-" * 50)
        print(f"[*] ROLLBACK: Attempting to reconnect to {backup_ssid}...")
        try:
            # Try to reconnect using saved credentials
            subprocess.check_call(
                f"nmcli con up '{backup_ssid}'", 
                shell=True, 
                timeout=20
            )
            print(f"[SUCCESS] Rolled back to {backup_ssid}")
            return False  # Original connection failed, but rollback succeeded
        except:
            print(f"[FAIL] Rollback failed. Trying to recreate connection...")
            # Recreate the connection profile
            run_command(f"nmcli connection delete '{backup_ssid}'", ignore_fail=True)
            run_command(f"nmcli con add type wifi ifname wlan0 con-name '{backup_ssid}' ssid '{backup_ssid}'")
            run_command(f"nmcli con modify '{backup_ssid}' wifi-sec.key-mgmt wpa-psk wifi-sec.psk '{backup_password}'")
            try:
                subprocess.check_call(f"nmcli con up '{backup_ssid}'", shell=True, timeout=20)
                print(f"[SUCCESS] Reconnected to {backup_ssid}")
            except:
                print(f"[FAIL] Could not reconnect to previous network")
    else:
        print("[!] No backup credentials available for rollback")
    
    return False

def is_connected_to_wifi():
    """Check if device is connected to a WiFi network (not hotspot)"""
    current = get_current_network()
    return current is not None and current != HOTSPOT_SSID

def is_hotspot_active():
    """Check if provisioning hotspot is currently active"""
    current = get_current_network()
    return current == HOTSPOT_SSID

def ensure_connectivity():
    """
    Ensure device has network connectivity.
    If not connected to WiFi, start hotspot automatically.
    """
    if not is_connected_to_wifi():
        print("[WIFI] No network connection detected")
        
        # Check if hotspot is already active
        if is_hotspot_active():
            print("[WIFI] Hotspot already active")
        else:
            print("[WIFI] Starting provisioning hotspot...")
            success = start_hotspot()
            if success:
                print("[WIFI] ✅ Hotspot started successfully")
            else:
                print("[WIFI] ❌ Failed to start hotspot")
    else:
        current_ssid = get_current_network()
        print(f"[WIFI] ✅ Connected to '{current_ssid}'")