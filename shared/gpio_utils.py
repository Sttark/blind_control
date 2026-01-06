import time
import threading
from typing import Dict, Callable, Optional

# Multi-library GPIO support for maximum compatibility
GPIO_LIBRARY = None
GPIO_AVAILABLE = False

# Try different GPIO libraries in order of preference
try:
    # First try RPi.GPIO (works on older Pi models and kernels)
    import RPi.GPIO as GPIO
    # Test if RPi.GPIO actually works by attempting setmode
    GPIO.setmode(GPIO.BCM)
    GPIO.setmode(GPIO.BOARD)  # Reset back
    GPIO_LIBRARY = "RPi.GPIO"
    GPIO_AVAILABLE = True
    print(f"GPIO: Using RPi.GPIO v{GPIO.VERSION}")
except Exception as e:
    print(f"GPIO: RPi.GPIO failed: {e}")
    try:
        # Fall back to gpiozero with lgpio backend (Pi 5 compatible)
        import gpiozero
        from gpiozero import Device
        from gpiozero.pins.lgpio import LGPIOFactory
        Device.pin_factory = LGPIOFactory()
        GPIO_LIBRARY = "gpiozero"
        GPIO_AVAILABLE = True
        print("GPIO: Using gpiozero with lgpio backend")
    except Exception as e2:
        print(f"GPIO: gpiozero failed: {e2}")
        try:
            # Last resort: try lgpio directly
            import lgpio
            GPIO_LIBRARY = "lgpio"
            GPIO_AVAILABLE = True
            print("GPIO: Using lgpio directly")
        except Exception as e3:
            print(f"GPIO: lgpio failed: {e3}")
            GPIO_LIBRARY = None
            GPIO_AVAILABLE = False
            print("GPIO: All GPIO libraries failed - running in test mode")

class GPIOController:
    """GPIO controller for blind remote control - supports multiple GPIO libraries"""
    
    def __init__(self, remote_power_pin: int, button_pins: Dict[str, int], test_mode: bool = False, default_channel: int = 0):
        self.remote_power_pin = remote_power_pin
        self.button_pins = button_pins
        self.remote_on = False
        self.channel_status = "All Channels"
        self.channel_selection_in_progress = False
        self.blinds_lowered = False
        self.test_mode = test_mode or not GPIO_AVAILABLE
        self.default_channel = default_channel  # 0 = All Channels, 1-16 = specific channel
        self.gpio_library = GPIO_LIBRARY
        
        # GPIO device objects for gpiozero/lgpio
        self.gpio_devices = {}
        self.lgpio_handle = None
        
        # Initialize GPIO only if not in test mode
        if not self.test_mode:
            print(f"GPIO: Initializing {self.gpio_library} GPIO control")
            self._init_gpio()
        else:
            print("Running in TEST MODE - GPIO operations will be mocked")
    
    def _init_gpio(self):
        """Initialize GPIO based on available library"""
        try:
            if self.gpio_library == "RPi.GPIO":
                self._init_rpi_gpio()
            elif self.gpio_library == "gpiozero":
                self._init_gpiozero()
            elif self.gpio_library == "lgpio":
                self._init_lgpio()
            else:
                raise Exception("No GPIO library available")
        except Exception as e:
            print(f"GPIO: Initialization failed: {e}")
            print("GPIO: Falling back to test mode")
            self.test_mode = True
    
    def _init_rpi_gpio(self):
        """Initialize using RPi.GPIO library"""
        GPIO.setmode(GPIO.BCM)
        self._set_pin_output(self.remote_power_pin, False)
        
        for pin in self.button_pins.values():
            self._set_pin_input(pin)
    
    def _init_gpiozero(self):
        """Initialize using gpiozero library"""
        from gpiozero import OutputDevice, InputDevice
        
        # Create output device for remote power
        self.gpio_devices['power'] = OutputDevice(self.remote_power_pin, initial_value=False)
        
        # Create input devices for buttons (with pull-up)
        for name, pin in self.button_pins.items():
            self.gpio_devices[f'button_{name}'] = InputDevice(pin, pull_up=True)
    
    def _init_lgpio(self):
        """Initialize using lgpio directly"""
        import lgpio
        
        # Open GPIO chip
        self.lgpio_handle = lgpio.gpiochip_open(0)
        
        # Configure remote power pin as output
        lgpio.gpio_claim_output(self.lgpio_handle, self.remote_power_pin, 0)
        
        # Configure button pins as inputs with pull-up
        for pin in self.button_pins.values():
            lgpio.gpio_claim_input(self.lgpio_handle, pin, lgpio.SET_PULL_UP)
    
    def _set_pin_output(self, pin: int, value: bool):
        """Set GPIO pin to output mode and value"""
        print(f"GPIO: Setting pin {pin} to {'HIGH' if value else 'LOW'} using {self.gpio_library}")
        try:
            if self.gpio_library == "RPi.GPIO":
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)
            elif self.gpio_library == "gpiozero":
                # For gpiozero, we need to reconfigure the pin as output
                from gpiozero import OutputDevice
                if pin == self.remote_power_pin:
                    self.gpio_devices['power'].on() if value else self.gpio_devices['power'].off()
                else:
                    # Close existing input device for this pin first
                    for name, button_pin in self.button_pins.items():
                        if button_pin == pin and f'button_{name}' in self.gpio_devices:
                            self.gpio_devices[f'button_{name}'].close()
                            del self.gpio_devices[f'button_{name}']
                            break
                    
                    # Create/recreate output device for button press
                    # Store in a temporary dict to keep it alive during button press
                    if not hasattr(self, '_temp_outputs'):
                        self._temp_outputs = {}
                    if pin in self._temp_outputs:
                        self._temp_outputs[pin].close()
                    self._temp_outputs[pin] = OutputDevice(pin, initial_value=value)
            elif self.gpio_library == "lgpio":
                import lgpio
                # Reclaim pin as output if needed
                try:
                    lgpio.gpio_free(self.lgpio_handle, pin)
                except:
                    pass
                lgpio.gpio_claim_output(self.lgpio_handle, pin, 1 if value else 0)
        except Exception as e:
            print(f"GPIO: Error setting pin {pin} to {value}: {e}")
    
    def _set_pin_input(self, pin: int):
        """Set GPIO pin back to input mode with pull-up"""
        try:
            if self.gpio_library == "RPi.GPIO":
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            elif self.gpio_library == "gpiozero":
                from gpiozero import InputDevice
                # Clean up temporary output device if it exists
                if hasattr(self, '_temp_outputs') and pin in self._temp_outputs:
                    self._temp_outputs[pin].close()
                    del self._temp_outputs[pin]
                # Recreate as input device
                for name, button_pin in self.button_pins.items():
                    if button_pin == pin:
                        if f'button_{name}' in self.gpio_devices:
                            self.gpio_devices[f'button_{name}'].close()
                        self.gpio_devices[f'button_{name}'] = InputDevice(pin, pull_up=True)
                        break
            elif self.gpio_library == "lgpio":
                import lgpio
                try:
                    lgpio.gpio_free(self.lgpio_handle, pin)
                except:
                    pass
                lgpio.gpio_claim_input(self.lgpio_handle, pin, lgpio.SET_PULL_UP)
        except Exception as e:
            print(f"GPIO: Error setting pin {pin} to input: {e}")
    
    def check_remote_power_state(self) -> bool:
        """Check the actual power state of the remote"""
        if self.test_mode:
            return self.remote_on  # Return the simulated state
        
        try:
            if self.gpio_library == "RPi.GPIO":
                return GPIO.input(self.remote_power_pin) == GPIO.HIGH
            elif self.gpio_library == "gpiozero":
                return self.gpio_devices['power'].is_active
            elif self.gpio_library == "lgpio":
                import lgpio
                return lgpio.gpio_read(self.lgpio_handle, self.remote_power_pin) == 1
        except Exception as e:
            print(f"GPIO: Error reading power state: {e}")
            return self.remote_on  # Return last known state
    
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
            self._set_pin_output(pin, False)  # Press button (LOW)
            time.sleep(duration)
            self._set_pin_input(pin)  # Release button (back to input with pull-up)
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
            self._set_pin_output(pin, False)  # Press button (LOW)
            time.sleep(1)  # 1 second press
            self._set_pin_input(pin)  # Release button
        
        threading.Thread(target=press_release).start()
        self.channel_status = "All Channels"
        print("All channels selected")
    
    def select_default_channel(self) -> None:
        """Select the configured default channel"""
        if self.default_channel == 0:
            # Default to All Channels
            self.select_all_channels()
        else:
            # Select specific channel
            self.select_channel(self.default_channel)
    
    def toggle_remote_power(self) -> bool:
        """Toggle remote power on/off"""
        if self.test_mode:
            self.remote_on = not self.remote_on
            if self.remote_on:
                time.sleep(1)  # Simulate initialization time
                self.select_default_channel()
            print(f"[TEST MODE] Remote power: {'ON' if self.remote_on else 'OFF'}")
            return self.remote_on
            
        if self.remote_on:
            self._set_pin_output(self.remote_power_pin, False)  # Turn off
        else:
            # Reset all button pins before turning on
            for pin in self.button_pins.values():
                self._set_pin_input(pin)
            self._set_pin_output(self.remote_power_pin, True)  # Turn on
            time.sleep(3)  # Wait for remote to initialize
            self.select_default_channel()
        
        time.sleep(0.1)  # Small delay to allow GPIO state to settle
        self.update_remote_state()
        return self.remote_on
    
    def power_on_remote(self) -> None:
        """Ensure remote is powered on"""
        if self.test_mode:
            if not self.remote_on:
                self.remote_on = True
                time.sleep(1)  # Simulate initialization
                self.select_default_channel()
                print("[TEST MODE] Remote powered on")
            return
            
        if not self.check_remote_power_state():
            for pin in self.button_pins.values():
                self._set_pin_input(pin)
            self._set_pin_output(self.remote_power_pin, True)
            time.sleep(3)  # Wait for remote to initialize
            self.select_default_channel()
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
        # Send three Up presses spaced out by dwell time to give the motor time to respond
        for attempt in range(3):
            self.press_button_action("Up")
            if attempt < 2:
                time.sleep(10)  # Dwell time between presses
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
                self._set_pin_output(pin, False)
                time.sleep(5)  # Hold for 5 seconds
                self._set_pin_input(pin)
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
                self._set_pin_output(self.remote_power_pin, False)
                time.sleep(2)  # Wait for 2 seconds
                
                # Turn power back on
                for pin in self.button_pins.values():
                    self._set_pin_input(pin)
                self._set_pin_output(self.remote_power_pin, True)
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
            
        try:
            self._set_pin_output(self.remote_power_pin, False)
            for pin in self.button_pins.values():
                self._set_pin_input(pin)
            
            # Clean up based on GPIO library
            if self.gpio_library == "RPi.GPIO":
                GPIO.cleanup()
            elif self.gpio_library == "gpiozero":
                # Close all gpiozero devices
                for device in self.gpio_devices.values():
                    device.close()
                if hasattr(self, '_temp_outputs'):
                    for device in self._temp_outputs.values():
                        device.close()
            elif self.gpio_library == "lgpio":
                import lgpio
                if self.lgpio_handle is not None:
                    lgpio.gpiochip_close(self.lgpio_handle)
        except Exception as e:
            print(f"GPIO: Error during cleanup: {e}")
    
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
