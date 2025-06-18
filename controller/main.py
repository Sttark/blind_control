from flask import Flask, render_template_string, redirect, url_for, request, jsonify
import time
import threading
import sys
import os
from datetime import datetime, timedelta

# Import shared utilities
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from shared import ControllerConfig, GPIOController, SunsetScheduler

# Load configuration
CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'local_config.json')
config_manager = ControllerConfig(CONFIG_FILE)

# Configuration variables
LOCATION_NAME = config_manager.get('location_name', 'Blind Control, South Building B')
HUB_URL = config_manager.get('hub_url', 'http://192.168.4.202:5001/')
WEATHER_API_KEY = config_manager.get('weather_api_key', 'b8c328a0f8be42ff936210148250404')
LOCATION = config_manager.get('location', '29607')
CLOUD_THRESHOLD = config_manager.get('cloud_threshold', 15)
MONITORING_INTERVAL = config_manager.get('monitoring_interval', 10)

# Schedule settings
LOWER_BLINDS_OFFSET = config_manager.get('schedule.lower_blinds_offset', 192)
RAISE_BLINDS_OFFSET = config_manager.get('schedule.raise_blinds_offset', 0)

# GPIO Pin Configuration
REMOTE_POWER_PIN = 4
BUTTON_PINS = {
    "Up": 21,
    "Stop": 24,
    "Down": 16,
    "Channel Up": 12,
    "Channel Down": 25
}

# Initialize GPIO Controller
gpio_controller = GPIOController(REMOTE_POWER_PIN, BUTTON_PINS)
sunset_scheduler = SunsetScheduler()

app = Flask(__name__)
last_hub_contact = datetime.now()  # Track when we last heard from the hub
standalone_mode = False  # Start in connected mode

# Start GPIO monitoring
gpio_controller.start_monitoring()

# Convenience functions that delegate to GPIO controller
def lower_blinds():
    return gpio_controller.lower_blinds()

def raise_blinds():
    return gpio_controller.raise_blinds()

def stop_blinds():
    return gpio_controller.stop_blinds()

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
            
            <div style="margin-top: 10px; display: flex; gap: 10px;">
                <a href="/schedule" style="flex: 1; display: block; text-align: center; background-color: #673AB7; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; font-size: 16px;">
                    View Sunset Schedule
                </a>
            </div>
            
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
    ''', button_names=BUTTON_PINS.keys(), remote_on=gpio_controller.remote_on, channel_status=gpio_controller.channel_status, 
        channel_selection_in_progress=gpio_controller.channel_selection_in_progress, location_name=LOCATION_NAME, 
        hub_url=HUB_URL, standalone_mode=standalone_mode)

@app.route('/toggle_remote', methods=['POST'])
def toggle_remote():
    # Don't allow toggling if channel selection is in progress
    if gpio_controller.channel_selection_in_progress:
        return redirect(url_for('index'))
        
    gpio_controller.toggle_remote_power()
    return redirect(url_for('index'))

@app.route('/press/<button_name>', methods=['POST'])
def press_button(button_name):
    # Don't allow button presses if channel selection is in progress
    if gpio_controller.channel_selection_in_progress:
        return redirect(url_for('index'))
        
    if gpio_controller.remote_on and button_name in BUTTON_PINS:
        def press_release():
            gpio_controller.press_button_action(button_name)
        threading.Thread(target=press_release).start()
    return redirect(url_for('index'))

@app.route('/pair', methods=['POST'])
def pair_button():
    # Don't allow button presses if channel selection is in progress
    if gpio_controller.channel_selection_in_progress:
        return redirect(url_for('index'))
        
    gpio_controller.pair_remote()
    return redirect(url_for('index'))

@app.route('/channel_selection_status')
def channel_selection_status():
    return jsonify({'in_progress': gpio_controller.channel_selection_in_progress})

@app.route('/go_to_all_channels', methods=['POST'])
def go_to_all_channels():
    # Don't allow channel selection if already in progress
    if gpio_controller.channel_selection_in_progress:
        return redirect(url_for('index'))
    
    # Use GPIO controller to handle all channels selection
    def process_all_channels():
        gpio_controller.channel_selection_in_progress = True
        try:
            gpio_controller.toggle_remote_power()  # Turn off
            time.sleep(2)
            gpio_controller.toggle_remote_power()  # Turn on
            time.sleep(3)
            gpio_controller.select_all_channels()
        finally:
            gpio_controller.channel_selection_in_progress = False
            print("All channels selection complete")
    
    threading.Thread(target=process_all_channels).start()
    return redirect(url_for('index'))

@app.route('/select_channel', methods=['POST'])
def select_channel():
    # Don't allow channel selection if not powered on or already in progress
    if not gpio_controller.remote_on or gpio_controller.channel_selection_in_progress:
        return redirect(url_for('index'))
    
    channel = int(request.form.get('channel', 1))
    if channel < 1 or channel > 16:
        channel = 1
    
    # Use GPIO controller to handle channel selection
    gpio_controller.select_channel(channel)
    return redirect(url_for('index'))

@app.route('/schedule')
def view_schedule():
    from astral import Astral
    
    # Get sunset time
    a = Astral()
    city = a['New York']
    sun_info = city.sun(date=datetime.now(), local=True)
    sunset = sun_info['sunset']
    
    # Calculate scheduled times
    lower_time = sunset - timedelta(minutes=LOWER_BLINDS_OFFSET)
    raise_time = sunset - timedelta(minutes=RAISE_BLINDS_OFFSET)
    
    # Format times for display
    sunset_str = sunset.strftime("%I:%M %p")
    lower_time_str = lower_time.strftime("%I:%M %p")
    raise_time_str = raise_time.strftime("%I:%M %p")
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Blind Schedule</title>
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
            .schedule-panel {
                background-color: #fff;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .schedule-item {
                margin-bottom: 15px;
                padding-bottom: 15px;
                border-bottom: 1px solid #eee;
            }
            .schedule-item:last-child {
                border-bottom: none;
                margin-bottom: 0;
                padding-bottom: 0;
            }
            .time {
                font-weight: bold;
                color: #2196F3;
            }
            .action-buttons {
                margin-top: 20px;
                display: flex;
                gap: 10px;
            }
            .action-buttons a {
                flex: 1;
                display: block;
                background-color: #4CAF50;
                color: white;
                text-align: center;
                padding: 12px 20px;
                text-decoration: none;
                border-radius: 8px;
                font-size: 16px;
                transition: background-color 0.3s;
            }
            .action-buttons a:hover {
                background-color: #45a049;
            }
            .action-buttons .home-button {
                background-color: #2196F3;
            }
            .action-buttons .home-button:hover {
                background-color: #1976D2;
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
        </style>
    </head>
    <body>
        <h1>{{ location_name }} Blind Schedule</h1>
        
        <div style="margin-bottom: 15px; text-align: center;">
            <a href="{{ hub_url }}" style="display: inline-block; background-color: #2196F3; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; font-size: 14px;">
                ← Back to Hub
            </a>
        </div>
        
        {% if standalone_mode %}
        <div class="standalone-mode">
            <p>STANDALONE MODE: Hub connection lost. Using local schedule settings.</p>
        </div>
        {% endif %}
        
        <div class="schedule-panel">
            <div class="schedule-item">
                <p><strong>Today's Sunset:</strong> <span class="time">{{ sunset_time }}</span></p>
            </div>
            
            <div class="schedule-item">
                <p><strong>Lower Blinds:</strong> <span class="time">{{ lower_time }}</span> ({{ lower_offset }} minutes before sunset)</p>
            </div>
            
            <div class="schedule-item">
                <p><strong>Raise Blinds:</strong> <span class="time">{{ raise_time }}</span> {% if raise_offset == 0 %}(at sunset){% else %}({{ raise_offset }} minutes before sunset){% endif %}</p>
            </div>
        </div>
        
        <div class="action-buttons">
            <a href="/" class="home-button">Back to Controls</a>
        </div>
    </body>
    </html>
    ''', sunset_time=sunset_str, lower_time=lower_time_str, raise_time=raise_time_str, 
        lower_offset=LOWER_BLINDS_OFFSET, raise_offset=RAISE_BLINDS_OFFSET,
        location_name=LOCATION_NAME, hub_url=HUB_URL, standalone_mode=standalone_mode)

@app.route('/cleanup')
def cleanup():
    gpio_controller.cleanup()
    return "GPIO Cleaned up."

# API endpoints for hub communication
@app.route('/api/status', methods=['GET'])
def get_status():
    global last_hub_contact
    last_hub_contact = datetime.now()  # Update last contact time
    
    return jsonify({
        'location_name': LOCATION_NAME,
        'remote_on': gpio_controller.remote_on,
        'channel_status': gpio_controller.channel_status,
        'blinds_lowered': gpio_controller.blinds_lowered,
        'standalone_mode': standalone_mode,
        'channel_selection_in_progress': gpio_controller.channel_selection_in_progress
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
        gpio_controller.toggle_remote_power()
        return jsonify({'success': True, 'remote_on': gpio_controller.remote_on})
    
    elif command == 'select_channel':
        channel = params.get('channel')
        if channel is None or not isinstance(channel, int) or channel < 1 or channel > 16:
            return jsonify({'success': False, 'error': 'Invalid channel'}), 400
        
        # Use GPIO controller to handle channel selection
        gpio_controller.select_channel(channel)
        return jsonify({'success': True})
    
    else:
        return jsonify({'success': False, 'error': f'Unknown command: {command}'}), 400

if __name__ == '__main__':
    print(f"Running Blind Controller for {LOCATION_NAME}")
    app.run(host='0.0.0.0', port=5000)
