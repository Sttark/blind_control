# Blind Control System - Update Protocol

This document describes the update protocol for the Blind Control System, which allows for safe and efficient updates while preserving local configurations.

## Overview

The Blind Control System now uses a configuration-based approach that separates code from configuration. This allows for easier updates without losing location-specific settings. The system includes several scripts to facilitate updates:

1. `update.sh` - Updates an individual blind controller
2. `hub/update_hub.sh` - Updates the hub
3. `hub/update_all_controllers.sh` - Updates all controllers from the hub

## Configuration Files

### Controller Configuration (`local_config.json`)

Each blind controller has a `local_config.json` file that contains location-specific settings:

```json
{
    "location_name": "South Building",
    "hub_url": "http://192.168.4.202:5001/",
    "weather_api_key": "b8c328a0f8be42ff936210148250404",
    "location": "29607",
    "cloud_threshold": 15,
    "monitoring_interval": 10
}
```

### Hub Configuration (`hub/config.json`)

The hub has a `config.json` file that contains the list of registered controllers:

```json
{
    "controllers": [
        {
            "name": "South Building",
            "url": "http://192.168.4.202:5000/",
            "description": "Controls for South Building blinds"
        },
        {
            "name": "North Building",
            "url": "http://192.168.4.103:5000/",
            "description": "Controls for North Building blinds"
        }
    ]
}
```

## Update Process

### Updating a Single Controller

To update a single blind controller:

1. SSH into the controller: `ssh pi@controller-ip`
2. Navigate to the blind control directory: `cd /home/pi/blind_control`
3. Run the update script: `sudo ./update.sh`

The update script will:
- Backup the local configuration
- Pull the latest code from the repository
- Restore the local configuration
- Restart the service

### Updating the Hub

To update the hub:

1. SSH into the hub: `ssh pi@hub-ip`
2. Navigate to the hub directory: `cd /home/pi/blind_control/hub`
3. Run the update script: `sudo ./update_hub.sh`

The update script will:
- Backup the hub configuration
- Pull the latest code from the repository
- Restore the hub configuration
- Restart the service

### Updating All Controllers from the Hub

To update all controllers from the hub:

1. SSH into the hub: `ssh pi@hub-ip`
2. Navigate to the hub directory: `cd /home/pi/blind_control/hub`
3. Run the update all script: `sudo ./update_all_controllers.sh`
4. Follow the prompts to select which controllers to update

The script will:
- Read the list of controllers from the hub's config.json
- Allow you to select which controllers to update
- Connect to each controller via SSH and run its update script
- Report the status of each update

**Note:** This requires SSH key-based authentication to be set up between the hub and all controllers. See the "SSH Key Setup" section below for details.

## SSH Key Setup

To enable the hub to update controllers without password prompts, you need to set up SSH key-based authentication:

1. On the hub, generate an SSH key pair (if not already done):
   ```
   ssh-keygen -t rsa -b 4096
   ```

2. Copy the public key to each controller:
   ```
   ssh-copy-id pi@controller-ip
   ```

3. Test the connection:
   ```
   ssh pi@controller-ip
   ```

You should be able to connect without a password prompt.

## Deployment with Configuration

The deployment scripts (`deploy.sh` and `hub/deploy_hub.sh`) have been updated to use the configuration-based approach:

- When deploying a new controller, `deploy.sh` will create a `local_config.json` file with the specified location name.
- When deploying a new hub, `hub/deploy_hub.sh` will create a default `config.json` file.

## Troubleshooting

### Update Failed

If an update fails, the script will attempt to restore the backup configuration. You can also manually restore the configuration:

1. For a controller: `cp local_config.backup.json local_config.json`
2. For the hub: `cp config.backup.json config.json`

### Service Not Restarting

If the service doesn't restart automatically after an update:

1. For a controller: `sudo systemctl restart blind_control`
2. For the hub: `sudo systemctl restart blind_control_hub`

### SSH Connection Issues

If the hub cannot connect to a controller via SSH:

1. Verify the controller is online: `ping controller-ip`
2. Check SSH key setup: `ssh -v pi@controller-ip`
3. Ensure the controller's IP address in the hub's config.json is correct

## Best Practices

1. **Always back up configurations before updates**
   - The update scripts do this automatically, but manual backups are recommended for important changes

2. **Test updates on one controller before updating all**
   - Use `update.sh` on a single controller to verify the update works as expected

3. **Keep track of custom configurations**
   - Document any changes made to configuration files

4. **Regularly check for updates**
   - Pull the latest code from the repository to stay up-to-date with bug fixes and new features
