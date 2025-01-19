import os
import json
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtGui import QPixmap, QFont, QPainter, QImage, QFontDatabase
from PyQt5.QtCore import Qt, QTimer, QTime, QDateTime
from datetime import datetime
from dateutil import parser
from PyQt5.QtCore import QFileSystemWatcher

class SlideGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(720, 480)

        # Set the background image based on the slide name
        slide_name = os.path.splitext(os.path.basename(__file__))[0]
        background_filename = f"{slide_name}bg.png"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.background_path = os.path.join(script_dir, "backgrounds", background_filename)

        # Define the weather data file
        self.weather_file = os.path.join(script_dir, "weatherdata", "home_weather.json")
        self.weather_data = self.load_weather_data(self.weather_file)

        # Map pressure trend to arrow symbols
        self.pressure_trend_mapping = {
            "up": "\u2191",    # Up arrow
            "down": "\u2193",  # Down arrow
            "steady": "\u2192" # Right arrow
        }

        # Load custom font
        font_path = os.path.join(script_dir, "fonts", "StarJR.ttf")
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print(f"Error: Failed to load font from {font_path}")
        self.custom_font_family = QFontDatabase.applicationFontFamilies(font_id)[0] if font_id != -1 else "Arial"

        # Initialize layout attributes
        self.left_x = 100
        self.right_x = 375
        self.left_y_start = 310
        self.left_y_spacing = 45
        self.right_y_start = 220
        self.right_y_spacing = 45

        self.location_font_size = 25

        # Timer to update time and date
        self.current_time = ""
        self.current_date = ""
        self.update_time_and_date()

        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time_and_date)
        self.time_timer.start(1000)  # Update every second

        # Timer to reload weather data
        self.weather_reload_timer = QTimer(self)
        self.weather_reload_timer.timeout.connect(self.reload_weather_data)
        self.weather_reload_timer.start(2000)  # Reload every 2 seconds

        # Initialize weather details
        self.update_weather_details()



    def reload_weather_data(self):
        """Reload the weather data periodically."""
        self.weather_data = self.load_weather_data(self.weather_file)
        self.update_weather_details()
        self.update()  # Trigger a repaint

    def load_weather_data(self, filepath):
        """Load weather data from the specified JSON file."""
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading weather data: {e}")
            return {
                "location": "Unknown",
                "temperature": 0,
                "conditions": "N/A",
                "wind_direction": "N/A",
                "wind_speed_mph": 0,
                "gusts_mph": 0,
                "humidity_percent": 0,
                "dewpoint": 0,
                "ceiling_feet": 0,
                "visibility_miles": 0,
                "pressure_inhg": 0.0,
                "pressure_trend": "steady",
                "icon_url": "",
                "observation_time": "Unknown time"
            }
        
    def load_weather_data(self, filepath):
        """Load weather data from the specified JSON file."""
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading weather data: {e}")
            return {
                "location": "Unknown",
                "temperature": 0,
                "conditions": "N/A",
                "wind_direction": "N/A",
                "wind_speed_mph": 0,
                "gusts_mph": 0,
                "humidity_percent": 0,
                "dewpoint": 0,
                "ceiling_feet": 0,
                "visibility_miles": 0,
                "pressure_inhg": 0.0,
                "pressure_trend": "steady",
                "icon_url": "",
                "observation_time": "Unknown time"
            }

    def update_weather_details(self):
        """Update weather details based on the loaded data."""
        pressure_trend_arrow = self.pressure_trend_mapping.get(self.weather_data["pressure_trend"].lower(), "")

        self.left_details = [
            (f"{int(self.weather_data['temperature'])}°", 250, 175, 48),  # Temperature
            ("", self.left_x, 50, 0),  # Placeholder for icon
        ]

        self.left_dynamic_details = [
            (self.weather_data["conditions"].capitalize(), 20),  # Conditions
            (f"Wind: {self.weather_data['wind_direction']} {int(self.weather_data['wind_speed_mph'])} mph", 20),  # Wind
            (f"Gusts: {int(self.weather_data['gusts_mph'])} mph", 20),  # Gusts
        ]

        self.right_details = [
            (f"Humidity: {int(self.weather_data['humidity_percent'])}%", self.right_x, 0, 20),  # Humidity
            (f"Dewpoint: {int(self.weather_data['dewpoint'])}°F", self.right_x, 0, 20),  # Dewpoint
            (f"Ceiling: {int(self.weather_data['ceiling_feet'])} ft", self.right_x, 0, 20),  # Ceiling
            (f"Visibility: {int(self.weather_data['visibility_miles'])} mi", self.right_x, 0, 20),  # Visibility
            (f"Pressure: {self.weather_data['pressure_inhg']:.2f} {pressure_trend_arrow}", self.right_x, 0, 20),  # Pressure
        ]

        # Update dynamic positions for text
        self.left_details += [
            (detail[0], self.left_x, self.left_y_start + i * self.left_y_spacing, detail[1])
            for i, detail in enumerate(self.left_dynamic_details)
        ]

        for index, detail in enumerate(self.right_details):
            self.right_details[index] = (
                detail[0],
                detail[1],
                self.right_y_start + index * self.right_y_spacing,
                detail[3],
            )

        # Update icon path
        icon_filename = self.weather_data["icon_url"].split("/")[-1]
        self.icon_path = os.path.join(os.path.dirname(self.weather_file), "icons", icon_filename)


    def update_time_and_date(self):
        """Update the current time and date."""
        self.current_time = QTime.currentTime().toString("hh:mm:ss AP")  # Time in HH:MM:SS AM/PM format
        self.current_date = QDateTime.currentDateTime().toString("ddd MMM dd")  # Date in DAY MON DATE format
        self.update()  # Trigger a repaint

    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw background
        background_pixmap = QPixmap(self.background_path)
        if not background_pixmap.isNull():
            painter.drawPixmap(0, 0, self.width(), self.height(), background_pixmap)

        # Draw location at its own coordinates
        self.draw_text_with_outline(painter, self.weather_data["location"], 450, 150, self.location_font_size)

        # Draw static text "Current \n Conditions" at the top of the page
        static_text = "Current\nConditions"
        font_size = 30  # Font size for the static text
        outline_width = 2  # Outline thickness
        line_spacing = 10  # Additional spacing between lines in pixels
        font = QFont(self.custom_font_family, font_size)
        font.setBold(True)
        painter.setFont(font)

        # Calculate text width and center it horizontally
        text_width = painter.fontMetrics().horizontalAdvance("Current")  # Width of the longest line
        x = 180 # Center horizontally
        y = 65  # Static text starts near the top

        # Draw each line of the static text
        for index, line in enumerate(static_text.split("\n")):
            self.draw_text_with_outline(
                painter,
                line,
                x,
                y + index * (font_size + line_spacing),  # Add spacing between lines
                font_size,
                outline_width
            )

        # Draw left-side weather details
        for text, x, y, font_size in self.left_details:
            if text:  # Skip empty placeholders
                self.draw_text_with_outline(painter, text, x, y, font_size)

        # Draw right-side weather details
        # Draw right-side weather details
        for text, x, y, font_size in self.right_details:
            if "Pressure:" in text and ("↑" in text or "↓" in text or "→" in text):
                # Split the Pressure text into value and arrow
                parts = text.split(" ")  # Example: ['Pressure:', '30.26', '↑']
                if len(parts) >= 3:
                    label, value, arrow = parts[0], parts[1], parts[2]

                    # Draw the label and value with the default font
                    self.draw_text_with_outline(painter, f"{label} {value}", x, y, font_size)

                    # Draw the arrow with a fallback font
                    arrow_font = QFont("Arial", font_size)  # Use Arial for the arrow
                    painter.setFont(arrow_font)

                    # Calculate the width of the label and value for positioning the arrow
                    label_value_width = painter.fontMetrics().width(f"{label} {value}")
                    # Calculate the width of the label and value for positioning the arrow
                    label_value_width = painter.fontMetrics().width(f"{label} {value}")
                    arrow_offset = 20  # Fixed spacing between the value and the arrow
                    self.draw_text_with_outline(painter, arrow, x + label_value_width + arrow_offset, y, font_size)

            else:
                # Draw other details normally
                self.draw_text_with_outline(painter, text, x, y, font_size)


        # Draw weather icon (overlapping placeholder position)
        if os.path.exists(self.icon_path):
            pixmap = QPixmap(self.icon_path)
            pixmap = pixmap.scaled(350, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(100, 120, pixmap)  # Icon below temperature on the left side

        # Draw time and date in the upper-right corner
        self.draw_text_with_outline(painter, self.current_time, 450, 70, 20)
        self.draw_text_with_outline(painter, self.current_date, 450, 100, 20)

        # Draw observation time at the bottom of the screen
        obs_time = self.weather_data.get("observation_time", "Unknown time")
        obs_time_display = f"Updated: {obs_time}"
        font_size = 16  # Font size for the observation time
        painter.setFont(QFont(self.custom_font_family, font_size))

        # Calculate text width and position for centering
        text_width = painter.fontMetrics().horizontalAdvance(obs_time_display)
        x = (self.width() - text_width) // 2
        y = self.height() - 20  # Position the text 20 pixels from the bottom

        self.draw_text_with_outline(painter, obs_time_display, x, y, font_size, 1)



    def draw_text_with_outline(self, painter, text, x, y, font_size, outline_width=1):
        """
        Draw text with an outline.

        Args:
            painter: QPainter object used for drawing.
            text: Text to draw.
            x: X-coordinate of the text.
            y: Y-coordinate of the text.
            font_size: Font size of the text.
            outline_width: Thickness of the outline in pixels (default: 1).
        """
        # Use fallback font for arrows if necessary
        if "↑" in text or "↓" in text or "→" in text:
            font = QFont("Arial", font_size)  # Fallback font for arrows
        else:
            font = QFont(self.custom_font_family, font_size)

        font = QFont(self.custom_font_family, font_size)
        font.setBold(True)
        painter.setFont(font)

        # Draw outline
        painter.setPen(Qt.black)
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    painter.drawText(x + dx, y + dy, text)

        # Draw main text
        painter.setPen(Qt.white)
        painter.drawText(x, y, text)



