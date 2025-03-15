import os
import sys
os.environ["QT_QPA_PLATFORM"] = "linuxfb"
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QCursor
import subprocess  # For running external scripts
from datetime import datetime
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QLabel
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QCursor
import speaker_and_GPIO_Test
import subprocess

GPIO_STATES_FILE = "./gpio_states.json"   # adjust the path as needed

class WeatherApp(QMainWindow):
    # Create a custom signal that carries the volume value (as an integer, for example)
    volumeChanged = pyqtSignal(int)
    def __init__(self):
        # Load settings from settings.json
        settings = self.load_settings()
        debug = settings.get("debug", False)
        self.slide_debug = settings.get("slide_debug", -1)  # Default to -1 (cycle normally)
        radar_refresh = settings.get("radar_refesh_min")
        weather_refresh = settings.get("weather_refesh_min")

        super().__init__()
        self.setWindowTitle("Weather GUI Slideshow")
        self.setFixedSize(720, 480)

        # Enable or disable window borders based on debug flag
        if debug:
            self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint)  # Remove window borders
            QApplication.setOverrideCursor(QCursor(Qt.BlankCursor))  # Hide mouse cursor

        # Set up the stacked widget to hold multiple GUIs
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        # Load slide modules dynamically based on available files
        self.guis = self.find_slides()
        self.current_index = 0

        # Load GUIs dynamically
        self.load_guis()

        # Set up a timer to cycle through GUIs
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_gui)
        self.timer.start(settings.get("cycle_interval", 5000))  # Default cycle interval 5000ms

        # If slide_debug is set to a valid slide number, show it and stop cycling
        if debug and 1 <= self.slide_debug <= len(self.guis):
            self.stack.setCurrentIndex(self.slide_debug - 1)
            self.timer.stop()

        # ----------------------------
        # Volume / Power-off Display Setup (Centered)
        # ----------------------------
        # Create a label of size 400x100 centered on a 720x480 screen.
        label_width, label_height = 400, 100
        x = (720 - label_width) // 2
        y = (480 - label_height) // 2
        self.volume_label = QLabel(self)
        self.volume_label.setGeometry(x, y, label_width, label_height)
        self.volume_label.setAlignment(Qt.AlignCenter)
        # Solid black background with large white text
        self.volume_label.setStyleSheet("background-color: black; color: white; font-size: 48px;")
        self.volume_label.hide()  # Start hidden

        # Timer to hide the display after 3 seconds
        self.display_timer = QTimer(self)
        self.display_timer.setSingleShot(True)
        self.display_timer.timeout.connect(self.hideDisplay)

        # Timer to poll the JSON file
        self.gpio_timer = QTimer(self)
        self.gpio_timer.timeout.connect(self.check_gpio_state)
        self.gpio_timer.start(200)  # every 200 ms

        self.last_volume = None

        # Timer to run radar script every 5 minutes
        if debug is False:
            # Run radar script on startup in a separate thread
            threading.Thread(target=self.run_radar_script, daemon=True).start()
            self.radar_timer = QTimer(self)
            self.radar_timer.timeout.connect(self.run_radar_script_in_thread)
            self.radar_timer.start(radar_refresh * 60 * 1000)  # Every x minutes (set in json)


        # Timer to run weather script every hour
        if debug is False:
            # Run weather script on startup in a separate thread
            threading.Thread(target=self.run_weather_script, daemon=True).start()
            self.weather_timer = QTimer(self)
            self.weather_timer.timeout.connect(self.run_weather_script_in_thread)
            self.weather_timer.start(weather_refresh * 60 * 1000)  # Every x minutes (set in json)

        # Timer to run regional weather script every hour
        if debug is False:
            # Run weather script on startup in a separate thread
            threading.Thread(target=self.run_regional_weather_script, daemon=True).start()
            self.regional_weather_timer = QTimer(self)
            self.regional_weather_timer.timeout.connect(self.run_regional_weather_script_in_thread)
            self.regional_weather_timer.start((weather_refresh * 60 * 1000)+60000)  # Every x minutes + 60 seconds (set in json) maybe there's a colission? 

    def check_and_run_radar(self):
        """Check if it's the 15-minute mark of the hour and run radar script."""
        now = datetime.now()
        if now.minute == 15 and now.second == 0:  # At the 15-minute mark
            print("Running radar script at 15-minute mark...")
            self.run_radar_script_in_thread()

    def run_radar_script_in_thread(self):
        """Run the radar script in a separate thread."""
        threading.Thread(target=self.run_radar_script, daemon=True).start()

    def run_radar_script(self):
        """Run the radar_getter/get_radar.py script."""
        radar_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "get_radar.py")
        try:
            subprocess.run(["python3", radar_script_path], check=True)
            print("Radar script executed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error running radar script: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def run_weather_script_in_thread(self):
        """Run the weather script in a separate thread."""
        threading.Thread(target=self.run_weather_script, daemon=True).start()

    def run_weather_script(self):
        """Run the weather_getter/get_weather.py script."""
        weather_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "get_weather.py")
        try:
            subprocess.run(["python3", weather_script_path], check=True)
            print("Weather script executed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error running weather script: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def run_regional_weather_script_in_thread(self):
        """Run the weather script in a separate thread."""
        threading.Thread(target=self.run_regional_weather_script, daemon=True).start()

    def run_regional_weather_script(self):
        """Run the weather_getter/get_weather.py script."""
        regional_weather_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "get_regional_weather.py")
        try:
            subprocess.run(["python3", regional_weather_script_path], check=True)
            print("Weather script executed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error running weather script: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def load_settings(self):
        """Load settings from settings.json file."""
        settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        try:
            with open(settings_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print("settings.json not found. Using default settings.")
            return {}
        except json.JSONDecodeError:
            print("Error decoding settings.json. Using default settings.")
            return {}

    def find_slides(self):
        """Find all valid slide files in the current directory."""
        slides = []
        for file_name in os.listdir(os.path.dirname(os.path.abspath(__file__))):
            if file_name.startswith("slide") and file_name.endswith(".py"):
                slides.append(file_name[:-3])  # Remove .py extension
        slides.sort()  # Ensure slides are loaded in order
        return slides

    def load_guis(self):
        """Dynamically load GUI modules and add them to the stack."""
        for gui_name in self.guis:
            try:
                module = __import__(gui_name)
                gui_class = getattr(module, "SlideGUI")
                gui_instance = gui_class()
                self.stack.addWidget(gui_instance)
            except (ImportError, AttributeError) as e:
                print(f"Error loading {gui_name}: {e}")

    def next_gui(self):
        """Switch to the next GUI in the stack."""
        if self.slide_debug == -1:  # Only cycle if slide_debug is -1
            self.current_index = (self.current_index + 1) % len(self.guis)
            self.stack.setCurrentIndex(self.current_index)

        # ---------------
    
    def showDisplay(self, text):
        self.volume_label.setText(text)
        self.volume_label.show()
        self.display_timer.start(3000)  # Hide after 3 seconds

    def hideDisplay(self):
        self.volume_label.hide()

    def check_gpio_state(self):
        """Read the JSON file and update the display accordingly."""
        try:
            if os.path.exists(GPIO_STATES_FILE):
                with open(GPIO_STATES_FILE, "r") as f:
                    data = json.load(f)
                # If there is a power_off_countdown, display that message
                if "power_off_countdown" in data:
                    countdown = data["power_off_countdown"]
                    self.showDisplay(f"Power off in {countdown}")
                else:
                    # Otherwise, display volume if it has changed.
                    volume = data.get("volume")
                    if volume is not None and volume != self.last_volume:
                        self.last_volume = volume
                        self.showDisplay(f"Volume: {volume}%")
        except Exception as e:
            print("Error reading gpio_states.json:", e)

if __name__ == "__main__":
    # Launch the GPIO script as a separate process.
    gpio_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "speaker_and_GPIO_Test.py")
    gpio_process = subprocess.Popen(["python3", gpio_script_path])
    app = QApplication(sys.argv)
    window = WeatherApp()
    window.show()
    exit_code = app.exec_()
    # Optionally terminate the GPIO process on exit.
    gpio_process.terminate()
    sys.exit(exit_code)
