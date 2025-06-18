import time
import threading
from typing import Dict, Callable, Optional

# Test mode: mock GPIO if not available or if test_mode is enabled
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("RPi.GPIO not available - running in test mode")

class GPIOController:
    """GPIO controller for blind remote control"""
    
    def __init__(self, remote_power_pin: int, button_pins: Dict[str, int], test_mode: bool = False):
        self.remote_power_pin = remote_power_pin
        self.button_pins = button_pins
        self.remote_on = False
        self.channel_status = "All Channels"
        self.channel_selection_in_progress = False
        self.blinds_lowered = False
        self.test_mode = test_mode or not GPIO_AVAILABLE
        
        # Initialize GPIO only if not in test mode
        if not self.test_mode:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.remote_power_pin, GPIO.OUT)
            GPIO.output(self.remote_power_pin, GPIO.LOW)
            
            for pin in self.button_pins.values():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        else:
            print("Running in TEST MODE - GPIO operations will be mocked")
    
    def check_remote_power_state(self) -> bool:
        """Check the actual power state of the remote"""
        if self.test_mode:
            return self.remote_on  # Return the simulated state
        return GPIO.input(self.remote_power_pin) == GPIO.HIGH
    
    def update_remote_state(self) -> None:
        """Update remote_on variable based on actual GPIO state"""
        if self.test_mode:
            return  # In test mode, we control the state manually
            
        actual_state = self.check_remote_power_state()
        if self.remote_on != actual_state:
            self.remote_on = actual_state
            print(f"Remote state updated to: {'ON' if self.remote_on else 'OFF'}")
    
    def press_button_action(self, button_name: str, duration: float = 0.8) -> bool:
        """Press a button for specified duration"""
        if self.test_mode:
            print(f"[TEST MODE] Pressed {button_name} button for {duration}s")
            time.sleep(0.1)  # Brief delay to simulate button press
            return True
            
        if button_name in self.button_pins:
            pin = self.button_pins[button_name]
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(duration)
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            print(f"Pressed {button_name} button for {duration}s")
            return True
        return False
    
    def select_all_channels(self) -> None:
        """Select all channels by pressing Channel Down button"""
        if self.test_mode:
            print("[TEST MODE] All channels selected")
            self.channel_status = "All Channels"
            return
            
        def press_release():
            pin = self.button_pins["Channel Down"]
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(1)  # 1 second press
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        threading.Thread(target=press_release).start()
        self.channel_status = "All Channels"
        print("All channels selected")
    
    def toggle_remote_power(self) -> bool:
        """Toggle remote power on/off"""
        if self.test_mode:
            self.remote_on = not self.remote_on
            if self.remote_on:
                time.sleep(1)  # Simulate initialization time
                self.select_all_channels()
            print(f"[TEST MODE] Remote power: {'ON' if self.remote_on else 'OFF'}")
            return self.remote_on
            
        if self.remote_on:
            GPIO.output(self.remote_power_pin, GPIO.LOW)
        else:
            # Reset all button pins before turning on
            for pin in self.button_pins.values():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.output(self.remote_power_pin, GPIO.HIGH)
            time.sleep(3)  # Wait for remote to initialize
            self.select_all_channels()
        
        time.sleep(0.1)  # Small delay to allow GPIO state to settle
        self.update_remote_state()
        return self.remote_on
    
    def power_on_remote(self) -> None:
        """Ensure remote is powered on"""
        if self.test_mode:
            if not self.remote_on:
                self.remote_on = True
                time.sleep(1)  # Simulate initialization
                self.select_all_channels()
                print("[TEST MODE] Remote powered on")
            return
            
        if not self.check_remote_power_state():
            for pin in self.button_pins.values():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.output(self.remote_power_pin, GPIO.HIGH)
            time.sleep(3)  # Wait for remote to initialize
            self.select_all_channels()
            time.sleep(1)
    
    def lower_blinds(self) -> bool:
        """Lower the blinds"""
        print("[TEST MODE] Lowering blinds" if self.test_mode else "Lowering blinds")
        self.power_on_remote()
        self.press_button_action("Down")
        self.blinds_lowered = True
        print("[TEST MODE] Blinds lowered" if self.test_mode else "Blinds lowered")
        return True
    
    def raise_blinds(self) -> bool:
        """Raise the blinds"""
        print("[TEST MODE] Raising blinds" if self.test_mode else "Raising blinds")
        self.power_on_remote()
        self.press_button_action("Up")
        self.blinds_lowered = False
        print("[TEST MODE] Blinds raised" if self.test_mode else "Blinds raised")
        return True
    
    def stop_blinds(self) -> bool:
        """Stop the blinds"""
        print("[TEST MODE] Stopping blinds" if self.test_mode else "Stopping blinds")
        self.power_on_remote()
        self.press_button_action("Stop")
        print("[TEST MODE] Blinds stopped" if self.test_mode else "Blinds stopped")
        return True
    
    def pair_remote(self) -> None:
        """Pair the remote (hold Up button for 5 seconds)"""
        if self.test_mode:
            print("[TEST MODE] Pairing remote (holding Up button for 5 seconds)")
            time.sleep(0.5)  # Brief delay to simulate pairing
            return
            
        if self.remote_on and "Up" in self.button_pins:
            def press_hold_release():
                pin = self.button_pins["Up"]
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(5)  # Hold for 5 seconds
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                print("Held Up button for 5 seconds (Pairing)")
            threading.Thread(target=press_hold_release).start()
    
    def select_channel(self, channel: int) -> None:
        """Select a specific channel (1-16)"""
        if channel < 1 or channel > 16:
            channel = 1
        
        self.channel_status = f"Channel {channel}"
        self.channel_selection_in_progress = True
        
        def navigate_to_channel():
            try:
                if self.test_mode:
                    print(f"[TEST MODE] Selecting channel {channel}")
                    time.sleep(2)  # Simulate channel selection time
                    self.channel_status = f"Channel {channel}"
                    return
                
                # Cut power to the remote
                GPIO.output(self.remote_power_pin, GPIO.LOW)
                time.sleep(2)  # Wait for 2 seconds
                
                # Turn power back on
                for pin in self.button_pins.values():
                    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.output(self.remote_power_pin, GPIO.HIGH)
                time.sleep(3)  # Wait for remote to initialize
                
                # Channel 1 is the default after power on
                if channel == 1:
                    pass  # No need to press any buttons
                elif channel <= 8:
                    # For channels 2-8, press Channel Up channel times
                    for _ in range(channel):
                        self.press_button_action("Channel Up")
                        time.sleep(0.5)
                else:
                    # For channels 9-16, press Channel Down (19-channel) times
                    for _ in range(19 - channel):
                        self.press_button_action("Channel Down")
                        time.sleep(0.5)
            finally:
                self.channel_selection_in_progress = False
                print(f"Channel selection complete: {self.channel_status}")
        
        threading.Thread(target=navigate_to_channel).start()
    
    def cleanup(self) -> None:
        """Clean up GPIO resources"""
        if self.test_mode:
            print("[TEST MODE] GPIO cleanup (simulated)")
            return
            
        GPIO.output(self.remote_power_pin, GPIO.LOW)
        for pin in self.button_pins.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.cleanup()
    
    def start_monitoring(self, monitor_callback: Optional[Callable] = None) -> None:
        """Start background monitoring of remote power state"""
        def monitor_remote_power():
            while True:
                if not self.test_mode:
                    self.update_remote_state()
                if monitor_callback:
                    monitor_callback(self)
                time.sleep(1)  # Check every second
        
        monitor_thread = threading.Thread(target=monitor_remote_power, daemon=True)
        monitor_thread.start()
