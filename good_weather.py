import argparse
import folium.plugins
import folium
import logging
import math
import matplotlib.pyplot as plt
import numpy as np
import requests
import tqdm
from scipy.interpolate import griddata


def get_bounding_box(latitude, longitude, radius):
    # Earth's radius in miles
    R = 3958.8

    # Convert radius to radians
    rad = radius / R

    # Convert latitude and longitude from degrees to radians
    lat = math.radians(latitude)
    lon = math.radians(longitude)

    # Calculate bounding box
    min_lat = lat - rad
    max_lat = lat + rad
    min_lon = lon - rad / math.cos(lat)
    max_lon = lon + rad / math.cos(lat)

    # Convert back to degrees
    min_lat = math.degrees(min_lat)
    max_lat = math.degrees(max_lat)
    min_lon = math.degrees(min_lon)
    max_lon = math.degrees(max_lon)

    return (min_lat, max_lat, min_lon, max_lon)


# Example usage
latitude = 37.7749  # Example latitude (New York City)
longitude = -122.4194  # Example longitude (New York City)
radius = 500  # Radius in miles

# Constants
OPENWEATHERMAP_API_KEY = open("API_KEY").read().strip()
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = get_bounding_box(latitude, longitude,
                                                      radius)


# Step 1: Fetch Weather Data
def fetch_weather_data(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    return data


# Step 2: Compute Scalar Values
def compute_scalar_values(weather_data):
    total_temp = 0
    total_sun_exposure = 0
    count = 0

    for item in weather_data['list']:
        temp = item['main']['temp']
        clouds = item['clouds']['all']
        sun_exposure = 1 - clouds / 100

        temp = temp * 9 / 5 + 32

        weighted_temp = (temp - 40) / 30  # Scaled between 0 and 1
        weighted_sun_exposure = sun_exposure

        total_temp += weighted_temp
        total_sun_exposure += weighted_sun_exposure
        count += 1

    avg_temp = total_temp / count
    avg_sun_exposure = total_sun_exposure / count

    scalar_value = (avg_temp + avg_sun_exposure) / 2
    return scalar_value, avg_temp * 30 + 40, avg_sun_exposure  # returning actual average temp and sun exposure


# Step 3: Bilinear Interpolation
def interpolate_values(coordinates, values, num_points=100):
    latitudes = [coord[0] for coord in coordinates]
    longitudes = [coord[1] for coord in coordinates]
    grid_x, grid_y = np.mgrid[LAT_MIN:LAT_MAX:num_points * 1j,
                              LON_MIN:LON_MAX:num_points * 1j]
    grid_z = griddata((latitudes, longitudes),
                      values, (grid_x, grid_y),
                      method='linear')
    return grid_x, grid_y, grid_z


# Step 4 & 5: Fetch Map Data and Overlay Heatmap
def create_heatmap(lat, lon, interpolated_values):
    map_folium = folium.Map(location=[lat, lon], zoom_start=10)
    folium.TileLayer('cartodbpositron').add_to(map_folium)

    # Interpolated values
    grid_x, grid_y, grid_z = interpolated_values

    # Convert the grid data into (lat, lon, value) triplets for plotting
    data = [[grid_x[i, j], grid_y[i, j], grid_z[i, j]]
            for i in range(grid_x.shape[0]) for j in range(grid_x.shape[1])
            if not np.isnan(grid_z[i, j])]

    # Add heatmap
    folium.plugins.HeatMap(data).add_to(map_folium)

    return map_folium


# Main Function
def main():
    # Setup basic logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Command line argument parsing
    parser = argparse.ArgumentParser(description='Generate a Weather Heatmap.')
    parser.add_argument(
        '--num-points',
        type=int,
        default=10,
        help='Number of points to sample in each dimension (default: 10)')
    args = parser.parse_args()
    num_points = args.num_points

    logging.info("Starting Heatmap Generation")
    coordinates = [(lat, lon)
                   for lat in np.linspace(LAT_MIN, LAT_MAX, num=num_points)
                   for lon in np.linspace(LON_MIN, LON_MAX, num=num_points)]

    weather_data = []
    scalar_values = []
    for lat, lon in tqdm.tqdm(coordinates, desc="Processing"):
        data = fetch_weather_data(lat, lon)
        weather_data.append(data)
        scalar_value, avg_temp, avg_sun_exposure = compute_scalar_values(data)
        logging.info(
            f"Grid Point ({lat}, {lon}) - Avg Temp: {avg_temp:.2f}°F, Sun Exposure: {avg_sun_exposure:.2f}"
        )
        # Store or process the scalar value as needed
        scalar_values.append(scalar_value)

    interpolated_values = interpolate_values(coordinates, scalar_values,
                                             num_points)

    center_lat = (LAT_MIN + LAT_MAX) / 2
    center_lon = (LON_MIN + LON_MAX) / 2

    heatmap = create_heatmap(center_lat, center_lon, interpolated_values)
    heatmap.save('heatmap.html')
    logging.info("Heatmap Generated and Saved")


main()
