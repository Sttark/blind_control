# Blind Control System

A Raspberry Pi-based web interface for controlling motorized window blinds remotely.

## Overview

This project provides a web-based control system for motorized window blinds. It uses a Raspberry Pi to interface with a physical remote control through GPIO pins, allowing users to control blinds from any device with a web browser on the local network.

The system now supports multiple controllers across different locations with a central hub interface.

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
   pip3 install flask RPi.GPIO
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

## Service Management

- **Start the service**: `sudo systemctl start blind_control`
- **Stop the service**: `sudo systemctl stop blind_control`
- **Check status**: `sudo systemctl status blind_control`
- **View logs**: `sudo journalctl -u blind_control`

## Development

To run the application in development mode:

```
python3 main.py
```

The web server will start on port 5000 and be accessible via the same URLs mentioned in the Usage section.

## Customization

You can customize the GPIO pin assignments by modifying the `REMOTE_POWER_PIN` and `BUTTON_PINS` variables in `main.py`.

## Multi-Controller Setup

This project now supports multiple blind controllers across different locations with a central hub interface.

### Hub Features

- **Central Dashboard**: A single page that lists all blind controllers
- **Easy Navigation**: Click on any controller to access its interface
- **Admin Panel**: Add, edit, or remove blind controllers through a simple interface

### Setting Up the Hub

1. Navigate to the hub directory:
   ```
   cd blind_control/hub
   ```

2. Install the required dependencies:
   ```
   pip3 install flask
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

### Deploying to a New Raspberry Pi

A deployment script is included to make it easy to set up the blind control system on a new Raspberry Pi:

1. SSH into your Raspberry Pi:
   ```
   ssh pi@your-raspberry-pi-ip
   ```

2. Clone the repository:
   ```
   git clone https://github.com/Sttark/blind_control.git
   cd blind_control
   ```

3. Make the deployment script executable:
   ```
   chmod +x deploy.sh
   ```

4. Run the deployment script:
   ```
   sudo ./deploy.sh
   ```

5. Follow the prompts to configure your blind controller with a location name.

6. Once installation is complete, add the new controller to your hub using the provided details.

For more details on the hub setup and usage, see the [Hub README](hub/README.md).

## Troubleshooting

- If the web interface is not accessible, ensure the service is running with `sudo systemctl status blind_control`
- If buttons are not responding correctly, verify the GPIO wiring and pin assignments
- To reset the GPIO pins, access the `/cleanup` endpoint in your browser
- If the hub interface is not accessible, check its service status with `sudo systemctl status blind_control_hub`

## Author

[Ryan Quinn](https://github.com/Sttark)
