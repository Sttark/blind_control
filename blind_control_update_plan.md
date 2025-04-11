# Blind Control System Update Plan

## Current Issue Identified

The North Building Pi is not displaying weather information correctly. After analyzing the code, we found that:

1. The title tag in the HTML is correctly set to "North Building Blinds Blind Control"
2. However, the h1 heading still says "South Building Blind Control"
3. This inconsistency suggests that when the code was deployed to the North Building Pi, not all references to "South Building" were updated

## Analysis of Current Deployment Approach

The current deployment process uses `deploy.sh` which:

1. Prompts for a location name (e.g., "North Building")
2. Updates specific strings in main.py using sed commands:
   ```bash
   sed -i "s/<title>South Building Blind Control<\/title>/<title>$location_name Blind Control<\/title>/g" main.py
   sed -i "s/<h1>South Building Blind Control<\/h1>/<h1>$location_name Blind Control<\/h1>/g" main.py
   ```
3. Creates a systemd service file with the location name

Limitations of this approach:
- It only updates specific hardcoded strings
- If the HTML structure changes, the sed commands might fail
- It doesn't handle other location-specific settings (like the hub URL)
- There's no verification that all references were updated

## Proposed Solutions for Better Update Management

### 1. Separate Code from Configuration

Modify the system to use a configuration file for location-specific settings:

```python
# At the top of main.py
import json
import os

# Load location-specific configuration
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'local_config.json')
try:
    with open(CONFIG_FILE, 'r') as f:
        local_config = json.load(f)
except FileNotFoundError:
    # Default configuration
    local_config = {
        "location_name": "Blind Control",
        "hub_url": "http://192.168.4.202:5001/"
    }

# Use these variables in the code
LOCATION_NAME = local_config.get('location_name', 'Blind Control')
HUB_URL = local_config.get('hub_url', 'http://192.168.4.202:5001/')
```

Then update the HTML template to use these variables:
```html
<title>{{ LOCATION_NAME }} Blind Control</title>
...
<h1>{{ LOCATION_NAME }} Blind Control</h1>
...
<a href="{{ HUB_URL }}" style="...">← Back to Hub</a>
```

### 2. Update the Deployment Script

Modify deploy.sh to create this configuration file instead of using sed:

```bash
# Create local configuration file
echo "Creating local configuration file..."
cat > local_config.json << EOL
{
    "location_name": "$location_name",
    "hub_url": "http://192.168.4.202:5001/"
}
EOL
```

### 3. Create a Dedicated Update Script

Add a simple update script that preserves local configuration:

```bash
#!/bin/bash
# update.sh - Update blind control system while preserving local configuration

# Backup local configuration
if [ -f "local_config.json" ]; then
  echo "Backing up local configuration..."
  cp local_config.json local_config.backup.json
fi

# Update code from repository
echo "Updating code from repository..."
git pull

# Restore local configuration
if [ -f "local_config.backup.json" ]; then
  echo "Restoring local configuration..."
  mv local_config.backup.json local_config.json
fi

# Restart service
echo "Restarting service..."
systemctl restart blind_control
```

### 4. Add Update Management to the Hub Interface

Create a web interface in the hub to manage updates across all Pis:

```python
@app.route('/manage_updates', methods=['GET', 'POST'])
def manage_updates():
    config = load_config()
    update_results = {}
    
    if request.method == 'POST':
        # Process update request
        controllers_to_update = request.form.getlist('controllers')
        
        for index, controller in enumerate(config['controllers']):
            if str(index) in controllers_to_update:
                # SSH into the Pi and run update commands
                controller_ip = controller['url'].split('//')[1].split(':')[0]
                try:
                    # This requires SSH key-based authentication to be set up
                    result = subprocess.run([
                        'ssh', f'pi@{controller_ip}',
                        'cd /home/pi/blind_control && git pull && sudo systemctl restart blind_control'
                    ], capture_output=True, text=True, timeout=30)
                    
                    update_results[controller['name']] = {
                        'success': result.returncode == 0,
                        'output': result.stdout if result.returncode == 0 else result.stderr
                    }
                except Exception as e:
                    update_results[controller['name']] = {
                        'success': False,
                        'output': str(e)
                    }
    
    # Render template with controllers and update results
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Update Management</title>
        <!-- CSS styles here -->
    </head>
    <body>
        <h1>Blind Control Update Management</h1>
        
        <form action="/manage_updates" method="post">
            {% for index, controller in enumerate(config['controllers']) %}
            <div>
                <input type="checkbox" id="controller{{ index }}" name="controllers" value="{{ index }}">
                <label for="controller{{ index }}">{{ controller['name'] }} ({{ controller['url'] }})</label>
            </div>
            {% endfor %}
            
            <button type="submit">Update Selected</button>
        </form>
        
        {% if update_results %}
        <h2>Update Results</h2>
        {% for name, result in update_results.items() %}
        <div>
            <h3>{{ name }}</h3>
            <pre>{{ result['output'] }}</pre>
        </div>
        {% endfor %}
        {% endif %}
    </body>
    </html>
    ''', config=config, update_results=update_results, enumerate=enumerate)
```

## Immediate Fix for North Building Pi

To fix the current issue with the North Building Pi, we need to:

1. Update the h1 heading in main.py to match the title:
   ```html
   <h1>North Building Blinds Blind Control</h1>
   ```

2. Check for any other references to "South Building" that might need to be updated

## Next Steps

1. **Short-term**: Fix the h1 heading on the North Building Pi
2. **Medium-term**: Implement the configuration file approach to separate code from configuration
3. **Long-term**: Add update management to the hub interface for easier maintenance

## Implementation Plan

1. First, modify main.py to use configuration variables instead of hardcoded values
2. Create the local_config.json approach and update deploy.sh
3. Add the update.sh script to the repository
4. Add the update management interface to the hub
5. Update documentation
