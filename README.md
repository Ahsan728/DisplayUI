
# PhotoScale
PhotoScale is a full-screen graphical control panel designed for Raspberry Pi-based systems, built using Pygame. It integrates live temperature readings from DS18B20 sensors and provides intuitive slider and switch controls to adjust connected PWM outputs via GPIO pins. This makes it suitable for controlling devices such as photo-reactors, heaters, lights, or similar lab equipment.

**Developer:** Ahsan  
**Version:** 1.0.7  
**GitHub:** [github.com/PhotoRX](https://github.com/PhotoRX)  
**Email:** photorx@iciq.es


## Features
- Full-Screen GUI: Designed for 1024x600 touchscreen displays.
- Live Temperature Monitoring: Reads data from up to 8 DS18B20 1-Wire temperature sensors.
- PWM Control: Adjust intensity (0–100%) for up to 4 connected devices using sliders.
- On/Off Switches: Toggle GPIO outputs independently.
- Developer Info Screen: Displays developer logos and contact information.
- Custom Icons & Logos: Menu buttons and logos are user-specified.

## Software Dependencies
Make sure the following Python packages are installed:

```bash
sudo apt-get update
sudo apt-get install python3-pygame python3-rpi.gpio
```
Or via pip:

```bash
pip3 install pygame RPi.GPIO
```
Enable the 1-Wire interface for the DS18B20 sensors:
```bash
sudo raspi-config
# Navigate to Interface Options > 1-Wire > Enable
```
## Other Configurations
**Cofigure Nano file :**
```bash
sudo nano /boot/config.txt

```
**Write this line in nano**
```makefile
dtoverlay=w1-gpio,gpiopin=4

```
**Reload Modules**
```bash
sudo modprobe -r w1_therm
sudo modprobe -r w1_gpio
sudo modprobe w1_gpio
sudo modprobe w1_therm

```
**Check Sensor Address**: 
```bash
cd /sys/bus/w1/devices
ls

```
Now change directory to DS18B20 sensor
```shell
cd 28-00000f3fd9a2
```
 **cat** command to read the contents of the w1_slave file.
```shell
cat w1_slave
```
## Tutorial
https://randomnerdtutorials.com/raspberry-pi-ds18b20-python/

## File Structure
Ensure the image files exist at the specified paths of Raspberry Pi:
```css
PhotoScaleDisplay/
├── Image Files/
│   ├── menu.png
│   ├── sett2.png
│   └── Dev.png
│   └── ICIQ.png
│   └── JLFlab.png
├── TempUI8.py
├── TempUI8.service
├── init_sensors.sh
├── test.py
```
Our main executable python script is `TempUI8.py`, and it will be automatically runned through a service routine file `TempUI8.service`.
`init_sensors.sh` file is for initializing the one wire sensors. And `test.py` is an optional python file, we just kept it for doing some test of execution, so that the main TempUI.py file does not affect. 


# Application Structure
**Screens:**
1. Temperature Screen
- Displays real-time readings from temperature sensors.

2. Settings Screen
- Allows slider-based control of PWM devices.
- Toggle switches for enabling/disabling outputs.

3. Developer Screen
- Displays logos and contact information.

**Components:**
- Sliders: Adjust intensity (PWM) from 0 to 100%.
- Toggle Switches: Enable or disable each output.
- Buttons: Navigate between screens using touch or mouse.


## Sensor Initialization Script
Before launching the UI, 1-Wire temperature sensors must be initialized properly. Use the init_sensors.sh script:
Already initialized in a service file automatically.
`init_sensors.sh`

```bash
#!/bin/bash
# Load one-wire modules
sleep 7

sudo modprobe -r w1_gpio w1_therm
sudo modprobe w1_gpio w1_therm w1_master_timeout=7

# Wait for sensors to stabilize
sleep 7  # Adjust delay if needed

# Start the Python application
/usr/bin/python3 /home/photorx2/TempUI8.py
```
Make it executable:
```bash
chmod +x /home/photorx2/init_sensors.sh
```

## Auto-Start on Boot Using `systemd`

Create a systemd service file so the app starts on boot.
Create the Service File:
`TempUI8.service`

```bash
[Unit]
Description=PhotoScale Temperature Monitoring Script
After=multi-user.target

[Service]
Environment="DISPLAY=:0"
Environment="XDG_RUNTIME_DIR=/run/user/1000"
ExecStart=/home/photorx2/init_sensors.sh
WorkingDirectory=/home/photorx2
StandardOutput=inherit
StandardError=inherit
Restart=always
User=photorx2

[Install]
WantedBy=multi-user.target
```

**Debugging**
- Enable and Start the Service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable TempUI8.service
sudo systemctl start TempUI8.service
```
Check status:
```bash
sudo systemctl status TempUI8.service
```
To stop the service:
```bash
sudo systemctl stop TempUI8.service
```
use `journalctl` to view the logs:
```bash
journalctl -u TempUI8.service

```
```bash
sudo systemctl restart TempUI8.service
sudo systemctl status TempUI8.service

```

## Finalized Version Till NOW

![image](https://github.com/user-attachments/assets/5ccbd0d0-11b8-4ecd-a4a4-132ef6975022)
![image](https://github.com/user-attachments/assets/50b7b608-33de-474c-bb66-9dd05f00d3ee)
![image](https://github.com/user-attachments/assets/7e09a182-4916-4f64-b276-1e1a274806b5)



## Notes
- The app runs in full-screen mode with the mouse cursor hidden for better touchscreen UX.
- Each slider only affects the GPIO output when its corresponding switch is ON.
- If a sensor is unresponsive, the display shows "N/A" instead of a temperature.
- Temperature readings are automatically refreshed every second.


## Troubleshooting
- No sensors detected: Ensure DS18B20 sensors are connected correctly and 1-Wire is enabled.
- GUI not launching: Check if Pygame is installed correctly. Use python3 and not python.
- GPIO errors: Make sure to run the script with appropriate permissions:

## Development & Simulation (Windows)
If you're developing on Windows, the script includes a **GPIO simulation** block. It mocks the `RPi.GPIO` library so the application can run without actual hardware.

Here's what it does:
- Bypasses real GPIO control
- Allows `TempUI8.py` to be executed and tested on Windows
- Prints: `Running on Windows: Using Mock GPIO for simulation`

This is useful for testing UI changes without needing to upload to a Raspberry Pi every time. Just add the following lines top of your script :

```bash
import sys

# Mock RPi.GPIO for Windows
if sys.platform == 'win32':
    import types

    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT"
        IN = "IN"
        HIGH = "HIGH"
        LOW = "LOW"
        
        def setmode(self, mode): pass
        def setup(self, pin, mode): pass
        def output(self, pin, state): pass
        def PWM(self, pin, frequency): return self.MockPWM()
        def cleanup(self): pass
        
        class MockPWM:
            def start(self, duty_cycle): pass
            def ChangeDutyCycle(self, duty_cycle): pass
            def stop(self): pass

    # Create a mock module and insert it into sys.modules
    sys.modules['RPi'] = types.ModuleType("RPi")
    sys.modules['RPi.GPIO'] = MockGPIO()
    
    print("Running on Windows: Using Mock GPIO for simulation")
else:
    import RPi.GPIO as GPIO  # Use real GPIO on Raspberry Pi
    
```
**Note** : During the simulation and test in windows, replace the logo and image file paths properly.
(i.e : `Image Files/ICIQ.png`) and so on. But during the Raspberry pi upload use the path like this `/home/photorx2/Downloads/ICIQ.png`

## License
MIT License
© 2025 JLF Lab, ICIQ




