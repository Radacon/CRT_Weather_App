import os
import json
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap, QFont, QPainter, QFontDatabase
from PyQt5.QtCore import Qt, QTimer, QTime, QDateTime
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QLabel



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

        # Load settings
        settings_path = os.path.join(script_dir, "settings.json")
        with open(settings_path, "r") as f:
            self.settings = json.load(f)

        # Process the map display layer
        self.map_display_layer = self.settings.get("weather_map_disp_layer", "")
        if "_animated" in self.map_display_layer:
            self.map_display_layer = self.map_display_layer.replace("_animated", "").upper()

        # Timer to update time and date
        self.current_time = ""
        self.current_date = ""
        self.update_time_and_date()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_and_date)
        self.timer.start(1000)  # Update every second

        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.gif_path = os.path.join(script_dir, "weathertiles", self.settings.get("weather_map_disp_layer", "default.gif"))+".gif"
        print(self.gif_path)
        self.last_mod_time = None  # Track modification time
        
        # Create a QLabel to display the GIF
        self.gif_label = QLabel(self)
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.update_gif_display()

        # Timer to check for updates
        self.gif_timer = QTimer(self)
        self.gif_timer.timeout.connect(self.check_and_update_gif)
        self.gif_timer.start(1000)  # Check every second

    def load_weather_data(self, filepath):
        """Load weather data from the specified JSON file."""
        try:
            with open(filepath, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading weather data: {e}")
            return []  # Return an empty list if data cannot be loaded

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

        # Draw static text "Local \n Radar" at the top of the page
        static_text = "Local\nRadar"
        font_size = 30  # Font size for the static text
        outline_width = 2  # Outline thickness
        line_spacing = 10  # Additional spacing between lines in pixels
        x = 180  # X-coordinate for the text
        y = 65   # Y-coordinate for the text

        for index, line in enumerate(static_text.split("\n")):
            self.draw_text_with_outline(
                painter,
                line,
                x,
                y + index * (font_size + line_spacing),  # Add spacing between lines
                font_size,
                outline_width
            )

        display_layer = self.settings.get("weather_map_disp_layer", "").replace("_animated", "").upper()

        # Font and text details
        font_size = 24
        outline_width = 2
        x = 525 # Center of the widget
        y = 52  # Adjust vertical position as needed
        font = QFont(self.custom_font_family, font_size)
        font.setBold(True)
        painter.setFont(font)

        # Calculate text dimensions for centering
        text_width = painter.fontMetrics().horizontalAdvance(display_layer)
        text_height = painter.fontMetrics().height()

        # Center the text at (x, y)
        centered_x = x - (text_width // 2)
        centered_y = y + (text_height // 4)  # Adjust for baseline alignment

        # Draw the text with outline
        self.draw_text_with_outline(painter, display_layer, centered_x, centered_y, font_size, outline_width)
    
        # Draw time and date in the upper-right corner
        self.draw_text_with_outline(painter, self.current_time, 10, 22, 20, 1)
        self.draw_text_with_outline(painter, self.current_date, 570, 22, 20, 1)

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

    def update_gif_display(self):
        """Update the GIF display."""
        if not os.path.exists(self.gif_path):
            print(f"Error: File '{self.gif_path}' does not exist.")
            return

        # Load the GIF
        movie = QMovie(self.gif_path)
        if not movie.isValid():
            print(f"Error: Unable to load GIF '{self.gif_path}'.")
            return
        
        # Get original size
        movie.start()
        movie_width = movie.frameRect().width()
        movie_height = movie.frameRect().height()
        movie.stop()

        # Center horizontally and align bottom
        x_offset = (self.width() - movie_width) // 2
        y_offset = self.height() - movie_height
        self.gif_label.setGeometry(x_offset, y_offset, movie_width, movie_height)

        # Set the movie to the label
        self.gif_label.setMovie(movie)
        movie.start()
        print(f"GIF loaded: {self.gif_path}")

    def check_and_update_gif(self):
        """Check if the GIF file has changed and reload it if needed."""
        try:
            current_mod_time = os.path.getmtime(self.gif_path)
        except FileNotFoundError:
            print(f"Error: File '{self.gif_path}' does not exist.")
            return

        if self.last_mod_time != current_mod_time:
            self.last_mod_time = current_mod_time
            print("GIF file updated. Reloading...")
            self.update_gif_display()

