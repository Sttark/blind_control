from flask import Flask, render_template_string, redirect, url_for, request, jsonify
import os
import json

app = Flask(__name__)

# Configuration file path
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

# Load blind controllers configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        # Default configuration
        return {
            "controllers": [
                {
                    "name": "South Building",
                    "url": "http://192.168.4.202:5000/",
                    "description": "Controls for South Building blinds"
                }
            ]
        }

# Save configuration
def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

@app.route('/')
def index():
    config = load_config()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Blind Control Hub</title>
        <style>
            * {
                box-sizing: border-box;
                font-family: Arial, sans-serif;
            }
            body {
                margin: 0;
                padding: 16px;
                background-color: #f5f5f5;
                max-width: 800px;
                margin: 0 auto;
            }
            h1 {
                text-align: center;
                color: #333;
                font-size: 28px;
                margin-bottom: 20px;
            }
            .controller-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .controller-card {
                background-color: #fff;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: transform 0.3s, box-shadow 0.3s;
                cursor: pointer;
                text-decoration: none;
                color: inherit;
                display: block;
            }
            .controller-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .controller-card h2 {
                margin-top: 0;
                color: #2196F3;
                font-size: 20px;
            }
            .controller-card p {
                color: #666;
                margin-bottom: 0;
            }
            .admin-panel {
                background-color: #fff;
                border-radius: 8px;
                padding: 20px;
                margin-top: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .admin-panel h2 {
                margin-top: 0;
                color: #333;
                font-size: 20px;
            }
            .admin-toggle {
                background-color: #673AB7;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
                text-align: left;
                margin-bottom: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .admin-toggle:hover {
                background-color: #5E35B1;
            }
            .admin-toggle:after {
                content: "▼";
                font-size: 12px;
            }
            .admin-toggle.active:after {
                content: "▲";
            }
            .admin-content {
                display: none;
                padding: 15px;
                background-color: #f9f9f9;
                border-radius: 8px;
                margin-bottom: 15px;
            }
            .admin-content.show {
                display: block;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input[type="text"] {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 15px;
                font-size: 16px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            button:hover {
                background-color: #45a049;
            }
            .controller-list {
                margin-top: 20px;
            }
            .controller-item {
                background-color: #f9f9f9;
                border-radius: 4px;
                padding: 15px;
                margin-bottom: 10px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .controller-item-info {
                flex: 1;
            }
            .controller-item-actions {
                display: flex;
                gap: 10px;
            }
            .edit-btn {
                background-color: #2196F3;
            }
            .edit-btn:hover {
                background-color: #1976D2;
            }
            .delete-btn {
                background-color: #f44336;
            }
            .delete-btn:hover {
                background-color: #d32f2f;
            }
        </style>
        <script>
            function toggleAdminPanel() {
                const content = document.getElementById('adminContent');
                const button = document.getElementById('adminToggle');
                content.classList.toggle('show');
                button.classList.toggle('active');
            }
            
            function editController(index) {
                const controllers = {{ config|tojson }}.controllers;
                const controller = controllers[index];
                
                document.getElementById('editIndex').value = index;
                document.getElementById('editName').value = controller.name;
                document.getElementById('editUrl').value = controller.url;
                document.getElementById('editDescription').value = controller.description;
                
                document.getElementById('editForm').style.display = 'block';
                document.getElementById('addForm').style.display = 'none';
            }
            
            function cancelEdit() {
                document.getElementById('editForm').style.display = 'none';
                document.getElementById('addForm').style.display = 'block';
            }
        </script>
    </head>
    <body>
        <h1>Blind Control Hub</h1>
        
        <div class="controller-grid">
            {% for controller in config['controllers'] %}
            <a href="{{ controller['url'] }}" class="controller-card">
                <h2>{{ controller['name'] }}</h2>
                <p>{{ controller['description'] }}</p>
            </a>
            {% endfor %}
        </div>
        
        <div class="admin-panel">
            <button id="adminToggle" class="admin-toggle" onclick="toggleAdminPanel()">
                Admin Settings
            </button>
            
            <div id="adminContent" class="admin-content">
                <div id="addForm">
                    <h3>Add New Controller</h3>
                    <form action="/add_controller" method="post">
                        <div class="form-group">
                            <label for="name">Name:</label>
                            <input type="text" id="name" name="name" required placeholder="e.g., North Building">
                        </div>
                        <div class="form-group">
                            <label for="url">URL:</label>
                            <input type="text" id="url" name="url" required placeholder="e.g., http://192.168.4.203:5000/">
                        </div>
                        <div class="form-group">
                            <label for="description">Description:</label>
                            <input type="text" id="description" name="description" placeholder="e.g., Controls for North Building blinds">
                        </div>
                        <button type="submit">Add Controller</button>
                    </form>
                </div>
                
                <div id="editForm" style="display: none;">
                    <h3>Edit Controller</h3>
                    <form action="/edit_controller" method="post">
                        <input type="hidden" id="editIndex" name="index">
                        <div class="form-group">
                            <label for="editName">Name:</label>
                            <input type="text" id="editName" name="name" required>
                        </div>
                        <div class="form-group">
                            <label for="editUrl">URL:</label>
                            <input type="text" id="editUrl" name="url" required>
                        </div>
                        <div class="form-group">
                            <label for="editDescription">Description:</label>
                            <input type="text" id="editDescription" name="description">
                        </div>
                        <button type="submit">Save Changes</button>
                        <button type="button" onclick="cancelEdit()" style="background-color: #999;">Cancel</button>
                    </form>
                </div>
                
                <div class="controller-list">
                    <h3>Manage Controllers</h3>
                    {% for controller in config['controllers'] %}
                    <div class="controller-item">
                        <div class="controller-item-info">
                            <strong>{{ controller['name'] }}</strong><br>
                            <small>{{ controller['url'] }}</small>
                        </div>
                        <div class="controller-item-actions">
                            <button class="edit-btn" onclick="editController({{ loop.index0 }})">Edit</button>
                            <form action="/delete_controller" method="post" style="display: inline;">
                                <input type="hidden" name="index" value="{{ loop.index0 }}">
                                <button type="submit" class="delete-btn" onclick="return confirm('Are you sure you want to delete this controller?')">Delete</button>
                            </form>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', config=config)

@app.route('/add_controller', methods=['POST'])
def add_controller():
    name = request.form.get('name')
    url = request.form.get('url')
    description = request.form.get('description', '')
    
    if not name or not url:
        return "Name and URL are required", 400
    
    config = load_config()
    config['controllers'].append({
        'name': name,
        'url': url,
        'description': description
    })
    save_config(config)
    
    return redirect(url_for('index'))

@app.route('/edit_controller', methods=['POST'])
def edit_controller():
    index = int(request.form.get('index'))
    name = request.form.get('name')
    url = request.form.get('url')
    description = request.form.get('description', '')
    
    if not name or not url:
        return "Name and URL are required", 400
    
    config = load_config()
    if 0 <= index < len(config['controllers']):
        config['controllers'][index] = {
            'name': name,
            'url': url,
            'description': description
        }
        save_config(config)
    
    return redirect(url_for('index'))

@app.route('/delete_controller', methods=['POST'])
def delete_controller():
    index = int(request.form.get('index'))
    
    config = load_config()
    if 0 <= index < len(config['controllers']):
        del config['controllers'][index]
        save_config(config)
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Create config file if it doesn't exist
    if not os.path.exists(CONFIG_FILE):
        save_config(load_config())
    
    print("Running Blind Control Hub on port 5001")
    app.run(host='0.0.0.0', port=5001)
