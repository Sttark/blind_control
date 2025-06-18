#!/bin/bash
set -e

echo "Testing deployment to 192.168.4.103..."

# Test SSH connectivity
echo "Testing SSH connection..."
if sshpass -p "Sttark#1" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no sttark@192.168.4.103 "echo 'SSH connection successful'"; then
    echo "SSH connection works!"
else
    echo "SSH connection failed!"
    exit 1
fi

# Test basic commands
echo "Testing basic commands..."
sshpass -p "Sttark#1" ssh -o StrictHostKeyChecking=no sttark@192.168.4.103 "
    echo 'Current directory:' \$(pwd)
    echo 'User:' \$(whoami)
    echo 'Home directory contents:'
    ls -la /home/sttark/
"

echo "Test completed successfully!"
