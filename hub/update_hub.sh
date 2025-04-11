#!/bin/bash

# Blind Control Hub Update Script
# This script updates the blind control hub while preserving configuration

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== Blind Control Hub Update =====${NC}"
echo "This script will update the blind control hub while preserving your configuration."
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

# Backup configuration
echo "Backing up configuration..."
if [ -f "config.json" ]; then
  cp config.json config.backup.json
  echo -e "${GREEN}✓ Configuration backed up${NC}"
else
  echo -e "${YELLOW}! No config.json found. Will create default configuration after update.${NC}"
fi

# Get current directory
CURRENT_DIR=$(pwd)
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR"

# Check if parent directory is a git repository
cd ..
if [ ! -d ".git" ]; then
  echo -e "${RED}Error: Not a git repository. Cannot update.${NC}"
  echo "This script must be run from the blind_control/hub directory."
  cd "$CURRENT_DIR"
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
  cd hub
  if [ -f "config.backup.json" ]; then
    echo "Restoring configuration backup..."
    mv config.backup.json config.json
  fi
  
  cd "$CURRENT_DIR"
  exit 1
else
  echo -e "${GREEN}✓ Code updated successfully${NC}"
  echo "$git_output"
fi

# Return to hub directory
cd hub

# Restore configuration
if [ -f "config.backup.json" ]; then
  echo "Restoring configuration..."
  mv config.backup.json config.json
  echo -e "${GREEN}✓ Configuration restored${NC}"
else
  # If no backup exists but config.json is needed, create a default config
  if [ ! -f "config.json" ]; then
    echo "Creating default configuration..."
    cat > config.json << EOL
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
    echo -e "${GREEN}✓ Default configuration created${NC}"
  fi
fi

# Check if systemd service exists and restart it
if systemctl list-unit-files | grep -q blind_control_hub.service; then
  echo "Restarting blind_control_hub service..."
  if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Cannot restart service without root privileges.${NC}"
    echo "Please run: sudo systemctl restart blind_control_hub"
  else
    systemctl restart blind_control_hub
    echo -e "${GREEN}✓ Service restarted${NC}"
  fi
else
  echo -e "${YELLOW}No blind_control_hub service found. If needed, restart manually.${NC}"
fi

cd "$CURRENT_DIR"

echo ""
echo -e "${GREEN}===== Update Complete =====${NC}"
echo ""
echo "Your blind control hub has been updated while preserving your configuration."
echo ""
