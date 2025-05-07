# Blind Control Hub

A central hub for managing multiple blind controllers across different locations.

## Overview

The Blind Control Hub provides a unified interface for accessing multiple blind controllers deployed on different Raspberry Pis. It serves as a central management system that:

1. Provides a dashboard to access all controllers
2. Monitors weather conditions and sunset times
3. Schedules blind actions based on these conditions
4. Sends commands to controllers
5. Monitors controller status and health
6. Centralizes schedule management for all controllers

## Features

- **Central Dashboard**: A single page that lists all blind controllers
- **Easy Navigation**: Click on any controller to access its interface
- **Admin Panel**: Add, edit, or remove blind controllers through a simple interface
- **Responsive Design**: Works on smartphones, tablets, and computers
- **Centralized Schedule Management**: Control blind timing settings from a single location
- **Weather-Based Control**: Automatically adjust blinds based on cloud cover
- **Sunset-Based Scheduling**: Schedule blind actions relative to sunset time

## Installation

To install the blind control hub:

1. Make sure you have the required dependencies:
   ```
   pip3 install flask astral schedule
   ```

2. Set up the systemd service for automatic startup:
   ```
   sudo cp blind_control_hub.service /etc/systemd/system/
   sudo systemctl enable blind_control_hub
   sudo systemctl start blind_control_hub
   ```

## Usage

1. Access the hub interface using one of the following methods:
   - When on a local network: `http://blind-control-hub.local:5001/`
   - Using the IP address: `http://[hub-ip-address]:5001/`

2. From the hub, you can:
   - Click on any controller card to access that specific blind controller
   - Use the Admin Settings panel to add, edit, or remove controllers
   - Configure the schedule settings for all controllers
   - View the current weather conditions and blind schedule

## Schedule Configuration

The hub manages the schedule for all controllers through the `hub_config.json` file. The current settings are:

- **Lower Blinds**: 3 hours and 12 minutes before sunset (192 minutes)
- **Raise Blinds**: Exactly at sunset (0 minutes before)

To modify these settings:

1. Click on "Admin Settings" to expand the admin panel
2. Scroll down to the "Hub Configuration" section
3. Update the "Lower Blinds Offset" and "Raise Blinds Offset" values
4. Click "Save Hub Configuration" to apply the changes

These settings will be used by all controllers connected to the hub.

## Adding a New Controller

1. Click on "Admin Settings" to expand the admin panel
2. Fill in the details for the new controller:
   - **Name**: A descriptive name for the location (e.g., "North Building")
   - **URL**: The full URL to access the controller (e.g., "http://192.168.4.203:5000/")
   - **Description**: Optional details about the controller
3. Click "Add Controller" to save

## Setting Up a New Controller

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

6. Add the new controller to the hub using the Admin Settings panel

The controller will run the `controller.py` script, which provides:
- A web interface for manual control
- API endpoints for the hub to send commands
- Standalone operation if the hub is unreachable
- A schedule view page to see the current blind schedule

## Service Management

- **Start the service**: `sudo systemctl start blind_control_hub`
- **Stop the service**: `sudo systemctl stop blind_control_hub`
- **Check status**: `sudo systemctl status blind_control_hub`
- **View logs**: `sudo journalctl -u blind_control_hub`

## File Structure

- **main.py**: The hub code that runs on the central Raspberry Pi
- **hub_config.json**: Hub configuration including schedule settings
- **config.json**: List of controllers managed by the hub

## Individual Programming

Each Pi in the system can be programmed individually:

### Programming the Hub

To update the hub:

1. SSH into the hub Raspberry Pi
2. Navigate to the hub directory: `cd /home/pi/blind_control/hub`
3. Make your changes directly to the code or configuration files
4. Restart the service: `sudo systemctl restart blind_control_hub`

### Programming Controllers

To update a controller:

1. SSH into the controller Raspberry Pi
2. Navigate to the blind control directory: `cd /home/pi/blind_control`
3. Make your changes directly to the code or configuration files
4. Restart the service: `sudo systemctl restart blind_control_controller`

## Centralized vs. Local Configuration

The system supports both centralized and local configuration:

- **Centralized Configuration**: The hub's `hub_config.json` file contains the schedule settings for all controllers
- **Local Configuration**: Each controller's `local_config.json` file can override the hub's schedule settings if needed
- **Standalone Mode**: If a controller loses connection to the hub, it will use its local configuration

## Troubleshooting

- If the hub interface is not accessible, ensure the service is running with `sudo systemctl status blind_control_hub`
- If a controller is not accessible from the hub, verify that the URL is correct and that the controller is running
- For mDNS resolution issues (using .local domains), ensure that Avahi/Bonjour is properly configured on your network
- If schedule changes don't appear on a controller, check that the controller is connected to the hub and restart the controller service
