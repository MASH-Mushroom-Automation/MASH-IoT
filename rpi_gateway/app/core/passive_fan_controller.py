"""
M.A.S.H. IoT - Passive Fan Controller
Handles timed interval control for passive exhaust fans.

Two modes:
1. Interval-based: Runs fan every X minutes for Y seconds
2. Clock-based: Runs fan at specific times of day
3. Flush mode: Overrides passive timing when sensor threshold exceeded
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Callable, Optional

logger = logging.getLogger(__name__)


class PassiveFanController:
    """
    Controls passive exhaust fans based on timed intervals or clock schedules.
    Can be overridden by flush mode when sensor thresholds are exceeded.
    """
    
    def __init__(self, config: Dict, actuator_callback: Callable[[str, str, str], None]):
        """
        Initialize passive fan controller.
        
        Args:
            config: Configuration dict from config.yaml
            actuator_callback: Function to call for actuator control (room, actuator, state)
        """
        self.config = config.get('passive_fans', {})
        self.actuator_callback = actuator_callback
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Track state of each passive fan
        self.fan_states = {
            'spawning_exhaust': {
                'enabled': False,
                'last_run': None,
                'flush_mode': False,
                'flush_start': None
            },
            'device_exhaust': {
                'enabled': False,
                'last_run': None
            }
        }
        
    def start(self):
        """Start the passive fan control thread."""
        if self.running:
            logger.warning("Passive fan controller already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._control_loop, daemon=True)
        self.thread.start()
        logger.info("Passive fan controller started")
    
    def stop(self):
        """Stop the passive fan control thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Passive fan controller stopped")
    
    def trigger_flush(self, room: str, sensor_data: Dict):
        """
        Trigger flush mode for a passive fan based on sensor readings.
        
        Args:
            room: Room name (e.g., 'spawning')
            sensor_data: Sensor readings dict with temp, humidity, co2
        """
        if room != 'spawning':
            return  # Only spawning room has flush mode
        
        spawning_config = self.config.get('spawning_exhaust', {})
        flush_config = spawning_config.get('flush_mode', {})
        
        if not flush_config.get('enabled', False):
            return
        
        # Check if flush should be triggered
        co2_trigger = flush_config.get('co2_trigger', 2000)
        current_co2 = sensor_data.get('co2', 0)
        
        if current_co2 > co2_trigger:
            # Start flush mode
            if not self.fan_states['spawning_exhaust']['flush_mode']:
                logger.warning(f"FLUSH MODE TRIGGERED: Spawning CO2 = {current_co2} ppm > {co2_trigger} ppm")
                self.fan_states['spawning_exhaust']['flush_mode'] = True
                self.fan_states['spawning_exhaust']['flush_start'] = time.time()
                self.actuator_callback('spawning', 'exhaust_fan', 'ON')
        else:
            # Check if flush mode should end (CO2 back to normal or timeout)
            if self.fan_states['spawning_exhaust']['flush_mode']:
                flush_duration = flush_config.get('duration_seconds', 300)
                elapsed = time.time() - self.fan_states['spawning_exhaust']['flush_start']
                
                if elapsed >= flush_duration or current_co2 < co2_trigger * 0.9:  # 10% hysteresis
                    logger.info(f"Flush mode ended: CO2 = {current_co2} ppm")
                    self.fan_states['spawning_exhaust']['flush_mode'] = False
                    self.fan_states['spawning_exhaust']['flush_start'] = None
                    self.actuator_callback('spawning', 'exhaust_fan', 'OFF')
    
    def _control_loop(self):
        """Main control loop running in separate thread."""
        logger.info("Passive fan control loop started")
        
        while self.running:
            try:
                # Check spawning room exhaust (interval-based)
                self._check_spawning_exhaust()
                
                # Check device room exhaust (clock-based)
                self._check_device_exhaust()
                
                # Sleep for 10 seconds between checks
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in passive fan control loop: {e}")
                time.sleep(10)
    
    def _check_spawning_exhaust(self):
        """Check if spawning exhaust should run (interval-based)."""
        config = self.config.get('spawning_exhaust', {})
        
        if not config.get('enabled', False):
            return
        
        # Don't override flush mode
        if self.fan_states['spawning_exhaust']['flush_mode']:
            return
        
        state = self.fan_states['spawning_exhaust']
        interval = config.get('interval_minutes', 30) * 60  # Convert to seconds
        duration = config.get('duration_seconds', 120)
        
        # Check if it's time to run
        if state['last_run'] is None:
            # First run
            logger.info("Starting spawning exhaust fan (first run)")
            self._run_fan('spawning', 'exhaust_fan', duration)
            state['last_run'] = time.time()
            state['enabled'] = True
        else:
            elapsed = time.time() - state['last_run']
            
            if elapsed >= interval:
                # Time for next run
                logger.info(f"Starting spawning exhaust fan (interval: {interval/60:.1f} min)")
                self._run_fan('spawning', 'exhaust_fan', duration)
                state['last_run'] = time.time()
    
    def _check_device_exhaust(self):
        """Check if device exhaust should run (clock-based)."""
        config = self.config.get('device_exhaust', {})
        
        if not config.get('enabled', False):
            return
        
        mode = config.get('mode', 'clock')
        
        if mode == 'clock':
            # Clock-based scheduling
            schedule = config.get('schedule', [])
            duration = config.get('duration_seconds', 180)
            current_time = datetime.now().strftime('%H:%M')
            
            state = self.fan_states['device_exhaust']
            
            # Check if current time matches any schedule entry
            for scheduled_time in schedule:
                # Allow 1-minute window for triggering
                if self._time_match(current_time, scheduled_time, window_minutes=1):
                    # Check if we haven't run recently (avoid duplicate triggers)
                    if state['last_run'] is None or (time.time() - state['last_run']) > 60:
                        logger.info(f"Starting device exhaust fan (scheduled: {scheduled_time})")
                        self._run_fan('device', 'exhaust_fan', duration)
                        state['last_run'] = time.time()
                        state['enabled'] = True
                        break
        elif mode == 'interval':
            # Interval-based (similar to spawning)
            interval = config.get('interval_minutes', 60) * 60
            duration = config.get('duration_seconds', 180)
            state = self.fan_states['device_exhaust']
            
            if state['last_run'] is None or (time.time() - state['last_run']) >= interval:
                logger.info(f"Starting device exhaust fan (interval: {interval/60:.1f} min)")
                self._run_fan('device', 'exhaust_fan', duration)
                state['last_run'] = time.time()
    
    def _run_fan(self, room: str, actuator: str, duration: int):
        """
        Run a fan for a specified duration.
        
        Args:
            room: Room name
            actuator: Actuator name
            duration: Duration in seconds
        """
        # Turn on fan
        self.actuator_callback(room, actuator, 'ON')
        
        # Schedule turn-off in separate thread
        def turn_off_after_delay():
            time.sleep(duration)
            # Only turn off if not in flush mode (for spawning)
            if room == 'spawning' and self.fan_states['spawning_exhaust']['flush_mode']:
                logger.info("Skipping passive turn-off (flush mode active)")
                return
            self.actuator_callback(room, actuator, 'OFF')
            logger.info(f"{room} {actuator} turned off after {duration}s")
        
        threading.Thread(target=turn_off_after_delay, daemon=True).start()
    
    def _time_match(self, current: str, target: str, window_minutes: int = 1) -> bool:
        """
        Check if current time matches target time within a window.
        
        Args:
            current: Current time string (HH:MM)
            target: Target time string (HH:MM)
            window_minutes: Tolerance window in minutes
        
        Returns:
            True if times match within window
        """
        try:
            current_dt = datetime.strptime(current, '%H:%M')
            target_dt = datetime.strptime(target, '%H:%M')
            diff = abs((current_dt - target_dt).total_seconds())
            return diff <= window_minutes * 60
        except Exception:
            return False
    
    def get_status(self) -> Dict:
        """Get current status of all passive fans."""
        return {
            'spawning_exhaust': {
                'enabled': self.fan_states['spawning_exhaust']['enabled'],
                'flush_mode': self.fan_states['spawning_exhaust']['flush_mode'],
                'last_run': self.fan_states['spawning_exhaust']['last_run'],
                'next_run': self._get_next_run_time('spawning_exhaust')
            },
            'device_exhaust': {
                'enabled': self.fan_states['device_exhaust']['enabled'],
                'last_run': self.fan_states['device_exhaust']['last_run'],
                'next_run': self._get_next_run_time('device_exhaust')
            }
        }
    
    def _get_next_run_time(self, fan_name: str) -> Optional[float]:
        """Calculate next run time for a fan."""
        config = self.config.get(fan_name, {})
        state = self.fan_states[fan_name]
        
        if fan_name == 'spawning_exhaust':
            if state['flush_mode']:
                return None  # In flush mode
            if state['last_run'] is None:
                return time.time()  # Run immediately
            interval = config.get('interval_minutes', 30) * 60
            return state['last_run'] + interval
        
        elif fan_name == 'device_exhaust':
            mode = config.get('mode', 'clock')
            if mode == 'clock':
                # Find next scheduled time
                schedule = config.get('schedule', [])
                current_time = datetime.now()
                
                for scheduled_time in schedule:
                    scheduled_dt = datetime.strptime(scheduled_time, '%H:%M').replace(
                        year=current_time.year,
                        month=current_time.month,
                        day=current_time.day
                    )
                    
                    if scheduled_dt > current_time:
                        return scheduled_dt.timestamp()
                
                # If no future time today, return first time tomorrow
                if schedule:
                    tomorrow = current_time + timedelta(days=1)
                    next_time = datetime.strptime(schedule[0], '%H:%M').replace(
                        year=tomorrow.year,
                        month=tomorrow.month,
                        day=tomorrow.day
                    )
                    return next_time.timestamp()
            else:
                # Interval mode
                if state['last_run'] is None:
                    return time.time()
                interval = config.get('interval_minutes', 60) * 60
                return state['last_run'] + interval
        
        return None
