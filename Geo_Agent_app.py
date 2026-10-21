import math
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import requests
import os

st.set_page_config(page_title="GeoAgent", layout="wide")

st.title("🌍 GeoAgent GIS Dashboard")
st.write("Your GIS AI Agent — Interactive Location Explorer")


# Load and cache the default dataset
@st.cache_data
def load_locations(file_path, file_modified):
    return pd.read_csv(file_path)

if st.sidebar.button("🔄 Refresh CSV Data"):
    st.cache_data.clear()
    st.rerun()


# Sidebar: upload GIS data
st.sidebar.header("📂 Upload GIS Data")
st.sidebar.divider()
show_all_locations = st.sidebar.checkbox(
    "🌍 Show all Indian locations",
    value=False,
    help="Display all locations using clustered markers."
)

uploaded_file = st.sidebar.file_uploader(
    "Upload a CSV file",
    type=["csv"]
)

import os

try:
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        csv_path = "india_cities.csv"
        file_modified = os.path.getmtime(csv_path)
        df = load_locations(csv_path, file_modified)

except Exception as e:
    st.error(f"Could not load the CSV file: {e}")
    st.stop()

# Validate required columns
required_columns = ["name", "latitude", "longitude", "type"]

if not all(col in df.columns for col in required_columns):
    st.error(
        "CSV must contain these columns: "
        "name, latitude, longitude, type"
    )
    st.stop()


# Clean and validate coordinates
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

df = df.dropna(subset=["name", "latitude", "longitude"])

df = df[
    df["latitude"].between(-90, 90)
    & df["longitude"].between(-180, 180)
].copy()

if df.empty:
    st.error("No valid location records found in the CSV.")
    st.stop()


city_options = sorted(
    df["name"].dropna().astype(str).unique().tolist()
)

st.subheader("📍 Interactive GIS Map")

search_text = st.text_input(
    "🔍 Search for an Indian city or town",
    placeholder="Type a name, e.g. Kolkata, Mumbai, Jaipur"
)

if search_text.strip():
    filtered_cities = [
        name for name in city_options
        if search_text.strip().casefold() in name.casefold()
    ]
else:
    filtered_cities = city_options

if not filtered_cities:
    st.warning("No matching locations found. Try another name.")
    st.stop()

selected_city = st.selectbox(
    "Choose a location",
    filtered_cities
)

city = df[
    df["name"].astype(str) == selected_city
].iloc[0]

city = df[df["name"].astype(str) == selected_city].iloc[0]
st.subheader("📊 Selected Location Details")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Latitude", f"{city['latitude']:.4f}°")

with col2:
    st.metric("Longitude", f"{city['longitude']:.4f}°")

with col3:
    st.metric("Location Type", str(city["type"]))


# Create a lightweight map with only the selected city's marker
# --------------------------------------------------
# BASEMAP SELECTOR
# --------------------------------------------------

st.sidebar.subheader("🗺️ Map Settings")

basemap_options = {
    "OpenStreetMap": "OpenStreetMap",
    "CartoDB Positron (Light)": "CartoDB positron",
    "CartoDB Dark": "CartoDB dark_matter",
    "CartoDB Voyager": (
        "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/"
        "{z}/{x}/{y}{r}.png"
    ),
    "OpenTopoMap": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    "Esri World Imagery": (
        "https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{z}/{y}/{x}"
    ),
    "OpenStreetMap HOT": (
        "https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"
    ),
}

basemap_attributions = {
    "CartoDB Voyager": (
        "© OpenStreetMap contributors © CARTO"
    ),
    "OpenTopoMap": (
        "Map data: © OpenStreetMap contributors, SRTM | "
        "Map style: © OpenTopoMap (CC-BY-SA)"
    ),
    "Esri World Imagery": (
        "Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, "
        "and the GIS User Community"
    ),
    "OpenStreetMap HOT": (
        "© OpenStreetMap contributors, Tiles style by Humanitarian "
        "OpenStreetMap Team"
    ),
}

selected_basemap = st.sidebar.selectbox(
    "Choose a basemap",
    list(basemap_options.keys()),
    index=0
)

# --------------------------------------------------
# MAP DISPLAY: SELECTED CITY OR ALL LOCATIONS
# --------------------------------------------------

city_map = folium.Map(
    location=[
        float(city["latitude"]),
        float(city["longitude"])
    ],
    zoom_start=5 if show_all_locations else 8,
    tiles=basemap_options[selected_basemap],
    attr=basemap_attributions.get(selected_basemap),
    prefer_canvas=True
)

if show_all_locations:
    # Cluster nearby locations for better performance
    marker_cluster = MarkerCluster().add_to(city_map)

    for _, row in df.iterrows():
        folium.Marker(
            location=[
                float(row["latitude"]),
                float(row["longitude"])
            ],
            tooltip=str(row["name"]),
            popup=f'{row["name"]} - {row["type"]}'
        ).add_to(marker_cluster)

else:
    # Display only the selected city's marker
    folium.Marker(
        location=[
            float(city["latitude"]),
            float(city["longitude"])
        ],
        tooltip=str(city["name"]),
        popup=f'{city["name"]} - {city["type"]}',
        icon=folium.Icon(
            color="red",
            icon="info-sign"
        )
    ).add_to(city_map)



# Selected city information
col1, col2, col3 = st.columns(3)

col1.metric("Selected City", city["name"])
col2.metric("Latitude", f'{city["latitude"]:.4f}')
col3.metric("Longitude", f'{city["longitude"]:.4f}')


# Display map
st_folium(
    city_map,
    width=None,
    height=480,
    key=f"geoagent_map_{selected_city}"
)


# Location statistics
st.subheader("📊 Location Statistics")

col1, col2, col3 = st.columns(3)

col1.metric("Total Locations", len(df))
col2.metric("Unique Names", df["name"].nunique())
col3.metric("Location Type", str(city["type"]))


# Show dataset
st.divider()
st.subheader("📋 All Location Data")

with st.expander("View location records"):
    st.dataframe(df, width="stretch")

st.success(f"Successfully loaded {len(df):,} locations!")


# Distance calculator

# ==========================================
# REAL ROAD DISTANCE & ROUTING USING OSRM
# ==========================================

st.divider()
st.subheader("🛣️ Real Road Distance & Route Analysis")
st.write("Calculate driving distance and estimated travel time between locations.")

city_names = sorted(df["name"].dropna().astype(str).unique().tolist())

if len(city_names) < 2:
    st.warning("At least two locations are required for routing.")
else:
    col1, col2 = st.columns(2)

    with col1:
        start_city = st.selectbox(
            "📍 Starting City",
            city_names,
            index=city_names.index("Kolkata")
            if "Kolkata" in city_names else 0,
            key="road_start"
        )

    destination_options = [
        name for name in city_names if name != start_city
    ]

    with col2:
        destination_city = st.selectbox(
            "🏁 Destination City",
            destination_options,
            index=destination_options.index("Delhi")
            if "Delhi" in destination_options else 0,
            key="road_destination"
        )

    start = df[df["name"].astype(str) == start_city].iloc[0]
    end = df[df["name"].astype(str) == destination_city].iloc[0]

    start_lat = float(start["latitude"])
    start_lon = float(start["longitude"])
    end_lat = float(end["latitude"])
    end_lon = float(end["longitude"])

    saved_route = st.session_state.get("road_route")
    if saved_route and (
        saved_route["start_city"] != start_city
        or saved_route["destination_city"] != destination_city
    ):
        st.session_state.pop("road_route")
        saved_route = None

    if st.button("🚗 Calculate Road Route", type="primary"):
        st.session_state.pop("road_route", None)

        url = (
            "https://router.project-osrm.org/route/v1/driving/"
            f"{start_lon},{start_lat};{end_lon},{end_lat}"
        )

        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false"
        }

        try:
            with st.spinner("Finding the road route..."):
                response = requests.get(
                    url, params=params, timeout=30
                )
                response.raise_for_status()
                result = response.json()

            if result.get("code") != "Ok" or not result.get("routes"):
                st.error(
                    "No road route found for these locations. "
                    "Try selecting different cities."
                )
            else:
                route = result["routes"][0]
                route_coords = route["geometry"]["coordinates"]
                if len(route_coords) < 2:
                    st.error("The routing service returned an incomplete route.")
                else:
                    st.session_state["road_route"] = {
                        "start_city": start_city,
                        "destination_city": destination_city,
                        "distance_m": route["distance"],
                        "duration_s": route["duration"],
                        "coordinates": route_coords,
                    }

        except requests.RequestException as e:
            st.error(
                f"Could not connect to the routing service: {e}. "
                "Check your internet connection and try again."
            )
        except (KeyError, IndexError, TypeError, ValueError) as e:
            st.error(f"Could not process the route response: {e}")

    saved_route = st.session_state.get("road_route")
    if saved_route:
        distance_km = saved_route["distance_m"] / 1000
        duration_min = saved_route["duration_s"] / 60

        metric1, metric2 = st.columns(2)
        metric1.metric("🛣️ Road Distance", f"{distance_km:,.2f} km")

        hours = int(duration_min // 60)
        minutes = int(duration_min % 60)
        metric2.metric(
            "⏱️ Estimated Driving Time",
            f"{hours} h {minutes} min"
        )

        # OSRM returns GeoJSON coordinates as [longitude, latitude].
        route_coords = [
            [lat, lon]
            for lon, lat in saved_route["coordinates"]
        ]
        route_map = folium.Map(
            location=[(start_lat + end_lat) / 2, (start_lon + end_lon) / 2],
            zoom_start=5,
            tiles=basemap_options[selected_basemap],
            attr=basemap_attributions.get(selected_basemap),
        )
        folium.Marker(
            [start_lat, start_lon],
            tooltip=f"Start: {start_city}",
            icon=folium.Icon(color="green", icon="play")
        ).add_to(route_map)
        folium.Marker(
            [end_lat, end_lon],
            tooltip=f"Destination: {destination_city}",
            icon=folium.Icon(color="red", icon="flag")
        ).add_to(route_map)
        folium.PolyLine(
            route_coords,
            color="blue",
            weight=5,
            opacity=0.85,
            tooltip=f"Road distance: {distance_km:,.2f} km"
        ).add_to(route_map)
        route_map.fit_bounds(route_coords)

        st_folium(
            route_map,
            width=None,
            height=500,
            key="osrm_road_route_map"
        )
        st.caption(
            "Routing provided by OSRM. Driving time is an estimate, "
            "not a live traffic prediction."
        )


# ==========================================
# NEARBY LOCATIONS FINDER - ROAD DISTANCE
# ==========================================

st.divider()
st.subheader("📍 Nearby Locations Finder")
st.write(
    "Find locations reachable within your chosen driving-distance limit."
)

# Cache road-distance responses for one hour
@st.cache_data(ttl=3600)
def get_osrm_table(origin_lon, origin_lat, destinations):
    coordinates = [(origin_lon, origin_lat)] + list(destinations)

    coordinate_text = ";".join(
        f"{lon},{lat}" for lon, lat in coordinates
    )

    url = (
        "https://router.project-osrm.org/table/v1/driving/"
        + coordinate_text
    )

    destination_indexes = ";".join(
        str(i) for i in range(1, len(coordinates))
    )

    response = requests.get(
        url,
        params={
            "sources": "0",
            "destinations": destination_indexes,
            "annotations": "distance,duration"
        },
        timeout=30
    )
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok":
        raise ValueError(
            f"OSRM could not calculate distances: {data.get('code')}"
        )

    return data["distances"][0], data["durations"][0]


# Calculate straight-line distance only to shortlist candidates
def straight_distance_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(
        math.radians, [lat1, lon1, lat2, lon2]
    )
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )
    a = max(0.0, min(1.0, a))
    return 6371 * 2 * math.asin(math.sqrt(a))


nearby_city_names = sorted(
    df["name"].dropna().astype(str).unique().tolist()
)

if len(nearby_city_names) < 2:
    st.warning("At least two locations are required.")
else:
    near_col1, near_col2 = st.columns(2)

    with near_col1:
        nearby_origin = st.selectbox(
            "📌 Search from",
            nearby_city_names,
            index=(
                nearby_city_names.index("Kolkata")
                if "Kolkata" in nearby_city_names else 0
            ),
            key="nearby_origin"
        )

    with near_col2:
        radius_km = st.slider(
            "🚗 Maximum road distance (km)",
            min_value=5,
            max_value=200,
            value=50,
            step=5,
            key="nearby_radius"
        )

    origin_row = df[
        df["name"].astype(str) == nearby_origin
    ].iloc[0]

    origin_lat = float(origin_row["latitude"])
    origin_lon = float(origin_row["longitude"])

    st.caption(
        "For performance, the search checks up to 50 closest "
        "straight-line candidates before applying the road-distance limit."
    )

    if st.button(
        "🔎 Find Nearby Locations",
        type="primary",
        key="find_nearby_locations"
    ):
        try:
            with st.spinner("Calculating road distances..."):

                # Straight-line distance is a safe initial filter:
                # road distance cannot be shorter than straight-line distance.
                candidates = df[
                    df["name"].astype(str) != nearby_origin
                ].copy()

                candidates["straight_km"] = candidates.apply(
                    lambda row: straight_distance_km(
                        origin_lat,
                        origin_lon,
                        float(row["latitude"]),
                        float(row["longitude"])
                    ),
                    axis=1
                )

                candidates = candidates[
                    candidates["straight_km"] <= radius_km
                ].sort_values("straight_km").head(50)

                if candidates.empty:
                    st.info(
                        "No locations are within this straight-line "
                        "pre-filter radius. Try a larger radius."
                    )
                else:
                    destinations = tuple(
                        (
                            float(row["longitude"]),
                            float(row["latitude"])
                        )
                        for _, row in candidates.iterrows()
                    )

                    road_distances, road_durations = get_osrm_table(
                        origin_lon,
                        origin_lat,
                        destinations
                    )

                    results = candidates.reset_index(drop=True).copy()
                    results["Road distance (km)"] = [
                        distance / 1000 if distance is not None else None
                        for distance in road_distances
                    ]
                    results["Driving time (min)"] = [
                        duration / 60 if duration is not None else None
                        for duration in road_durations
                    ]

                    results = results.dropna(
                        subset=["Road distance (km)"]
                    )
                    results = results[
                        results["Road distance (km)"] <= radius_km
                    ].sort_values("Road distance (km)")

                    st.session_state["nearby_results"] = results
                    st.session_state["nearby_origin_name"] = nearby_origin
                    st.session_state["nearby_origin_lat"] = origin_lat
                    st.session_state["nearby_origin_lon"] = origin_lon
                    st.session_state["nearby_radius_used"] = radius_km

        except requests.RequestException as e:
            st.error(
                f"Routing service connection failed: {e}. "
                "Check your internet connection and try again."
            )
        except (ValueError, KeyError, IndexError, TypeError) as e:
            st.error(f"Could not calculate nearby locations: {e}")

    # Show stored results after Streamlit reruns
    if (
        "nearby_results" in st.session_state
        and st.session_state.get("nearby_origin_name") == nearby_origin
        and st.session_state.get("nearby_radius") == radius_km
    ):
        results = st.session_state["nearby_results"]

        st.subheader("📊 Nearby Search Results")
        st.metric("Locations found", len(results))

        if results.empty:
            st.info(
                "No routable locations were found within this road radius."
            )
        else:
            display_results = results[
                [
                    "name",
                    "type",
                    "Road distance (km)",
                    "Driving time (min)"
                ]
            ].rename(columns={
                "name": "Location",
                "type": "Type"
            })

            st.dataframe(
                display_results,
                hide_index=True,
                width="stretch"
            )

            nearby_map = folium.Map(
                location=[
                    st.session_state["nearby_origin_lat"],
                    st.session_state["nearby_origin_lon"]
                ],
                zoom_start=8,
                tiles=basemap_options[selected_basemap]
            )

            folium.Marker(
                [
                    st.session_state["nearby_origin_lat"],
                    st.session_state["nearby_origin_lon"]
                ],
                tooltip=f"Search origin: {nearby_origin}",
                icon=folium.Icon(color="red", icon="home")
            ).add_to(nearby_map)

            for _, row in results.iterrows():
                distance = row["Road distance (km)"]
                duration = row["Driving time (min)"]

                folium.Marker(
                    [
                        float(row["latitude"]),
                        float(row["longitude"])
                    ],
                    tooltip=str(row["name"]),
                    popup=(
                        f'{row["name"]}<br>'
                        f'Road distance: {distance:.2f} km<br>'
                        f'Estimated driving time: {duration:.0f} min'
                    ),
                    icon=folium.Icon(color="blue", icon="map-marker")
                ).add_to(nearby_map)

            st_folium(
                nearby_map,
                width=None,
                height=450,
                key="nearby_locations_map"
            )

            st.caption(
                "The map displays the origin and nearby locations. "
                "Markers are not connected by road-route lines. "
                "Driving times are estimates without live traffic."
            )
