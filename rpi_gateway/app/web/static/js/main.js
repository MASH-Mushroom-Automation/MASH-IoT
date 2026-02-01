// Main JavaScript file for MASH IoT Dashboard
// Handles view toggling and future dynamic data updates.

document.addEventListener('DOMContentLoaded', function() {
    const fruitingBtn = document.getElementById('show-fruiting');
    const spawningBtn = document.getElementById('show-spawning');
    const fruitingView = document.getElementById('fruiting-view');
    const spawningView = document.getElementById('spawning-view');

    // Function to switch views
    function switchView(viewToShow) {
        // Hide all views first
        fruitingView.style.display = 'none';
        spawningView.style.display = 'none';

        // Deactivate all buttons
        fruitingBtn.classList.remove('active');
        spawningBtn.classList.remove('active');

        // Show the selected view and activate its button
        if (viewToShow === 'fruiting') {
            fruitingView.style.display = 'block';
            fruitingBtn.classList.add('active');
        } else if (viewToShow === 'spawning') {
            spawningView.style.display = 'block';
            spawningBtn.classList.add('active');
        }
    }

    // Add click event listeners
    if (fruitingBtn) {
        fruitingBtn.addEventListener('click', () => switchView('fruiting'));
    }
    
    if (spawningBtn) {
        spawningBtn.addEventListener('click', () => switchView('spawning'));
    }

    // Set the initial view
    switchView('fruiting');
    
    // Start auto-refresh if on dashboard page
    if (fruitingView && spawningView) {
        updateDashboardData();
        setInterval(updateDashboardData, 3000); // Update every 3 seconds
    }
});

// Function to fetch and update data via AJAX
async function updateDashboardData() {
    try {
        const response = await fetch('/api/latest_data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        // Update Arduino connection status
        const arduinoStatus = document.querySelector('.system-status span:first-child span:last-child');
        if (arduinoStatus) {
            if (data.arduino_connected) {
                arduinoStatus.textContent = 'Connected';
                arduinoStatus.className = 'status-ok';
            } else {
                arduinoStatus.textContent = 'Offline';
                arduinoStatus.className = 'status-error';
            }
        }
        
        // Update Backend connection status
        const backendStatus = document.querySelector('.system-status span:nth-child(2) span:last-child');
        if (backendStatus) {
            if (data.backend_connected) {
                backendStatus.textContent = 'Online';
                backendStatus.className = 'status-ok';
            } else {
                backendStatus.textContent = 'Offline';
                backendStatus.className = 'status-warning';
            }
        }
        
        // Update Uptime
        const uptimeEl = document.getElementById('uptime');
        if (uptimeEl && data.uptime) {
            uptimeEl.textContent = data.uptime;
        }
        
        // Update Fruiting Room condition
        if (data.fruiting_condition) {
            const fruitingConditionEl = document.querySelector('#fruiting-view .room-condition span');
            if (fruitingConditionEl) {
                fruitingConditionEl.textContent = data.fruiting_condition;
                // Update class based on condition
                fruitingConditionEl.className = 'status-' + data.fruiting_condition_class;
            }
        }
        
        // Update Spawning Room condition
        if (data.spawning_condition) {
            const spawningConditionEl = document.querySelector('#spawning-view .room-condition span');
            if (spawningConditionEl) {
                spawningConditionEl.textContent = data.spawning_condition;
                // Update class based on condition
                spawningConditionEl.className = 'status-' + data.spawning_condition_class;
            }
        }
        
        // Update Fruiting Room sensor values
        if (data.fruiting_data) {
            const fruitingCO2 = document.querySelector('#fruiting-view .sensor-card.co2 .sensor-value');
            const fruitingTemp = document.querySelector('#fruiting-view .sensor-card.temp .sensor-value');
            const fruitingHumidity = document.querySelector('#fruiting-view .sensor-card.humidity .sensor-value');
            
            if (fruitingCO2) fruitingCO2.textContent = data.fruiting_data.co2 !== null ? data.fruiting_data.co2.toFixed(1) : '--';
            if (fruitingTemp) fruitingTemp.textContent = data.fruiting_data.temp !== null ? data.fruiting_data.temp.toFixed(1) : '--';
            if (fruitingHumidity) fruitingHumidity.textContent = data.fruiting_data.humidity !== null ? data.fruiting_data.humidity.toFixed(1) : '--';
        } else {
            // Set all to '--' if no data
            const fruitingValues = document.querySelectorAll('#fruiting-view .sensor-value');
            fruitingValues.forEach(val => val.textContent = '--');
        }
        
        // Update Spawning Room sensor values
        if (data.spawning_data) {
            const spawningCO2 = document.querySelector('#spawning-view .sensor-card.co2 .sensor-value');
            const spawningTemp = document.querySelector('#spawning-view .sensor-card.temp .sensor-value');
            const spawningHumidity = document.querySelector('#spawning-view .sensor-card.humidity .sensor-value');
            
            if (spawningCO2) spawningCO2.textContent = data.spawning_data.co2 !== null ? data.spawning_data.co2.toFixed(1) : '--';
            if (spawningTemp) spawningTemp.textContent = data.spawning_data.temp !== null ? data.spawning_data.temp.toFixed(1) : '--';
            if (spawningHumidity) spawningHumidity.textContent = data.spawning_data.humidity !== null ? data.spawning_data.humidity.toFixed(1) : '--';
        } else {
            // Set all to '--' if no data
            const spawningValues = document.querySelectorAll('#spawning-view .sensor-value');
            spawningValues.forEach(val => val.textContent = '--');
        }
        
        // Update actuator icons
        updateActuatorIcons('#fruiting-view', data.fruiting_actuators);
        updateActuatorIcons('#spawning-view', data.spawning_actuators);

    } catch (error) {
        console.error("Could not fetch dashboard data:", error);
        // Mark Arduino as offline on error
        const arduinoStatus = document.querySelector('.system-status span:first-child span:last-child');
        if (arduinoStatus) {
            arduinoStatus.textContent = 'Offline';
            arduinoStatus.className = 'status-error';
        }
    }
}

function updateActuatorIcons(viewSelector, actuators) {
    const view = document.querySelector(viewSelector);
    if (!view || !actuators) return;
    
    const fanIcon = view.querySelector('.icon-fan');
    const blowerIcon = view.querySelector('.icon-blower');
    const mistIcon = view.querySelector('.icon-mist');
    const lightIcon = view.querySelector('.icon-light');
    
    if (fanIcon) {
        actuators.exhaust_fan ? fanIcon.classList.add('active') : fanIcon.classList.remove('active');
    }
    if (blowerIcon) {
        actuators.blower_fan ? blowerIcon.classList.add('active') : blowerIcon.classList.remove('active');
    }
    if (mistIcon) {
        actuators.humidifier ? mistIcon.classList.add('active') : mistIcon.classList.remove('active');
    }
    if (lightIcon) {
        actuators.led ? lightIcon.classList.add('active') : lightIcon.classList.remove('active');
    }
}

// --- Manual Controls Page Logic ---
const controlSwitches = document.querySelectorAll('.controls-container input[type="checkbox"]');

controlSwitches.forEach(sw => {
    sw.addEventListener('change', function() {
        const room = this.dataset.room;
        const actuator = this.dataset.actuator;
        const state = this.checked ? 'ON' : 'OFF';

        // Send the command to the backend
        sendCommand(room, actuator, state);
    });
});

async function sendCommand(room, actuator, state) {
    try {
        const response = await fetch('/api/control_actuator', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ room, actuator, state }),
        });

        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Command sent successfully:', result);
        // Optionally, provide user feedback here
            
    } catch (error) {
        console.error('Failed to send command:', error);
        // Optionally, revert the switch state and show an error to the user
    }
}
