# -*- coding: utf-8 -*-
import os
import glob
import time
import pygame
from pygame.locals import *

# Initialize Pygame
pygame.init()

# Set up display (adjust resolution to match your display)
screen = pygame.display.set_mode((1024, 600), pygame.FULLSCREEN)

# Set up fonts for title and temperature
title_font = pygame.font.Font(None, 120)  # Larger font for the title
font = pygame.font.Font(None, 150)        # Font for temperature

# Define colors (using RGB values)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
TITLE_COLOR = (255, 215, 0)  # Gold color for title

# Initialize temperature sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# Function to read raw temperature data from the sensor
def read_temp_raw():
    with open(device_file, 'r') as f:
        lines = f.readlines()
    return lines

# Function to extract the temperature in Celsius and Fahrenheit
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f
    return None, None

# Load and scale the icon
try:
    # Load an icon image if you have one (example path given)
    icon = pygame.image.load('/home/PhotoRX/Downloads/Tempicon.png')  # Replace with actual icon path
    icon = pygame.transform.scale(icon, (100, 250))  # Smaller dimensions for better fit
except:
    # Fallback: use a degree symbol rendered as text if the image is not found
    icon = font.render("\u00B0", True, WHITE)

# Main loop to display temperature continuously
running = True
while running:
    # Event handling to exit on ESC key press
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:  # Exit on pressing ESC
                running = False

    # Read temperature
    temperature_celsius, temperature_fahrenheit = read_temp()

    # Fill the screen with a color (black)
    screen.fill((0, 0, 0))

    # Render and display the title centered
    title_text = title_font.render("PhotoScale", True, TITLE_COLOR)
    title_rect = title_text.get_rect(center=(screen.get_width() // 2, 60))  # Adjust vertical position
    screen.blit(title_text, title_rect)

    # Display the scaled temperature icon to the right of temperature values
    icon_x = 580  # Updated X-coordinate for positioning to the right of temperature
    icon_y = 150  # Updated Y-coordinate for centering vertically with text
    screen.blit(icon, (icon_x, icon_y))  # Position the icon in the desired area

    # Create the text surfaces with custom colors
    temp_c_text = font.render(f'{temperature_celsius:.2f} \u00B0C', True, RED)  # Red for Celsius
    temp_f_text = font.render(f'{temperature_fahrenheit:.2f} \u00B0F', True, BLUE)  # Blue for Fahrenheit

    # Display the temperature texts on the screen at specified positions
    screen.blit(temp_c_text, (100, 150))  # Adjust coordinates as needed
    screen.blit(temp_f_text, (100, 300))  # Adjust coordinates as needed

    # Update the display
    pygame.display.flip()

    # Delay to control the update rate (e.g., 1 second between readings)
    time.sleep(1)

# Quit Pygame on exit
pygame.quit()