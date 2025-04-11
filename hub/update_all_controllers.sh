#!/bin/bash

# Blind Control System - Update All Controllers Script
# This script updates all blind controllers registered in the hub

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== Blind Control System - Update All Controllers =====${NC}"
echo "This script will update all blind controllers registered in the hub."
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

# Get current directory
CURRENT_DIR=$(pwd)
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR"

# Check if config.json exists
if [ ! -f "config.json" ]; then
  echo -e "${RED}Error: config.json not found.${NC}"
  echo "This script must be run from the blind_control/hub directory."
  cd "$CURRENT_DIR"
  exit 1
fi

# Parse config.json to get controller URLs
echo "Reading controller configuration..."
CONTROLLERS=$(grep -o '"url": "[^"]*"' config.json | cut -d'"' -f4)
CONTROLLER_NAMES=$(grep -o '"name": "[^"]*"' config.json | cut -d'"' -f4)

# Convert to arrays
IFS=$'\n' read -d '' -ra URL_ARRAY <<< "$CONTROLLERS"
IFS=$'\n' read -d '' -ra NAME_ARRAY <<< "$CONTROLLER_NAMES"

if [ ${#URL_ARRAY[@]} -eq 0 ]; then
  echo -e "${RED}Error: No controllers found in config.json.${NC}"
  cd "$CURRENT_DIR"
  exit 1
fi

echo -e "Found ${#URL_ARRAY[@]} controllers:"
for i in "${!NAME_ARRAY[@]}"; do
  echo -e "  ${i+1}. ${NAME_ARRAY[$i]} (${URL_ARRAY[$i]})"
done
echo ""

# Ask which controllers to update
echo "Which controllers would you like to update?"
echo "  a) All controllers"
echo "  s) Select specific controllers"
echo "  c) Cancel"
read -p "Enter choice [a/s/c]: " update_choice

case "$update_choice" in
  a|A)
    SELECTED_INDICES=$(seq 0 $((${#URL_ARRAY[@]}-1)))
    ;;
  s|S)
    echo "Enter the numbers of the controllers to update (separated by spaces):"
    read -a selected_numbers
    SELECTED_INDICES=()
    for num in "${selected_numbers[@]}"; do
      if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 1 ] && [ "$num" -le ${#URL_ARRAY[@]} ]; then
        SELECTED_INDICES+=($((num-1)))
      else
        echo -e "${YELLOW}Warning: Invalid selection '$num', skipping.${NC}"
      fi
    done
    if [ ${#SELECTED_INDICES[@]} -eq 0 ]; then
      echo -e "${RED}No valid controllers selected. Exiting.${NC}"
      cd "$CURRENT_DIR"
      exit 1
    fi
    ;;
  *)
    echo "Update cancelled."
    cd "$CURRENT_DIR"
    exit 0
    ;;
esac

# Function to extract hostname from URL
extract_hostname() {
  local url=$1
  # Remove protocol (http:// or https://)
  local hostname=${url#*://}
  # Remove port and path
  hostname=${hostname%%:*}
  hostname=${hostname%%/*}
  echo "$hostname"
}

# Update selected controllers
echo ""
echo -e "${GREEN}Starting update process...${NC}"
echo ""

for index in $SELECTED_INDICES; do
  controller_name="${NAME_ARRAY[$index]}"
  controller_url="${URL_ARRAY[$index]}"
  controller_host=$(extract_hostname "$controller_url")
  
  echo -e "${YELLOW}Updating ${controller_name} (${controller_url})...${NC}"
  
  # Check if controller is reachable
  if ping -c 1 "$controller_host" &> /dev/null; then
    echo "  Controller is reachable."
    
    # Try to SSH into the controller and run the update script
    echo "  Connecting via SSH..."
    ssh_output=$(ssh -o ConnectTimeout=5 pi@"$controller_host" "cd /home/pi/blind_control && sudo ./update.sh" 2>&1)
    ssh_status=$?
    
    if [ $ssh_status -eq 0 ]; then
      echo -e "  ${GREEN}✓ Update successful${NC}"
    else
      echo -e "  ${RED}✗ Update failed${NC}"
      echo "  Error: $ssh_output"
    fi
  else
    echo -e "  ${RED}✗ Controller is not reachable${NC}"
  fi
  
  echo ""
done

cd "$CURRENT_DIR"

echo -e "${GREEN}===== Update Process Complete =====${NC}"
echo ""
echo "Summary:"
echo "  - Attempted to update ${#SELECTED_INDICES[@]} controllers"
echo "  - Check the output above for any errors"
echo ""
echo "Note: This script requires SSH key-based authentication to be set up between"
echo "the hub and all controllers. If any updates failed, you may need to set up"
echo "SSH keys or update the controllers manually."
echo ""
