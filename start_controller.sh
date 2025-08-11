#!/bin/bash

# Simple controller startup script
# Usage: ./start_controller.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}=== Blind Control Controller Startup ===${NC}"
echo

# Verify we're in the right directory
if [ ! -f "$SCRIPT_DIR/controller/main.py" ]; then
    log_error "This doesn't appear to be the blind_control repository directory"
    log_error "Please run this script from the root of the cloned repository"
    exit 1
fi

# Get Pi's IP address
PI_IP=$(hostname -I | awk '{print $1}')
HOSTNAME=$(hostname)

log_info "Starting controller setup..."
echo "  Pi IP Address: $PI_IP"
echo "  Hostname: $HOSTNAME"
echo

# Create default local configuration (will be updated by hub)
log_info "Creating default configuration..."
cat > "$SCRIPT_DIR/local_config.json" << EOF
{
    "location_name": "Unconfigured Controller ($HOSTNAME)",
    "hub_url": "http://192.168.4.202:5001/",
    "weather_api_key": "b8c328a0f8be42ff936210148250404",
    "location": "29607",
    "cloud_threshold": 15,
    "monitoring_interval": 10,
    "schedule": {
        "lower_blinds_offset": 192,
        "raise_blinds_offset": 0
    },
    "default_channel": 0
}
EOF

log_success "Default configuration created"

# Install Python dependencies
log_info "Installing Python dependencies..."
if pip3 install --break-system-packages flask RPi.GPIO gpiozero lgpio astral schedule requests; then
    log_success "Dependencies installed"
else
    log_warning "Some dependencies may have failed to install. The controller might still work."
fi

# Stop any existing service
log_info "Stopping any existing blind control service..."
sudo systemctl stop blind_control_controller 2>/dev/null || true
sudo systemctl disable blind_control_controller 2>/dev/null || true

# Install systemd service
log_info "Installing systemd service..."
sudo cp "$SCRIPT_DIR/configs/systemd/blind_control_controller.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable blind_control_controller

# Start the service
log_info "Starting blind control service..."
if sudo systemctl start blind_control_controller; then
    log_success "Service started successfully"
else
    log_error "Failed to start service. Check logs with: sudo journalctl -u blind_control_controller"
    exit 1
fi

# Wait a moment for service to initialize
sleep 2

# Check service status
log_info "Checking service status..."
if sudo systemctl is-active --quiet blind_control_controller; then
    log_success "Service is running"
else
    log_error "Service is not running properly"
    sudo systemctl status blind_control_controller --no-pager
    exit 1
fi

echo
echo -e "${GREEN}=== Controller Ready! ===${NC}"
echo
echo -e "${GREEN}Controller Information:${NC}"
echo "  Status: Running (unconfigured)"
echo "  IP Address: $PI_IP"
echo "  Web Interface: http://$PI_IP:5000"
echo "  Hostname: $HOSTNAME"
echo
echo -e "${GREEN}Next Steps:${NC}"
echo "1. Access the hub admin panel: http://192.168.4.202:5001"
echo "2. Click 'Add New Controller'"
echo "3. Fill in the form:"
echo "   - Name: [Choose a descriptive name]"
echo "   - URL: http://$PI_IP:5000/"
echo "   - Description: [Location description]"
echo "4. Click 'Add Controller'"
echo "5. Test the controller functionality"
echo
echo -e "${BLUE}Useful Commands:${NC}"
echo "  Check status: sudo systemctl status blind_control_controller"
echo "  View logs: sudo journalctl -u blind_control_controller -f"
echo "  Restart: sudo systemctl restart blind_control_controller"
echo
echo -e "${YELLOW}Ready to be added to hub at: http://$PI_IP:5000/${NC}"
