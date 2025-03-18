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
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Blind Control</title>
        <style>
            * {
                box-sizing: border-box;
                font-family: Arial, sans-serif;
            }
            body {
                margin: 0;
                padding: 16px;
                background-color: #f5f5f5;
                max-width: 600px;
                margin: 0 auto;
            }
            h1 {
                text-align: center;
                color: #333;
                font-size: 24px;
                margin-bottom: 20px;
            }
            .status-panel {
                background-color: #fff;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .control-panel {
                background-color: #fff;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .button-group {
                display: flex;
                justify-content: space-between;
                margin-bottom: 15px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
                margin: 5px 0;
                transition: background-color 0.3s;
            }
            button:hover {
                background-color: #45a049;
            }
            .power-button {
                background-color: #f44336;
            }
            .power-button:hover {
                background-color: #d32f2f;
            }
            .direction-buttons {
                display: flex;
                flex-direction: column;
                gap: 10px;
                margin-bottom: 15px;
            }
            .direction-buttons .button-row {
                display: flex;
                justify-content: space-between;
                gap: 10px;
            }
            .direction-buttons button {
                flex: 1;
                margin: 0;
            }
            .up-button {
                background-color: #2196F3;
            }
            .up-button:hover {
                background-color: #1976D2;
            }
            .stop-button {
                background-color: #FF9800;
            }
            .stop-button:hover {
                background-color: #F57C00;
            }
            .down-button {
                background-color: #2196F3;
            }
            .down-button:hover {
                background-color: #1976D2;
            }
            .channel-form {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .channel-form .input-row {
                display: flex;
                gap: 10px;
            }
            select {
                flex: 1;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
            }
            .channel-form button {
                flex: 0 0 80px;
            }
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .status-on {
                background-color: #4CAF50;
            }
            .status-off {
                background-color: #f44336;
            }
        </style>
    </head>
    <body>
        <h1>Blind Control</h1>
        
        <div class="status-panel">
            <p>
                <span class="status-indicator {{ 'status-on' if remote_on else 'status-off' }}"></span>
                <strong>Remote:</strong> {{ 'ON' if remote_on else 'OFF' }}
            </p>
            {% if remote_on %}
            <p><strong>Channel:</strong> {{ channel_status }}</p>
            {% endif %}
        </div>
        
        <div class="control-panel">
            <form action="/toggle_remote" method="post">
                <button type="submit" class="power-button">Power {{ 'OFF' if remote_on else 'ON' }}</button>
            </form>
            
            {% if remote_on %}
            <h2>Blind Controls</h2>
            <div class="direction-buttons">
                <div class="button-row">
                    <form action="/press/Up" method="post" style="flex: 1;">
                        <button type="submit" class="up-button">Up</button>
                    </form>
                </div>
                <div class="button-row">
                    <form action="/press/Stop" method="post" style="flex: 1;">
                        <button type="submit" class="stop-button">Stop</button>
                    </form>
                </div>
                <div class="button-row">
                    <form action="/press/Down" method="post" style="flex: 1;">
                        <button type="submit" class="down-button">Down</button>
                    </form>
                </div>
            </div>
            
            <h2>Channel Selection</h2>
            <form action="/go_to_all_channels" method="post">
                <button type="submit">All Channels</button>
            </form>
            
            <form action="/select_channel" method="post" class="channel-form">
                <div class="input-row">
                    <select name="channel" id="channel">
                        {% for i in range(1, 17) %}
                            <option value="{{ i }}">Channel {{ i }}</option>
                        {% endfor %}
                    </select>
                    <button type="submit">Go</button>
                </div>
            </form>
            {% endif %}
        </div>
    </body>
    </html>
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
