// M.A.S.H. IoT - Safety Watchdog (Simplified)
// Tracks serial connection status for diagnostics
// Hardware WDT (avr/wdt.h) handles crash recovery from I2C lockups

#ifndef SAFETY_H
#define SAFETY_H

#include <Arduino.h>

class SafetyWatchdog {
private:
    unsigned long lastHeartbeat;
    unsigned long timeout;
    bool isActive;
    bool hasTriggered;
    unsigned long triggeredAt;
    unsigned long recoveryCount;
    
public:
    SafetyWatchdog(unsigned long timeoutMs);
    
    // Start monitoring
    void begin();
    
    // Call this when serial data is received (resets timeout counter)
    // Returns true if recovery occurred (was triggered, now restored)
    bool heartbeat();
    
    // Check if timeout occurred (call in main loop)
    // NOTE: This only tracks serial silence, it does NOT shut down relays.
    // The hardware WDT handles crash recovery from I2C lockups.
    bool checkTimeout();
    
    // Reset watchdog
    void reset();
    
    // Get status
    bool isSafe();
    
    // Get time since last heartbeat in milliseconds
    unsigned long getTimeSinceLastHeartbeat();
    
    // Get total recovery count
    unsigned long getRecoveryCount();
};

#endif // SAFETY_H
