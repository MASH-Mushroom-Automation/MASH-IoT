# 🎛️ AI System Quick Reference

**MASH IoT - Intelligent Humidity Control**

---

## 🔍 Real-Time Monitoring

### Dashboard URL
```
http://raspberrypi.local:5000/dashboard
```

### Key Indicators

**Humidifier System Card:**
- 🟢 **Green Badge "AUTO"** - AI is controlling the system
- 🔵 **Mist Maker ON** - Generating moisture (5s phase)
- 🔵 **Humidifier Fan ON** - Distributing moisture (10s phase)
- ⚪ **Both OFF** - Cycle idle (humidity OK)

**Humidity Gauge:**
- **Target Zone:** 85-95% (green range)
- **Optimal:** ~90%
- **Below 85%:** Cycle should start
- **Above 95%:** Cycle should stop

---

## 📊 Log Messages

### Normal Operation

```bash
# Watch live logs
ssh pi@raspberrypi.local
journalctl -u mash-iot -f | grep HUMIDIFIER
```

**Cycle Start:**
```
[INFO] [AI-HUMIDIFIER] Started cycle - Humidity 83.5% < target 85%
```

**Phase Transitions:**
```
[DEBUG] [HUMIDIFIER] Switching to FAN phase
[DEBUG] [HUMIDIFIER] Switching to MIST phase
```

**Periodic Status (every 5s):**
```
[DEBUG] [HUMIDIFIER] Phase=mist, elapsed=3.2s, humidity=88.3%, rate=0.25%/s
```

**Smart Stop:**
```
[INFO] [AI-HUMIDIFIER] Stopped cycle - Predicted overshoot (humidity=90.2%, rate=0.28%/s)
```

### Warnings/Errors

**Emergency Stop:**
```
[WARNING] [AI-HUMIDIFIER] Emergency stop - Humidity too high (96.5%)
```

**Anomaly Detected:**
```
[WARNING] Anomaly detected: {'temp': 22.5, 'humidity': 125.0, 'co2': 950}
[WARNING] Skipping actuation for anomalous fruiting data
```

---

## 🔧 Quick Diagnostics

### Check System Status

```bash
# Is the service running?
sudo systemctl status mash-iot

# Check recent errors
sudo journalctl -u mash-iot --since "5 minutes ago" | grep -i error

# View AI decisions
sudo journalctl -u mash-iot --since "1 hour ago" | grep AI-HUMIDIFIER
```

### Check Sensor Readings

```bash
# Current readings
curl http://raspberrypi.local:5000/api/sensor_readings | jq

# Expected output:
{
  "fruiting_room": {
    "temperature_celsius": 22.5,
    "humidity_percent": 88.3,
    "co2_ppm": 950
  }
}
```

### Check Actuator States

```bash
# Current actuator status
curl http://raspberrypi.local:5000/api/actuator_states | jq

# Look for:
{
  "mist_maker": true,      # or false
  "humidifier_fan": false  # or true
}
```

---

## 🎯 Expected Behavior

### Scenario 1: Humidity Low (80-84%)

**What You Should See:**
1. Humidity gauge shows red (below range)
2. Cycle starts automatically
3. Mist Maker turns ON for 5 seconds
4. Humidifier Fan turns ON for 10 seconds
5. Cycle repeats until humidity reaches 85-90%

**Log Pattern:**
```
[INFO] Started cycle - Humidity 82.0%
[DEBUG] Phase=mist, elapsed=2.5s, humidity=82.3%
[DEBUG] Switching to FAN phase
[DEBUG] Phase=fan, elapsed=5.0s, humidity=84.1%
[DEBUG] Switching to MIST phase
... (continues)
[INFO] Stopped cycle - Predicted overshoot (humidity=89.5%)
```

### Scenario 2: Humidity Optimal (85-95%)

**What You Should See:**
1. Humidity gauge shows green (in range)
2. Cycle may start if humidity drops toward 85%
3. Cycle stops proactively when approaching 90%
4. System maintains stability

**Log Pattern:**
```
[DEBUG] Phase=fan, humidity=89.2%, rate=0.15%/s
[INFO] Stopped cycle - Predicted overshoot (humidity=89.8%, rate=0.20%/s)
(10 minutes pass with no activity)
[INFO] Started cycle - Humidity 84.5%
```

### Scenario 3: Humidity High (96%+)

**What You Should See:**
1. Humidity gauge shows red (above range)
2. Cycle immediately stops if running
3. All humidifier components OFF
4. System waits for humidity to drop naturally

**Log Pattern:**
```
[WARNING] Emergency stop - Humidity too high (96.8%)
(System idle until humidity drops below 90%)
```

---

## ⚠️ Troubleshooting

### Issue: Cycle Won't Start

**Symptoms:** Humidity at 82%, but nothing happens

**Check:**
```bash
# 1. Is service running?
sudo systemctl status mash-iot

# 2. Are there sensor errors?
curl http://raspberrypi.local:5000/api/sensor_readings

# 3. Are anomalies being detected?
sudo journalctl -u mash-iot -n 50 | grep -i anomaly
```

**Common Causes:**
- Sensor disconnected (humidity = 0 or 255)
- Anomaly detection blocking (humidity >100%)
- Config file error (target thresholds wrong)

**Fix:**
```bash
# Restart service
sudo systemctl restart mash-iot

# Check sensor connection
python scripts/test_sensors.py
```

### Issue: Overshooting Target

**Symptoms:** Humidity goes to 97% frequently

**Check:**
```bash
# Is prediction working?
sudo journalctl -u mash-iot | grep "rate="

# Should see: "rate=0.XX%/s" in logs
```

**Common Causes:**
- Not enough sensor readings (need 2+ readings)
- Safety margin too small
- Trend calculation disabled

**Fix:**
```python
# In logic_engine.py, increase safety margin:
safety_margin = 3  # Was 2

# Or reduce hysteresis:
humidity_hysteresis: 3  # Was 5 in config.yaml
```

### Issue: Rapid Cycling (On/Off Every Minute)

**Symptoms:** Cycle starts, stops, starts again repeatedly

**Check:**
```bash
# How often is cycle starting?
sudo journalctl -u mash-iot --since "10 minutes ago" | grep "Started cycle"

# Should be <3 times per 10 minutes
```

**Common Causes:**
- Hysteresis too small
- Sensor noise causing false readings
- Prediction not preventing overshoot

**Fix:**
```yaml
# In config.yaml, increase hysteresis:
humidity_hysteresis: 7  # Was 5
```

---

## 📞 Emergency Commands

### Stop All Actuators Immediately

```bash
# Send OFF commands to all actuators
curl -X POST http://raspberrypi.local:5000/api/control_actuator \
  -H "Content-Type: application/json" \
  -d '{"actuator": "mist_maker", "state": "OFF"}'

curl -X POST http://raspberrypi.local:5000/api/control_actuator \
  -H "Content-Type: application/json" \
  -d '{"actuator": "humidifier_fan", "state": "OFF"}'
```

### Disable AI Control (Manual Mode)

```bash
# Stop the service
sudo systemctl stop mash-iot

# Control manually via dashboard
# Navigate to: http://raspberrypi.local:5000/controls
```

### Re-enable AI Control

```bash
# Start the service
sudo systemctl start mash-iot

# Verify it's running
sudo systemctl status mash-iot
```

---

## 📈 Performance Targets

### Humidity Control

| Metric | Target | Acceptable | Poor |
|--------|--------|-----------|------|
| Time in range (85-95%) | >95% | 90-95% | <90% |
| Overshoot events/hour | 0 | <1 | >1 |
| Response time (80%→85%) | <30s | <60s | >60s |
| Cycle frequency/hour | 2-4 | 4-6 | >6 |

### Cycle Timing

| Phase | Target | Tolerance |
|-------|--------|-----------|
| Mist | 5.0s | ±0.2s |
| Fan | 10.0s | ±0.2s |
| Total | 15.0s | ±0.3s |

---

## 🔔 Alert Thresholds

**INFO** - Normal operation, cycle events  
**DEBUG** - Periodic status, phase changes  
**WARNING** - Emergency stops, high humidity  
**ERROR** - Sensor failures, ML model errors

**Critical Alerts (requires attention):**
- Humidity >98% for >5 minutes
- Sensor disconnected
- Multiple anomalies in 10 minutes
- Actuator communication failure

---

## 📱 Mobile Monitoring

### Quick Status Check

```bash
# From phone browser:
http://raspberrypi.local:5000/dashboard

# Via SSH app (Termius, JuiceSSH):
ssh pi@raspberrypi.local
sudo journalctl -u mash-iot -f | grep HUMIDIFIER
```

### Telegram Notifications (Future)

```bash
# Install telegram bot (coming soon)
pip install python-telegram-bot
python scripts/setup_telegram_bot.py
```

---

## 📚 More Information

- **Full Documentation:** [AI_IMPLEMENTATION_GUIDE.md](AI_IMPLEMENTATION_GUIDE.md)
- **Implementation Summary:** [AI_IMPLEMENTATION_SUMMARY.md](AI_IMPLEMENTATION_SUMMARY.md)
- **Code Reference:** `rpi_gateway/app/core/logic_engine.py`

---

**Print this card and keep it near your monitoring station! 📋**
