# Blind Control Hub

A central hub for managing multiple blind controllers across different locations.

## Overview

The Blind Control Hub provides a unified interface for accessing multiple blind controllers deployed on different Raspberry Pis. It serves as a landing page that lists all available blind controllers and allows easy navigation between them.

## Features

- **Central Dashboard**: A single page that lists all blind controllers
- **Easy Navigation**: Click on any controller to access its interface
- **Admin Panel**: Add, edit, or remove blind controllers through a simple interface
- **Responsive Design**: Works on smartphones, tablets, and computers

## Installation

### Automated Installation

A deployment script is included to make it easy to set up the blind control hub:

1. SSH into your Raspberry Pi:
   ```
   ssh pi@your-raspberry-pi-ip
   ```

2. Clone the repository:
   ```
   git clone https://github.com/Sttark/blind_control.git
   cd blind_control/hub
   ```

3. Make the deployment script executable:
   ```
   chmod +x deploy_hub.sh
   ```

4. Run the deployment script:
   ```
   sudo ./deploy_hub.sh
   ```

5. Once installation is complete, access the hub interface and add your blind controllers.

### Manual Installation

If you prefer to install manually:

1. Make sure you have the required dependencies:
   ```
   pip3 install flask
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

## Adding a New Controller

1. Click on "Admin Settings" to expand the admin panel
2. Fill in the details for the new controller:
   - **Name**: A descriptive name for the location (e.g., "North Building")
   - **URL**: The full URL to access the controller (e.g., "http://192.168.4.203:5000/")
   - **Description**: Optional details about the controller
3. Click "Add Controller" to save

## Deploying a New Blind Controller

To deploy the blind control system to a new Raspberry Pi:

1. Clone the repository on the new Raspberry Pi:
   ```
   git clone https://github.com/Sttark/blind_control.git
   cd blind_control
   ```

2. Install the required dependencies:
   ```
   pip3 install flask RPi.GPIO astral schedule
   ```

3. Update the title in `main.py` to reflect the location (e.g., change "South Building" to "North Building")

4. Set up the systemd service:
   ```
   sudo cp blind_control.service /etc/systemd/system/
   sudo systemctl enable blind_control
   sudo systemctl start blind_control
   ```

5. Add the new controller to the hub using the Admin Settings panel

## Service Management

- **Start the service**: `sudo systemctl start blind_control_hub`
- **Stop the service**: `sudo systemctl stop blind_control_hub`
- **Check status**: `sudo systemctl status blind_control_hub`
- **View logs**: `sudo journalctl -u blind_control_hub`

## Update Management

The hub now includes tools for managing updates across all connected controllers:

### Updating the Hub

To update the hub itself:

1. SSH into the hub Raspberry Pi
2. Navigate to the hub directory: `cd /home/pi/blind_control/hub`
3. Run the update script: `sudo ./update_hub.sh`

The script will back up your configuration, update the code, and restore your configuration.

### Updating All Controllers

The hub can now update all connected controllers remotely:

1. SSH into the hub Raspberry Pi
2. Navigate to the hub directory: `cd /home/pi/blind_control/hub`
3. Run the update all script: `sudo ./update_all_controllers.sh`
4. Follow the prompts to select which controllers to update

This requires SSH key-based authentication to be set up between the hub and all controllers. For detailed instructions, see the [Update Protocol Documentation](../UPDATE_PROTOCOL.md).

## Troubleshooting

- If the hub interface is not accessible, ensure the service is running with `sudo systemctl status blind_control_hub`
- If a controller is not accessible from the hub, verify that the URL is correct and that the controller is running
- For mDNS resolution issues (using .local domains), ensure that Avahi/Bonjour is properly configured on your network
- For update-related issues, refer to the [Update Protocol Documentation](../UPDATE_PROTOCOL.md#troubleshooting)
