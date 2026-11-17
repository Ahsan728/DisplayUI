import os
import glob
import time
import threading
import pygame
import logging
import RPi.GPIO as GPIO

# Setup logging
logging.basicConfig(level=logging.ERROR)

# Constants for colors, screen settings, etc.
WHITE = (255, 255, 255)
RED = (255, 0, 0)
CYAN = (0, 255, 255)
TITLE_COLOR = (255, 215, 0)
BUTTON_HIGHLIGHT = (0, 180, 180)
SCREEN_SIZE = (1024, 600)

# Fonts
pygame.font.init()
TITLE_FONT = pygame.font.Font(None, 120)
TEMP_FONT = pygame.font.Font(None, 60)
SETTINGS_FONT = pygame.font.Font(None, 50)
DEVELOPER_FONT = pygame.font.Font(None, 30)

# GPIO Setup
GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)

# Define GPIOs for PWM (Sliders)
PWM_GPIO_PINS = [17, 18, 19, 20]  # 4 PWM-controlled GPIOs
pwm_channels = {}

for pin in PWM_GPIO_PINS:
    GPIO.setup(pin, GPIO.OUT)
    pwm_channels[pin] = GPIO.PWM(pin, 500)  # 500Hz frequency
    pwm_channels[pin].start(0)  # Start with full brightness (100%)

# Define GPIOs for Toggle Switches
TOGGLE_GPIO_PINS = [27, 22, 23, 24]  # 4 GPIOs for ON/OFF switching

for pin in TOGGLE_GPIO_PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)  # Initialize all switches OFF


class PhotoScaleApp:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False)
        self.screen = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)
        self.running = True
        self.current_screen = "temperature"
        self.sensor_data = ["Init..."] * len(self.get_device_files())  # Show "Initializing..." initially
        
        # **New: Store slider & switch states**
        self.slider_values = {gpio: 0 for gpio in PWM_GPIO_PINS}  # Store slider values
        self.switch_states = {gpio: False for gpio in TOGGLE_GPIO_PINS}  # Store switch states
        
        self.buttons = self.create_buttons()
        self.sliders = self.create_sliders()
        self.toggle_switches = self.create_toggle_switches()

        # Link sliders to their corresponding toggle switches
        for i in range(4):
            self.sliders[i].switch = self.toggle_switches[i]

        # Load developer screen logos
        self.dev_logo1 = self.load_logo("/home/photorx2/Downloads/ICIQ.png", (150, 180))
        self.dev_logo2 = self.load_logo("/home/photorx2/Downloads/JLFlab.png", (150, 180))

        # Start sensor reading thread
        threading.Thread(target=self.sensor_thread, daemon=True).start()

    def load_logo(self, path, size):
        try:
            image = pygame.image.load(path)
            return pygame.transform.scale(image, size)
        except pygame.error as e:
            logging.error(f"Failed to load logo image: {path}, error: {e}")
            return None

    def get_device_files(self):
        base_dir = '/sys/bus/w1/devices/'
        device_files = glob.glob(os.path.join(base_dir, '28*', 'w1_slave'))

        if not device_files:
            logging.error("No temperature sensors found! Check wiring and configuration.")
        
        return device_files


    def create_buttons(self):
        return [
            Button("/home/photorx2/Downloads/menu.png", 22, 130, 88, 90, self.show_temperature_screen),
            Button("/home/photorx2/Downloads/sett2.png", 22, 245, 88, 90, self.show_settings_screen),
            Button("/home/photorx2/Downloads/Dev.png", 22, 360, 86, 88, self.show_developer_screen)
        ]


    def create_sliders(self):
        sliders = [
            Slider(170, 160, 450, 0, 100, self.slider_values[PWM_GPIO_PINS[0]], "PRX 1", PWM_GPIO_PINS[0]),
            Slider(170, 240, 450, 0, 100, self.slider_values[PWM_GPIO_PINS[1]], "PRX 2", PWM_GPIO_PINS[1]),
            Slider(170, 320, 450, 0, 100, self.slider_values[PWM_GPIO_PINS[2]], "PRX 3", PWM_GPIO_PINS[2]),
            Slider(170, 400, 450, 0, 100, self.slider_values[PWM_GPIO_PINS[3]], "PRX 4", PWM_GPIO_PINS[3])
        ]
        return sliders


    def create_toggle_switches(self):
        switches = [
            ToggleSwitch(650, 150, 100, 40, TOGGLE_GPIO_PINS[0], "SW 1", self.switch_states[TOGGLE_GPIO_PINS[0]], self.sliders[0]),
            ToggleSwitch(650, 230, 100, 40, TOGGLE_GPIO_PINS[1], "SW 2", self.switch_states[TOGGLE_GPIO_PINS[1]], self.sliders[1]),
            ToggleSwitch(650, 310, 100, 40, TOGGLE_GPIO_PINS[2], "SW 3", self.switch_states[TOGGLE_GPIO_PINS[2]], self.sliders[2]),
            ToggleSwitch(650, 390, 100, 40, TOGGLE_GPIO_PINS[3], "SW 4", self.switch_states[TOGGLE_GPIO_PINS[3]], self.sliders[3])
        ]
        return switches


    def sensor_thread(self):
        logging.info("Sensor thread started.")
        
        while self.running:
            try:
                device_files = self.get_device_files()
                
                if not device_files:
                    logging.warning("No temperature sensors found! Check wiring and configuration.")
                    self.sensor_data = ["N/A"] * 8  # Store "N/A" for all sensors
                    time.sleep(1)
                    continue  # Skip loop iteration if no sensors are found
                
                new_data = []
                for device_file in device_files:
                    temp = self.read_temp(device_file)
                    if temp is None or temp == -99.99:
                        logging.error(f"Sensor at {device_file} is not responding.")
                        new_data.append("N/A")  # **Store "N/A" instead of numbers**
                    else:
                        new_data.append(f"{temp:.2f}")  # Store as formatted string

                self.sensor_data = new_data  # **Thread-safe update**

            except Exception as e:
                logging.error(f"Sensor thread error: {e}")

            time.sleep(1)



    def read_temp_raw(self, device_file):
        try:
            with open(device_file, 'r') as f:
                lines = f.readlines()
            return lines
        except (FileNotFoundError, IOError) as e:
            logging.error(f"Error reading temperature file {device_file}: {e}")
            return []

    def read_temp(self, device_file):
        for _ in range(5):  # Retry up to 5 times
            lines = self.read_temp_raw(device_file)
            if len(lines) < 2:
                time.sleep(0.1)
                continue
            if lines[0].strip().endswith('YES'):
                equals_pos = lines[1].find('t=')
                if equals_pos != -1:
                    temp_string = lines[1][equals_pos + 2:]
                    try:
                        temp_c = float(temp_string) / 1000.0
                        if temp_c == 85.0 or temp_c < -10.0 or temp_c > 100.0:
                            time.sleep(0.1)
                            continue  # Ignore invalid readings
                        return temp_c
                    except ValueError:
                        logging.error(f"Invalid temperature value: {temp_string}")
                        return -99.99  # Return safe default value if parsing fails
            time.sleep(0.1)

        logging.error(f"Failed to initialize sensor: {device_file}")
        return -99.99  # Return -99.99 instead of None

    def handle_events(self):
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.running = False
                elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
                    for button in self.buttons:
                        if event.type == pygame.MOUSEBUTTONDOWN and button.is_clicked(event.pos):
                            button.highlight()
                            button.action()
                        elif event.type == pygame.MOUSEBUTTONUP:
                            button.reset_color()

                    if self.current_screen == "settings":
                        for slider in self.sliders:
                            slider.handle_event(event)

                        for switch in self.toggle_switches:
                            switch.handle_event(event)
        except Exception as e:
            logging.error(f"Error in handle_events(): {e}")

    def update_dimmer(self, gpio, value):
        if gpio not in pwm_channels:
            logging.error(f"Attempted to update a non-existent PWM channel: GPIO {gpio}")
            return
        
        duty_cycle = max(0, min(100, 100 - int(value)))
        
        if pwm_channels[gpio]:  # Ensure PWM is initialized before changing duty cycle
            pwm_channels[gpio].ChangeDutyCycle(duty_cycle)



    def update_display(self):
        self.screen.fill((0, 0, 0))
        for button in self.buttons:
            button.draw(self.screen)
        if self.current_screen == "temperature":
            self.draw_temperature_screen()
        elif self.current_screen == "settings":
            self.draw_settings_screen()
        elif self.current_screen == "developer":
            self.draw_developer_screen()
        pygame.display.flip()

    def draw_temperature_screen(self):
        title_text = TITLE_FONT.render("PhotoScale", True, TITLE_COLOR)
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 60))
        self.screen.blit(title_text, title_rect)

        left_x, right_x = 140, 410
        y_start = 140
        y_gap = 90
        half = len(self.sensor_data) // 2

        for idx, temp_c in enumerate(self.sensor_data):
            temp_display = temp_c  # **No need to format, already a string**

            label_text = TEMP_FONT.render(f"R{idx + 1}: ", True, CYAN)
            temp_text = TEMP_FONT.render(temp_display + "\u00B0", True, RED)  # Append "°C" here

            if idx < half:
                self.screen.blit(label_text, (left_x, y_start + idx * y_gap))
                self.screen.blit(temp_text, (left_x + 80, y_start + idx * y_gap))
            else:
                self.screen.blit(label_text, (right_x, y_start + (idx - half) * y_gap))
                self.screen.blit(temp_text, (right_x + 80, y_start + (idx - half) * y_gap))

    def draw_settings_screen(self):
        settings_title = TITLE_FONT.render("Settings", True, TITLE_COLOR)
        settings_rect = settings_title.get_rect(center=(self.screen.get_width() // 2, 60))
        self.screen.blit(settings_title, settings_rect)

        for slider in self.sliders:
            slider.draw(self.screen)

        for switch in self.toggle_switches:
            switch.draw(self.screen)

    def draw_developer_screen(self):
        developer_title = TITLE_FONT.render("Developer", True, TITLE_COLOR)
        developer_rect = developer_title.get_rect(center=(self.screen.get_width() // 2, 60))
        self.screen.blit(developer_title, developer_rect)
        if self.dev_logo1:
            self.screen.blit(self.dev_logo1, (250, 140))
        if self.dev_logo2:
            self.screen.blit(self.dev_logo2, (410, 140))
        # Add name and email with colorful fonts
        name_text = DEVELOPER_FONT.render("MD Shahnauze Ahsan", True, (0, 255, 0))  # Green color for name
        email_text = DEVELOPER_FONT.render("photorx@iciq.es", True, (255, 0, 0))  # Blue color for email
        
        # Position the text below the logos
        name_rect = name_text.get_rect(center=(self.screen.get_width() // 2, 380))
        email_rect = email_text.get_rect(center=(self.screen.get_width() // 2, 410))
        
        self.screen.blit(name_text, name_rect)
        self.screen.blit(email_text, email_rect)
        
    def show_temperature_screen(self):
        self.current_screen = "temperature"

    def show_settings_screen(self):
        self.current_screen = "settings"

        # **Re-create sliders and switches with stored values**
        self.sliders = self.create_sliders()
        self.toggle_switches = self.create_toggle_switches()

        # Re-link sliders to switches
        for i in range(4):
            self.sliders[i].switch = self.toggle_switches[i]

    def show_developer_screen(self):
        self.current_screen = "developer"


    def main_loop(self):
        try: 
            while self.running:
                self.handle_events()
                self.update_display()
                time.sleep(0.1)
        except Exception as e:
            logging.error(f"Unexpected crash in main loop: {e}")
        finally:
            logging.info("Cleaning up GPIO and quitting Pygame...")
            for pin in PWM_GPIO_PINS:
                pwm_channels[pin].ChangeDutyCycle(0)
                pwm_channels[pin].stop()
            GPIO.cleanup()
            pygame.quit()



class Button:
    def __init__(self, image_path, x, y, width, height, action):
        try:
            self.image = pygame.image.load(image_path)
            self.image = pygame.transform.scale(self.image, (width, height))
        except pygame.error:
            logging.error(f"Failed to load image: {image_path}")
            self.image = None
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

class Slider:
    def __init__(self, x, y, width, min_val, max_val, value, label, gpio):
        self.rect = pygame.Rect(x, y, width, 20)
        self.knob_rect = pygame.Rect(x + (value / max_val) * width - 10, y - 10, 20, 40)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.label = label
        self.gpio = gpio
        self.dragging = False
        self.switch = None  # This will be set later

    def draw(self, screen):
        pygame.draw.line(screen, WHITE, (self.rect.x, self.rect.y + 10),
                         (self.rect.x + self.rect.width, self.rect.y + 10), 4)
        pygame.draw.rect(screen, WHITE, self.knob_rect)
        label_text = SETTINGS_FONT.render(f"{self.label}: {int(self.value)}", True, WHITE)
        screen.blit(label_text, (self.rect.x, self.rect.y - 40))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.knob_rect.collidepoint(event.pos):
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            new_x = max(self.rect.x, min(event.pos[0], self.rect.x + self.rect.width))
            self.knob_rect.x = new_x - 10
            self.value = (new_x - self.rect.x) / self.rect.width * (self.max_val - self.min_val)
            
            # **New: Save the slider value in the app's memory**
            app.slider_values[self.gpio] = self.value  

            # **Check if the linked switch is ON before updating PWM**
            if self.switch and self.switch.state:
                app.update_dimmer(self.gpio, self.value)
            else:
                app.update_dimmer(self.gpio, 0)  # Stop PWM if switch is OFF

    def set_pwm(self, value):
        pwm_channels[self.gpio].ChangeDutyCycle(value)

class ToggleSwitch:
    def __init__(self, x, y, width, height, gpio, label, state, slider):
        self.rect = pygame.Rect(x, y, width, height)
        self.knob_rect = pygame.Rect(x, y, width // 2, height)
        self.state = state  # Preserve state from memory
        self.GPIO = gpio  # Store the pin number correctly
        self.label = label
        self.slider = slider  # Link the switch to its corresponding slider

        # Ensure GPIO is set correctly before restoring state
        GPIO.setup(self.GPIO, GPIO.OUT)  
        GPIO.output(self.GPIO, GPIO.HIGH if self.state else GPIO.LOW)  

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect, border_radius=10)  # Background
        pygame.draw.rect(screen, CYAN if self.state else RED, self.knob_rect, border_radius=10)  # Knob


    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.state = not self.state  # Toggle state
            GPIO.output(self.GPIO, GPIO.HIGH if self.state else GPIO.LOW)

            # **New: Save the switch state**
            app.switch_states[self.GPIO] = self.state  

            # Move knob visually
            self.knob_rect.x = self.rect.x + (self.rect.width // 2) if self.state else self.rect.x

            # **Disable slider's PWM if switch is OFF**
            if not self.state:
                self.slider.set_pwm(0)  # Stop PWM

if __name__ == "__main__":
    app = PhotoScaleApp()
    app.main_loop()
