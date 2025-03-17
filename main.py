from flask import Flask, render_template_string, redirect, url_for
import RPi.GPIO as GPIO
import time
import threading

app = Flask(__name__)

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

remote_on = False

@app.route('/')
def index():
    return render_template_string('''
    <h1>Remote Control Web Interface</h1>
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
    ''', button_names=BUTTON_PINS.keys(), remote_on=remote_on)

@app.route('/toggle_remote', methods=['POST'])
def toggle_remote():
    global remote_on
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
    GPIO.output(REMOTE_POWER_PIN, GPIO.LOW)
    for pin in BUTTON_PINS.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.cleanup()
    return "GPIO Cleaned up."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
