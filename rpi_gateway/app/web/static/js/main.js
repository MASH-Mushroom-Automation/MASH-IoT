// M.A.S.H. IoT - Main Dashboard Logic
// Handles view toggling, live data polling, and manual controls.

document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. View Toggling (Fruiting vs Spawning) ---
    const fruitingBtn = document.getElementById('show-fruiting');
    const spawningBtn = document.getElementById('show-spawning');
    const fruitingView = document.getElementById('fruiting-view');
    const spawningView = document.getElementById('spawning-view');

    function switchView(viewToShow) {
        // Safety check if elements exist
        if (!fruitingView || !spawningView) return;

        fruitingView.style.display = 'none';
        spawningView.style.display = 'none';

        if (fruitingBtn) fruitingBtn.classList.remove('active');
        if (spawningBtn) spawningBtn.classList.remove('active');

        if (viewToShow === 'fruiting') {
            fruitingView.style.display = 'block';
            if (fruitingBtn) fruitingBtn.classList.add('active');
        } else if (viewToShow === 'spawning') {
            spawningView.style.display = 'block';
            if (spawningBtn) spawningBtn.classList.add('active');
        }
    }

    if (fruitingBtn) fruitingBtn.addEventListener('click', () => switchView('fruiting'));
    if (spawningBtn) spawningBtn.addEventListener('click', () => switchView('spawning'));

    // Set initial view
    switchView('fruiting');

    // --- 2. Live Data Polling ---
    // Start auto-refresh only if we are on the dashboard
    if (document.querySelector('.system-status')) {
        updateDashboardData();
        setInterval(updateDashboardData, 3000); // Update every 3 seconds
    }
});

// Function to fetch and update data via AJAX
async function updateDashboardData() {
    try {
        const response = await fetch('/api/latest_data');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        
        // --- UPDATE SYSTEM STATUS (Using IDs for reliability) ---
        
        // Arduino Status
        const arduinoStatus = document.getElementById('arduino-status');
        if (arduinoStatus) {
            arduinoStatus.textContent = data.arduino_connected ? 'Connected' : 'Offline';
            arduinoStatus.className = data.arduino_connected ? 'status-ok' : 'status-error';
        }
        
        // Cloud Status (The FIX: Uses the ID we added to dashboard.html)
        const cloudStatus = document.getElementById('cloud-status');
        if (cloudStatus) {
            cloudStatus.textContent = data.backend_connected ? 'Online' : 'Offline';
            cloudStatus.className = data.backend_connected ? 'status-ok' : 'status-warning';
        }
        
        // WiFi Status
        const wifiStatus = document.getElementById('wifi-status');
        // We let the separate WiFi checker handle the text, or update basic status here
        // (The separate updateWiFiStatus function below handles the specific network name)
        
        // Uptime
        const uptimeEl = document.getElementById('uptime');
        if (uptimeEl && data.uptime) {
            uptimeEl.textContent = data.uptime;
        }
        
        // --- UPDATE ROOM CONDITIONS ---
        updateRoomCondition('#fruiting-view', data.fruiting_condition, data.fruiting_condition_class);
        updateRoomCondition('#spawning-view', data.spawning_condition, data.spawning_condition_class);
        
        // --- UPDATE SENSOR VALUES ---
        updateSensorValues('#fruiting-view', data.fruiting_data);
        updateSensorValues('#spawning-view', data.spawning_data);
        
        // --- UPDATE ACTUATOR ICONS ---
        updateActuatorIcons('#fruiting-view', data.fruiting_actuators);
        updateActuatorIcons('#spawning-view', data.spawning_actuators);

        // Update WiFi Details
        updateWiFiStatus();

    } catch (error) {
        console.error("Dashboard update failed:", error);
    }
}

// Helper: Update Room Condition Text/Color
function updateRoomCondition(viewSelector, text, colorClass) {
    if (!text) return;
    const el = document.querySelector(`${viewSelector} .room-condition span`);
    if (el) {
        el.textContent = text;
        el.className = 'status-' + colorClass;
    }
}

// Helper: Update Sensor Cards
function updateSensorValues(viewSelector, sensorData) {
    const view = document.querySelector(viewSelector);
    if (!view) return;

    const setVal = (type, val) => {
        const el = view.querySelector(`.sensor-card.${type} .sensor-value`);
        if (el) el.textContent = (sensorData && val !== null && val !== undefined) ? Number(val).toFixed(1) : '--';
    };

    if (sensorData) {
        setVal('co2', sensorData.co2);
        setVal('temp', sensorData.temp);
        setVal('humidity', sensorData.humidity);
    } else {
        setVal('co2', null);
        setVal('temp', null);
        setVal('humidity', null);
    }
}

// Helper: Update Actuator Icons (Active/Inactive state)
function updateActuatorIcons(viewSelector, actuators) {
    const view = document.querySelector(viewSelector);
    if (!view || !actuators) return;
    
    const updateIcon = (cls, isActive) => {
        const icon = view.querySelector(cls);
        if (icon) isActive ? icon.classList.add('active') : icon.classList.remove('active');
    };

    updateIcon('.icon-mist', actuators.mist_maker);
    updateIcon('.icon-humidifier-fan', actuators.humidifier_fan);
    updateIcon('.icon-exhaust', actuators.exhaust_fan);
    updateIcon('.icon-intake', actuators.intake_fan);
    updateIcon('.icon-light', actuators.led);
}

// --- WiFi Status Checker ---
async function updateWiFiStatus() {
    try {
        const response = await fetch('/api/wifi_status');
        const data = await response.json();
        
        const wifiStatusEl = document.getElementById('wifi-status');
        if (wifiStatusEl) {
            if (data.connected && data.current_network) {
                wifiStatusEl.textContent = data.current_network;
                wifiStatusEl.className = 'status-ok';
            } else {
                wifiStatusEl.textContent = 'Disconnected';
                wifiStatusEl.className = 'status-warning';
            }
        }
    } catch (error) {
        // console.error('WiFi check failed'); 
        // Suppress error to avoid log spam
    }
}

// --- 3. Manual Controls Page Logic ---
// Only runs if we are on the controls page
const controlSwitches = document.querySelectorAll('.controls-container input[type="checkbox"]');

if (controlSwitches.length > 0) {
    controlSwitches.forEach(sw => {
        sw.addEventListener('change', function() {
            const room = this.dataset.room;
            const actuator = this.dataset.actuator;
            const state = this.checked ? 'ON' : 'OFF';

            // Send the command to the backend
            sendCommand(room, actuator, state);
        });
    });
}

async function sendCommand(room, actuator, state) {
    try {
        const response = await fetch('/api/control_actuator', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room, actuator, state }),
        });

        if (!response.ok) throw new Error(`Status: ${response.status}`);
        
        const result = await response.json();
        console.log('Command sent:', result);
            
    } catch (error) {
        console.error('Command failed:', error);
        alert("Failed to toggle actuator. Check connection.");
    }
}