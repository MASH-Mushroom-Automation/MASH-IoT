// M.A.S.H. IoT - Actuator Controls JavaScript
// Handles grid card toggle interactions and auto control mode

document.addEventListener('DOMContentLoaded', function() {
    // ========== AUTO CONTROL MODE TOGGLE ==========
    const autoControlToggle = document.getElementById('auto-control-toggle');
    const autoStatusText = document.getElementById('auto-status-text');
    const allCards = document.querySelectorAll('.actuator-card');

    // Initialize card states based on auto mode
    if (autoControlToggle) {
        // Set initial disabled state
        const isAutoMode = autoControlToggle.checked;
        updateCardsDisabledState(isAutoMode);
        
        autoControlToggle.addEventListener('change', function() {
            const isAutoMode = this.checked;
            
            // Update status text
            autoStatusText.textContent = isAutoMode ? 'Automatic Control' : 'Manual Control';
            
            // Disable/enable manual cards based on auto mode
            updateCardsDisabledState(isAutoMode);
            
            // Send auto mode change to backend
            toggleAutoMode(isAutoMode);
        });
    }
    
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

    // ========== ACTUATOR CARD CLICK HANDLERS ==========
    allCards.forEach(card => {
        card.addEventListener('click', function() {
            // Don't toggle if auto mode is enabled
            if (this.classList.contains('disabled')) {
                showNotification(
                    'Automatic control is enabled. Switch to Manual mode to control actuators directly.',
                    'warning'
                );
                return;
            }

            const room = this.dataset.room;
            const actuator = this.dataset.actuator;
            const currentState = this.dataset.state;
            const newState = currentState === 'on' ? 'off' : 'on';
            
            // Optimistically update UI
            this.dataset.state = newState;
            const statusElement = this.querySelector('.card-status');
            statusElement.dataset.status = newState;
            statusElement.querySelector('.status-text').textContent = newState.toUpperCase();
            
            // Send command to backend
            sendActuatorCommand(room, actuator, newState, this);
        });
    });

    // ========== API FUNCTIONS ==========
    
    async function sendActuatorCommand(room, actuator, state, cardElement) {
        try {
            const response = await fetch('/api/control_actuator', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    room: room, 
                    actuator: actuator, 
                    state: state.toUpperCase() 
                }),
            });

            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Command sent successfully:', result);
            
            if (result.success) {
                showNotification(`${actuator.replace('_', ' ').toUpperCase()} turned ${state.toUpperCase()}`, 'success');
            } else {
                throw new Error(result.message || 'Command failed');
            }
            
        } catch (error) {
            console.error('Failed to send command:', error);
            
            // Revert UI on error
            const revertState = state === 'on' ? 'off' : 'on';
            cardElement.dataset.state = revertState;
            const statusElement = cardElement.querySelector('.card-status');
            statusElement.dataset.status = revertState;
            statusElement.querySelector('.status-text').textContent = revertState.toUpperCase();
            
            showNotification('Failed to control actuator: ' + error.message, 'error');
        }
    }

    async function toggleAutoMode(enabled) {
        try {
            const response = await fetch('/api/set_auto_mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ enabled: enabled }),
            });

            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Auto mode updated:', result);
            
            showNotification(
                enabled ? 'Automatic control enabled' : 'Manual control enabled', 
                'info'
            );
            
        } catch (error) {
            console.error('Failed to update auto mode:', error);
            showNotification('Failed to update control mode', 'error');
            
            // Revert toggle on error
            autoControlToggle.checked = !enabled;
        }
    }

    // ========== STATUS POLLING ==========
    // Poll actuator states every 3 seconds
    setInterval(async () => {
        try {
            const response = await fetch('/api/actuator_states');
            if (!response.ok) return;
            
            const data = await response.json();
            
            // Update card states
            Object.keys(data).forEach(room => {
                const roomData = data[room];
                Object.keys(roomData).forEach(actuator => {
                    const state = roomData[actuator].state ? 'on' : 'off';
                    const isAuto = roomData[actuator].auto || false;
                    
                    const card = document.querySelector(
                        `.actuator-card[data-room=\"${room}\"][data-actuator=\"${actuator}\"]`
                    );
                    
                    if (card) {
                        card.dataset.state = state;
                        const statusElement = card.querySelector('.card-status');
                        if (statusElement) {
                            statusElement.dataset.status = state;
                            statusElement.querySelector('.status-text').textContent = state.toUpperCase();
                        }
                        
                        // Update auto badge visibility
                        const autoBadge = card.querySelector('.card-auto-badge');
                        if (autoBadge) {
                            autoBadge.style.display = isAuto ? 'flex' : 'none';
                        }
                    }
                });
            });
            
        } catch (error) {
            console.error('Failed to poll actuator states:', error);
        }
    }, 3000);

    // ========== NOTIFICATION SYSTEM ==========
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas ${getIconForType(type)}"></i>
            <span>${message}</span>
        `;
        
        // Style
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '15px 20px',
            borderRadius: '8px',
            backgroundColor: getColorForType(type),
            color: '#fff',
            boxShadow: '0 4px 15px rgba(0,0,0,0.3)',
            zIndex: '10000',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            animation: 'slideIn 0.3s ease',
            maxWidth: '400px'
        });
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    function getIconForType(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    function getColorForType(type) {
        const colors = {
            success: '#4CAF50',
            error: '#e74c3c',
            warning: '#f39c12',
            info: '#3498db'
        };
        return colors[type] || colors.info;
    }
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
