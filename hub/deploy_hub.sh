#!/bin/bash

# Blind Control Hub Deployment Script
# This script automates the deployment of the blind control hub to a Raspberry Pi

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== Blind Control Hub Deployment =====${NC}"
echo "This script will set up the blind control hub on this Raspberry Pi."
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root (use sudo).${NC}"
  exit 1
fi

# Create installation directory
echo "Creating installation directory..."
mkdir -p /home/pi/blind_control/hub
cd /home/pi/blind_control

# Clone repository if not already cloned
if [ ! -f "main.py" ]; then
  echo "Cloning repository..."
  git clone https://github.com/Sttark/blind_control.git .
  if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to clone repository. Exiting.${NC}"
    exit 1
  fi
fi

# Install dependencies
echo "Installing dependencies..."
# Try to install using apt (preferred method for Debian-based systems)
echo "Installing packages using apt..."
apt update
apt install -y python3-flask
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to install dependencies using apt. Exiting.${NC}"
  exit 1
fi

# Update service file
echo "Creating systemd service file..."
cat > hub/blind_control_hub.service << EOL
[Unit]
Description=Blind Control Hub Web Interface
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/blind_control/hub/main.py
WorkingDirectory=/home/pi/blind_control/hub
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOL

# Create default config.json if it doesn't exist
echo "Checking for config.json..."
if [ ! -f "hub/config.json" ]; then
  echo "Creating default config.json..."
  cat > hub/config.json << EOL
{
    "controllers": [
        {
            "name": "South Building",
            "url": "http://192.168.4.202:5000/",
            "description": "Controls for South Building blinds"
        }
    ]
}
EOL
  echo "Default config.json created."
else
  echo "config.json already exists, keeping existing configuration."
fi

# Create default hub_config.json if it doesn't exist
echo "Checking for hub_config.json..."
if [ ! -f "hub/hub_config.json" ]; then
  echo "Creating default hub_config.json..."
  cat > hub/hub_config.json << EOL
{
    "weather_api_key": "b8c328a0f8be42ff936210148250404",
    "location": "29607",
    "cloud_threshold": 15,
    "monitoring_interval": 10,
    "schedule": {
        "lower_blinds_offset": 150,
        "raise_blinds_offset": 10
    }
}
EOL
  echo "Default hub_config.json created."
else
  echo "hub_config.json already exists, keeping existing configuration."
fi

# No update scripts needed

# Copy service file
echo "Installing systemd service..."
cp hub/blind_control_hub.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable blind_control_hub
systemctl start blind_control_hub

# Check service status
echo "Checking service status..."
systemctl status blind_control_hub --no-pager

# Get IP address
ip_address=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}===== Installation Complete =====${NC}"
echo ""
echo -e "Your blind control hub is now running."
echo -e "You can access it at: ${YELLOW}http://$ip_address:5001/${NC}"
echo ""
echo -e "Service management commands:"
echo -e "  ${YELLOW}sudo systemctl start blind_control_hub${NC} - Start the service"
echo -e "  ${YELLOW}sudo systemctl stop blind_control_hub${NC} - Stop the service"
echo -e "  ${YELLOW}sudo systemctl restart blind_control_hub${NC} - Restart the service"
echo -e "  ${YELLOW}sudo systemctl status blind_control_hub${NC} - Check service status"
echo ""
echo -e "To add blind controllers to the hub:"
echo -e "1. Deploy the blind control system to each Raspberry Pi using the main deploy.sh script"
echo -e "2. Access the hub interface and use the Admin Settings panel to add each controller"
echo -e "3. Enter the name, URL, and description for each controller"
echo ""
