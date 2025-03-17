from flask import Flask, render_template_string, redirect, url_for
import time
import threading
import sys
import os

# Flag to check if we should use GPIO
use_gpio = True
gpio_error = None

try:
    import RPi.GPIO as GPIO
    
    REMOTE_POWER_PIN = 4
    BUTTON_PINS = {
        "Up": 21,
        "Stop": 24,
        "Down": 16,
        "Channel Up": 12,
        "Channel Down": 25
    }

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(REMOTE_POWER_PIN, GPIO.OUT)
    GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)

    for pin in BUTTON_PINS.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
except Exception as e:
    use_gpio = False
    gpio_error = str(e)
    print(f"GPIO Error: {gpio_error}")
    print("Running in demo mode without GPIO functionality")
    # Create dummy values for demo mode
    REMOTE_POWER_PIN = 0
    BUTTON_PINS = {
        "Up": 0,
        "Stop": 0,
        "Down": 0,
        "Channel Up": 0,
        "Channel Down": 0
    }

app = Flask(__name__)
remote_on = False

@app.route('/')
def index():
    status_link = '<p><a href="/status">View System Status</a></p>'
    demo_mode_warning = ''
    if not use_gpio:
        demo_mode_warning = '<div style="background-color: #ffcccc; padding: 10px; margin: 10px 0; border-radius: 5px;"><strong>Warning:</strong> Running in demo mode without GPIO functionality. GPIO operations will be simulated.</div>'
    
    return render_template_string('''
    <h1>Remote Control Web Interface</h1>
    {{ demo_mode_warning|safe }}
    <form action="/toggle_remote" method="post">
        <button type="submit">Power</button>
    </form>
    <p><strong>Current Remote State:</strong> {{ 'ON' if remote_on else 'OFF' }}</p>
    <br>
    {% for name in button_names %}
        <form action="/press/{{ name }}" method="post">
            <button type="submit">Press {{ name }}</button>
        </form>
    {% endfor %}
    {{ status_link|safe }}
    ''', button_names=BUTTON_PINS.keys(), remote_on=remote_on, demo_mode_warning=demo_mode_warning, status_link=status_link)

@app.route('/toggle_remote', methods=['POST'])
def toggle_remote():
    global remote_on
    if not use_gpio:
        # In demo mode, just toggle the state
        remote_on = not remote_on
        return redirect(url_for('index'))
        
    if remote_on:
        GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)
        remote_on = False
    else:
        for pin in BUTTON_PINS.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.output(REMOTE_POWER_PIN, GPIO.HIGH)
        remote_on = True
    return redirect(url_for('index'))

@app.route('/press/<button_name>', methods=['POST'])
def press_button(button_name):
    if not use_gpio:
        # In demo mode, just acknowledge the button press
        return redirect(url_for('index'))
        
    if remote_on and button_name in BUTTON_PINS:
        def press_release():
            pin = BUTTON_PINS[button_name]
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(1)  # 1 second press
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        threading.Thread(target=press_release).start()
    return redirect(url_for('index'))

@app.route('/cleanup')
def cleanup():
    if not use_gpio:
        return "Running in demo mode, no GPIO to clean up."
        
    GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)
    for pin in BUTTON_PINS.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.cleanup()
    return "GPIO Cleaned up."

@app.route('/status')
def status():
    return render_template_string('''
    <h1>System Status</h1>
    <p><strong>GPIO Mode:</strong> {{ "Active" if use_gpio else "Demo (Disabled)" }}</p>
    {% if not use_gpio %}
    <p><strong>GPIO Error:</strong> {{ gpio_error }}</p>
    {% endif %}
    <p><strong>Remote State:</strong> {{ 'ON' if remote_on else 'OFF' }}</p>
    <p><strong>SSL Certificates:</strong> {{ "Found" if ssl_found else "Not Found" }}</p>
    <a href="/">Back to Control Panel</a>
    ''', use_gpio=use_gpio, gpio_error=gpio_error, remote_on=remote_on, 
        ssl_found=os.path.exists('/home/sttark/Desktop/ssl/cert.pem') and os.path.exists('/home/sttark/Desktop/ssl/key.pem'))

if __name__ == '__main__':
    # Check for command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Remote Control Web Interface')
    parser.add_argument('--http', action='store_true', help='Run in HTTP mode (no SSL)')
    args = parser.parse_args()
    
    # Check if SSL certificates exist
    cert_path = '/home/sttark/Desktop/ssl/cert.pem'
    key_path = '/home/sttark/Desktop/ssl/key.pem'
    
    if args.http or not (os.path.exists(cert_path) and os.path.exists(key_path)):
        print("Running in HTTP mode (no SSL).")
        print("Warning: You will see security warnings when submitting forms.")
        app.run(host='0.0.0.0', port=5000)
    else:
        print(f"Using SSL certificates from {cert_path} and {key_path}")
        # Use ssl_context='adhoc' for a temporary self-signed certificate that works with any hostname
        app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')
