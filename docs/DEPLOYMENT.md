# Blind Control System Deployment Guide

This guide covers deploying the reorganized blind control system with the new modular architecture.

## System Architecture

The system now uses a clean, modular architecture:

```
blind_control/
├── hub/                    # Hub application (central server)
├── controller/             # Controller application (individual Pi)
├── shared/                 # Shared utilities and libraries
├── deploy/                 # Deployment scripts
├── configs/                # Configuration templates and systemd services
└── docs/                   # Documentation
```

## Quick Start

### Deploying a New Controller

To deploy a controller to a new Raspberry Pi:

```bash
# Deploy to a remote Pi
./deploy/deploy_controller.sh "Blind Control, North Building #1" pi@192.168.4.103

# Or prepare for local installation
./deploy/deploy_controller.sh "Blind Control, North Building #1"
```

### Setting Up the Hub

The hub should be deployed on the central Raspberry Pi that coordinates all controllers.

## Detailed Deployment Steps

### Prerequisites

1. **Raspberry Pi Setup**:
   - Raspberry Pi OS installed
   - SSH enabled
   - Python 3 installed
   - GPIO access configured

2. **Network Configuration**:
   - All Pis on the same network
   - Static IP addresses recommended
   - SSH key authentication set up (for remote deployment)

### Controller Deployment

1. **Remote Deployment** (Recommended):
   ```bash
   ./deploy/deploy_controller.sh "Location Name" pi@IP_ADDRESS
   ```

2. **Manual Deployment**:
   ```bash
   # On the target Pi
   git clone https://github.com/Sttark/blind_control.git
   cd blind_control
   
   # Edit local_config.json with location-specific settings
   cp configs/controller_config_template.json local_config.json
   # Edit the location_name and other settings
   
   # Install dependencies
   pip3 install flask RPi.GPIO astral schedule requests
   
   # Install systemd service
   sudo cp configs/systemd/blind_control_controller.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable blind_control_controller
   sudo systemctl start blind_control_controller
   ```

### Hub Deployment

1. **Install Hub**:
   ```bash
   # On the hub Pi
   git clone https://github.com/Sttark/blind_control.git
   cd blind_control
   
   # Configure hub settings
   cp configs/hub_config_template.json hub/hub_config.json
   # Edit weather API key, location, etc.
   
   # Install dependencies
   pip3 install flask astral schedule requests
   
   # Install systemd service
   sudo cp configs/systemd/blind_control_hub.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable blind_control_hub
   sudo systemctl start blind_control_hub
   ```

2. **Add Controllers to Hub**:
   - Access hub web interface: `http://hub-ip:5001`
   - Use Admin Settings to add controllers
   - Or manually edit `hub/config.json`

## Configuration

### Controller Configuration (`local_config.json`)

```json
{
    "location_name": "Blind Control, Location Name",
    "hub_url": "http://192.168.4.202:5001/",
    "weather_api_key": "your_api_key",
    "location": "zip_code",
    "cloud_threshold": 15,
    "monitoring_interval": 10,
    "schedule": {
        "lower_blinds_offset": 192,
        "raise_blinds_offset": 0
    }
}
```

### Hub Configuration (`hub/hub_config.json`)

```json
{
    "weather_api_key": "your_api_key",
    "location": "zip_code",
    "cloud_threshold": 15,
    "monitoring_interval": 10,
    "schedule": {
        "lower_blinds_offset": 192,
        "raise_blinds_offset": 0
    }
}
```

### Controllers List (`hub/config.json`)

```json
{
    "controllers": [
        {
            "name": "Blind Control, South Building B",
            "url": "http://192.168.4.202:5000/",
            "description": "Controls for South Building B blinds"
        }
    ]
}
```

## Service Management

### Controller Services

```bash
# Start/stop controller
sudo systemctl start blind_control_controller
sudo systemctl stop blind_control_controller

# Check status
sudo systemctl status blind_control_controller

# View logs
sudo journalctl -u blind_control_controller -f
```

### Hub Services

```bash
# Start/stop hub
sudo systemctl start blind_control_hub
sudo systemctl stop blind_control_hub

# Check status
sudo systemctl status blind_control_hub

# View logs
sudo journalctl -u blind_control_hub -f
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**:
   - Check Python dependencies: `pip3 list`
   - Verify file permissions: `ls -la /opt/blind_control/`
   - Check logs: `sudo journalctl -u service_name`

2. **GPIO Errors**:
   - Ensure user is in gpio group: `sudo usermod -a -G gpio pi`
   - Check GPIO permissions: `ls -la /dev/gpiomem`

3. **Network Issues**:
   - Verify IP addresses in configuration
   - Test connectivity: `ping hub_ip`
   - Check firewall settings

4. **Hub Can't Reach Controllers**:
   - Verify controller URLs in hub config
   - Test API endpoints: `curl http://controller_ip:5000/api/status`

### Rollback Procedure

If deployment fails, you can rollback using the backup branch:

```bash
git checkout backup-before-reorganization
sudo systemctl restart blind_control_controller
```

## Updates

### Updating Controllers

```bash
# On each controller Pi
cd /opt/blind_control
git pull
sudo systemctl restart blind_control_controller
```

### Updating Hub

```bash
# On hub Pi
cd /opt/blind_control
git pull
sudo systemctl restart blind_control_hub
```

## Security Considerations

1. **SSH Keys**: Use key-based authentication for deployment
2. **Network**: Consider VPN for remote access
3. **Firewall**: Limit access to necessary ports (5000, 5001)
4. **Updates**: Keep system packages updated

## Support

For issues or questions:
1. Check the logs first
2. Verify configuration files
3. Test network connectivity
4. Consult troubleshooting section
