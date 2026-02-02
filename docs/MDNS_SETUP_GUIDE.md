# mDNS/Avahi Setup for MASH IoT Gateway

## What is mDNS?

mDNS (multicast DNS) allows devices to discover each other on a local network without a DNS server. The Flutter mobile app uses mDNS to automatically find MASH IoT devices when connected to the same WiFi network or hotspot.

## Installation on Raspberry Pi

```bash
# 1. Install Avahi daemon (required for mDNS on Linux)
sudo apt-get update
sudo apt-get install -y avahi-daemon avahi-utils

# 2. Enable and start Avahi
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# 3. Verify Avahi is running
sudo systemctl status avahi-daemon

# 4. Install Python dependencies
cd MASH-IoT/rpi_gateway
source venv/bin/activate
pip install -r requirements.txt
```

## How It Works

### RPi Side (Server)
- `app/utils/mdns_advertiser.py` advertises the service using zeroconf library
- Service type: `_mash-iot._tcp.local.`
- Broadcasts on port 5353 (mDNS standard)
- Includes device info in TXT records (name, ID, API version)

### Flutter App Side (Client)
- `lib/services/mdns_discovery_service.dart` discovers devices
- Listens for `_mash-iot._tcp` services on the network
- Automatically updates device list in real-time

## Testing mDNS

### On Raspberry Pi:

```bash
# Check if service is being advertised
avahi-browse -a

# Look for _mash-iot._tcp service
avahi-browse -r _mash-iot._tcp

# Test with specific lookup
avahi-resolve -n mash-iot-gateway.local
```

Expected output:
```
+ wlan0 IPv4 mash-iot-gateway                            _mash-iot._tcp       local
= wlan0 IPv4 mash-iot-gateway                            _mash-iot._tcp       local
   hostname = [mash-iot-gateway.local]
   address = [10.42.0.1]
   port = [5000]
   txt = ["name=MASH IoT Chamber" "type=rpi-gateway" "api_version=v1"]
```

### From Mobile Device:

1. Connect phone to RPi hotspot: `RPi_IoT_Provisioning` or `MASH-Device`
2. Open MASH Grower Mobile app
3. Go to "Connect to Chamber" screen
4. Should automatically discover device within 10 seconds

### Manual Test from Another Computer:

```bash
# Linux/Mac
dns-sd -B _mash-iot._tcp

# Or use avahi-browse
avahi-browse -r _mash-iot._tcp

# Windows (requires Bonjour)
dns-sd -B _mash-iot._tcp
```

## Troubleshooting

### Device Not Discovered

**Problem:** Mobile app can't find device

**Check:**
```bash
# 1. Is Avahi running?
sudo systemctl status avahi-daemon

# 2. Is Flask app running?
sudo systemctl status mash-iot-gateway

# 3. Is mDNS advertising?
avahi-browse -a | grep mash

# 4. Check firewall
sudo ufw status
sudo ufw allow 5353/udp  # If firewall is active
```

### mDNS Not Working in Hotspot Mode

**Problem:** Works on WiFi but not when RPi is in hotspot mode

**Solution:** Ensure Avahi is configured to advertise on all interfaces

Edit `/etc/avahi/avahi-daemon.conf`:
```ini
[server]
use-ipv4=yes
use-ipv6=no
allow-interfaces=wlan0,ap0  # Add your interfaces
```

Restart:
```bash
sudo systemctl restart avahi-daemon
```

### Python Errors

**Error:** `ModuleNotFoundError: No module named 'zeroconf'`

**Fix:**
```bash
cd MASH-IoT/rpi_gateway
source venv/bin/activate
pip install zeroconf
```

**Error:** `OSError: [Errno 98] Address already in use`

**Cause:** Another mDNS service is running

**Fix:**
```bash
# Check what's using port 5353
sudo netstat -tulpn | grep 5353

# Usually it's avahi-daemon (which is good - we want it)
# Python zeroconf works alongside it
```

## Network Requirements

### Hotspot Mode (Provisioning)
- RPi IP: `10.42.0.1`
- Mobile device connects to `RPi_IoT_Provisioning` or `MASH-Device`
- mDNS works on 10.42.0.0/24 subnet
- Device advertised as: `mash-iot-gateway.local`

### Station Mode (Normal WiFi)
- RPi gets IP from router (e.g., `192.168.1.100`)
- Both mobile and RPi on same WiFi network
- mDNS works on home network subnet
- Device advertised as: `mash-iot-gateway.local`

## Device Naming

The device is advertised with these identifiers:

```python
# In config/config.yaml
device:
  serial_number: "mash-iot-gateway"  # Used as mDNS service ID
  name: "MASH IoT Chamber"          # Human-readable name
```

Change these to customize your device name:
```bash
nano MASH-IoT/rpi_gateway/config/config.yaml
```

Restart Flask app for changes to take effect.

## Advanced Configuration

### Custom Service Properties

Edit `app/utils/mdns_advertiser.py`:

```python
properties = {
    'name': self.device_name,
    'type': 'rpi-gateway',
    'api_version': 'v1',
    'device_id': self.device_id,
    'manufacturer': 'MASH',
    # Add custom properties:
    'location': 'Lab A',
    'firmware_version': '1.0.0',
}
```

### Multiple Devices

Each device must have a unique `device_id`:

```yaml
# Device 1
device:
  serial_number: "mash-chamber-01"
  name: "Fruiting Chamber 1"

# Device 2
device:
  serial_number: "mash-chamber-02"
  name: "Fruiting Chamber 2"
```

## References

- [mDNS RFC 6762](https://tools.ietf.org/html/rfc6762)
- [Avahi Documentation](https://www.avahi.org/)
- [Python zeroconf Library](https://github.com/python-zeroconf/python-zeroconf)
- [Flutter multicast_dns Package](https://pub.dev/packages/multicast_dns)
