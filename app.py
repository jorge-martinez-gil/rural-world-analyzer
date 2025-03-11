import streamlit as st
import osmnx as ox
import folium
from folium.plugins import MarkerCluster, HeatMap
import pandas as pd
from streamlit_folium import st_folium
import math
import logging

logging.basicConfig(level=logging.ERROR)

RADIUS_DEFAULT = 1000  # Default radius (between 300 and 3000 meters)
example_coordinates = {
    "Hagenberg, Austria": (48.36964, 14.5128),
    "Lienz, Austria": (46.8294, 12.7687),
}

map_themes = {
    "OpenStreetMap": "OpenStreetMap",
    "Stamen Terrain": "Stamen Terrain",
    "Stamen Toner": "Stamen Toner",
    "CartoDB Positron": "CartoDB positron",
    "CartoDB Dark Matter": "CartoDB dark_matter"
}

def compute_zoom_level(radius: int) -> int:
    if radius < 500:
        return 15
    zoom = 15 - int(math.log(radius / 500, 2))
    return max(10, min(zoom, 18))

@st.cache_data(show_spinner=False)
def get_amenities(latitude: float, longitude: float, amenity_type: str = 'all', radius: int = RADIUS_DEFAULT) -> pd.DataFrame:
    tags = {'amenity': True} if amenity_type == 'all' else {'amenity': amenity_type}
    try:
        # Use the new features_from_point function
        return ox.features_from_point((latitude, longitude), tags=tags, dist=radius)
    except Exception as e:
        error_message = f"Error fetching amenities: {e}"
        st.error(error_message)
        logging.error(error_message)
        return pd.DataFrame()

def add_markers_to_map(folium_map: folium.Map, amenities: pd.DataFrame, amenity_type: str) -> None:
    marker_cluster = MarkerCluster().add_to(folium_map)
    for _, row in amenities.iterrows():
        geom = row.geometry
        if not geom:
            continue
        if geom.geom_type == 'Point':
            coords = [geom.y, geom.x]
        elif geom.geom_type in ['Polygon', 'MultiPolygon']:
            coords = [geom.centroid.y, geom.centroid.x]
        else:
            continue
        name = row.get('name', 'N/A')
        tooltip = f"{amenity_type.capitalize()}: {name}"
        folium.Marker(location=coords, popup=tooltip, tooltip=tooltip).add_to(marker_cluster)

def add_heatmap_to_map(folium_map: folium.Map, amenities: pd.DataFrame) -> None:
    heat_data = []
    for _, row in amenities.iterrows():
        geom = row.geometry
        if not geom:
            continue
        if geom.geom_type == 'Point':
            heat_data.append([geom.y, geom.x])
        elif geom.geom_type in ['Polygon', 'MultiPolygon']:
            heat_data.append([geom.centroid.y, geom.centroid.x])
    if heat_data:
        HeatMap(heat_data).add_to(folium_map)

def main():
    st.title("Rural World Analyzer")
    st.markdown("This application helps you analyze rural areas by displaying nearby amenities on an interactive map.")

    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    st.sidebar.markdown("**Select a Test Area**")
    test_area = st.sidebar.selectbox("Test Area:", list(example_coordinates.keys()))
    selected_coords = example_coordinates[test_area]
    
    st.sidebar.markdown("**Set Coordinates**")
    lat = st.sidebar.number_input("Latitude:", value=selected_coords[0])
    lon = st.sidebar.number_input("Longitude:", value=selected_coords[1])
    
    st.sidebar.markdown("**Choose Amenity Type**")
    amenity_type = st.sidebar.selectbox(
        "Amenity Type:",
        ['all', 'restaurant', 'hospital', 'school', 'bank', 'cafe', 'pharmacy', 'cinema', 'parking', 'fuel']
    )
    
    st.sidebar.markdown("**Map Settings**")
    map_theme = st.sidebar.selectbox("Map Theme:", list(map_themes.keys()))
    radius = st.sidebar.number_input("Radius (meters):", value=RADIUS_DEFAULT, min_value=300, max_value=3000)
    show_markers = st.sidebar.checkbox("Show Markers", value=True)
    show_heatmap = st.sidebar.checkbox("Show Heatmap", value=True)

    # Initialize session state flag for amenities display
    if "show_amenities" not in st.session_state:
        st.session_state.show_amenities = False

    if st.sidebar.button("Show Amenities"):
        st.session_state.show_amenities = True

    if st.session_state.show_amenities:
        with st.spinner("Fetching amenities..."):
            amenities = get_amenities(lat, lon, amenity_type, radius)
        
        if amenities.empty:
            st.warning("No amenities found in the selected area.")
        else:
            zoom_level = compute_zoom_level(radius)
            tiles = map_themes.get(map_theme, "OpenStreetMap")
            folium_map = folium.Map(location=[lat, lon], zoom_start=zoom_level, tiles=tiles)
            
            # Draw a blue circle covering the search area.
            folium.Circle(
                location=[lat, lon],
                radius=radius,
                color="blue",
                fill=True,
                fill_opacity=0.1,
                popup=f"Radius: {radius} m"
            ).add_to(folium_map)
            
            if show_markers:
                add_markers_to_map(folium_map, amenities, amenity_type)
            if show_heatmap:
                add_heatmap_to_map(folium_map, amenities)
            
            st.markdown("### Interactive Map")
            st_folium(folium_map, width=700, height=500)

if __name__ == "__main__":
    main()


