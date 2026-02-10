// M.A.S.H. IoT - Safety Watchdog
// Monitors serial connection and shuts down relays if RPi disconnects
// Supports automatic recovery when serial communication resumes

#ifndef SAFETY_H
#define SAFETY_H

#include <Arduino.h>

class SafetyWatchdog {
private:
    unsigned long lastHeartbeat;
    unsigned long timeout;
    bool isActive;
    bool hasTriggered;
    unsigned long triggeredAt;        // When watchdog was triggered
    unsigned long recoveryCount;      // Number of recoveries since boot
    
public:
    SafetyWatchdog(unsigned long timeoutMs);
    
    // Start monitoring
    void begin();
    
    // Call this when serial data is received (resets timeout counter)
    // Returns true if recovery occurred (was triggered, now restored)
    bool heartbeat();
    
    // Check if timeout occurred (call in main loop)
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
