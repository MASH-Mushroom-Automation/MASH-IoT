# 🧠 AI Logic Implementation Guide

**Date:** 2024-01-20  
**System:** MASH IoT - Mushroom Cultivation Automation  
**Component:** Smart Environmental Control System

---

## 🎯 Overview

The MASH IoT system now features intelligent automation using Machine Learning to control environmental conditions in the fruiting chamber. The AI system manages the **Humidifier System** (Mist Maker + Humidifier Fan) with predictive control to maintain optimal humidity without overshooting.

### Key Features

✅ **Smart Cycle Management** - Automated Mist 5s → Fan 10s cycle  
✅ **Predictive Control** - Stops before overshooting target humidity  
✅ **Trend Analysis** - Monitors humidity rate of change  
✅ **Isolation Forest** - Filters sensor anomalies  
✅ **Decision Tree** - Makes intelligent actuation decisions  
✅ **Hysteresis** - Prevents rapid on/off cycling

---

## 🏗️ Architecture

### Two-Stage ML Pipeline

```
┌──────────────────┐
│  Sensor Readings │
│ (Temp, RH, CO₂)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   STAGE 1:       │
│ Anomaly Detection│  ← Isolation Forest
│  (Fault Filter)  │    - Prediction = -1 → Anomaly
└────────┬─────────┘    - Prediction = 1 → Normal
         │
         ▼ (Normal Data)
┌──────────────────┐
│   STAGE 2:       │
│ Actuation Control│  ← Decision Tree + Rule-Based
│  (Smart Cycle)   │    - Trend analysis
└────────┬─────────┘    - Predictive stopping
         │
         ▼
┌──────────────────┐
│  Arduino Commands│
│  (JSON Serial)   │
└──────────────────┘
```

---

## 🔧 Humidifier System Cycle

### State Machine

The Humidifier System operates as a state machine with three phases:

```
     START
       │
       ▼
┌──────────────┐
│     IDLE     │ ◄─────┐
└──┬───────────┘       │
   │ humidity < 85%    │
   ▼                   │
┌──────────────┐       │
│ MIST PHASE   │       │
│  (5 seconds) │       │
└──┬───────────┘       │
   │ timer expired     │
   ▼                   │
┌──────────────┐       │
│  FAN PHASE   │       │
│ (10 seconds) │       │
└──┬───────────┘       │
   │ timer expired     │
   └───────────────────┘
   
STOP CONDITIONS:
- Humidity >= 90% (target reached)
- Predicted overshoot detected
- Humidity > 95% (emergency stop)
```

### Phase Details

| Phase | Duration | Mist Maker | Humidifier Fan | Purpose |
|-------|----------|------------|----------------|---------|
| **IDLE** | Indefinite | OFF | OFF | Waiting for humidity drop |
| **MIST** | 5 seconds | **ON** | OFF | Generate moisture |
| **FAN** | 10 seconds | OFF | **ON** | Distribute moisture |

### Cycle Logic

```python
# Start Condition
if humidity < 85% and not cycle_active:
    start_cycle()  # Begin MIST phase

# Stop Conditions
if cycle_active:
    if humidity >= 90% and will_overshoot():
        stop_cycle()  # Predictive stop
    elif humidity >= 95%:
        stop_cycle()  # Emergency stop
    elif humidity > 97%:
        stop_cycle()  # Critical stop

# Phase Transitions
if current_phase == "mist" and elapsed >= 5s:
    switch_to_fan_phase()
elif current_phase == "fan" and elapsed >= 10s:
    switch_to_mist_phase()
```

---

## 🧮 Predictive Control Algorithm

### Humidity Trend Analysis

The system tracks the last 3 humidity readings (15 seconds of data) to calculate the rate of change:

```python
humidity_rate = (last_reading - first_reading) / time_delta  # % per second
```

**Example:**
- Reading 1: 87% @ t=0s
- Reading 2: 88.5% @ t=5s  
- Reading 3: 90% @ t=10s
- **Rate:** (90 - 87) / 10 = **0.3% per second**

### Overshoot Prediction

Before the cycle continues, the AI predicts future humidity:

```python
predicted_humidity = current_humidity + (rate * 15)  # Predict 15s ahead

if predicted_humidity > (target + 2% safety_margin):
    stop_cycle()  # Prevent overshoot
```

**Example:**
- Current: 90%
- Rate: 0.3%/s
- Predicted: 90 + (0.3 × 15) = **94.5%**
- Target: 95% (max threshold)
- **Decision:** Stop cycle now (94.5% + 2% = 96.5% > 95%)

---

## 📊 Configuration

### Humidity Thresholds (config.yaml)

```yaml
fruiting_room:
  humidity_target: 90  # Target %RH
  humidity_hysteresis: 5  # ±5% band (85-95%)
  humidity_safety_margin: 2  # Stop 2% before max
```

### Cycle Timings (logic_engine.py)

```python
class HumidifierCycleManager:
    MIST_DURATION = 5.0   # seconds
    FAN_DURATION = 10.0   # seconds
```

---

## 🔍 Monitoring & Logging

### Log Levels

**INFO** - Cycle start/stop events
```
[AI-HUMIDIFIER] Started cycle - Humidity 83.5% < target 85%
[AI-HUMIDIFIER] Stopped cycle - Predicted overshoot (humidity=92.1%, rate=0.4%/s)
```

**DEBUG** - Periodic cycle status (every 5s)
```
[HUMIDIFIER] Phase=mist, elapsed=3.2s, humidity=88.3%, rate=0.25%/s
```

**WARNING** - Emergency conditions
```
[AI-HUMIDIFIER] Emergency stop - Humidity too high (97.2%)
```

### Cycle Phase Info API

Get real-time cycle status:

```python
phase_info = humidifier_cycle.get_phase_info()

# Returns:
{
    "active": True,
    "phase": "mist",  # or "fan", "idle"
    "elapsed": 3.2,   # seconds in current phase
    "remaining": 1.8, # seconds until phase switch
    "total_runtime": 47.5  # total cycle runtime
}
```

---

## 🚀 Testing Scenarios

### Test 1: Normal Cycle Start
**Conditions:** Humidity drops to 83%  
**Expected:** 
- Cycle starts with MIST phase
- Mist Maker ON for 5s
- Switches to FAN phase
- Humidifier Fan ON for 10s
- Repeats until humidity reaches 90%

### Test 2: Predictive Stop
**Conditions:** Humidity rising at 0.4%/s, currently 91%  
**Expected:**
- Predicted: 91 + (0.4 × 15) = 97% > 95% max
- Cycle stops immediately
- Logs: "Predicted overshoot"

### Test 3: Emergency Stop
**Conditions:** Humidity suddenly spikes to 96%  
**Expected:**
- Cycle stops immediately
- Logs: "Emergency stop - Humidity too high"

### Test 4: Anomaly Detection
**Conditions:** Sensor reads humidity = 120% (impossible)  
**Expected:**
- Isolation Forest detects anomaly
- Actuation skipped
- Logs: "Skipping actuation for anomalous data"

---

## 🛠️ Code Reference

### Main Classes

1. **`HumidifierCycleManager`** - State machine for mist/fan cycle
   - `start_cycle()` - Begin cycle
   - `stop_cycle()` - End cycle
   - `get_current_states()` - Get mist/fan ON/OFF states
   - `get_phase_info()` - Get cycle monitoring data

2. **`MushroomAI`** - Main AI controller
   - `detect_anomaly()` - Isolation Forest anomaly detection
   - `predict_actuator_states()` - Decision Tree actuation
   - `_calculate_humidity_trend()` - Rate of change analysis
   - `_predict_humidity_overshoot()` - Predictive stopping
   - `_rule_based_fruiting_actuation()` - Enhanced control logic

### File Locations

- **Logic Engine:** `rpi_gateway/app/core/logic_engine.py`
- **ML Models:** `rpi_gateway/data/models/`
  - `isolation_forest.pkl` - Anomaly detector
  - `decision_tree.pkl` - Actuation model
- **Configuration:** `rpi_gateway/config.yaml`

---

## 📈 Performance Metrics

### Success Criteria

✅ **Humidity Stability:** Maintain 90% ±2% for >90% of time  
✅ **Overshoot Prevention:** <1% overshoot occurrences  
✅ **Cycle Efficiency:** <5 cycles per hour on average  
✅ **Response Time:** <30s from low humidity to cycle start  

### Monitoring Endpoints

- **Dashboard:** http://raspberrypi.local:5000/dashboard
- **Sensor Readings:** `/api/sensor_readings`
- **Actuator States:** `/api/actuator_states`
- **Alerts:** `/api/alerts`

---

## 🐛 Troubleshooting

### Issue: Cycle won't start
**Symptoms:** Humidity low, but cycle stays idle  
**Check:**
- Anomaly detection blocking? (Check logs for "anomalous data")
- Humidity reading valid? (Should be 0-100%)
- Config threshold correct? (`humidity_target - 5`)

**Fix:**
```bash
# Check sensor readings
curl http://raspberrypi.local:5000/api/sensor_readings

# Verify config
cat rpi_gateway/config.yaml | grep humidity
```

### Issue: Overshooting target
**Symptoms:** Humidity exceeds 95%  
**Check:**
- Trend calculation working? (Need 2+ readings)
- Safety margin too small? (Default 2%)
- Cycle stopping too late?

**Fix:**
```python
# In logic_engine.py, increase safety margin:
safety_margin = 3  # Was 2
```

### Issue: Rapid on/off cycling
**Symptoms:** Cycle starts and stops every few seconds  
**Check:**
- Hysteresis too small?
- Sensor noise triggering false readings?

**Fix:**
```yaml
# In config.yaml, increase hysteresis:
humidity_hysteresis: 7  # Was 5
```

---

## 🔮 Future Enhancements

### Planned Features

1. **Adaptive Cycle Timing** - Adjust mist/fan duration based on room size
2. **Seasonal Adjustments** - Account for ambient temperature/humidity
3. **Multi-Room Coordination** - Optimize airflow between chambers
4. **Energy Optimization** - Minimize power consumption
5. **Reinforcement Learning** - Self-tuning based on outcomes

### Model Training

To retrain the AI models with new data:

```bash
cd rpi_gateway
python app/core/logic_engine.py --train --data data/training_samples.csv
```

---

## 📚 References

- **Isolation Forest:** Outlier detection for sensor fault filtering
- **Decision Tree:** Classification for optimal actuation states
- **Hysteresis:** Prevent rapid state changes in control systems
- **Predictive Control:** Model Predictive Control (MPC) principles

---

## ✅ Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Cycle State Machine | ✅ Complete | HumidifierCycleManager class |
| Trend Analysis | ✅ Complete | 3-reading moving window |
| Predictive Stop | ✅ Complete | 15s lookahead with safety |
| Anomaly Detection | ✅ Complete | Isolation Forest integration |
| Logging System | ✅ Complete | INFO/DEBUG/WARNING levels |
| Dashboard UI | ✅ Complete | Humidifier System card |
| Arduino Integration | ✅ Complete | Separate mist/fan commands |

**Last Updated:** 2024-01-20  
**Version:** 1.0  
**Author:** MASH IoT Development Team
