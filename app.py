import streamlit as st
import osmnx as ox
import folium
from folium.plugins import MarkerCluster, HeatMap
import pandas as pd
import plotly.express as px
from streamlit_folium import folium_static
import math

# ---------------------------
# Constants & Example Data
# ---------------------------
RADIUS_DEFAULT = 1000
example_coordinates = {
    "Hagenberg, Austria": (48.36964, 14.5128),
    "Lienz, Austria": (46.8294, 12.7687),
}

# Map theme options
map_themes = {
    "OpenStreetMap": "OpenStreetMap",
    "Stamen Terrain": "Stamen Terrain",
    "Stamen Toner": "Stamen Toner",
    "CartoDB Positron": "CartoDB positron",       # Day mode look
    "CartoDB Dark Matter": "CartoDB dark_matter"    # Night mode look
}

# ---------------------------
# Helper Functions
# ---------------------------
def compute_zoom_level(radius: int) -> int:
    """Computes an appropriate zoom level based on the search radius."""
    if radius < 500:
        return 15
    zoom = 15 - int(math.log(radius / 500, 2))
    return max(10, min(zoom, 18))

@st.cache_data(show_spinner=False)
def get_amenities(latitude: float, longitude: float, amenity_type: str = 'all', radius: int = RADIUS_DEFAULT) -> pd.DataFrame:
    """
    Fetches amenities around the given latitude and longitude using OSMnx.
    If amenity_type is 'all', all amenities are returned; otherwise only the specified type.
    """
    tags = {'amenity': True} if amenity_type == 'all' else {'amenity': amenity_type}
    try:
        return ox.geometries_from_point((latitude, longitude), tags=tags, dist=radius)
    except Exception as e:
        st.error(f"Error fetching amenities: {e}")
        return pd.DataFrame()

def add_markers_to_map(m: folium.Map, amenities: pd.DataFrame, amenity_type: str) -> None:
    """Adds markers for each amenity using MarkerCluster with enhanced tooltips."""
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in amenities.iterrows():
        if row.geometry is None:
            continue
        # Determine coordinates based on geometry type
        if row.geometry.geom_type == 'Point':
            coords = [row.geometry.y, row.geometry.x]
        elif row.geometry.geom_type in ['Polygon', 'MultiPolygon']:
            coords = [row.geometry.centroid.y, row.geometry.centroid.x]
        else:
            continue
        # Use the amenity name if available
        name = row.get('name', 'N/A')
        tooltip = f"{amenity_type.capitalize()}: {name}"
        folium.Marker(
            location=coords,
            popup=tooltip,
            tooltip=tooltip
        ).add_to(marker_cluster)

def add_heatmap_to_map(m: folium.Map, amenities: pd.DataFrame) -> None:
    """Adds a heatmap layer to the map based on the amenity coordinates."""
    heat_data = []
    for _, row in amenities.iterrows():
        if row.geometry is None:
            continue
        if row.geometry.geom_type == 'Point':
            heat_data.append([row.geometry.y, row.geometry.x])
        elif row.geometry.geom_type in ['Polygon', 'MultiPolygon']:
            heat_data.append([row.geometry.centroid.y, row.geometry.centroid.x])
    if heat_data:
        HeatMap(heat_data).add_to(m)

def create_plotly_chart(amenities: pd.DataFrame, amenity_type: str):
    """Creates a Plotly bar chart to display the distribution of amenities."""
    if amenity_type == 'all':
        if 'amenity' in amenities.columns:
            counts = amenities['amenity'].value_counts().reset_index()
            counts.columns = ['Amenity', 'Count']
        else:
            counts = pd.DataFrame()
    else:
        counts = pd.DataFrame({'Amenity': [amenity_type], 'Count': [len(amenities)]})
    if not counts.empty:
        fig = px.bar(counts, x='Amenity', y='Count', title="Amenity Distribution")
        return fig
    else:
        return None

# ---------------------------
# Main Application
# ---------------------------
def main():
    st.title("Rural world analyzer")
    st.markdown("### Visualization & Dashboard")
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    test_area = st.sidebar.selectbox("Select a Test Area:", list(example_coordinates.keys()))
    selected_coords = example_coordinates[test_area]
    lat = st.sidebar.number_input("Latitude:", value=selected_coords[0])
    lon = st.sidebar.number_input("Longitude:", value=selected_coords[1])
    amenity_type = st.sidebar.selectbox("Select Amenity Type:", ['all', 'restaurant', 'hospital', 'school', 'bank', 'cafe', 'pharmacy', 'cinema', 'parking', 'fuel'])
    map_theme = st.sidebar.selectbox("Select Map Theme:", list(map_themes.keys()))
    
    # Toggles for visualization layers
    show_markers = st.sidebar.checkbox("Show Markers", value=True)
    show_heatmap = st.sidebar.checkbox("Show Heatmap", value=True)
    
    # When the user clicks the button, fetch data and render visualizations
    if st.sidebar.button("Show Amenities"):
        with st.spinner("Fetching amenities..."):
            amenities = get_amenities(lat, lon, amenity_type, RADIUS_DEFAULT)
            if amenities.empty:
                st.warning("No amenities found in the selected area.")
                return
            
            # Create folium map with the selected theme and computed zoom level
            zoom_level = compute_zoom_level(RADIUS_DEFAULT)
            m = folium.Map(location=[lat, lon], zoom_start=zoom_level, tiles=map_themes[map_theme])
            
            # Add markers and heatmap layers based on user selections
            if show_markers:
                add_markers_to_map(m, amenities, amenity_type)
            if show_heatmap:
                add_heatmap_to_map(m, amenities)
            
            # Render the folium map in the app
            folium_static(m, width=700, height=500)
            
            # Create and display a dynamic Plotly dashboard
            chart = create_plotly_chart(amenities, amenity_type)
            if chart:
                st.plotly_chart(chart)
            else:
                st.write("No chart data available.")

if __name__ == "__main__":
    main()
