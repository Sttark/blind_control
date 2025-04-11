#!/bin/bash

# Blind Control System Update Script
# This script updates the blind control system while preserving local configuration

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== Blind Control System Update =====${NC}"
echo "This script will update the blind control system while preserving your local configuration."
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}Note: Some operations may require root privileges.${NC}"
  echo "Continue anyway? (y/n)"
  read continue_response
  if [ "$continue_response" != "y" ]; then
    echo "Update cancelled."
    exit 1
  fi
fi

# Backup local configuration
echo "Backing up local configuration..."
if [ -f "local_config.json" ]; then
  cp local_config.json local_config.backup.json
  echo -e "${GREEN}✓ Configuration backed up${NC}"
else
  echo -e "${YELLOW}! No local_config.json found. Will create default configuration after update.${NC}"
fi

# Get current directory
CURRENT_DIR=$(pwd)
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR"

# Check if this is a git repository
if [ ! -d ".git" ]; then
  echo -e "${RED}Error: Not a git repository. Cannot update.${NC}"
  echo "This script must be run from the blind_control directory."
  exit 1
fi

# Pull latest code
echo "Updating code from repository..."
git_output=$(git pull 2>&1)
git_status=$?

if [ $git_status -ne 0 ]; then
  echo -e "${RED}Error updating code:${NC}"
  echo "$git_output"
  
  # Restore backup if update failed
  if [ -f "local_config.backup.json" ]; then
    echo "Restoring configuration backup..."
    mv local_config.backup.json local_config.json
  fi
  
  exit 1
else
  echo -e "${GREEN}✓ Code updated successfully${NC}"
  echo "$git_output"
fi

# Restore local configuration
if [ -f "local_config.backup.json" ]; then
  echo "Restoring local configuration..."
  mv local_config.backup.json local_config.json
  echo -e "${GREEN}✓ Configuration restored${NC}"
else
  # If no backup exists but main.py requires it, create a default config
  if grep -q "local_config.json" main.py && [ ! -f "local_config.json" ]; then
    echo "Creating default configuration..."
    cat > local_config.json << EOL
{
    "location_name": "South Building",
    "hub_url": "http://192.168.4.202:5001/",
    "weather_api_key": "b8c328a0f8be42ff936210148250404",
    "location": "29607",
    "cloud_threshold": 15,
    "monitoring_interval": 10
}
EOL
    echo -e "${GREEN}✓ Default configuration created${NC}"
  fi
fi

# Check if systemd service exists and restart it
if systemctl list-unit-files | grep -q blind_control.service; then
  echo "Restarting blind_control service..."
  if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Cannot restart service without root privileges.${NC}"
    echo "Please run: sudo systemctl restart blind_control"
  else
    systemctl restart blind_control
    echo -e "${GREEN}✓ Service restarted${NC}"
  fi
else
  echo -e "${YELLOW}No blind_control service found. If needed, restart manually.${NC}"
fi

echo ""
echo -e "${GREEN}===== Update Complete =====${NC}"
echo ""
echo "Your blind control system has been updated while preserving your local configuration."
echo ""
