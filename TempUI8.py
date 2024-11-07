# -*- coding: utf-8 -*-
import os
import glob
import time
import pygame
from pygame.locals import *

# Initialize Pygame
pygame.init()

# Hide the mouse cursor
pygame.mouse.set_visible(False)

# Set up display (adjust resolution to match your display)
screen = pygame.display.set_mode((1024, 600), pygame.FULLSCREEN)

# Set up fonts for title and temperature
title_font = pygame.font.Font(None, 100)  # Font for the title
temp_font = pygame.font.Font(None, 60)   # Font for temperature
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
    with open(device_file, 'r') as f:
        lines = f.readlines()
    return lines

# Function to extract the temperature in Celsius
def read_temp(device_file):
    lines = read_temp_raw(device_file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(device_file)
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
    icon = pygame.transform.scale(icon, (160, 220))
except:
    icon = temp_font.render("\u00B0", True, WHITE)

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
        elif event.type == MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            for button in buttons:
                if button.is_clicked(pos):
                    button.highlight()
                    button.action()

        elif event.type == MOUSEBUTTONUP:
            for button in buttons:
                button.reset_color()

    # Fill the screen with a color (black)
    screen.fill((0, 0, 0))

    # Draw side buttons on the left side
    for button in buttons:
        button.draw(screen)

    # Display the current screen based on current_screen variable
    if current_screen == "temperature":
        # Temperature screen
        title_text = title_font.render("PhotoScale", True, TITLE_COLOR)
        title_rect = title_text.get_rect(center=(screen.get_width() // 2, 50))
        screen.blit(title_text, title_rect)

        # Display temperature data for each sensor in two columns
        left_x = 140
        right_x = 410
        y_start = 130
        y_offset = 80  # Space between sensor readings

        for idx, device_file in enumerate(device_files):
            temp_c = read_temp(device_file)
            temp_c_text = temp_font.render(f'R{idx+1}: {temp_c:.2f}\u00B0C', True, RED)
            x_position = left_x if idx < 4 else right_x
            y_position = y_start + (idx % 4) * y_offset
            screen.blit(temp_c_text, (x_position, y_position))

        # Temperature icon remains on the right
        screen.blit(icon, (650, 140))

    elif current_screen == "settings":
        # Settings screen
        settings_title = title_font.render("Settings", True, TITLE_COLOR)
        settings_rect = settings_title.get_rect(center=(screen.get_width() // 2, 60))
        screen.blit(settings_title, settings_rect)

        # Placeholder settings information
        setting_text_1 = settings_font.render("Right Reactor: Intensity", True, WHITE)
        setting_text_2 = settings_font.render("Left Reactor: Intensity", True, WHITE)
        screen.blit(setting_text_1, (200, 200))
        screen.blit(setting_text_2, (200, 300))

    # Update the display
    pygame.display.flip()
    time.sleep(0.05)  # Adjust refresh rate

# Quit Pygame on exit
pygame.quit()
