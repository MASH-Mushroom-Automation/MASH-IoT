// M.A.S.H. IoT - Safety Implementation (Simplified)
// Tracks serial connection status for diagnostics and recovery signaling
// NOTE: Relay shutdown removed. Hardware WDT handles crash recovery.

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
    Serial.println(F("[WATCHDOG] Serial monitor started (diagnostics only)"));
    Serial.println(F("[WATCHDOG] Hardware WDT handles crash recovery"));
}

bool SafetyWatchdog::heartbeat() {
    lastHeartbeat = millis();
    
    // If we were previously in triggered (timeout) state, serial resumed
    if (hasTriggered) {
        unsigned long downtime = millis() - triggeredAt;
        hasTriggered = false;
        triggeredAt = 0;
        recoveryCount++;
        
        Serial.print(F("[WATCHDOG] Serial resumed after "));
        Serial.print(downtime / 1000);
        Serial.println(F("s silence"));
        
        // Signal RPi to restore relay states
        Serial.println(F("{\"watchdog\":\"recovered\"}"));
        
        return true;  // Recovery occurred
    }
    
    return false;  // Normal heartbeat
}

bool SafetyWatchdog::checkTimeout() {
    if (!isActive) return false;
    
    unsigned long elapsed = millis() - lastHeartbeat;
    
    if (elapsed > timeout && !hasTriggered) {
        hasTriggered = true;
        triggeredAt = millis();
        Serial.print(F("[WATCHDOG] No serial data for "));
        Serial.print(elapsed / 1000);
        Serial.println(F("s (RPi keepalive missing)"));
        // NOTE: No relay shutdown here. This is diagnostics only.
        // If the I2C bus is locked, loop() is frozen anyway and
        // the hardware WDT will force-reset the Arduino.
        return true;
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
