import os
import json
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap, QFont, QPainter, QFontDatabase
from PyQt5.QtCore import Qt, QTimer, QTime, QDateTime
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

        # Load custom font
        font_path = os.path.join(script_dir, "fonts", "StarJR.ttf")
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print(f"Error: Failed to load font from {font_path}")
        self.custom_font_family = QFontDatabase.applicationFontFamilies(font_id)[0] if font_id != -1 else "Arial"

        self.weather_file = os.path.join(script_dir, "weatherdata", "regional_weather.json")

        # Timer to reload weather data
        self.weather_reload_timer = QTimer(self)
        self.weather_reload_timer.timeout.connect(self.reload_weather_data)
        self.weather_reload_timer.start(2000)  # Reload every 2 seconds

        # Load regional weather data initially
        self.regional_weather = self.load_weather_data(self.weather_file)

        # Timer to update time and date
        self.current_time = ""
        self.current_date = ""
        self.update_time_and_date()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_and_date)
        self.timer.start(1000)  # Update every second

    def load_weather_data(self, filepath):
        """Load weather data from the specified JSON file."""
        try:
            with open(filepath, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading weather data: {e}")
            return {"regional_weather": [], "observation_time": "Unknown time"}

    def reload_weather_data(self):
        """Reload the weather data periodically."""
        self.regional_weather = self.load_weather_data(self.weather_file)
        self.update()  # Trigger a repaint to refresh the UI

    def update_time_and_date(self):
        """Update the current time and date."""
        self.current_time = QTime.currentTime().toString("hh:mm:ss AP")  # Time in HH:MM:SS AM/PM format
        self.current_date = QDateTime.currentDateTime().toString("ddd MMM dd")  # Date in DAY MON DATE format
        self.update()  # Trigger a repaint

    # (Keep the rest of your methods like `calculate_column_widths`, `paintEvent`, and `draw_text_with_outline` as is)



    def update_time_and_date(self):
        """Update the current time and date."""
        self.current_time = QTime.currentTime().toString("hh:mm:ss AP")  # Time in HH:MM:SS AM/PM format
        self.current_date = QDateTime.currentDateTime().toString("ddd MMM dd")  # Date in DAY MON DATE format
        self.update()  # Trigger a repaint

    def calculate_column_widths(self, painter, font_size):
        """Calculate dynamic column widths based on the largest strings in each column."""
        max_location_width = max(
            painter.fontMetrics().horizontalAdvance(entry["location"])
            for entry in self.regional_weather["regional_weather"]  # Access the list
        )
        max_observation_width = max(
            painter.fontMetrics().horizontalAdvance(entry["conditions"])
            for entry in self.regional_weather["regional_weather"]  # Access the list
        )
        max_temperature_width = max(
            painter.fontMetrics().horizontalAdvance(str(int(entry["temperature"])))
            for entry in self.regional_weather["regional_weather"]  # Access the list
        )
        return max_location_width, max_observation_width, max_temperature_width


    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw background
        background_pixmap = QPixmap(self.background_path)
        if not background_pixmap.isNull():
            painter.drawPixmap(0, 0, self.width(), self.height(), background_pixmap)

        # Draw static text "Regional \n Observations" at the top of the page
        static_text = "Regional\nObservations"
        font_size = 30  # Font size for the static text
        outline_width = 2  # Outline thickness
        line_spacing = 10  # Additional spacing between lines in pixels
        font = QFont(self.custom_font_family, font_size)
        font.setBold(True)
        painter.setFont(font)

        # Draw each line of the static text
        x = 180  # Static text position (adjust as needed)
        y = 65   # Starting Y position for the static text
        for index, line in enumerate(static_text.split("\n")):
            self.draw_text_with_outline(
                painter,
                line,
                x,
                y + index * (font_size + line_spacing),  # Add spacing between lines
                font_size,
                outline_width
            )

        # Draw time and date in the upper-right corner
        self.draw_text_with_outline(painter, self.current_time, 450, 70, 20, 1)
        self.draw_text_with_outline(painter, self.current_date, 450, 100, 20, 1)

        # Calculate column widths dynamically
        weather_font_size = 24
        outline_width = 1
        column_spacing = 50  # Spacing between columns
        column_widths = self.calculate_column_widths(painter, weather_font_size)
        location_width, observation_width, temperature_width = column_widths

        # Calculate column starting positions
        box_width = 540  # Total box width
        box_x = (self.width() - box_width) // 2  # Centered horizontally
        location_x = box_x + 20
        observation_x = location_x + location_width + column_spacing
        temperature_x = observation_x + observation_width + column_spacing

        # Draw column headers "WEATHER" and "°F"
        header_font_size = 16
        header_y = 135  # Y position for column headers

        self.draw_text_with_outline(painter, "WEATHER", observation_x+observation_width//2, header_y, header_font_size, outline_width)
        self.draw_text_with_outline(painter, "°F", temperature_x, header_y, header_font_size, outline_width)

        # Draw regional weather data
        weather_y = 165  # Starting Y position for data rows
        weather_line_spacing = 15  # Vertical spacing between lines

        for index, entry in enumerate(self.regional_weather["regional_weather"]):
            location = entry["location"]
            observation = entry["conditions"]
            temperature = str(int(entry["temperature"]))  # Convert temperature to string

            y_position = weather_y + index * (weather_font_size + weather_line_spacing)

            # Draw each column's text
            self.draw_text_with_outline(painter, location, location_x, y_position, weather_font_size, outline_width)
            self.draw_text_with_outline(painter, observation, observation_x, y_position, weather_font_size, outline_width)
            self.draw_text_with_outline(painter, temperature, temperature_x, y_position, weather_font_size, outline_width)

        # Draw observation time at the bottom of the screen
        obs_time = self.regional_weather.get("observation_time", "Unknown time")
        obs_time_display = f"Updated: {obs_time}"
        font_size = 16  # Font size for the observation time
        painter.setFont(QFont(self.custom_font_family, font_size))

        # Calculate text width and position for centering
        text_width = painter.fontMetrics().horizontalAdvance(obs_time_display)
        x = (self.width() - text_width) // 2
        y = self.height() - 20  # Position the text 20 pixels from the bottom

        self.draw_text_with_outline(painter, obs_time_display, x, y, font_size, outline_width)

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

