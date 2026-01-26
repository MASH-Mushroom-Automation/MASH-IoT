// M.A.S.H. IoT - Safety Implementation
// Watchdog timer to prevent relay stuck-on scenarios

#include "safety.h"
#include "config.h"

SafetyWatchdog::SafetyWatchdog(unsigned long timeoutMs) {
    timeout = timeoutMs;
    lastHeartbeat = 0;
    isActive = false;
    hasTriggered = false;
}

void SafetyWatchdog::begin() {
    lastHeartbeat = millis();
    isActive = true;
    hasTriggered = false;
    Serial.println(F("[WATCHDOG] Started"));
}

void SafetyWatchdog::heartbeat() {
    lastHeartbeat = millis();
    
    // Reset trigger flag if we were previously disconnected
    if (hasTriggered) {
        hasTriggered = false;
        Serial.println(F("[WATCHDOG] Connection restored"));
    }
}

bool SafetyWatchdog::checkTimeout() {
    if (!isActive) return false;
    
    unsigned long elapsed = millis() - lastHeartbeat;
    
    if (elapsed > timeout && !hasTriggered) {
        hasTriggered = true;
        Serial.println(F("[WATCHDOG] TIMEOUT! Serial connection lost"));
        return true;  // Trigger safety shutdown
    }
    
    return false;
}

void SafetyWatchdog::reset() {
    lastHeartbeat = millis();
    hasTriggered = false;
}

bool SafetyWatchdog::isSafe() {
    return !hasTriggered;
}
