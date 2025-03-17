from flask import Flask, render_template_string, redirect, url_for, request
import time
import threading
import sys
import os
import RPi.GPIO as GPIO

REMOTE_POWER_PIN = 4
BUTTON_PINS = {
    "Up": 21,
    "Stop": 24,
    "Down": 16,
    "Channel Up": 12,
    "Channel Down": 25
}

GPIO.setmode(GPIO.BCM)
GPIO.setup(REMOTE_POWER_PIN, GPIO.OUT)
GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)

for pin in BUTTON_PINS.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

app = Flask(__name__)
remote_on = False
channel_status = "All Channels"  # Default channel status

# Function to check the actual power state of the remote
def check_remote_power_state():
    return GPIO.input(REMOTE_POWER_PIN) == GPIO.HIGH

# Update remote_on variable based on actual GPIO state
def update_remote_state():
    global remote_on
    actual_state = check_remote_power_state()
    if remote_on != actual_state:
        remote_on = actual_state
        print(f"Remote state updated to: {'ON' if remote_on else 'OFF'}")

# Background thread to periodically check the remote power state
def monitor_remote_power():
    while True:
        update_remote_state()
        time.sleep(1)  # Check every second

# Start the monitoring thread
monitor_thread = threading.Thread(target=monitor_remote_power, daemon=True)
monitor_thread.start()

@app.route('/')
def index():
    return render_template_string('''
    <h1>Remote Control Web Interface</h1>
    <form action="/toggle_remote" method="post">
        <button type="submit">Power</button>
    </form>
    <p><strong>Current Remote State:</strong> {{ 'ON' if remote_on else 'OFF' }}</p>
    {% if remote_on %}
    <p><strong>Channel Selection:</strong> {{ channel_status }}</p>
    {% endif %}
    <br>
    <!-- Display only Up, Stop, Down buttons -->
    {% for name in ['Up', 'Stop', 'Down'] %}
        <form action="/press/{{ name }}" method="post">
            <button type="submit">{{ name }}</button>
        </form>
    {% endfor %}
    <br>
    <form action="/go_to_all_channels" method="post">
        <button type="submit">Go to All Channels</button>
    </form>
    <br>
    <form action="/select_channel" method="post">
        <label for="channel">Select a Channel:</label>
        <select name="channel" id="channel">
            {% for i in range(1, 17) %}
                <option value="{{ i }}">Channel {{ i }}</option>
            {% endfor %}
        </select>
        <button type="submit">Go</button>
    </form>
    ''', button_names=BUTTON_PINS.keys(), remote_on=remote_on, channel_status=channel_status)

# Function to select all channels by pressing Channel Down button
def select_all_channels():
    global channel_status
    # Press Channel Down button once to select all channels
    def press_release():
        pin = BUTTON_PINS["Channel Down"]
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(1)  # 1 second press
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    threading.Thread(target=press_release).start()
    channel_status = "All Channels"
    print("All channels selected")

# Function to press a button
def press_button_action(button_name):
    if button_name in BUTTON_PINS:
        pin = BUTTON_PINS[button_name]
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(.8)  # 0.8 second press
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print(f"Pressed {button_name} button")

@app.route('/toggle_remote', methods=['POST'])
def toggle_remote():
    global remote_on
    if remote_on:
        GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)
        # The monitor_thread will update remote_on
    else:
        for pin in BUTTON_PINS.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.output(REMOTE_POWER_PIN, GPIO.HIGH)
        # The monitor_thread will update remote_on
        time.sleep(3)  # Wait for remote to initialize
        # Automatically select all channels when power is turned on
        select_all_channels()
    time.sleep(0.1)  # Small delay to allow GPIO state to settle
    update_remote_state()  # Update state immediately after toggle
    return redirect(url_for('index'))

@app.route('/press/<button_name>', methods=['POST'])
def press_button(button_name):
    if remote_on and button_name in BUTTON_PINS:
        def press_release():
            press_button_action(button_name)
        threading.Thread(target=press_release).start()
    return redirect(url_for('index'))

@app.route('/go_to_all_channels', methods=['POST'])
def go_to_all_channels():
    # Cut power to the remote
    GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)
    time.sleep(2)  # Wait for 2 seconds
    
    # Turn power back on
    for pin in BUTTON_PINS.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.output(REMOTE_POWER_PIN, GPIO.HIGH)
    time.sleep(3)  # Wait for remote to initialize
    
    # The monitor_thread will update remote_on automatically
    
    # Select all channels
    select_all_channels()
    return redirect(url_for('index'))

@app.route('/select_channel', methods=['POST'])
def select_channel():
    global channel_status
    
    if not remote_on:
        return redirect(url_for('index'))
    
    channel = int(request.form.get('channel', 1))
    if channel < 1 or channel > 16:
        channel = 1
    
    # Update channel status immediately for UI display
    channel_status = f"Channel {channel}"
    print(f"Selected {channel_status}")
    
    # Function to navigate to the selected channel
    def navigate_to_channel():
        # Cut power to the remote
        GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)
        time.sleep(2)  # Wait for 2 seconds
        
        # Turn power back on
        for pin in BUTTON_PINS.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.output(REMOTE_POWER_PIN, GPIO.HIGH)
        time.sleep(3)  # Wait for remote to initialize
        
        # Channel 1 is the default after power on
        if channel == 1:
            pass  # No need to press any buttons
        elif channel <= 8:
            # For channels 2-8, press Channel Up channel times (adding one more click)
            for _ in range(channel):
                press_button_action("Channel Up")
                time.sleep(0.5)  # 0.5 second dwell time between button presses
        else:
            # For channels 9-16, press Channel Down (19-channel) times (adding two more clicks)
            for _ in range(19 - channel):
                press_button_action("Channel Down")
                time.sleep(0.5)  # 0.5 second dwell time between button presses
    
    threading.Thread(target=navigate_to_channel).start()
    return redirect(url_for('index'))

@app.route('/cleanup')
def cleanup():
    GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)
    for pin in BUTTON_PINS.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.cleanup()
    return "GPIO Cleaned up."


if __name__ == '__main__':
    print("Running in HTTP mode.")
    app.run(host='0.0.0.0', port=5000)
