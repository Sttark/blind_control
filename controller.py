from flask import Flask, render_template_string, redirect, url_for, request, jsonify
import time
import threading
import sys
import os
import json
import RPi.GPIO as GPIO
import requests
from datetime import datetime, timedelta

# Load configuration from local_config.json
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'local_config.json')
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    # Default configuration
    config = {
        "location_name": "South Building",
        "hub_url": "http://192.168.4.202:5001/",
        "weather_api_key": "b8c328a0f8be42ff936210148250404",
        "location": "29607",
        "cloud_threshold": 15,
        "monitoring_interval": 10
    }
    # Save default configuration
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Configuration variables
LOCATION_NAME = config.get('location_name', 'South Building')
HUB_URL = config.get('hub_url', 'http://192.168.4.202:5001/')
WEATHER_API_KEY = config.get('weather_api_key', 'b8c328a0f8be42ff936210148250404')
LOCATION = config.get('location', '29607')  # Zip code
CLOUD_THRESHOLD = config.get('cloud_threshold', 15)  # Consider sunny if cloud cover is below 15%
MONITORING_INTERVAL = config.get('monitoring_interval', 10)  # Check weather every 10 minutes (in minutes)

# GPIO Pin Configuration
REMOTE_POWER_PIN = 4
BUTTON_PINS = {
    "Up": 21,
    "Stop": 24,
    "Down": 16,
    "Channel Up": 12,
    "Channel Down": 25
}

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(REMOTE_POWER_PIN, GPIO.OUT)
GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)

for pin in BUTTON_PINS.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

app = Flask(__name__)
remote_on = False
channel_status = "All Channels"  # Default channel status
channel_selection_in_progress = False  # Flag to track if channel selection is in progress
blinds_lowered = False  # Track current blind state
last_hub_contact = datetime.now()  # Track when we last heard from the hub
standalone_mode = False  # Start in connected mode

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
        return True
    return False

# Function to lower the blinds
def lower_blinds():
    global blinds_lowered
    print("Lowering blinds")
    
    # Make sure remote is on
    if not check_remote_power_state():
        # Turn on remote
        for pin in BUTTON_PINS.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.output(REMOTE_POWER_PIN, GPIO.HIGH)
        time.sleep(3)  # Wait for remote to initialize
        select_all_channels()
        time.sleep(1)
    
    # Press the Down button
    press_button_action("Down")
    blinds_lowered = True
    print("Blinds lowered")
    return True

# Function to raise the blinds
def raise_blinds():
    global blinds_lowered
    print("Raising blinds")
    
    # Make sure remote is on
    if not check_remote_power_state():
        # Turn on remote
        for pin in BUTTON_PINS.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.output(REMOTE_POWER_PIN, GPIO.HIGH)
        time.sleep(3)  # Wait for remote to initialize
        select_all_channels()
        time.sleep(1)
    
    # Press the Up button
    press_button_action("Up")
    blinds_lowered = False
    print("Blinds raised")
    return True

# Function to stop the blinds
def stop_blinds():
    print("Stopping blinds")
    
    # Make sure remote is on
    if not check_remote_power_state():
        # Turn on remote
        for pin in BUTTON_PINS.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.output(REMOTE_POWER_PIN, GPIO.HIGH)
        time.sleep(3)  # Wait for remote to initialize
        select_all_channels()
        time.sleep(1)
    
    # Press the Stop button
    press_button_action("Stop")
    print("Blinds stopped")
    return True

# Function to check hub connectivity
def check_hub_connectivity():
    global last_hub_contact, standalone_mode
    
    # If we haven't heard from the hub in 5 minutes, switch to standalone mode
    if (datetime.now() - last_hub_contact).total_seconds() > 300:  # 5 minutes
        if not standalone_mode:
            standalone_mode = True
            print(f"No contact from hub for 5 minutes. Switching to standalone mode.")
    else:
        if standalone_mode:
            standalone_mode = False
            print(f"Hub contact restored. Switching to connected mode.")

# Background thread to check hub connectivity
def monitor_hub_connectivity():
    while True:
        check_hub_connectivity()
        time.sleep(60)  # Check every minute

# Start the hub connectivity monitoring thread
hub_monitor_thread = threading.Thread(target=monitor_hub_connectivity, daemon=True)
hub_monitor_thread.start()

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ location_name }} Blind Control</title>
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
            button:disabled {
                background-color: #cccccc;
                cursor: not-allowed;
                opacity: 0.7;
            }
            .power-button {
                background-color: #f44336;
            }
            .power-button:hover {
                background-color: #d32f2f;
            }
            .power-button:disabled {
                background-color: #ffcccb;
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
            .up-button:disabled {
                background-color: #bbdefb;
            }
            .stop-button {
                background-color: #FF9800;
            }
            .stop-button:hover {
                background-color: #F57C00;
            }
            .stop-button:disabled {
                background-color: #ffe0b2;
            }
            .down-button {
                background-color: #2196F3;
            }
            .down-button:hover {
                background-color: #1976D2;
            }
            .down-button:disabled {
                background-color: #bbdefb;
            }
            .pair-button {
                background-color: #9C27B0;
            }
            .pair-button:hover {
                background-color: #7B1FA2;
            }
            .pair-button:disabled {
                background-color: #E1BEE7;
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
            select:disabled {
                background-color: #f5f5f5;
                cursor: not-allowed;
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
            .processing-alert {
                background-color: #fff3cd;
                color: #856404;
                border-radius: 8px;
                padding: 15px;
                margin: 15px 0;
                text-align: center;
                font-weight: bold;
                border: 1px solid #ffeeba;
            }
            .standalone-mode {
                background-color: #f8d7da;
                color: #721c24;
                border-radius: 8px;
                padding: 15px;
                margin: 15px 0;
                text-align: center;
                font-weight: bold;
                border: 1px solid #f5c6cb;
            }
            /* Advanced dropdown styles */
            .advanced-dropdown {
                position: relative;
                display: inline-block;
                width: 100%;
                margin-top: 15px;
            }
            .advanced-dropdown-btn {
                background-color: #673AB7;
                color: white;
                width: 100%;
                text-align: left;
                padding: 12px 20px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .advanced-dropdown-btn:hover {
                background-color: #5E35B1;
            }
            .advanced-dropdown-btn:after {
                content: "▼";
                font-size: 12px;
                margin-left: 10px;
            }
            .advanced-dropdown-btn.active:after {
                content: "▲";
            }
            .advanced-dropdown-content {
                display: none;
                background-color: #f9f9f9;
                border-radius: 8px;
                padding: 15px;
                margin-top: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border: 1px solid #ddd;
            }
            .advanced-dropdown-content.show {
                display: block;
            }
        </style>
        <script>
            // Function to check if channel selection is complete
            function checkChannelSelectionStatus() {
                fetch('/channel_selection_status')
                    .then(response => response.json())
                    .then(data => {
                        if (data.in_progress) {
                            // If still in progress, check again in 1 second
                            setTimeout(checkChannelSelectionStatus, 1000);
                        } else {
                            // If complete, reload the page to update UI
                            window.location.reload();
                        }
                    });
            }

            // Start checking if we're in channel selection mode
            {% if channel_selection_in_progress %}
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(checkChannelSelectionStatus, 1000);
            });
            {% endif %}
            
            // Advanced dropdown toggle function
            function toggleAdvancedDropdown() {
                const dropdownContent = document.getElementById("advancedDropdownContent");
                const dropdownBtn = document.getElementById("advancedDropdownBtn");
                dropdownContent.classList.toggle("show");
                dropdownBtn.classList.toggle("active");
            }
            
            // Close dropdown if user clicks outside of it
            document.addEventListener('click', function(event) {
                const dropdown = document.getElementById("advancedDropdown");
                const dropdownBtn = document.getElementById("advancedDropdownBtn");
                
                if (!dropdown.contains(event.target) && !dropdownBtn.contains(event.target)) {
                    const dropdownContent = document.getElementById("advancedDropdownContent");
                    if (dropdownContent.classList.contains("show")) {
                        dropdownContent.classList.remove("show");
                        dropdownBtn.classList.remove("active");
                    }
                }
            });
        </script>
    </head>
    <body>
        <h1>{{ location_name }} Blind Control</h1>
        
        <div style="margin-bottom: 15px; text-align: center;">
            <a href="{{ hub_url }}" style="display: inline-block; background-color: #2196F3; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; font-size: 14px;">
                ← Back to Hub
            </a>
        </div>
        
        {% if standalone_mode %}
        <div class="standalone-mode">
            <p>STANDALONE MODE: Hub connection lost. Operating independently.</p>
        </div>
        {% endif %}
        
        <div class="status-panel">
            <p>
                <span class="status-indicator {{ 'status-on' if remote_on else 'status-off' }}"></span>
                <strong>Remote:</strong> {{ 'ON' if remote_on else 'OFF' }}
            </p>
            {% if remote_on %}
            <p><strong>Channel:</strong> {{ channel_status }}</p>
            {% endif %}
        </div>
        
        {% if channel_selection_in_progress %}
        <div class="processing-alert">
            <p>Channel selection in progress... Please wait.</p>
        </div>
        {% endif %}
        
        <div class="control-panel">
            <form action="/toggle_remote" method="post">
                <button type="submit" class="power-button" {% if channel_selection_in_progress %}disabled{% endif %}>Power {{ 'OFF' if remote_on else 'ON' }}</button>
            </form>
            
            {% if remote_on %}
            <h2>Blind Controls</h2>
            <div class="direction-buttons">
                <div class="button-row">
                    <form action="/press/Up" method="post" style="flex: 1;">
                        <button type="submit" class="up-button" {% if channel_selection_in_progress %}disabled{% endif %}>Up</button>
                    </form>
                </div>
                <div class="button-row">
                    <form action="/press/Stop" method="post" style="flex: 1;">
                        <button type="submit" class="stop-button" {% if channel_selection_in_progress %}disabled{% endif %}>Stop</button>
                    </form>
                </div>
                <div class="button-row">
                    <form action="/press/Down" method="post" style="flex: 1;">
                        <button type="submit" class="down-button" {% if channel_selection_in_progress %}disabled{% endif %}>Down</button>
                    </form>
                </div>
            </div>
            
            <div id="advancedDropdown" class="advanced-dropdown">
                <button id="advancedDropdownBtn" type="button" class="advanced-dropdown-btn" onclick="toggleAdvancedDropdown()">
                    Advanced Options
                </button>
                <div id="advancedDropdownContent" class="advanced-dropdown-content">
                    <h3>Pairing</h3>
                    <form action="/pair" method="post" style="margin-bottom: 20px;">
                        <button type="submit" class="pair-button" {% if channel_selection_in_progress %}disabled{% endif %}>Pair</button>
                    </form>
                    
                    <h3>Channel Selection</h3>
                    <form action="/go_to_all_channels" method="post" style="margin-bottom: 10px;">
                        <button type="submit" {% if channel_selection_in_progress %}disabled{% endif %}>All Channels</button>
                    </form>
                    
                    <form action="/select_channel" method="post" class="channel-form">
                        <div class="input-row">
                            <select name="channel" id="channel" {% if channel_selection_in_progress %}disabled{% endif %}>
                                {% for i in range(1, 17) %}
                                    <option value="{{ i }}">Channel {{ i }}</option>
                                {% endfor %}
                            </select>
                            <button type="submit" {% if channel_selection_in_progress %}disabled{% endif %}>Go</button>
                        </div>
                    </form>
                </div>
            </div>
            {% endif %}
        </div>
    </body>
    </html>
    ''', button_names=BUTTON_PINS.keys(), remote_on=remote_on, channel_status=channel_status, 
        channel_selection_in_progress=channel_selection_in_progress, location_name=LOCATION_NAME, 
        hub_url=HUB_URL, standalone_mode=standalone_mode)

@app.route('/toggle_remote', methods=['POST'])
def toggle_remote():
    global remote_on
    
    # Don't allow toggling if channel selection is in progress
    if channel_selection_in_progress:
        return redirect(url_for('index'))
        
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
    # Don't allow button presses if channel selection is in progress
    if channel_selection_in_progress:
        return redirect(url_for('index'))
        
    if remote_on and button_name in BUTTON_PINS:
        def press_release():
            press_button_action(button_name)
        threading.Thread(target=press_release).start()
    return redirect(url_for('index'))

@app.route('/pair', methods=['POST'])
def pair_button():
    # Don't allow button presses if channel selection is in progress
    if channel_selection_in_progress:
        return redirect(url_for('index'))
        
    if remote_on and "Up" in BUTTON_PINS:
        def press_hold_release():
            pin = BUTTON_PINS["Up"]
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(5)  # Hold for 5 seconds
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            print("Held Up button for 5 seconds (Pairing)")
        threading.Thread(target=press_hold_release).start()
    return redirect(url_for('index'))

@app.route('/channel_selection_status')
def channel_selection_status():
    return jsonify({'in_progress': channel_selection_in_progress})

@app.route('/go_to_all_channels', methods=['POST'])
def go_to_all_channels():
    global channel_selection_in_progress
    
    # Don't allow channel selection if already in progress
    if channel_selection_in_progress:
        return redirect(url_for('index'))
    
    # Set flag to indicate channel selection is in progress
    channel_selection_in_progress = True
    
    # Function to handle the channel selection process
    def process_all_channels():
        global channel_selection_in_progress
        try:
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
        finally:
            # Reset the flag when channel selection is complete
            channel_selection_in_progress = False
            print("All channels selection complete")
    
    # Start the process in a background thread
    threading.Thread(target=process_all_channels).start()
    return redirect(url_for('index'))

@app.route('/select_channel', methods=['POST'])
def select_channel():
    global channel_status, channel_selection_in_progress
    
    # Don't allow channel selection if not powered on or already in progress
    if not remote_on or channel_selection_in_progress:
        return redirect(url_for('index'))
    
    channel = int(request.form.get('channel', 1))
    if channel < 1 or channel > 16:
        channel = 1
    
    # Update channel status immediately for UI display
    channel_status = f"Channel {channel}"
    print(f"Selected {channel_status}")
    
    # Set the flag to indicate channel selection is in progress
    channel_selection_in_progress = True
    
    # Function to navigate to the selected channel
    def navigate_to_channel():
        global channel_selection_in_progress
        try:
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
        finally:
            # Reset the flag when channel selection is complete
            channel_selection_in_progress = False
            print(f"Channel selection complete: {channel_status}")
    
    # Start the channel selection process in a background thread
    threading.Thread(target=navigate_to_channel).start()
    return redirect(url_for('index'))

@app.route('/cleanup')
def cleanup():
    GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)
    for pin in BUTTON_PINS.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.cleanup()
    return "GPIO Cleaned up."

# API endpoints for hub communication
@app.route('/api/status', methods=['GET'])
def get_status():
    global last_hub_contact
    last_hub_contact = datetime.now()  # Update last contact time
    
    return jsonify({
        'location_name': LOCATION_NAME,
        'remote_on': remote_on,
        'channel_status': channel_status,
        'blinds_lowered': blinds_lowered,
        'standalone_mode': standalone_mode,
        'channel_selection_in_progress': channel_selection_in_progress
    })

@app.route('/api/command', methods=['POST'])
def execute_command():
    global last_hub_contact
    last_hub_contact = datetime.now()  # Update last contact time
    
    if not request.json:
        return jsonify({'success': False, 'error': 'Invalid request format'}), 400
    
    command = request.json.get('command')
    params = request.json.get('params', {})
    
    if command == 'raise_blinds':
        success = raise_blinds()
        return jsonify({'success': success})
    
    elif command == 'lower_blinds':
        success = lower_blinds()
        return jsonify({'success': success})
    
    elif command == 'stop_blinds':
        success = stop_blinds()
        return jsonify({'success': success})
    
    elif command == 'toggle_remote':
        if remote_on:
            GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)
        else:
            for pin in BUTTON_PINS.values():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.output(REMOTE_POWER_PIN, GPIO.HIGH)
            time.sleep(3)  # Wait for remote to initialize
            select_all_channels()
        time.sleep(0.1)  # Small delay to allow GPIO state to settle
        update_remote_state()  # Update state immediately after toggle
        return jsonify({'success': True, 'remote_on': remote_on})
    
    elif command == 'select_channel':
        channel = params.get('channel')
        if channel is None or not isinstance(channel, int) or channel < 1 or channel > 16:
            return jsonify({'success': False, 'error': 'Invalid channel'}), 400
        
        # Start channel selection in a background thread
        global channel_status, channel_selection_in_progress
        channel_status = f"Channel {channel}"
        channel_selection_in_progress = True
        
        def navigate_to_channel():
            global channel_selection_in_progress
            try:
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
            finally:
                # Reset the flag when channel selection is complete
                channel_selection_in_progress = False
                print(f"Channel selection complete: Channel {channel}")
        
        # Start the channel selection process in a background thread
        threading.Thread(target=navigate_to_channel).start()
        return jsonify({'success': True})
    
    else:
        return jsonify({'success': False, 'error': f'Unknown command: {command}'}), 400

if __name__ == '__main__':
    print(f"Running Blind Controller for {LOCATION_NAME}")
    app.run(host='0.0.0.0', port=5000)
