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

# Set up fonts for title, temperature, and smaller side buttons
title_font = pygame.font.Font(None, 120)  # Font for the title
temp_font = pygame.font.Font(None, 150)   # Font for temperature
button_font = pygame.font.Font(None, 30)  # Smaller font for side buttons
settings_font = pygame.font.Font(None, 60)  # Smaller font for Settings screen text

# Define colors (using RGB values)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
TITLE_COLOR = (255, 215, 0)  # Gold color for title
BUTTON_COLOR = (0, 128, 128)  # Base color for side buttons
BUTTON_HIGHLIGHT = (0, 180, 180)  # Highlight color for buttons on touch

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

# Define button class
class Button:
    def __init__(self, text, x, y, width, height, action):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.action = action
        self.color = BUTTON_COLOR

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=10)
        label = button_font.render(self.text, True, WHITE)
        label_rect = label.get_rect(center=self.rect.center)
        screen.blit(label, label_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def highlight(self):
        self.color = BUTTON_HIGHLIGHT

    def reset_color(self):
        self.color = BUTTON_COLOR

# Define actions for each button
def show_temperature_screen():
    global current_screen
    current_screen = "temperature"

def show_settings_screen():
    global current_screen
    current_screen = "settings"

# Initialize smaller buttons
buttons = [
    Button("Home", 20, 100, 100, 50, show_temperature_screen),
    Button("Settings", 20, 180, 100, 50, show_settings_screen),
]

# Load and scale the icon
try:
    icon = pygame.image.load('/home/PhotoRX/Downloads/Tempicon.png')  # Replace with actual icon path
    icon = pygame.transform.scale(icon, (100, 220))  # Smaller dimensions for better alignment
except:
    icon = temp_font.render("\u00B0", True, WHITE)  # Fallback: use degree symbol if image is missing

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
                    button.highlight()  # Highlight button when clicked
                    button.action()  # Perform the button's action

        elif event.type == MOUSEBUTTONUP:
            for button in buttons:
                button.reset_color()  # Reset button color after release

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

        # Display temperature data
        temperature_celsius, temperature_fahrenheit = read_temp()
        temp_c_text = temp_font.render(f'{temperature_celsius:.2f} \u00B0C', True, RED)
        temp_f_text = temp_font.render(f'{temperature_fahrenheit:.2f} \u00B0F', True, BLUE)
        screen.blit(temp_c_text, (180, 130))
        screen.blit(temp_f_text, (180, 250))

        # Display the temperature icon next to the Celsius text
        icon_x = 620  # Position closer to the Celsius text
        icon_y = 130  # Adjusted Y-coordinate for alignment
        screen.blit(icon, (icon_x, icon_y))

    elif current_screen == "settings":
         # Settings screen
        settings_title = title_font.render("Settings", True, TITLE_COLOR)
        settings_rect = settings_title.get_rect(center=(screen.get_width() // 2, 60))
        screen.blit(settings_title, settings_rect)

        # Placeholder settings information with reduced font size
        setting_text_1 = settings_font.render("Right Reactor: Intensity", True, WHITE)
        setting_text_2 = settings_font.render("Left Reactor: Intensity", True, WHITE)
        screen.blit(setting_text_1, (200, 200))
        screen.blit(setting_text_2, (200, 300))

    # Update the display
    pygame.display.flip()
    time.sleep(0.1)  # Adjust refresh rate

# Quit Pygame on exit
pygame.quit()