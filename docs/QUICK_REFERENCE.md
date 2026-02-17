# Quick Reference: System Improvements

## 🎯 What Was Fixed

### 1. Condition Status Bug
**Before:** Spawning room showed "Optimal" at 563 ppm CO2 (should be >2000 ppm)  
**After:** Shows "Critical" - correctly identifies low CO2 as a problem

### 2. Control Locking
**Before:** Users could control actuators during automation  
**After:** Controls are disabled and show toast notification when auto mode is ON

### 3. AI System Status
**Before:** No way to verify if ML models are loaded  
**After:** Detailed AI Insights page shows model status and provides setup instructions

### 4. Alerts Display
**Before:** Basic table with minimal information  
**After:** Enhanced UI with statistics, color coding, and empty state

---

## 🚀 Quick Start

### Run System Tests
```bash
cd rpi_gateway
python test_improvements.py
```

### Train ML Models (if needed)
```bash
cd rpi_gateway
python -m app.core.logic_engine
```

### Start the System
```bash
cd rpi_gateway
python -m app.main
```

### Access Dashboard
```
http://localhost:5000/dashboard
```

---

## 📊 Dashboard Features

### Condition Status Colors
- 🟢 **Green (Optimal)**: All sensors within target range
- 🟡 **Yellow (Warning)**: One or more sensors outside tolerance
- 🔴 **Red (Critical)**: Severe deviation from targets

### Status Calculation
- **Temperature**: ±2°C tolerance (configurable)
- **Humidity**: ±10% tolerance (configurable)
- **CO2**: Below max threshold (1000 ppm fruiting, 2000 ppm spawning)

---

## 🎮 Controls Page

### Auto Mode Toggle
- **ON (Green)**: Automation active, controls disabled
- **OFF (Gray)**: Manual control enabled

### Visual Feedback
- Disabled cards: Semi-transparent (60% opacity)
- Enabled cards: Full brightness with hover effect
- Toast notifications: Appear top-right corner

### Actuator Cards Show:
- Current state (ON/OFF)
- Voltage rating
- Auto badge (if controlled by automation)
- Timed badge (for scheduled operations)

---

## 🤖 AI Insights Page

### What to Check
1. **scikit-learn Installation**: Should show green checkmark
2. **ML Enabled**: Should show "Machine Learning ENABLED"
3. **Model Status**: Both models should show "Model Loaded"

### If Models Missing
1. Check if `rpi_gateway/data/models/` directory exists
2. Run training script: `python -m app.core.logic_engine`
3. Refresh AI Insights page

### Fallback Behavior
- **Without ML**: System uses rule-based logic (works fine!)
- **With ML**: Enhanced anomaly detection and smart actuation

---

## 🚨 Alerts Page

### Alert Levels
- **CRITICAL**: Immediate attention required
- **ERROR**: System malfunction or failure
- **WARNING**: Deviation from optimal conditions
- **INFO**: Normal operations log

### Alert Sources
- Temperature out of range
- Humidity too low/high
- CO2 exceeding threshold
- Sensor communication errors
- Manual control actions

### Statistics Dashboard
Shows count of:
- Critical alerts (red)
- Errors (red)
- Warnings (orange)

---

## 🔧 Configuration

### File: `config/config.yaml`

#### Fruiting Room Thresholds
```yaml
fruiting_room:
  temp_target: 24.0      # Target temperature
  temp_tolerance: 2.0    # ±2°C acceptable
  humidity_target: 90.0   # Target humidity
  humidity_tolerance: 10.0  # ±10% acceptable
  co2_max: 1000          # Maximum CO2 ppm
```

#### Spawning Room Thresholds
```yaml
spawning_room:
  temp_target: 25.0
  temp_tolerance: 2.0
  humidity_target: 95.0
  humidity_tolerance: 10.0
  co2_max: 2000          # Higher CO2 tolerance
```

### To Modify Thresholds:
1. Edit `config/config.yaml`
2. Restart the application
3. Condition status will update automatically

---

## 📝 Troubleshooting

### Issue: Controls Don't Disable
**Check:**
- Auto mode toggle in controls page
- JavaScript console for errors (F12)
- Network tab for API calls

**Solution:**
- Ensure `controls.js` is loaded
- Check Flask app is running
- Verify `/api/set_auto_mode` endpoint works

### Issue: Wrong Condition Status
**Check:**
- Sensor values in dashboard
- Thresholds in `config.yaml`
- Console logs for calculation errors

**Solution:**
- Run `test_improvements.py` to verify calculation
- Check sensor data is valid (not null)
- Ensure config file is loaded correctly

### Issue: Alerts Not Appearing
**Check:**
- Database file exists: `rpi_gateway/data/sensor_data.db`
- Logic engine has database reference
- Flask app has database in config

**Solution:**
```python
# In main.py, verify:
self.ai.db = self.db  # Database passed to logic engine
self.app.config['DB'] = self.db  # Database passed to Flask
```

### Issue: ML Models Not Loading
**Check:**
- `scikit-learn` installed: `pip list | grep scikit`
- Model files exist in `rpi_gateway/data/models/`
- File permissions on model directory

**Solution:**
```bash
pip install scikit-learn joblib
python -m app.core.logic_engine  # Train models
```

---

## 📊 Testing Checklist

### Before Deployment
- [ ] Run `test_improvements.py` - all tests pass
- [ ] Dashboard shows correct condition status
- [ ] Controls disable when auto mode ON
- [ ] Toast notification appears on disabled click
- [ ] AI Insights shows model status
- [ ] Alerts page displays correctly
- [ ] Configuration loaded from YAML

### After Deployment
- [ ] Arduino connects successfully
- [ ] Sensor data updates in real-time
- [ ] Condition status changes with sensor values
- [ ] Alerts appear for threshold violations
- [ ] Manual controls work in manual mode
- [ ] Automation works in auto mode

---

## 🎨 UI Color Scheme

### Status Colors
- **Success/Optimal**: `#4CAF50` (Green)
- **Warning**: `#f39c12` (Orange)
- **Error/Critical**: `#e74c3c` (Red)
- **Info**: `#3498db` (Blue)

### Gradients
- **Primary**: `#667eea` → `#764ba2` (Purple gradient)
- **Cards**: White background with subtle shadows

### Typography
- **Font**: Segoe UI, sans-serif
- **Headings**: Bold, larger size
- **Body**: Regular weight, good line height

---

## 🔄 System Flow

```
Sensor Reading → Anomaly Detection → Condition Calculation
                                   ↓
                              Alert Generation
                                   ↓
                            Database Storage
                                   ↓
                        Dashboard/Alerts Display
```

---

## 💡 Pro Tips

1. **Monitor Alerts**: Check alerts page regularly for patterns
2. **Adjust Tolerances**: Fine-tune thresholds based on your mushroom species
3. **Use Auto Mode**: Let ML handle routine operations
4. **Manual Override**: Switch to manual for maintenance
5. **Check AI Insights**: Verify ML system is working optimally

---

## 📞 Support

### Logs Location
- Flask logs: Console output
- System logs: Database `system_logs` table
- Arduino logs: Serial monitor

### Debug Mode
```python
# In main.py, change:
orchestrator.start(host='0.0.0.0', port=5000, debug=True)
```

### Verbose Logging
```python
# In main.py, change:
logging.basicConfig(level=logging.DEBUG)
```

---

**Last Updated**: January 31, 2026  
**Version**: 2.0.0  
**Author**: M.A.S.H. Development Team
