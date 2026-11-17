#!/bin/bash
# Load one-wire modules
sleep 7 

sudo modprobe -r w1_gpio w1_therm
sudo modprobe w1_gpio w1_therm w1_master_timeout=7


# Wait for sensors to stabilize
sleep 7  # Adjust the delay time as necessary

# Start the Python script
/usr/bin/python3 /home/photorx2/TempUI8.py
