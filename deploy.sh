#!/bin/bash

# Blind Control System Deployment Script
# This script automates the deployment of the blind control system to a new Raspberry Pi

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== Blind Control System Deployment =====${NC}"
echo "This script will set up the blind control system on this Raspberry Pi."
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root (use sudo).${NC}"
  exit 1
fi

# Prompt for location name
echo -e "${YELLOW}Enter the location name for this blind controller (e.g., North Building):${NC}"
read location_name

if [ -z "$location_name" ]; then
  echo -e "${RED}Location name cannot be empty. Exiting.${NC}"
  exit 1
fi

echo ""
echo -e "${GREEN}Setting up blind controller for: ${YELLOW}$location_name${NC}"
echo ""

# Create installation directory
echo "Creating installation directory..."
mkdir -p /home/pi/blind_control
cd /home/pi/blind_control

# Clone repository if not already cloned
if [ ! -f "main.py" ]; then
  echo "Cloning repository..."
  git clone https://github.com/Sttark/blind_control.git .
  if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to clone repository. Exiting.${NC}"
    exit 1
  fi
else
  echo "Repository already exists, updating..."
  git pull
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install flask RPi.GPIO astral schedule
if [ $? -ne 0 ]; then
  echo -e "${YELLOW}Warning: Some dependencies may not have installed correctly.${NC}"
fi

# Update location name in main.py
echo "Updating location name in main.py..."
sed -i "s/<title>South Building Blind Control<\/title>/<title>$location_name Blind Control<\/title>/g" main.py
sed -i "s/<h1>South Building Blind Control<\/h1>/<h1>$location_name Blind Control<\/h1>/g" main.py

# Update service file
echo "Creating systemd service file..."
cat > blind_control.service << EOL
[Unit]
Description=Blind Control Web Interface for $location_name
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/blind_control/main.py
WorkingDirectory=/home/pi/blind_control
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOL

# Copy service file
echo "Installing systemd service..."
cp blind_control.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable blind_control
systemctl start blind_control

# Check service status
echo "Checking service status..."
systemctl status blind_control --no-pager

# Get IP address
ip_address=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}===== Installation Complete =====${NC}"
echo ""
echo -e "Your blind controller for ${YELLOW}$location_name${NC} is now running."
echo -e "You can access it at: ${YELLOW}http://$ip_address:5000/${NC}"
echo ""
echo -e "To add this controller to your hub, use these details:"
echo -e "  Name: ${YELLOW}$location_name${NC}"
echo -e "  URL: ${YELLOW}http://$ip_address:5000/${NC}"
echo -e "  Description: ${YELLOW}Controls for $location_name blinds${NC}"
echo ""
echo -e "Service management commands:"
echo -e "  ${YELLOW}sudo systemctl start blind_control${NC} - Start the service"
echo -e "  ${YELLOW}sudo systemctl stop blind_control${NC} - Stop the service"
echo -e "  ${YELLOW}sudo systemctl restart blind_control${NC} - Restart the service"
echo -e "  ${YELLOW}sudo systemctl status blind_control${NC} - Check service status"
echo ""
