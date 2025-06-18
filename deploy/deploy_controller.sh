#!/bin/bash

# Deployment script for blind control controllers
# Usage: ./deploy_controller.sh "Location Name" [target_host]

set -e  # Exit on any error

# Check if location name is provided
if [ -z "$1" ]; then
    echo "Usage: $0 \"Location Name\" [target_host]"
    echo "Example: $0 \"Blind Control, North Building #1\" pi@192.168.4.103"
    exit 1
fi

LOCATION_NAME="$1"
TARGET_HOST="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Blind Control Controller Deployment ==="
echo "Location: $LOCATION_NAME"
echo "Target: ${TARGET_HOST:-local}"
echo "Project root: $PROJECT_ROOT"
echo

# Function to deploy locally
deploy_local() {
    echo "Deploying controller locally..."
    
    # Create controller directory structure
    mkdir -p /tmp/blind_controller_deploy
    
    # Copy only controller files
    echo "Copying controller files..."
    cp -r "$PROJECT_ROOT/controller" /tmp/blind_controller_deploy/
    cp -r "$PROJECT_ROOT/shared" /tmp/blind_controller_deploy/
    
    # Create local configuration
    echo "Creating local configuration..."
    cat > /tmp/blind_controller_deploy/local_config.json << EOF
{
    "location_name": "$LOCATION_NAME",
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
EOF
    
    # Copy systemd service file
    echo "Setting up systemd service..."
    cp "$PROJECT_ROOT/configs/systemd/blind_control_controller.service" /tmp/blind_controller_deploy/
    
    echo "Local deployment prepared in /tmp/blind_controller_deploy"
    echo "To complete installation:"
    echo "1. Copy files to target location"
    echo "2. Install systemd service"
    echo "3. Start the service"
}

# Function to deploy remotely
deploy_remote() {
    echo "Deploying controller to $TARGET_HOST..."
    
    # Check SSH connectivity
    if ! ssh -o ConnectTimeout=5 "$TARGET_HOST" "echo 'SSH connection successful'"; then
        echo "Error: Cannot connect to $TARGET_HOST via SSH"
        echo "Please ensure:"
        echo "1. SSH keys are set up"
        echo "2. Target host is reachable"
        echo "3. Username and IP are correct"
        exit 1
    fi
    
    # Create temporary deployment directory
    TEMP_DIR=$(mktemp -d)
    echo "Using temporary directory: $TEMP_DIR"
    
    # Copy controller files
    echo "Preparing controller files..."
    mkdir -p "$TEMP_DIR/blind_control"
    cp -r "$PROJECT_ROOT/controller" "$TEMP_DIR/blind_control/"
    cp -r "$PROJECT_ROOT/shared" "$TEMP_DIR/blind_control/"
    
    # Create local configuration
    echo "Creating configuration for $LOCATION_NAME..."
    cat > "$TEMP_DIR/blind_control/local_config.json" << EOF
{
    "location_name": "$LOCATION_NAME",
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
EOF
    
    # Copy systemd service file
    cp "$PROJECT_ROOT/configs/systemd/blind_control_controller.service" "$TEMP_DIR/blind_control/"
    
    # Create installation script
    cat > "$TEMP_DIR/install.sh" << 'EOF'
#!/bin/bash
set -e

echo "Installing Blind Control Controller..."

# Stop existing service if running
sudo systemctl stop blind_control_controller 2>/dev/null || true

# Create application directory
sudo mkdir -p /opt/blind_control
sudo chown pi:pi /opt/blind_control

# Copy application files
cp -r blind_control/* /opt/blind_control/

# Install systemd service
sudo cp /opt/blind_control/blind_control_controller.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable blind_control_controller

# Install Python dependencies
pip3 install flask RPi.GPIO astral schedule requests

# Start service
sudo systemctl start blind_control_controller

echo "Installation complete!"
echo "Service status:"
sudo systemctl status blind_control_controller --no-pager
EOF
    
    chmod +x "$TEMP_DIR/install.sh"
    
    # Transfer files to target
    echo "Transferring files to $TARGET_HOST..."
    scp -r "$TEMP_DIR"/* "$TARGET_HOST:/tmp/"
    
    # Execute installation
    echo "Executing installation on $TARGET_HOST..."
    ssh "$TARGET_HOST" "cd /tmp && ./install.sh"
    
    # Cleanup
    rm -rf "$TEMP_DIR"
    
    echo "Deployment completed successfully!"
    echo "Controller '$LOCATION_NAME' is now running on $TARGET_HOST"
}

# Main deployment logic
if [ -z "$TARGET_HOST" ]; then
    deploy_local
else
    deploy_remote
fi

echo
echo "=== Deployment Summary ==="
echo "Location: $LOCATION_NAME"
echo "Status: Complete"
echo
echo "Next steps:"
echo "1. Verify the controller is accessible via web interface"
echo "2. Add this controller to the hub configuration if needed"
echo "3. Test blind control functionality"
