# M.A.S.H. IoT System Improvements Summary

## Overview
This document summarizes the comprehensive improvements made to the M.A.S.H. IoT system, focusing on dynamic condition monitoring, automation controls, AI/ML integration, and alerts management.

---

## 1. Dynamic Condition Status ✅

### Problem
- Spawning room showed "Optimal" even with CO2 at 563 ppm (target: >2000 ppm)
- Fruiting room always showed "Optimal" regardless of actual sensor values
- Condition status was hardcoded and not responsive to sensor data

### Solution
**File: `rpi_gateway/app/web/routes.py`**
- Added `calculate_room_condition()` function with intelligent threshold checking
- Implements severity-based status: `Optimal`, `Warning`, `Critical`
- Considers all sensors: temperature, humidity, and CO2
- Uses configurable thresholds from `config.yaml`

**Algorithm:**
```python
# Temperature deviation beyond tolerance triggers warnings/critical
temp_diff = abs(temp - temp_target)
if temp_diff > temp_tolerance * 1.5:  # Critical
elif temp_diff > temp_tolerance:       # Warning

# CO2 above max triggers alerts
if co2 > co2_max * 1.3:    # Critical (30% above)
elif co2 > co2_max:        # Warning
```

**File: `rpi_gateway/app/web/templates/dashboard.html`**
- Updated to display dynamic condition status
- Color-coded indicators: green (Optimal), yellow (Warning), red (Critical)

---

## 2. Actuator Control with Automation Lock 🔒

### Problem
- Users could manually control actuators even when automation was active
- No visual feedback when controls were disabled
- No notification when user tried to control during auto mode

### Solution
**File: `rpi_gateway/app/web/static/js/controls.js`**

**Features Added:**
1. **Visual Disabled State**
   - Cards become semi-transparent (opacity: 0.6)
   - Cursor changes to `not-allowed`
   - Applied when automation toggle is enabled

2. **Toast Notifications**
   - Custom notification system with animations
   - Clear message: "Automatic control is enabled. Switch to Manual mode to control actuators directly."
   - Auto-dismiss after 3 seconds
   - Color-coded by severity (success, warning, error, info)

3. **Initialization on Page Load**
   - Checks auto mode state on page load
   - Automatically disables cards if automation is active
   - Prevents confusion about why controls aren't responding

**Code Highlights:**
```javascript
function updateCardsDisabledState(isAutoMode) {
    allCards.forEach(card => {
        if (isAutoMode) {
            card.classList.add('disabled');
            card.style.opacity = '0.6';
            card.style.cursor = 'not-allowed';
        } else {
            card.classList.remove('disabled');
            card.style.opacity = '1';
            card.style.cursor = 'pointer';
        }
    });
}
```

---

## 3. AI/ML System Verification & Enhancement 🤖

### Enhanced AI Insights Page
**File: `rpi_gateway/app/web/templates/ai_insights.html`**

**New Features:**
1. **Detailed System Status**
   - Checks if `scikit-learn` is installed
   - Shows ML enabled/disabled status
   - Displays individual model loading status

2. **Model Status Cards**
   - Anomaly Detection (Isolation Forest): Loaded/Not Found
   - Actuation Control (Decision Tree): Loaded/Not Found
   - Visual indicators with icons

3. **Comprehensive Documentation**
   - Explains how each ML stage works
   - Shows fallback behavior when models aren't available
   - Provides training instructions

4. **Installation Guidance**
   - Clear instructions for installing scikit-learn
   - Code snippets for model training
   - File paths for model storage

**File: `rpi_gateway/app/web/routes.py`**
```python
@web_bp.route('/ai_insights')
def ai_insights():
    logic_engine = getattr(current_app, 'logic_engine', None)
    ml_enabled = False
    anomaly_model_loaded = False
    actuation_model_loaded = False
    
    if logic_engine:
        ml_enabled = logic_engine.ml_enabled
        anomaly_model_loaded = logic_engine.anomaly_detector is not None
        actuation_model_loaded = logic_engine.actuator_model is not None
```

---

## 4. Logic Engine Integration 🔧

### Problem
- Database reference not properly initialized in ML engine
- Alerts weren't being saved to database
- Logic engine not accessible from Flask routes

### Solution
**File: `rpi_gateway/app/core/logic_engine.py`**
```python
def __init__(self, model_dir: str = "rpi_gateway/data/models", config: Dict = None):
    self.db = None  # Initialize db attribute
    # ... rest of initialization

# Update alert saving
if alerts and self.db is not None:
    for room, alert_type, message, severity in alerts:
        try:
            self.db.insert_alert(room, alert_type, message, severity)
            logger.info(f"[ALERT] {message}")
        except Exception as e:
            logger.error(f"[ALERT] Failed to save alert: {e}")
```

**File: `rpi_gateway/app/main.py`**
```python
# Pass logic engine to Flask app
self.app.logic_engine = self.ai

# Pass database reference to ML engine
self.ai.db = self.db
```

---

## 5. Alerts System Enhancement 🚨

### Enhanced Alerts Page
**File: `rpi_gateway/app/web/templates/alerts.html`**

**New Features:**
1. **Alert Statistics Dashboard**
   - Count of Critical alerts
   - Count of Error alerts
   - Count of Warning alerts
   - Color-coded stat cards

2. **Improved Table Design**
   - Modern gradient header
   - Hover effects on rows
   - Better badge styling
   - Responsive layout

3. **Empty State Design**
   - "All Systems Nominal" message
   - Green checkmark icon
   - Encouraging message when no alerts exist

4. **Color Coding**
   - Critical/Error: Red badges
   - Warning: Orange badges
   - Info: Blue badges

### Alert Generation
Alerts are automatically generated by the logic engine when:
- Temperature deviates beyond tolerance
- Humidity is too low/high
- CO2 exceeds maximum threshold

All alerts are:
1. Logged to console with timestamp
2. Saved to SQLite database
3. Displayed in the Alerts page
4. Available for backend sync (if connected)

---

## 6. Configuration Validation 📋

### Thresholds from `config.yaml`

**Fruiting Room:**
```yaml
fruiting_room:
  temp_target: 24.0  # °C
  temp_tolerance: 2.0
  humidity_target: 90.0  # %
  humidity_tolerance: 10.0
  co2_max: 1000  # ppm
```

**Spawning Room:**
```yaml
spawning_room:
  temp_target: 25.0  # °C
  temp_tolerance: 2.0
  humidity_target: 95.0  # %
  humidity_tolerance: 10.0
  co2_max: 2000  # ppm (higher during spawn run)
```

---

## Testing Checklist ✓

### 1. Dynamic Condition Status
- [ ] Fruiting room shows "Critical" when CO2 > 1300 ppm
- [ ] Fruiting room shows "Warning" when CO2 > 1000 ppm
- [ ] Spawning room shows "Warning" when CO2 < 2000 ppm
- [ ] Spawning room shows "Critical" when CO2 < 1400 ppm
- [ ] Temperature deviations trigger appropriate status
- [ ] Humidity deviations trigger appropriate status

### 2. Control Disabling
- [ ] Cards are disabled (opacity 0.6) when auto mode is ON
- [ ] Toast notification appears when clicking disabled card
- [ ] Cards become clickable when auto mode is OFF
- [ ] State persists correctly after page reload

### 3. AI Insights
- [ ] Shows correct ML library installation status
- [ ] Displays model loading status correctly
- [ ] Shows fallback status when models missing
- [ ] Provides clear instructions for setup

### 4. Alerts System
- [ ] Alerts appear in the alerts page
- [ ] Alert counts are correct in stat cards
- [ ] Color coding matches severity
- [ ] Timestamps are formatted correctly
- [ ] Empty state shows when no alerts

### 5. Anomaly Detection
- [ ] Filters out impossible sensor values (temp > 50°C)
- [ ] Logs anomaly detections to console
- [ ] Prevents actuation on anomalous data

### 6. Actuation Control
- [ ] Exhaust fan activates when CO2 exceeds threshold
- [ ] Humidifier activates when humidity drops
- [ ] LED follows time schedule
- [ ] Hysteresis prevents rapid cycling

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Flask Web Server                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Dashboard  │  │  Controls   │  │ AI Insights │        │
│  │  (Dynamic   │  │  (Locked    │  │  (Status    │        │
│  │  Condition) │  │  in Auto)   │  │  Display)   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              M.A.S.H. Orchestrator (main.py)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Logic Engine (MushroomAI)               │  │
│  │  ┌───────────────────┐  ┌─────────────────────────┐ │  │
│  │  │ Anomaly Detection │  │  Actuation Control      │ │  │
│  │  │ (Isolation Forest)│  │  (Decision Tree/Rules)  │ │  │
│  │  └───────────────────┘  └─────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Arduino Serial Communication                   │
│  ┌───────────┐  ┌───────────┐  ┌──────────────────┐       │
│  │  Sensors  │  │ Actuators │  │  Command Queue   │       │
│  └───────────┘  └───────────┘  └──────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   SQLite Database                           │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐     │
│  │ Sensor Data│  │   Alerts   │  │  Command Logs    │     │
│  └────────────┘  └────────────┘  └──────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## Files Modified

1. **`rpi_gateway/app/web/routes.py`**
   - Added `calculate_room_condition()` function
   - Updated `get_live_data()` to include condition status
   - Enhanced `ai_insights()` route with ML status

2. **`rpi_gateway/app/web/templates/dashboard.html`**
   - Updated to use dynamic condition status

3. **`rpi_gateway/app/web/templates/ai_insights.html`**
   - Complete redesign with detailed status information

4. **`rpi_gateway/app/web/templates/alerts.html`**
   - Enhanced UI with statistics and better styling

5. **`rpi_gateway/app/web/static/js/controls.js`**
   - Added disable state management
   - Implemented toast notification system

6. **`rpi_gateway/app/core/logic_engine.py`**
   - Fixed database reference initialization
   - Improved error handling for alerts

7. **`rpi_gateway/app/main.py`**
   - Added logic engine to Flask app context

---

## Next Steps

1. **Train ML Models** (if not already done)
   ```bash
   python -m app.core.logic_engine
   ```

2. **Verify Database**
   - Check that `rpi_gateway/data/sensor_data.db` exists
   - Verify tables are created correctly

3. **Test with Real Data**
   - Connect Arduino and verify sensor readings
   - Monitor condition status changes
   - Check alert generation

4. **Deploy to Raspberry Pi**
   - Transfer updated files
   - Restart the service
   - Monitor logs for any issues

---

## Troubleshooting

### Issue: ML Models Not Loading
**Solution:** Run training script to generate models
```bash
cd rpi_gateway
python -m app.core.logic_engine
```

### Issue: Alerts Not Appearing
**Solution:** Check database connection and logic engine initialization
```python
# In main.py, verify:
self.ai.db = self.db  # Database reference is passed
```

### Issue: Controls Not Disabling
**Solution:** Check auto mode toggle in Flask app config
```python
# In routes.py, verify:
auto_mode_enabled = config.get('system', {}).get('auto_mode', True)
```

---

## Summary of Improvements

✅ **Dynamic condition monitoring** - Accurately reflects system status  
✅ **Control locking** - Prevents manual interference with automation  
✅ **Toast notifications** - Clear user feedback  
✅ **ML system verification** - Comprehensive status display  
✅ **Enhanced alerts** - Better visualization and statistics  
✅ **Proper integration** - All components properly connected  

The M.A.S.H. IoT system now provides reliable, intelligent, and user-friendly mushroom cultivation automation! 🍄
