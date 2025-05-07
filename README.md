# Blind Control System

A Raspberry Pi-based web interface for controlling motorized window blinds remotely.

## Overview

This project provides a web-based control system for motorized window blinds. It uses a Raspberry Pi to interface with a physical remote control through GPIO pins, allowing users to control blinds from any device with a web browser on the local network.

The system supports multiple controllers across different locations with a central hub interface. The architecture consists of:

1. **Hub**: A central server that provides a dashboard to access all controllers, schedules actions based on sunset times and weather conditions, and sends commands to controllers.

2. **Controllers**: Individual Raspberry Pis connected to blind remotes that can operate independently if the hub is unreachable.

## Repository

https://github.com/Sttark/blind_control

## Features

- **Remote Power Control**: Turn the blind remote on/off
- **Blind Movement**: Move blinds up, down, or stop them at any position
- **Pairing Functionality**: Pair the remote with new blinds
- **Channel Selection**: Control up to 16 different blinds/blind groups by selecting channels
- **Mobile-Friendly Interface**: Responsive design works on smartphones, tablets, and computers
- **Status Indicators**: Visual feedback on remote power status and current channel
- **Automatic Channel Reset**: Automatically resets to "All Channels" mode when powered on
- **Centralized Schedule Management**: Control blind timing settings from a single location
- **Schedule Viewing**: View the current blind schedule on each controller
- **Standalone Mode**: Controllers can operate independently if the hub is unreachable

## Hardware Requirements

- Raspberry Pi (with GPIO pins)
- Remote control for motorized blinds
- Appropriate wiring to connect the Raspberry Pi GPIO pins to the remote control buttons

## GPIO Pin Configuration

The system uses the following GPIO pins (BCM mode):

- **Remote Power**: GPIO 4
- **Up Button**: GPIO 21
- **Stop Button**: GPIO 24
- **Down Button**: GPIO 16
- **Channel Up Button**: GPIO 12
- **Channel Down Button**: GPIO 25

## Installation

1. Clone this repository to your Raspberry Pi:
   ```
   git clone https://github.com/Sttark/blind_control.git
   cd blind_control
   ```

2. Install the required dependencies:
   ```
   pip3 install flask RPi.GPIO astral schedule
   ```

3. Set up the systemd service for automatic startup:
   ```
   sudo cp blind_control.service /etc/systemd/system/
   sudo systemctl enable blind_control
   sudo systemctl start blind_control
   ```

## Usage

1. Access the web interface using one of the following methods:
   - When on a Sttark network: `http://192.168.4.202:5000/`
   - When not on a Sttark network: Connect to ZeroTier and use `http://192.168.194.210:5000/`
   - Alternatively: `http://blind-control-south.local:5000/` (mDNS)
2. Use the interface buttons to control your blinds:
   - Power button turns the remote on/off
   - Direction buttons (Up/Stop/Down) control blind movement
   - Pair button initiates pairing mode (holds "Up" for 5 seconds)
   - Channel selection allows controlling different blinds or blind groups
3. View the current schedule by clicking the "View Sunset Schedule" button

## Service Management

- **Start the service**: `sudo systemctl start blind_control`
- **Stop the service**: `sudo systemctl stop blind_control`
- **Check status**: `sudo systemctl status blind_control`
- **View logs**: `sudo journalctl -u blind_control`

## Development

To run the application in development mode:

```
python3 controller.py
```

The web server will start on port 5000 and be accessible via the same URLs mentioned in the Usage section.

## Customization

You can customize the GPIO pin assignments by modifying the `REMOTE_POWER_PIN` and `BUTTON_PINS` variables in `controller.py`.

## Multi-Controller Setup

This project now supports multiple blind controllers across different locations with a central hub interface.

### Hub Features

- **Central Dashboard**: A single page that lists all blind controllers
- **Easy Navigation**: Click on any controller to access its interface
- **Admin Panel**: Add, edit, or remove blind controllers through a simple interface
- **Centralized Schedule Management**: Control blind timing settings from a single location

### Setting Up the Hub

1. Navigate to the hub directory:
   ```
   cd blind_control/hub
   ```

2. Install the required dependencies:
   ```
   pip3 install flask astral schedule
   ```

3. Set up the systemd service for the hub:
   ```
   sudo cp blind_control_hub.service /etc/systemd/system/
   sudo systemctl enable blind_control_hub
   sudo systemctl start blind_control_hub
   ```

4. Access the hub interface:
   ```
   http://blind-control-hub.local:5001/
   ```

### Setting Up a New Controller

To set up the blind control system on a new Raspberry Pi:

1. SSH into your Raspberry Pi:
   ```
   ssh pi@your-raspberry-pi-ip
   ```

2. Clone the repository:
   ```
   git clone https://github.com/Sttark/blind_control.git
   cd blind_control
   ```

3. Install the required dependencies:
   ```
   sudo apt update
   sudo apt install -y python3-flask python3-rpi.gpio python3-astral python3-schedule
   ```

4. Create a local configuration file with your location-specific settings:
   ```
   cat > local_config.json << EOL
   {
       "location_name": "Your Location Name",
       "hub_url": "http://192.168.4.202:5001/",
       "weather_api_key": "b8c328a0f8be42ff936210148250404",
       "location": "29607",
       "cloud_threshold": 15,
       "monitoring_interval": 10,
       "schedule": {
           "lower_blinds_offset": 192,
           "raise_blinds_offset": 0
       }
   }
   EOL
   ```

5. Set up the systemd service for automatic startup:
   ```
   sudo cp blind_control_controller.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable blind_control_controller
   sudo systemctl start blind_control_controller
   ```

6. Once installation is complete, add the new controller to your hub using the Admin Settings panel.

For more details on the hub setup and usage, see the [Hub README](hub/README.md).

## Configuration

The system uses a configuration-based approach that separates code from configuration:

- **Configuration-Based Approach**: Each controller has a `local_config.json` file with location-specific settings
- **Hub Configuration**: The hub has configuration files for controllers and global settings
- **Centralized Schedule Management**: The hub's `hub_config.json` file contains the schedule settings for all controllers
- **Local Schedule Override**: Each controller's `local_config.json` file can override the hub's schedule settings if needed

## File Structure

- **controller.py**: The main controller code that runs on each Raspberry Pi
- **main.py**: Legacy controller code (not used by default)
- **local_config.json**: Local configuration for each controller
- **hub/main.py**: The hub code that runs on the central Raspberry Pi
- **hub/hub_config.json**: Hub configuration including schedule settings
- **hub/config.json**: List of controllers managed by the hub

## Troubleshooting

- If the web interface is not accessible, ensure the service is running with `sudo systemctl status blind_control_controller`
- If buttons are not responding correctly, verify the GPIO wiring and pin assignments
- To reset the GPIO pins, access the `/cleanup` endpoint in your browser
- If the hub interface is not accessible, check its service status with `sudo systemctl status blind_control_hub`
- If schedule changes don't appear on a controller, check that the controller is connected to the hub and restart the controller service

## Author

[Ryan Quinn](https://github.com/Sttark)
