
# GeoAgent — GIS Location Analysis Dashboard

GeoAgent is a Python-based interactive GIS dashboard built with Streamlit and Folium. It helps users explore locations, visualize them on interactive maps, and calculate road-network distances.

## Features

- Load location data from a CSV file.
- Search and select locations.
- Interactive maps with multiple basemap options.
- Calculate road distance and estimated driving time using OSRM.
- Find nearby locations within a selected road-distance limit.
- View nearby search results in a table and on a map.

## Technologies Used

- Python
- Streamlit
- Pandas
- Folium
- Streamlit-Folium
- Requests
- OpenStreetMap-compatible basemaps
- OSRM Routing Service

## Project Structure

```text
Geo_Agent/
├── Geo_Agent_app.py
├── india_cities.csv
├── requirements.txt
├── README.md
└── .venv/
```

## Installation

### 1. Open the project folder

Open the Geo_Agent folder in VS Code.

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Run the application

```bash
python -m streamlit run Geo_Agent_app.py
```

## Data Requirements

The CSV dataset should contain these columns:

- `name`
- `latitude`
- `longitude`
- `type`

Latitude and longitude must contain valid geographic coordinates.

## Routing Information

GeoAgent uses the public OSRM routing service to calculate road distances and estimated driving times. The estimates do not include live traffic conditions. The public service may impose usage limits, so avoid excessive requests.

## Future Improvements

- Location-type filters
- Advanced spatial analysis
- Improved dashboard design
- Deployment as a public web application


Developed as a GIS and geospatial technology project.
