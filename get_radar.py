import os
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import matplotlib.pyplot as plt
import geopandas as gpd
import matplotlib.patches as patches
from math import log, tan, pi
import math
import pandas as pd
import urllib.request
import zipfile
import os
import time
from datetime import datetime
import schedule
from datetime import datetime
import glob
import json

TILE_SIZE = 256  # Tile dimensions in pixels
WEB_MERCATOR_EPSG = 3857  # Web Mercator projection
MILES_TO_METERS = 1609.34  # Conversion factor

# Load settings from JSON
def load_settings(file_path):
    try:
        with open(file_path, 'r') as file:
            settings = json.load(file)
            return settings
    except FileNotFoundError:
        print(f"Error: Settings file '{file_path}' not found.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON in settings file '{file_path}'.")
        exit(1)

# Load settings
settings_path = "./settings.json"  # Path to your settings.json file
settings = load_settings(settings_path)

# Extract values from settings
API_KEY = settings.get("api_key")
latitude = settings.get("lat", 47.6)  # Default: Seattle latitude
longitude = settings.get("lon", -122.3)  # Default: Seattle longitude
radius_miles = settings.get("zoom_miles", 200)  # Default: 200 miles

# Validate critical settings
if not API_KEY:
    print("Error: API key is missing in settings.json.")
    exit(1)

# Example: Verify loaded settings
print(f"Loaded settings: Latitude={latitude}, Longitude={longitude}, Radius Miles={radius_miles}, API Key={API_KEY}")

# Convert latitude/longitude to Web Mercator coordinates
def latlon_to_web_mercator(lat, lon):
    print("latlon_to_web_mercator")
    x = lon * 20037508.34 / 180  # Longitude to meters
    y = (
        20037508.34
        * log(tan((90 + lat) * pi / 360))
        / pi
        if abs(lat) < 90
        else 20037508.34
    )  # Latitude to meters
    return x, y

# Calculate the appropriate zoom level for a given radius
def calculate_zoom(radius_miles):
    print("calculate_zoom")
    square_size_meters = radius_miles * MILES_TO_METERS * 2  # Total square size in meters
    earth_circumference_meters = 40075016.68

    for zoom in range(10):  # Zoom levels from 0 to 9
        tile_size = earth_circumference_meters / (2**zoom)  # Tile size in meters
        # Calculate number of tiles intersecting the square in both x and y directions
        tiles_in_x = square_size_meters / tile_size
        tiles_in_y = square_size_meters / tile_size
        total_tiles = math.ceil(tiles_in_x) * math.ceil(tiles_in_y)  # Round up to include partial tiles

        #I like to use between 16 and 32 but for testing we'll set it to 4-8

        if 4 <= total_tiles <= 8:  # Ensure total tiles fall within the target range
            print(f"Selected Zoom Level: {zoom}")
            print(f"Tile Size: {tile_size:.2f} meters, Total Tiles: {total_tiles}")
            return zoom

    # Default to maximum zoom level if no match is found
    print("Defaulting to maximum zoom level: 9")
    return 9

# Determine which tiles intersect the square area of interest
def get_tiles_in_square(lat, lon, radius_miles, zoom):
    print("get_tiles_in_square")
    # Convert center latitude/longitude to Web Mercator
    x_center, y_center = latlon_to_web_mercator(lat, lon)

    # Calculate square size in meters
    square_size = radius_miles * MILES_TO_METERS * 2

    # Calculate square bounds in Web Mercator
    x_min = x_center - square_size / 2
    x_max = x_center + square_size / 2
    y_min = y_center - square_size / 2
    y_max = y_center + square_size / 2

    # Calculate tile size in meters at the given zoom level
    earth_circumference_meters = 40075016.68
    tile_size = earth_circumference_meters / (2**zoom)

    # Determine tile range
    x_tile_min = int((x_min + 20037508.34) // tile_size)
    x_tile_max = int((x_max + 20037508.34) // tile_size)
    y_tile_min = int((20037508.34 - y_max) // tile_size)
    y_tile_max = int((20037508.34 - y_min) // tile_size)

    # Generate list of intersecting tiles
    tiles = [
        (x, y)
        for x in range(x_tile_min, x_tile_max + 1)
        for y in range(y_tile_min, y_tile_max + 1)
    ]

    print(f"[DEBUG] Intersecting Tiles: {tiles}")
    return tiles

def fetch_specific_local_tiles(tiles, zoom, layer, timestamp):
    print(f"fetch_specific_local_tiles for layer: {layer}")
    # Ensure the output folder exists
    output_folder = "./weathertiles/"
    os.makedirs(output_folder, exist_ok=True)

    # Calculate local mosaic dimensions
    x_tile_min = min(tile[0] for tile in tiles)
    x_tile_max = max(tile[0] for tile in tiles)
    y_tile_min = min(tile[1] for tile in tiles)
    y_tile_max = max(tile[1] for tile in tiles)

    width = (x_tile_max - x_tile_min + 1) * TILE_SIZE
    height = (y_tile_max - y_tile_min + 1) * TILE_SIZE
    mosaic = Image.new("RGBA", (width, height))

    for x, y in tiles:
        tile_url = f"https://tile.openweathermap.org/map/{layer}/{zoom}/{x}/{y}.png?appid={API_KEY}"
        print(f"Fetching tile ({x}, {y}) from {tile_url}")

        for attempt in range(3):  # Retry up to 3 times
            try:
                response = requests.get(tile_url, timeout=10)  # Set timeout
                if response.status_code == 200:
                    tile_image = Image.open(BytesIO(response.content))

                    # Calculate pixel position in the mosaic
                    x_pixel = (x - x_tile_min) * TILE_SIZE
                    y_pixel = (y - y_tile_min) * TILE_SIZE

                    # Paste the tile onto the mosaic
                    mosaic.paste(tile_image, (x_pixel, y_pixel))
                    break  # Exit retry loop on success
                else:
                    print(f"Failed to fetch tile ({x}, {y}): HTTP {response.status_code}")
                    break  # No need to retry if server responded
            except requests.exceptions.SSLError as e:
                print(f"SSL Error fetching tile ({x}, {y}): {e}")
            except requests.exceptions.RequestException as e:
                print(f"Request Error fetching tile ({x}, {y}): {e}")
            except Exception as e:
                print(f"Unexpected error fetching tile ({x}, {y}): {e}")
            
            print(f"Retrying ({attempt + 1}/3)...")
        else:
            print(f"Failed to fetch tile ({x}, {y}) after 3 attempts.")

    # Save the stitched mosaic to the output folder
    #output_filename = os.path.join(output_folder, f"{timestamp}_{layer}.png")
    #print(f"Saving mosaic for layer {layer} to {output_filename}")
    #mosaic.save(output_filename)

    return mosaic, x_tile_min, y_tile_min

# Load and filter boundaries
def load_boundaries():
    #Thanks to https://www.naturalearthdata.com/downloads/10m-cultural-vectors/ for the shapes!

    print("load_boundaries")
    # Paths to shapefiles
    country_shapefile_path = "./shapefiles/countries/ne_10m_admin_0_countries.shp"
    state_shapefile_path = "./shapefiles/states/ne_10m_admin_1_states_provinces.shp"
    county_shapefile_path = "./shapefiles/counties/ne_10m_admin_2_counties.shp"

    # Ensure all shapefiles exist
    if not os.path.exists(country_shapefile_path):
        raise FileNotFoundError(f"Country shapefile not found at {country_shapefile_path}. Please provide it.")
    if not os.path.exists(state_shapefile_path):
        raise FileNotFoundError(f"State shapefile not found at {state_shapefile_path}. Please provide it.")
    if not os.path.exists(county_shapefile_path):
        raise FileNotFoundError(f"County shapefile not found at {county_shapefile_path}. Please provide it.")

    # Load country boundaries
    country_boundaries = gpd.read_file(country_shapefile_path)
    country_boundaries = country_boundaries.to_crs(epsg=WEB_MERCATOR_EPSG)
    country_boundaries["type"] = "country"

    # Load state boundaries
    state_boundaries = gpd.read_file(state_shapefile_path)
    state_boundaries = state_boundaries.to_crs(epsg=WEB_MERCATOR_EPSG)
    state_boundaries["type"] = "state"

    # Load county boundaries
    county_boundaries = gpd.read_file(county_shapefile_path)
    county_boundaries = county_boundaries.to_crs(epsg=WEB_MERCATOR_EPSG)
    county_boundaries["type"] = "county"

    # Combine boundaries into a single GeoDataFrame
    combined_boundaries = gpd.GeoDataFrame(
        pd.concat([country_boundaries, state_boundaries, county_boundaries], ignore_index=True),
        crs=WEB_MERCATOR_EPSG
    )

    return combined_boundaries

def fetch_all_layers(tiles, zoom, lat, lon, radius_miles, weather_map_disp_layer):
    print(f"Fetching specified layer: {weather_map_disp_layer}")

    # Map layer file names to their API keys and corresponding folder names
    layer_file_mapping = {
        "temperature_animated": ("temp_new", "temperature"),
        "wind_animated": ("wind_new", "wind"),
        "pressure_animated": ("pressure_new", "pressure"),
        "precipitation_animated": ("precipitation_new", "precipitation"),
        "clouds_animated": ("clouds_new", "clouds"),
    }

    # Validate the provided layer
    if weather_map_disp_layer not in layer_file_mapping:
        print(f"Error: Invalid file name '{weather_map_disp_layer}' specified.")
        exit(1)

    # Extract the corresponding layer key and subfolder
    layer_key, subfolder = layer_file_mapping[weather_map_disp_layer]

    # Extract just the layer name (e.g., "clouds" from "clouds_animated")
    layer_name = weather_map_disp_layer.split("_")[0]

    # Generate a timestamp for the filenames
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Load boundaries once to overlay
    boundaries = load_boundaries()

    # Split boundaries into categories for styling
    country_boundaries = boundaries[boundaries["type"] == "country"]
    state_boundaries = boundaries[boundaries["type"] == "state"]
    county_boundaries = boundaries[boundaries["type"] == "county"]

    # Fetch the mosaic for the specified layer
    mosaic, x_tile_min, y_tile_min = fetch_specific_local_tiles(tiles, zoom, layer_key, timestamp)

    # Calculate the extent for the local mosaic
    tile_size_meters = 40075016.68 / (2**zoom)
    extent = (
        x_tile_min * tile_size_meters - 20037508.34,
        (x_tile_min + mosaic.width // TILE_SIZE) * tile_size_meters - 20037508.34,
        20037508.34 - (y_tile_min + mosaic.height // TILE_SIZE) * tile_size_meters,
        20037508.34 - y_tile_min * tile_size_meters,
    )

    # Calculate square bounds in Web Mercator
    square_size = radius_miles * MILES_TO_METERS * 2
    x_marker, y_marker = latlon_to_web_mercator(lat, lon)
    x_min = x_marker - square_size / 2
    x_max = x_marker + square_size / 2
    y_min = y_marker - square_size / 2
    y_max = y_marker + square_size / 2

    # Create a figure and overlay the boundaries on the mosaic
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(
        mosaic,
        extent=extent,
        origin="upper",
    )

    # Set the background to black
    ax.set_facecolor("black")

    # Plot the boundaries with white lines
    county_boundaries.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=1)
    state_boundaries.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2)
    country_boundaries.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=3)

    # Add a red dot at the latitude/longitude point of interest
    ax.scatter(x_marker, y_marker, color='red', s=100)

    # Set plot limits to crop the region of interest
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    # Hide axes for a clean output
    ax.axis("off")

    # Save the combined image to the appropriate subfolder
    layer_folder = os.path.join("./weathertiles/", subfolder)
    os.makedirs(layer_folder, exist_ok=True)  # Ensure the subfolder exists
    output_filename = os.path.join(layer_folder, f"{timestamp}_{layer_name}.png")
    print(f"Saving combined mosaic to {output_filename}")
    fig.savefig(output_filename, bbox_inches="tight", pad_inches=0, dpi=300, facecolor="black")
    plt.close(fig)  # Free memory

    # Resize and crop the image to 720x480
    crop_to_aspect_ratio(output_filename, target_width=720, target_height=360)

    # Generate a GIF for the specified layer with a 2-second delay between frames
    generate_gif_from_images(layer_folder, "animated", delay_between_frames=500)



def crop_to_aspect_ratio(image_path, target_width, target_height):
    print(f"Cropping {image_path} to aspect ratio {target_width}:{target_height}")
    
    # Open the image
    img = Image.open(image_path)
    original_width, original_height = img.size
    target_aspect = target_width / target_height
    original_aspect = original_width / original_height

    if original_aspect > target_aspect:
        # Wider than target aspect ratio, crop width
        new_width = int(target_aspect * original_height)
        offset = (original_width - new_width) // 2
        box = (offset, 0, offset + new_width, original_height)
    else:
        # Taller than target aspect ratio, crop height
        new_height = int(original_width / target_aspect)
        offset = (original_height - new_height) // 2
        box = (0, offset, original_width, offset + new_height)

    # Crop the image
    cropped_img = img.crop(box)

    # Resize the image to the target dimensions
    cropped_img = cropped_img.resize((target_width, target_height), Image.LANCZOS)

    # Extract the timestamp from the filename
    filename = os.path.basename(image_path)
    timestamp_str = filename.split("_")[0]  # Assumes the filename starts with YYYYMMDDHHMMSS
    time_str = f"{timestamp_str[8:10]}:{timestamp_str[10:12]}"  # Extract HH:MM

    # Add the timestamp with an outline to the bottom-left corner
    draw = ImageDraw.Draw(cropped_img)
    font_size = 36  # Adjust font size as needed
    try:
        font = ImageFont.truetype("./fonts/StarJR.ttf", font_size)  # Use a default system font
    except IOError:
        font = ImageFont.load_default()  # Fallback to default font if arial is not found

    # Calculate text position
    text_position = (10, target_height - font_size - 10)  # Bottom-left corner with padding

    # Draw outline
    outline_color = "black"
    fill_color = "white"
    x, y = text_position

    # Draw the text outline (shifted in 8 directions)
    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)]:
        draw.text((x + dx, y + dy), time_str, font=font, fill=outline_color)

    # Draw the filled text
    draw.text(text_position, time_str, font=font, fill=fill_color)

    # Save the updated image
    cropped_img.save(image_path)
    print(f"Cropped, resized, and annotated image saved to {image_path}")

    # Check and delete old images if count exceeds 10
    directory = os.path.dirname(image_path)
    png_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".png")]
    max_radar_frames=24
    if len(png_files) > max_radar_frames:
        # Sort files by modification time
        png_files.sort(key=os.path.getmtime)
        files_to_delete = png_files[:-max_radar_frames]  # Keep the 10 most recent files
        for file in files_to_delete:
            os.remove(file)
            print(f"Deleted old image: {file}")

def generate_gif_from_images(parent_folder, output_filename_suffix, delay_between_frames=2000):
    """
    Generate a GIF from all .png files in subfolders of the parent folder's parent directory.
    
    Args:
        parent_folder (str): The subfolder path that needs to step up one level.
        output_filename_suffix (str): The suffix to add to the GIF filename (e.g., 'animated').
        delay_between_frames (int): Delay between frames in milliseconds (default: 2000ms).
    """
    # Step up one level to the parent directory
    actual_parent_folder = os.path.dirname(parent_folder)
    print(f"Adjusted parent folder: {actual_parent_folder}")

    # Find subfolders within the adjusted parent folder
    subfolders = [
        os.path.join(actual_parent_folder, sub)
        for sub in os.listdir(actual_parent_folder)
        if os.path.isdir(os.path.join(actual_parent_folder, sub))
    ]
    print(f"Identified subfolders: {subfolders}")

    if not subfolders:
        print(f"No subfolders found in {actual_parent_folder}. Exiting GIF generation.")
        return

    for subfolder in subfolders:
        print(f"Processing images in subfolder: {subfolder}")

        # Collect all .png files in the current subfolder
        png_files = sorted(glob.glob(os.path.join(subfolder, "*.png")), key=os.path.getmtime)
        print(f"Found PNG files in {subfolder}: {png_files}")

        if not png_files:
            print(f"No .png files found in {subfolder}. Skipping...")
            continue

        # Open all images as PIL Image objects
        images = [Image.open(file) for file in png_files]

        # Output GIF filename
        subfolder_name = os.path.basename(subfolder)
        gif_output_path = os.path.join(actual_parent_folder, f"{subfolder_name}_{output_filename_suffix}.gif")

        # Save as GIF with a delay between frames
        images[0].save(
            gif_output_path,
            save_all=True,
            append_images=images[1:],
            duration=delay_between_frames,
            loop=0,
        )
        print(f"GIF saved to {gif_output_path}")

def main():
    start_time = time.time()  # Record the start time

    # Load settings
    settings_path = "./settings.json"  # Path to your settings.json file
    settings = load_settings(settings_path)

    # Extract values from settings
    API_KEY = settings.get("api_key")
    latitude = settings.get("lat", 47.6)  # Default: Seattle latitude
    longitude = settings.get("lon", -122.3)  # Default: Seattle longitude
    radius_miles = settings.get("zoom_miles", 200)  # Default: 200 miles
    weather_map_disp_layer = settings.get("weather_map_disp_layer")

    # Validate critical settings
    if not API_KEY:
        print("Error: API key is missing in settings.json.")
        exit(1)

    # Calculate the appropriate zoom level
    zoom = calculate_zoom(radius_miles)

    # Get tiles for the specified area
    tiles = get_tiles_in_square(latitude, longitude, radius_miles, zoom)

    # Fetch and save mosaics for the specified layer
    fetch_all_layers(tiles, zoom, latitude, longitude, radius_miles, weather_map_disp_layer)


    print("All mosaics with boundaries generated and saved.")

    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print(f"Total execution time: {elapsed_time:.2f} seconds")

# Run main
main()


