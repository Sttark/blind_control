# Blind Control System

A Raspberry Pi-based web interface for controlling motorized window blinds remotely.

## Overview

This project provides a web-based control system for motorized window blinds in the South Building. It uses a Raspberry Pi to interface with a physical remote control through GPIO pins, allowing users to control blinds from any device with a web browser on the local network.

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

1. Access the web interface by navigating to `http://blind-control-south.local:5000/` in your web browser
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

The web server will start on port 5000 and be accessible at `http://blind-control-south.local:5000/`.

## Customization

You can customize the GPIO pin assignments by modifying the `REMOTE_POWER_PIN` and `BUTTON_PINS` variables in `main.py`.

## Troubleshooting

- If the web interface is not accessible, ensure the service is running with `sudo systemctl status blind_control`
- If buttons are not responding correctly, verify the GPIO wiring and pin assignments
- To reset the GPIO pins, access the `/cleanup` endpoint in your browser

## Author

[Ryan Quinn](https://github.com/Sttark)
