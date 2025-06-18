from flask import Flask, render_template_string, redirect, url_for, request, jsonify
import os
import json
import requests
import time
import threading
import schedule
from datetime import datetime, timedelta
from astral import Astral

app = Flask(__name__)

# Configuration file path
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
HUB_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'hub_config.json')

# Load blind controllers configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        # Default configuration
        return {
            "controllers": [
                {
                    "name": "South Building",
                    "url": "http://192.168.4.202:5000/",
                    "description": "Controls for South Building blinds"
                }
            ]
        }

# Load hub configuration
def load_hub_config():
    if os.path.exists(HUB_CONFIG_FILE):
        with open(HUB_CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        # Default configuration
        default_config = {
            "weather_api_key": "b8c328a0f8be42ff936210148250404",
            "location": "29607",
            "cloud_threshold": 15,
            "monitoring_interval": 10,
            "schedule": {
                "lower_blinds_offset": 150,  # 2.5 hours before sunset in minutes
                "raise_blinds_offset": 10    # 10 minutes before sunset in minutes
            }
        }
        # Save default configuration
        with open(HUB_CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config

# Save configuration
def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Save hub configuration
def save_hub_config(config):
    with open(HUB_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Load configurations
config = load_config()
hub_config = load_hub_config()

# Extract hub configuration values
WEATHER_API_KEY = hub_config.get('weather_api_key', 'b8c328a0f8be42ff936210148250404')
LOCATION = hub_config.get('location', '29607')  # Zip code
CLOUD_THRESHOLD = hub_config.get('cloud_threshold', 15)  # Consider sunny if cloud cover is below 15%
MONITORING_INTERVAL = hub_config.get('monitoring_interval', 10)  # Check weather every 10 minutes (in minutes)
LOWER_BLINDS_OFFSET = hub_config.get('schedule', {}).get('lower_blinds_offset', 192)  # 3 hours and 12 minutes before sunset
RAISE_BLINDS_OFFSET = hub_config.get('schedule', {}).get('raise_blinds_offset', 0)  # At sunset

# Global variables for tracking state
controller_status = {}  # Store status of each controller
blinds_lowered = False  # Track if blinds are currently lowered

# Function to get sunset time for the current day
def get_sunset_time():
    # Initialize Astral
    a = Astral()
    # New York City coordinates (approximate for East Coast)
    # You may need to adjust these coordinates for your specific location
    city = a['New York']
    
    # Get today's sun information
    sun_info = city.sun(date=datetime.now(), local=True)
    sunset = sun_info['sunset']
    
    print(f"Today's sunset time: {sunset.strftime('%H:%M:%S')}")
    return sunset

# Function to get current cloud cover percentage
def get_cloud_cover():
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={LOCATION}&aqi=no"
        response = requests.get(url)
        data = response.json()
        
        # Get cloud cover percentage (0-100)
        cloud_cover = data['current']['cloud']
        
        # Also get condition text for logging
        condition = data['current']['condition']['text']
        
        print(f"Current conditions: {condition}, Cloud cover: {cloud_cover}%")
        return cloud_cover, condition
    except Exception as e:
        print(f"Error checking weather: {e}")
        return None, None

# Function to determine if it's overcast
def is_overcast():
    cloud_cover, _ = get_cloud_cover()
    if cloud_cover is not None:
        return cloud_cover >= CLOUD_THRESHOLD
    return False

# Function to send command to a controller
def send_command_to_controller(controller_url, command, params=None):
    try:
        if params is None:
            params = {}
        
        url = f"{controller_url.rstrip('/')}/api/command"
        response = requests.post(url, json={
            "command": command,
            "params": params
        }, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error sending command to {controller_url}: {response.status_code} {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"Exception sending command to {controller_url}: {e}")
        return {"success": False, "error": str(e)}

# Function to get status from a controller
def get_controller_status(controller_url):
    try:
        url = f"{controller_url.rstrip('/')}/api/status"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting status from {controller_url}: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"Exception getting status from {controller_url}: {e}")
        return None

# Function to update status of all controllers
def update_all_controller_status():
    global controller_status
    
    for controller in config['controllers']:
        url = controller['url']
        status = get_controller_status(url)
        if status:
            controller_status[url] = status
            print(f"Updated status for {controller['name']}: {status}")
        else:
            # If we can't reach the controller, mark it as offline
            if url in controller_status:
                controller_status[url]['offline'] = True
            else:
                controller_status[url] = {"offline": True}

# Function to lower blinds on all controllers
def lower_blinds_on_all_controllers():
    global blinds_lowered
    
    # Check if it's cloudy (above threshold)
    if is_overcast():
        print(f"Cloud cover is above threshold ({CLOUD_THRESHOLD}%). Skipping blind lowering.")
        return
    
    print("Lowering blinds on all controllers")
    
    for controller in config['controllers']:
        url = controller['url']
        result = send_command_to_controller(url, "lower_blinds")
        if result and result.get('success'):
            print(f"Successfully lowered blinds on {controller['name']}")
        else:
            print(f"Failed to lower blinds on {controller['name']}")
    
    blinds_lowered = True

# Function to raise blinds on all controllers
def raise_blinds_on_all_controllers():
    global blinds_lowered
    
    print("Raising blinds on all controllers")
    
    for controller in config['controllers']:
        url = controller['url']
        result = send_command_to_controller(url, "raise_blinds")
        if result and result.get('success'):
            print(f"Successfully raised blinds on {controller['name']}")
        else:
            print(f"Failed to raise blinds on {controller['name']}")
    
    blinds_lowered = False

# Function to schedule blind actions for the day
def schedule_blind_actions():
    # Clear any existing jobs
    schedule.clear()
    
    # Get today's sunset time
    sunset = get_sunset_time()
    
    # Calculate times for lowering and raising blinds
    lower_time = sunset - timedelta(minutes=LOWER_BLINDS_OFFSET)
    raise_time = sunset - timedelta(minutes=RAISE_BLINDS_OFFSET)
    
    # Format times for scheduler (HH:MM format)
    lower_time_str = lower_time.strftime("%H:%M")
    raise_time_str = raise_time.strftime("%H:%M")
    
    # Schedule the jobs
    schedule.every().day.at(lower_time_str).do(lower_blinds_on_all_controllers)
    schedule.every().day.at(raise_time_str).do(raise_blinds_on_all_controllers)
    
    print(f"Scheduled to lower blinds at {lower_time_str} ({LOWER_BLINDS_OFFSET} minutes before sunset, if not too cloudy)")
    print(f"Scheduled to raise blinds at {raise_time_str} (at sunset)")

# Function to monitor cloud cover and control blinds
def monitor_cloud_cover():
    global blinds_lowered
    
    while True:
        # Get current time
        now = datetime.now()
        
        # Get sunset time
        sunset = get_sunset_time()
        
        # Define monitoring period (from LOWER_BLINDS_OFFSET minutes before sunset to sunset)
        monitoring_start = sunset - timedelta(minutes=LOWER_BLINDS_OFFSET)
        
        # Only monitor during relevant hours
        if monitoring_start <= now <= sunset:
            cloud_cover, condition = get_cloud_cover()
            
            if cloud_cover is not None:
                print(f"Current cloud cover: {cloud_cover}%, Condition: {condition}")
                
                # If it was cloudy but now it's sunny, lower the blinds
                if blinds_lowered == False and cloud_cover < CLOUD_THRESHOLD:
                    print(f"Cloud cover dropped below threshold ({CLOUD_THRESHOLD}%). It's sunny now - lowering blinds.")
                    lower_blinds_on_all_controllers()
                
                # If it was sunny but now it's cloudy, raise the blinds
                elif blinds_lowered == True and cloud_cover >= CLOUD_THRESHOLD:
                    print(f"Cloud cover increased above threshold ({CLOUD_THRESHOLD}%). It's cloudy now - raising blinds.")
                    raise_blinds_on_all_controllers()
        
        # Reset blind state at the end of the day
        elif now.hour >= 23:
            blinds_lowered = False
            
        # Sleep for the monitoring interval
        time.sleep(MONITORING_INTERVAL * 60)

# Function to run the scheduler
def run_scheduler():
    # Schedule blind actions for today
    schedule_blind_actions()
    
    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# Start the scheduler in a background thread
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

# Start the cloud cover monitoring thread
cloud_monitor_thread = threading.Thread(target=monitor_cloud_cover, daemon=True)
cloud_monitor_thread.start()

# Start the controller status update thread
def run_status_updater():
    while True:
        update_all_controller_status()
        time.sleep(60)  # Update every minute

status_thread = threading.Thread(target=run_status_updater, daemon=True)
status_thread.start()

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Blind Control Hub</title>
        <style>
            * {
                box-sizing: border-box;
                font-family: Arial, sans-serif;
            }
            body {
                margin: 0;
                padding: 16px;
                background-color: #f5f5f5;
                max-width: 800px;
                margin: 0 auto;
            }
            h1 {
                text-align: center;
                color: #333;
                font-size: 28px;
                margin-bottom: 20px;
            }
            .controller-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .controller-card {
                background-color: #fff;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: transform 0.3s, box-shadow 0.3s;
                cursor: pointer;
                text-decoration: none;
                color: inherit;
                display: block;
                position: relative;
            }
            .controller-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .controller-card h2 {
                margin-top: 0;
                color: #2196F3;
                font-size: 20px;
            }
            .controller-card p {
                color: #666;
                margin-bottom: 0;
            }
            .status-indicator {
                position: absolute;
                top: 10px;
                right: 10px;
                width: 12px;
                height: 12px;
                border-radius: 50%;
            }
            .status-online {
                background-color: #4CAF50;
            }
            .status-offline {
                background-color: #f44336;
            }
            .status-standalone {
                background-color: #FF9800;
            }
            .admin-panel {
                background-color: #fff;
                border-radius: 8px;
                padding: 20px;
                margin-top: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .admin-panel h2 {
                margin-top: 0;
                color: #333;
                font-size: 20px;
            }
            .admin-toggle {
                background-color: #673AB7;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
                text-align: left;
                margin-bottom: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .admin-toggle:hover {
                background-color: #5E35B1;
            }
            .admin-toggle:after {
                content: "▼";
                font-size: 12px;
            }
            .admin-toggle.active:after {
                content: "▲";
            }
            .admin-content {
                display: none;
                padding: 15px;
                background-color: #f9f9f9;
                border-radius: 8px;
                margin-bottom: 15px;
            }
            .admin-content.show {
                display: block;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input[type="text"] {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 15px;
                font-size: 16px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            button:hover {
                background-color: #45a049;
            }
            .controller-list {
                margin-top: 20px;
            }
            .controller-item {
                background-color: #f9f9f9;
                border-radius: 4px;
                padding: 15px;
                margin-bottom: 10px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .controller-item-info {
                flex: 1;
            }
            .controller-item-actions {
                display: flex;
                gap: 10px;
            }
            .edit-btn {
                background-color: #2196F3;
            }
            .edit-btn:hover {
                background-color: #1976D2;
            }
            .delete-btn {
                background-color: #f44336;
            }
            .delete-btn:hover {
                background-color: #d32f2f;
            }
            .control-buttons {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            .control-buttons button {
                flex: 1;
                padding: 15px;
                font-size: 18px;
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
            .weather-panel {
                background-color: #fff;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .weather-panel h2 {
                margin-top: 0;
                color: #333;
                font-size: 20px;
            }
            .weather-info {
                display: flex;
                align-items: center;
                margin-bottom: 15px;
            }
            .weather-icon {
                width: 64px;
                height: 64px;
                margin-right: 15px;
            }
            .weather-details {
                flex: 1;
            }
            .weather-condition {
                font-size: 18px;
                margin-bottom: 5px;
            }
            .cloud-status {
                margin-top: 15px;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
            }
            .cloud-status.overcast {
                background-color: #e1f5fe;
                color: #0288d1;
            }
            .cloud-status.clear {
                background-color: #f1f8e9;
                color: #689f38;
            }
            .schedule-panel {
                background-color: #fff;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .schedule-panel h2 {
                margin-top: 0;
                color: #333;
                font-size: 20px;
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
        </style>
        <script>
            function toggleAdminPanel() {
                const content = document.getElementById('adminContent');
                const button = document.getElementById('adminToggle');
                content.classList.toggle('show');
                button.classList.toggle('active');
            }
            
            function editController(index) {
                const controllers = {{ config|tojson }}.controllers;
                const controller = controllers[index];
                
                document.getElementById('editIndex').value = index;
                document.getElementById('editName').value = controller.name;
                document.getElementById('editUrl').value = controller.url;
                document.getElementById('editDescription').value = controller.description;
                
                document.getElementById('editForm').style.display = 'block';
                document.getElementById('addForm').style.display = 'none';
            }
            
            function cancelEdit() {
                document.getElementById('editForm').style.display = 'none';
                document.getElementById('addForm').style.display = 'block';
            }
            
            // Auto-refresh the page every 60 seconds to update status
            setTimeout(function() {
                window.location.reload();
            }, 60000);
        </script>
    </head>
    <body>
        <h1>Blind Control Hub</h1>
        
        
        <div class="weather-panel">
            <h2>Current Weather</h2>
            <div class="weather-info">
                <div class="weather-details">
                    <div class="weather-condition">{{ condition }}</div>
                    <div>Cloud Cover: {{ cloud_cover }}%</div>
                </div>
            </div>
            
            <div class="cloud-status {{ 'overcast' if is_overcast else 'clear' }}">
                {% if is_overcast %}
                    Currently CLOUDY (above {{ cloud_threshold }}% cloud cover)
                    <p>Blinds will be raised during monitoring period</p>
                {% else %}
                    Currently SUNNY (below {{ cloud_threshold }}% cloud cover)
                    <p>Blinds will be lowered during monitoring period</p>
                {% endif %}
            </div>
        </div>
        
        <div class="schedule-panel">
            <h2>Today's Schedule</h2>
            <div class="schedule-item">
                <p><strong>Sunset:</strong> <span class="time">{{ sunset_time }}</span></p>
            </div>
            
            <div class="schedule-item">
                <p><strong>Lower Blinds:</strong> <span class="time">{{ lower_time }}</span> ({{ lower_offset }} minutes before sunset)</p>
            </div>
            
            <div class="schedule-item">
                <p><strong>Raise Blinds:</strong> <span class="time">{{ raise_time }}</span> {% if raise_offset == 0 %}(at sunset){% else %}({{ raise_offset }} minutes before sunset){% endif %}</p>
            </div>
            
            <form action="/reschedule" method="get" style="margin-top: 15px;">
                <button type="submit">Refresh Schedule</button>
            </form>
        </div>
        
        <h2>Controllers</h2>
        <div class="controller-grid">
            {% for controller in config['controllers'] %}
            <a href="{{ controller['url'] }}" class="controller-card">
                <h2>{{ controller['name'] }}</h2>
                <p>{{ controller['description'] }}</p>
                
                {% set status = controller_status.get(controller['url'], {}) %}
                {% if status.get('offline', False) %}
                    <span class="status-indicator status-offline" title="Offline"></span>
                {% elif status.get('standalone_mode', False) %}
                    <span class="status-indicator status-standalone" title="Standalone Mode"></span>
                {% else %}
                    <span class="status-indicator status-online" title="Online"></span>
                {% endif %}
                
                {% if status and not status.get('offline', False) %}
                    <div style="margin-top: 10px;">
                        <p><strong>Remote:</strong> {{ 'ON' if status.get('remote_on', False) else 'OFF' }}</p>
                        {% if status.get('remote_on', False) %}
                            <p><strong>Channel:</strong> {{ status.get('channel_status', 'Unknown') }}</p>
                        {% endif %}
                    </div>
                {% endif %}
            </a>
            {% endfor %}
        </div>
        
        <div class="admin-panel">
            <button id="adminToggle" class="admin-toggle" onclick="toggleAdminPanel()">
                Admin Settings
            </button>
            
            <div id="adminContent" class="admin-content">
                <div id="addForm">
                    <h3>Add New Controller</h3>
                    <form action="/add_controller" method="post">
                        <div class="form-group">
                            <label for="name">Name:</label>
                            <input type="text" id="name" name="name" required placeholder="e.g., North Building">
                        </div>
                        <div class="form-group">
                            <label for="url">URL:</label>
                            <input type="text" id="url" name="url" required placeholder="e.g., http://192.168.4.203:5000/">
                        </div>
                        <div class="form-group">
                            <label for="description">Description:</label>
                            <input type="text" id="description" name="description" placeholder="e.g., Controls for North Building blinds">
                        </div>
                        <button type="submit">Add Controller</button>
                    </form>
                </div>
                
                <div id="editForm" style="display: none;">
                    <h3>Edit Controller</h3>
                    <form action="/edit_controller" method="post">
                        <input type="hidden" id="editIndex" name="index">
                        <div class="form-group">
                            <label for="editName">Name:</label>
                            <input type="text" id="editName" name="name" required>
                        </div>
                        <div class="form-group">
                            <label for="editUrl">URL:</label>
                            <input type="text" id="editUrl" name="url" required>
                        </div>
                        <div class="form-group">
                            <label for="editDescription">Description:</label>
                            <input type="text" id="editDescription" name="description">
                        </div>
                        <button type="submit">Save Changes</button>
                        <button type="button" onclick="cancelEdit()" style="background-color: #999;">Cancel</button>
                    </form>
                </div>
                
                <div class="controller-list">
                    <h3>Manage Controllers</h3>
                    {% for controller in config['controllers'] %}
                    <div class="controller-item">
                        <div class="controller-item-info">
                            <strong>{{ controller['name'] }}</strong><br>
                            <small>{{ controller['url'] }}</small>
                        </div>
                        <div class="controller-item-actions">
                            <button class="edit-btn" onclick="editController({{ loop.index0 }})">Edit</button>
                            <form action="/delete_controller" method="post" style="display: inline;">
                                <input type="hidden" name="index" value="{{ loop.index0 }}">
                                <button type="submit" class="delete-btn" onclick="return confirm('Are you sure you want to delete this controller?')">Delete</button>
                            </form>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                
                <div style="margin-top: 20px;">
                    <h3>Hub Configuration</h3>
                    <form action="/update_hub_config" method="post">
                        <div class="form-group">
                            <label for="weather_api_key">Weather API Key:</label>
                            <input type="text" id="weather_api_key" name="weather_api_key" value="{{ hub_config.weather_api_key }}" required>
                        </div>
                        <div class="form-group">
                            <label for="location">Location (Zip Code):</label>
                            <input type="text" id="location" name="location" value="{{ hub_config.location }}" required>
                        </div>
                        <div class="form-group">
                            <label for="cloud_threshold">Cloud Threshold (%):</label>
                            <input type="text" id="cloud_threshold" name="cloud_threshold" value="{{ hub_config.cloud_threshold }}" required>
                        </div>
                        <div class="form-group">
                            <label for="monitoring_interval">Monitoring Interval (minutes):</label>
                            <input type="text" id="monitoring_interval" name="monitoring_interval" value="{{ hub_config.monitoring_interval }}" required>
                        </div>
                        <div class="form-group">
                            <label for="lower_blinds_offset">Lower Blinds Offset (minutes before sunset):</label>
                            <input type="text" id="lower_blinds_offset" name="lower_blinds_offset" value="{{ hub_config.schedule.lower_blinds_offset }}" required>
                        </div>
                        <div class="form-group">
                            <label for="raise_blinds_offset">Raise Blinds Offset (minutes before sunset):</label>
                            <input type="text" id="raise_blinds_offset" name="raise_blinds_offset" value="{{ hub_config.schedule.raise_blinds_offset }}" required>
                        </div>
                        <button type="submit">Save Hub Configuration</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', config=config, 
        controller_status=controller_status,
        hub_config=hub_config,
        cloud_cover=get_cloud_cover()[0] or 0,
        condition=get_cloud_cover()[1] or "Unknown",
        is_overcast=is_overcast(),
        cloud_threshold=CLOUD_THRESHOLD,
        sunset_time=get_sunset_time().strftime("%I:%M %p"),
        lower_time=(get_sunset_time() - timedelta(minutes=LOWER_BLINDS_OFFSET)).strftime("%I:%M %p"),
        raise_time=(get_sunset_time() - timedelta(minutes=RAISE_BLINDS_OFFSET)).strftime("%I:%M %p"),
        lower_offset=LOWER_BLINDS_OFFSET,
        raise_offset=RAISE_BLINDS_OFFSET)

@app.route('/add_controller', methods=['POST'])
def add_controller():
    global config
    name = request.form.get('name')
    url = request.form.get('url')
    description = request.form.get('description', '')
    
    if not name or not url:
        return "Name and URL are required", 400
    
    config = load_config()
    config['controllers'].append({
        'name': name,
        'url': url,
        'description': description
    })
    save_config(config)
    
    return redirect(url_for('index'))

@app.route('/edit_controller', methods=['POST'])
def edit_controller():
    global config
    index = int(request.form.get('index'))
    name = request.form.get('name')
    url = request.form.get('url')
    description = request.form.get('description', '')
    
    if not name or not url:
        return "Name and URL are required", 400
    
    config = load_config()
    if 0 <= index < len(config['controllers']):
        config['controllers'][index] = {
            'name': name,
            'url': url,
            'description': description
        }
        save_config(config)
    
    return redirect(url_for('index'))

@app.route('/delete_controller', methods=['POST'])
def delete_controller():
    global config
    index = int(request.form.get('index'))
    
    config = load_config()
    if 0 <= index < len(config['controllers']):
        del config['controllers'][index]
        save_config(config)
    
    return redirect(url_for('index'))

@app.route('/update_hub_config', methods=['POST'])
def update_hub_config():
    global WEATHER_API_KEY, LOCATION, CLOUD_THRESHOLD, MONITORING_INTERVAL, LOWER_BLINDS_OFFSET, RAISE_BLINDS_OFFSET, hub_config
    
    # Get form data
    weather_api_key = request.form.get('weather_api_key')
    location = request.form.get('location')
    cloud_threshold = int(request.form.get('cloud_threshold', 15))
    monitoring_interval = int(request.form.get('monitoring_interval', 10))
    lower_blinds_offset = int(request.form.get('lower_blinds_offset', 150))
    raise_blinds_offset = int(request.form.get('raise_blinds_offset', 10))
    
    # Update hub config
    hub_config = load_hub_config()
    hub_config['weather_api_key'] = weather_api_key
    hub_config['location'] = location
    hub_config['cloud_threshold'] = cloud_threshold
    hub_config['monitoring_interval'] = monitoring_interval
    hub_config['schedule'] = {
        'lower_blinds_offset': lower_blinds_offset,
        'raise_blinds_offset': raise_blinds_offset
    }
    save_hub_config(hub_config)
    
    # Update global variables
    WEATHER_API_KEY = weather_api_key
    LOCATION = location
    CLOUD_THRESHOLD = cloud_threshold
    MONITORING_INTERVAL = monitoring_interval
    LOWER_BLINDS_OFFSET = lower_blinds_offset
    RAISE_BLINDS_OFFSET = raise_blinds_offset
    
    # Reschedule blind actions with new settings
    schedule_blind_actions()
    
    return redirect(url_for('index'))

@app.route('/reschedule', methods=['GET'])
def reschedule():
    # Reschedule the blind actions
    schedule_blind_actions()
    return redirect(url_for('index'))

@app.route('/raise_all', methods=['POST'])
def raise_all():
    # Raise blinds on all controllers
    raise_blinds_on_all_controllers()
    return redirect(url_for('index'))

@app.route('/stop_all', methods=['POST'])
def stop_all():
    # Stop blinds on all controllers
    for controller in config['controllers']:
        url = controller['url']
        send_command_to_controller(url, "stop_blinds")
    return redirect(url_for('index'))

@app.route('/lower_all', methods=['POST'])
def lower_all():
    # Lower blinds on all controllers
    lower_blinds_on_all_controllers()
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("Running Blind Control Hub on port 5001")
    app.run(host='0.0.0.0', port=5001)
