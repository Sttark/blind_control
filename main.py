import RPi.GPIO as GPIO
import tkinter as tk
from tkinter import messagebox
import threading
import time

# GPIO pin definitions
REMOTE_POWER_PIN = 4

BUTTON_PINS = {
    "Up": 21,
    "Stop": 24,
    "Down": 16,
    "Channel Down": 25,
    "Channel Up": 12
}

# Track state
remote_on = False

# GPIO setup
GPIO.setmode(GPIO.BCM)

# Set all button pins to input mode with pull-up resistors initially
for pin in BUTTON_PINS.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Setup remote power pin
GPIO.setup(REMOTE_POWER_PIN, GPIO.OUT)
GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)  # Start with remote off

# GUI functions
def toggle_remote_power():
    global remote_on
    if not remote_on:
        # BEFORE turning on power, reset all button pins to input with pull-up resistors
        for pin in BUTTON_PINS.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.output(REMOTE_POWER_PIN, GPIO.HIGH)
        remote_on = True
        power_button.config(text="Turn Remote OFF")
        status_label.config(text="Remote is ON")
    else:
        GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)
        remote_on = False
        power_button.config(text="Turn Remote ON")
        status_label.config(text="Remote is OFF")

        # Reset all button pins to input with pull-up
        for pin in BUTTON_PINS.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def momentary_press(name):
    if not remote_on:
        messagebox.showwarning("Remote is OFF", "Turn ON the remote before pressing buttons.")
        return

    def press_and_release():
        pin = BUTTON_PINS[name]
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
        status_label.config(text=f"{name} button is PRESSED")

        time.sleep(1)  # 1 second press duration

        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        status_label.config(text=f"{name} button is RELEASED")

    # Run in a thread to avoid freezing the GUI
    threading.Thread(target=press_and_release).start()

def cleanup_and_exit():
    GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)
    for pin in BUTTON_PINS.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.cleanup()
    root.destroy()

# Build GUI
root = tk.Tk()
root.title("Remote Control Panel")

power_button = tk.Button(root, text="Turn Remote ON", width=30, command=toggle_remote_power)
power_button.pack(pady=10)

for name in BUTTON_PINS:
    btn = tk.Button(root, text=name, width=30, command=lambda n=name: momentary_press(n))
    btn.pack(pady=5)

status_label = tk.Label(root, text="Remote is OFF", fg="blue")
status_label.pack(pady=10)

exit_button = tk.Button(root, text="Exit and Cleanup", width=30, command=cleanup_and_exit)
exit_button.pack(pady=20)

root.protocol("WM_DELETE_WINDOW", cleanup_and_exit)
root.mainloop()
