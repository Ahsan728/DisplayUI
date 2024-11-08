# -*- coding: utf-8 -*-
import os
import glob
import time
import threading
import pygame
from pygame.locals import *

# Initialize Pygame
pygame.init()

# Hide the mouse cursor
pygame.mouse.set_visible(False)

# Set up display
screen = pygame.display.set_mode((1024, 600), pygame.FULLSCREEN)

# Set up fonts for title and temperature
title_font = pygame.font.Font(None, 120)  # Font for the title
temp_font = pygame.font.Font(None, 60)    # Font for temperature
settings_font = pygame.font.Font(None, 40)  # Smaller font for Settings screen text

# Define colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
TITLE_COLOR = (255, 215, 0)  # Gold color for title
BUTTON_HIGHLIGHT = (0, 180, 180)  # Highlight color for buttons on touch

# Initialize temperature sensors
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folders = glob.glob(base_dir + '28*')  # Detect all devices starting with '28'
device_files = [folder + '/w1_slave' for folder in device_folders]

# Function to read raw temperature data from a sensor
def read_temp_raw(device_file):
    try:
        with open(device_file, 'r') as f:
            lines = f.readlines()
        return lines
    except (FileNotFoundError, IOError):
        return []  # Return an empty list if the file cannot be read

# Function to extract the temperature in Celsius
def read_temp(device_file):
    lines = read_temp_raw(device_file)
    if len(lines) < 2:  # Ensure there are at least 2 lines
        return None  # Return None if data is incomplete or corrupted
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(device_file)
        if len(lines) < 2:  # Re-check after reading again
            return None
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c
    return None

# Define button class
class Button:
    def __init__(self, image_path, x, y, width, height, action):
        self.image = pygame.image.load(image_path) if image_path else None
        if self.image:
            self.image = pygame.transform.scale(self.image, (width, height))
        self.rect = pygame.Rect(x, y, width, height)
        self.action = action
        self.highlighted = False

    def draw(self, screen):
        if self.highlighted:
            pygame.draw.rect(screen, BUTTON_HIGHLIGHT, self.rect, border_radius=10)
        if self.image:
            screen.blit(self.image, self.rect.topleft)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def highlight(self):
        self.highlighted = True

    def reset_color(self):
        self.highlighted = False

# Define slider class
class Slider:
    def __init__(self, x, y, width, min_val, max_val, value, label):
        self.rect = pygame.Rect(x, y, width, 20)
        self.knob_rect = pygame.Rect(x + (value / max_val) * width - 10, y - 10, 20, 40)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.label = label
        self.dragging = False

    def draw(self, screen):
        pygame.draw.line(screen, WHITE, (self.rect.x, self.rect.y + 10), 
                         (self.rect.x + self.rect.width, self.rect.y + 10), 4)
        pygame.draw.rect(screen, WHITE, self.knob_rect)
        label_text = settings_font.render(f"{self.label}: {int(self.value)}", True, WHITE)
        screen.blit(label_text, (self.rect.x, self.rect.y - 40))

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and self.knob_rect.collidepoint(event.pos):
            self.dragging = True
        elif event.type == MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == MOUSEMOTION and self.dragging:
            new_x = max(self.rect.x, min(event.pos[0], self.rect.x + self.rect.width))
            self.knob_rect.x = new_x - 10
            self.value = (new_x - self.rect.x) / self.rect.width * (self.max_val - self.min_val)

# Define actions for each button
def show_temperature_screen():
    global current_screen
    current_screen = "temperature"

def show_settings_screen():
    global current_screen
    current_screen = "settings"

# Initialize buttons with icons
buttons = [
    Button("/home/PhotoRX/Downloads/menu.png", 22, 150, 88, 90, show_temperature_screen),  # Home Icon
    Button("/home/PhotoRX/Downloads/sett2.png", 22, 270, 88, 90, show_settings_screen),  # Settings Icon
]

# Load and scale the temperature icon
try:
    icon = pygame.image.load('/home/PhotoRX/Downloads/Tempicon32.png')
    icon = pygame.transform.scale(icon, (180, 210))
except:
    icon = temp_font.render("\u00B0", True, WHITE)


# Load and scale the temperature icon
try:
    icon2 = pygame.image.load('/home/PhotoRX/Downloads/Brightness1.png')
    icon2 = pygame.transform.scale(icon2, (135, 150))
except:
    icon2 = temp_font.render("\u00B0", True, WHITE)


# Sensor data management
sensor_data = [None] * len(device_files)

def sensor_thread():
    """Thread to continuously read temperature data from sensors."""
    while True:
        for idx, device_file in enumerate(device_files):
            sensor_data[idx] = read_temp(device_file)
        time.sleep(1)  # Adjust to reduce CPU usage

# Start sensor reading thread
threading.Thread(target=sensor_thread, daemon=True).start()

# Initialize sliders
sliders = [
    Slider(200, 190, 400, 0, 100, 0, "Right Reactor"),
    Slider(200, 270, 400, 0, 100, 0, "Left Reactor"),
    Slider(200, 350, 400, 0, 100, 0, "Top Reactor"),
    Slider(200, 430, 400, 0, 100, 0, "Bottom Reactor"),
]

# Main loop to display screens
current_screen = "temperature"  # Start with the temperature screen
running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
        elif event.type in (MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP):
            for button in buttons:
                if event.type == MOUSEBUTTONDOWN and button.is_clicked(event.pos):
                    button.highlight()
                    button.action()
                elif event.type == MOUSEBUTTONUP:
                    button.reset_color()
            if current_screen == "settings":
                for slider in sliders:
                    slider.handle_event(event)

    # Fill the screen with a color (black)
    screen.fill((0, 0, 0))

    # Draw side buttons on the left side
    for button in buttons:
        button.draw(screen)

    # Display the current screen based on current_screen variable
    if current_screen == "temperature":
        # Temperature screen
        title_text = title_font.render("PhotoScale", True, TITLE_COLOR)
        title_rect = title_text.get_rect(center=(screen.get_width() // 2, 60))
        screen.blit(title_text, title_rect)

        # Display temperature data for each sensor
        left_x, right_x = 140, 410  # Left and right alignment
        y_start = 140  # Start position for sensor data
        y_gap = 80  # Gap between each sensor

        for idx in range(4):  # First 4 sensors on the left
            temp_c = sensor_data[idx]
            temp_display = f'{temp_c:.2f} \u00B0C' if temp_c is not None else 'N/A'
            temp_c_text = temp_font.render(f'R{idx+1}: {temp_display}', True, RED)
            screen.blit(temp_c_text, (left_x, y_start + idx * y_gap))

        for idx in range(4, 8):  # Next 4 sensors on the right
            temp_c = sensor_data[idx]
            temp_display = f'{temp_c:.2f} \u00B0C' if temp_c is not None else 'N/A'
            temp_c_text = temp_font.render(f'R{idx+1}: {temp_display}', True, RED)
            screen.blit(temp_c_text, (right_x, y_start + (idx - 4) * y_gap))

        # Display the temperature icon
        icon_x = 630
        screen.blit(icon, (icon_x, 150))

    elif current_screen == "settings":
        # Settings screen
        settings_title = title_font.render("Settings", True, TITLE_COLOR)
        settings_rect = settings_title.get_rect(center=(screen.get_width() // 2, 60))
        screen.blit(settings_title, settings_rect)

        # Draw sliders
        for slider in sliders:
            slider.draw(screen)

        # Draw the new icon in the desired position (to the right of the sliders)
        icon2_x = 640
        screen.blit(icon2, (icon2_x, 125))

            

    # Update the display
    pygame.display.flip()
    time.sleep(0.1)  # Adjust refresh rate

# Quit Pygame on exit
pygame.quit()
