# Simple Controller Deployment

The easiest way to set up new blind controllers.

## 🚀 **Quick Setup Process**

### **Step 1: Clone Repository (On New Pi)**
```bash
cd /home/sttark
git clone https://github.com/Sttark/blind_control.git
cd blind_control
```

### **Step 2: Start Controller**
```bash
./start_controller.sh
```

The script will:
- ✅ Install dependencies
- ✅ Set up systemd service
- ✅ Start the controller
- ✅ Show you the IP address and next steps

### **Step 3: Add to Hub (From Hub Admin)**
1. Go to hub admin: `http://192.168.4.202:5001`
2. Click "Add New Controller"
3. Fill in the form:
   - **Name**: `North Blind Control` (or whatever you want)
   - **URL**: `http://[pi-ip]:5000/` (from Step 2 output)
   - **Description**: `Blinds for [location]`
4. Click "Add Controller"

### **Done!** 🎉

---

## 📋 **Complete Example**

### **On New Pi:**
```bash
cd /home/sttark
git clone https://github.com/Sttark/blind_control.git
cd blind_control
./start_controller.sh
```

**Output shows:**
```
Controller Information:
  IP Address: 192.168.194.203
  Web Interface: http://192.168.194.203:5000
  
Ready to be added to hub at: http://192.168.194.203:5000/
```

### **In Hub Admin Panel:**
- **Name**: `East Building Controller`
- **URL**: `http://192.168.194.203:5000/`
- **Description**: `Controls for East Building blinds`

---

## ✅ **Advantages of This Approach**

### **Simple & Intuitive**
- **No SSH complexity** - direct setup on target Pi
- **Visual feedback** - use the hub admin interface you already know
- **Clear workflow** - clone, start, add via web interface

### **Flexible**
- **Name controllers** whatever makes sense to you
- **See IP addresses** clearly before adding to hub
- **Test controllers** before adding them

### **Reliable**
- **No network dependencies** between Pis during setup
- **Self-contained** - each Pi configures itself
- **Version controlled** - all code from GitHub

---

## 🔧 **What Gets Created**

### **On New Pi:**
- Controller service running on port 5000
- Default configuration (will be managed by hub)
- Systemd service for auto-start

### **In Hub:**
- New controller entry in admin panel
- Ability to control and schedule the new controller
- Unified dashboard access

---

## 🛠 **Troubleshooting**

### **If start_controller.sh Fails:**
```bash
# Check dependencies
pip3 list | grep -E "(flask|RPi|astral|schedule|requests)"

# Check if port 5000 is free
sudo netstat -tlnp | grep :5000

# Check service logs
sudo journalctl -u blind_control_controller --no-pager
```

### **If Controller Doesn't Appear in Hub:**
1. Verify controller is running: `http://[pi-ip]:5000`
2. Check hub can reach controller IP
3. Ensure URL in hub admin has trailing slash: `http://[pi-ip]:5000/`

### **To Update Controller:**
```bash
cd /home/sttark/blind_control
git pull
sudo systemctl restart blind_control_controller
```

---

## 🎯 **This Workflow vs Others**

### **vs SSH Deployment**
- ❌ SSH: Complex setup, network dependencies, failure points
- ✅ This: Simple clone and start, no SSH needed

### **vs Manual Configuration**
- ❌ Manual: Need to create config files, remember settings
- ✅ This: Automatic setup, configure via familiar web interface

### **vs Auto-Discovery**
- ❌ Auto-discovery: Complex implementation, harder to debug
- ✅ This: Simple and explicit, you control when controllers are added

---

This approach gives you the best of both worlds: simple setup with the familiar hub admin interface for management!
