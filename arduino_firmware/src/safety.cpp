// M.A.S.H. IoT - Safety Implementation
// Watchdog timer to prevent relay stuck-on scenarios
// Supports automatic recovery when RPi serial resumes

#include "safety.h"
#include "config.h"

SafetyWatchdog::SafetyWatchdog(unsigned long timeoutMs) {
    timeout = timeoutMs;
    lastHeartbeat = 0;
    isActive = false;
    hasTriggered = false;
    triggeredAt = 0;
    recoveryCount = 0;
}

void SafetyWatchdog::begin() {
    lastHeartbeat = millis();
    isActive = true;
    hasTriggered = false;
    triggeredAt = 0;
    recoveryCount = 0;
    Serial.println(F("[WATCHDOG] Started"));
}

bool SafetyWatchdog::heartbeat() {
    lastHeartbeat = millis();
    
    // If we were previously in triggered (shutdown) state, this means
    // the RPi serial connection has resumed. Signal recovery so the
    // main loop can restore relay states.
    if (hasTriggered) {
        unsigned long downtime = millis() - triggeredAt;
        hasTriggered = false;
        triggeredAt = 0;
        recoveryCount++;
        
        Serial.print(F("[WATCHDOG] Connection restored after "));
        Serial.print(downtime / 1000);
        Serial.println(F("s downtime"));
        
        // Send recovery signal as JSON so RPi can detect it and
        // call restore_relay_states() without needing a USB replug
        Serial.println(F("{\"watchdog\":\"recovered\"}"));
        
        return true;  // Recovery occurred
    }
    
    return false;  // Normal heartbeat, no recovery needed
}

bool SafetyWatchdog::checkTimeout() {
    if (!isActive) return false;
    
    unsigned long elapsed = millis() - lastHeartbeat;
    
    if (elapsed > timeout && !hasTriggered) {
        hasTriggered = true;
        triggeredAt = millis();
        Serial.print(F("[WATCHDOG] TIMEOUT after "));
        Serial.print(elapsed / 1000);
        Serial.println(F("s without serial data. Shutting down relays."));
        return true;  // Trigger safety shutdown
    }
    
    return false;
}

void SafetyWatchdog::reset() {
    lastHeartbeat = millis();
    hasTriggered = false;
    triggeredAt = 0;
}

bool SafetyWatchdog::isSafe() {
    return !hasTriggered;
}

unsigned long SafetyWatchdog::getTimeSinceLastHeartbeat() {
    return millis() - lastHeartbeat;
}

unsigned long SafetyWatchdog::getRecoveryCount() {
    return recoveryCount;
}
