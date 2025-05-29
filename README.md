# CRT Weather App

This project transforms a New Old Stock (NOS) Cathode Ray Tube (CRT) display into a retro weather station, inspired by vintage weather displays like the WeatherStar4000+. It aims to provide a unique audio-visual-tactile experience by combining classic hardware with modern weather data.

For more details, you can refer to the original blog post: [Retro CRT Weather Display Blog Post](https://farnsworth.engineering/index.php/2025/03/17/retro-crt-weather-display/)

Watch a demonstration of the project here: [YouTube Video Demo](#)

## Features

### Hardware Features

- **Composite Video Output**: Designed to display weather information on a CRT via composite video.
- **Audio Integration**: Includes a speaker for playing music or sound effects, enhancing the retro experience.
- **Display Control**: Ability to turn the CRT display on and off.
- **Interactive Controls**: Features a rotary encoder and button for controlling volume, muting audio, and power management.
- **LED Indicators**: Incorporates LEDs for visual feedback.
- **USB to Serial UART**: Provides console access for debugging and interaction without requiring WiFi.

### Software Features

- **Dynamic Weather Display**: Graphically mimics the WeatherStar4000+ with dynamic weather elements and radar maps.

## Installation and Setup

To get this application running, you will need to:

### 1. Acquire Hardware

Obtain a suitable NOS CRT display.

### 2. Clone the Repository

```bash
git clone https://github.com/Radacon/CRT_Weather_App.git /home/dietpi/Clock
```

### 3. Configure API Key

- Obtain a weather API key from OpenWeatherMap.
- Locate the `settings.json.example` file (or similar configuration file) in the repository.
- Rename this file to `settings.json`.
- Edit `settings.json` and insert your OpenWeatherMap API key into the designated field.

Further instructions for wiring and specific hardware setup are likely detailed within the repository's documentation or the associated blog post.

## Usage

Once set up, the application will display current weather conditions and radar information on the connected CRT. The rotary encoder and button allow for interactive control over audio and display power.

## Credits

- **Adrian Black**: Inspiration for the project, particularly his work with retro CRT displays.
- **ChatGPT**: Acknowledged for generating a significant portion of the project's code (and this readme lmao)
- **Remington Bullis**: https://github.com/rembullis
- **Tristan Mullin**: https://github.com/t-mullin
- **TWCClassics.com**: https://twcclassics.com/
- **Natural Earth**: For providing shapefiles used in the radar map ([https://www.naturalearthdata.com/](https://www.naturalearthdata.com/))
