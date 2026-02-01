# 🚀 AI System Deployment Checklist

**Project:** MASH IoT - Intelligent Humidity Control  
**Version:** 1.0.0  
**Date:** 2024-01-20

---

## ✅ Pre-Deployment Checks

### 1. Code Review

- [x] `logic_engine.py` - HumidifierCycleManager class added
- [x] `logic_engine.py` - Trend analysis methods added
- [x] `logic_engine.py` - Overshoot prediction added
- [x] `logic_engine.py` - Enhanced fruiting actuation logic
- [x] Documentation created (4 files)
- [ ] Code tested locally (optional)
- [ ] Syntax validated with `python -m py_compile`

### 2. Dependencies

```bash
# Check required Python packages
pip list | grep -E "(scikit-learn|joblib|numpy)"
```

Required versions:
- [ ] scikit-learn >= 1.0.0
- [ ] joblib >= 1.1.0
- [ ] numpy >= 1.21.0

If missing:
```bash
pip install scikit-learn joblib numpy
```

### 3. Configuration Files

- [ ] `config.yaml` has `humidity_target`, `humidity_hysteresis`
- [ ] ML models exist: `rpi_gateway/data/models/isolation_forest.pkl`
- [ ] ML models exist: `rpi_gateway/data/models/decision_tree.pkl`

Check:
```bash
ls -lh rpi_gateway/data/models/
```

If missing models:
```bash
# Generate default models (optional)
python rpi_gateway/app/core/logic_engine.py --train
```

---

## 📦 Deployment Steps

### Step 1: Backup Current System

```bash
# On Raspberry Pi
cd ~/mash-iot
git stash  # Save any uncommitted changes
git branch backup-$(date +%Y%m%d)  # Create backup branch
```

### Step 2: Pull Latest Code

```bash
# On development machine
cd "c:\Users\Ryzen\Desktop\ThesisDev\Mobile IoT\MASH-IoT"
git add rpi_gateway/app/core/logic_engine.py
git add docs/AI_*.md
git commit -m "feat: AI-powered humidity control with predictive cycle management"
git push origin main
```

```bash
# On Raspberry Pi
cd ~/mash-iot
git pull origin main
```

### Step 3: Verify File Changes

```bash
# Check that new code is present
grep -n "HumidifierCycleManager" rpi_gateway/app/core/logic_engine.py
grep -n "_calculate_humidity_trend" rpi_gateway/app/core/logic_engine.py
grep -n "_predict_humidity_overshoot" rpi_gateway/app/core/logic_engine.py
```

Expected output:
```
27:class HumidifierCycleManager:
127:    def _calculate_humidity_trend(self, current_humidity: float) -> float:
161:    def _predict_humidity_overshoot(self, current_humidity: float, target: float, rate: float) -> bool:
```

### Step 4: Restart Service

```bash
# Stop the service
sudo systemctl stop mash-iot

# Clear any stale state
sudo systemctl reset-failed mash-iot

# Start the service
sudo systemctl start mash-iot

# Check status
sudo systemctl status mash-iot
```

Expected output:
```
● mash-iot.service - MASH IoT Gateway
   Loaded: loaded (/etc/systemd/system/mash-iot.service)
   Active: active (running) since ...
```

### Step 5: Monitor Startup

```bash
# Watch logs for errors
sudo journalctl -u mash-iot -f
```

Look for:
- ✅ `Loaded Isolation Forest model for anomaly detection`
- ✅ `Loaded Decision Tree model for actuation control`
- ✅ `Flask app started on port 5000`
- ❌ `Error:` or `Traceback:` (should not appear)

Press `Ctrl+C` to stop watching logs.

---

## 🧪 Post-Deployment Testing

### Test 1: Dashboard Accessibility

```bash
# From Raspberry Pi
curl -I http://localhost:5000/dashboard

# Expected: HTTP/1.1 200 OK
```

From browser:
- [ ] Navigate to http://raspberrypi.local:5000/dashboard
- [ ] Page loads successfully
- [ ] Humidifier System card shows "Mist 5s → Fan 10s cycle" description
- [ ] Auto badge (green) is visible

### Test 2: Sensor Readings

```bash
curl http://localhost:5000/api/sensor_readings | jq
```

Expected output:
```json
{
  "fruiting_room": {
    "temperature_celsius": 22.5,
    "humidity_percent": 88.3,
    "co2_ppm": 950
  }
}
```

- [ ] All values are reasonable (not 0 or 255)
- [ ] Temperature between 18-26°C
- [ ] Humidity between 70-100%
- [ ] CO₂ between 400-2000 ppm

### Test 3: Actuator States

```bash
curl http://localhost:5000/api/actuator_states | jq
```

Expected output:
```json
{
  "mist_maker": false,
  "humidifier_fan": false,
  "exhaust_fan": false,
  ...
}
```

- [ ] All actuators return boolean values
- [ ] States match physical relay status

### Test 4: AI Cycle Behavior

**If humidity is LOW (<85%):**

```bash
# Watch for cycle start
sudo journalctl -u mash-iot -f | grep HUMIDIFIER
```

Within 30 seconds, you should see:
```
[INFO] [AI-HUMIDIFIER] Started cycle - Humidity XX.X%
```

Then observe:
- [ ] Mist Maker turns ON (check relay LED)
- [ ] After 5 seconds, Mist Maker turns OFF
- [ ] Humidifier Fan turns ON
- [ ] After 10 seconds, Humidifier Fan turns OFF
- [ ] Cycle repeats until humidity reaches ~90%

**If humidity is OPTIMAL (85-95%):**

- [ ] Cycle should be idle (both OFF)
- [ ] No log messages about starting cycle
- [ ] System stable

**If humidity is HIGH (>95%):**

- [ ] Cycle immediately stops if running
- [ ] Log shows: `[WARNING] Emergency stop - Humidity too high`

### Test 5: Predictive Stopping

**When humidity approaches 90% during cycle:**

```bash
# Watch for predictive stop
sudo journalctl -u mash-iot -f | grep "Predicted overshoot"
```

Expected:
```
[INFO] [AI-HUMIDIFIER] Stopped cycle - Predicted overshoot (humidity=XX.X%, rate=X.XX%/s)
```

- [ ] Cycle stops BEFORE reaching 95%
- [ ] Humidity stabilizes at 90-93%
- [ ] No overshoot to 96%+ occurs

### Test 6: Anomaly Detection

**Simulate sensor fault (optional):**

```bash
# Temporarily disconnect sensor cable
# Wait 10 seconds
# Reconnect cable
```

Expected logs:
```
[WARNING] Anomaly detected: {...}
[WARNING] Skipping actuation for anomalous data
```

- [ ] System safely skips actuation during fault
- [ ] Resumes normal operation after reconnection

---

## 📊 Performance Monitoring (First 24 Hours)

### Metrics to Track

```bash
# Create monitoring script
cat > /tmp/monitor_humidity.sh << 'EOF'
#!/bin/bash
while true; do
    date
    curl -s http://localhost:5000/api/sensor_readings | jq '.fruiting_room.humidity_percent'
    curl -s http://localhost:5000/api/actuator_states | jq '{mist: .mist_maker, fan: .humidifier_fan}'
    echo "---"
    sleep 60
done
EOF

chmod +x /tmp/monitor_humidity.sh
/tmp/monitor_humidity.sh >> /tmp/humidity_log.txt &
```

### Check Results After 24h

```bash
# Stop monitoring
pkill -f monitor_humidity

# Analyze results
cat /tmp/humidity_log.txt | grep "humidity_percent"

# Calculate statistics
awk '/humidity_percent/ {sum+=$1; count++} END {print "Average:", sum/count}' /tmp/humidity_log.txt
```

**Success Criteria:**
- [ ] Average humidity: 88-92%
- [ ] Time in range (85-95%): >90%
- [ ] Overshoot events (>95%): <3 per day
- [ ] Cycle frequency: 2-6 cycles per hour

---

## ⚠️ Rollback Plan (If Issues Occur)

### Symptoms Requiring Rollback

- Service fails to start
- Python errors in logs
- Actuators not responding
- Humidity control unstable (>10 cycles/hour)

### Rollback Steps

```bash
# 1. Stop the service
sudo systemctl stop mash-iot

# 2. Revert to backup branch
cd ~/mash-iot
git checkout backup-YYYYMMDD  # Use date from Step 1

# 3. Restart service
sudo systemctl start mash-iot

# 4. Verify service is working
sudo systemctl status mash-iot
curl http://localhost:5000/dashboard
```

### Report Issues

Document the problem:
```bash
# Collect logs
sudo journalctl -u mash-iot --since "1 hour ago" > /tmp/mash-iot-error.log

# Include sensor data
curl http://localhost:5000/api/sensor_readings >> /tmp/mash-iot-error.log

# Include error details
echo "Error Description: [DESCRIBE ISSUE]" >> /tmp/mash-iot-error.log
```

---

## 📱 User Notification

### Inform Stakeholders

**Deployment Announcement:**

> **Subject:** MASH IoT - AI Humidity Control Now Live 🧠
>
> The MASH IoT system has been upgraded with intelligent humidity control using Machine Learning.
>
> **New Features:**
> - Automatic Humidifier System cycle (Mist 5s → Fan 10s)
> - Predictive control to prevent humidity overshoot
> - Anomaly detection for sensor fault protection
>
> **What You'll See:**
> - Humidifier System card on dashboard shows AI control
> - Logs will show "[AI-HUMIDIFIER]" entries
> - More stable humidity (85-95% range)
>
> **Monitoring:**
> - Dashboard: http://raspberrypi.local:5000/dashboard
> - Logs: `sudo journalctl -u mash-iot -f`
>
> Please report any issues or unusual behavior.
>
> **Documentation:**
> - [AI Implementation Guide](docs/AI_IMPLEMENTATION_GUIDE.md)
> - [Quick Reference](docs/AI_QUICK_REFERENCE.md)

---

## ✅ Deployment Sign-Off

### Completed By

- **Developer:** _____________________ Date: _____
- **Tester:** _____________________ Date: _____
- **Operator:** _____________________ Date: _____

### Final Checklist

- [ ] Code deployed to Raspberry Pi
- [ ] Service restarted successfully
- [ ] Dashboard accessible
- [ ] Sensor readings valid
- [ ] Actuators responding
- [ ] AI cycle tested
- [ ] Logs reviewed (no errors)
- [ ] Performance monitored (1 hour minimum)
- [ ] Documentation updated
- [ ] Stakeholders notified

### Notes

```
____________________________________________________________________________

____________________________________________________________________________

____________________________________________________________________________
```

---

**Deployment Status:** ⏳ PENDING / ✅ COMPLETE / ❌ ROLLED BACK

**Sign-Off Date:** ___________________

**Next Review:** ___________________
