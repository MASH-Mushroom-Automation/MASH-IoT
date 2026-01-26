// M.A.S.H. IoT - Safety Watchdog
// Monitors serial connection and shuts down relays if RPi disconnects

#ifndef SAFETY_H
#define SAFETY_H

#include <Arduino.h>

class SafetyWatchdog {
private:
    unsigned long lastHeartbeat;
    unsigned long timeout;
    bool isActive;
    bool hasTriggered;
    
public:
    SafetyWatchdog(unsigned long timeoutMs);
    
    // Start monitoring
    void begin();
    
    // Call this when serial data is received
    void heartbeat();
    
    // Check if timeout occurred (call in main loop)
    bool checkTimeout();
    
    // Reset watchdog
    void reset();
    
    // Get status
    bool isSafe();
};

#endif // SAFETY_H
