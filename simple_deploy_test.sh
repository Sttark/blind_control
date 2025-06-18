#!/bin/bash
set -e

TARGET_IP="192.168.4.103"
NAME="Blind Control, North Building #1"

echo "=== Simple Deployment Test to $TARGET_IP ==="

# Test SSH connectivity first
echo "Testing SSH connection..."
if ! sshpass -p "Sttark#1" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no sttark@$TARGET_IP "echo 'SSH connection successful'"; then
    echo "ERROR: Cannot connect to $TARGET_IP via SSH"
    exit 1
fi

# Clean up any existing installation
echo "Cleaning up existing installation..."
sshpass -p "Sttark#1" ssh -o StrictHostKeyChecking=no sttark@$TARGET_IP "
    sudo systemctl stop blind_control_controller 2>/dev/null || true
    sudo systemctl stop blind_control 2>/dev/null || true
    sudo systemctl disable blind_control_controller 2>/dev/null || true
    sudo systemctl disable blind_control 2>/dev/null || true
    sudo rm -f /etc/systemd/system/blind_control*.service
    sudo systemctl daemon-reload
    sudo rm -rf /opt/blind_control
    rm -rf /home/sttark/blind_control
    pkill -f 'python.*blind' || true
"

echo "Cleanup completed successfully!"

# Clone fresh repository
echo "Installing fresh code..."
sshpass -p "Sttark#1" ssh -o StrictHostKeyChecking=no sttark@$TARGET_IP "
    cd /home/sttark
    git clone https://github.com/Sttark/blind_control.git
    cd blind_control
    echo 'Repository cloned successfully'
"

echo "Code installation completed!"

# Run deployment script
echo "Running deployment..."
sshpass -p "Sttark#1" ssh -o StrictHostKeyChecking=no sttark@$TARGET_IP "
    cd /home/sttark/blind_control
    ./deploy/deploy_controller.sh '$NAME'
"

echo "Deployment completed successfully!"
