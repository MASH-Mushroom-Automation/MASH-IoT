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
});

// Future implementation: Function to fetch and update data via AJAX
/*
async function updateDashboardData() {
    try {
        const response = await fetch('/api/latest_data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        // Update sensor values for both rooms
        // Example for fruiting CO2:
        // document.querySelector('#fruiting-view .sensor-card.co2 .sensor-value').textContent = data.fruiting_data.co2.toFixed(1);
        
        // Update actuator icons
        // Example for fruiting exhaust fan:
        // const fanIcon = document.querySelector('#fruiting-view .icon-fan');
        // if (data.fruiting_actuators.exhaust_fan) {
        //     fanIcon.classList.add('active');
        // } else {
        //     fanIcon.classList.remove('active');
        // }

    } catch (error) {
        console.error("Could not fetch dashboard data:", error);
    }
}

// Update data every 5 seconds
// setInterval(updateDashboardData, 5000);
*/

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
