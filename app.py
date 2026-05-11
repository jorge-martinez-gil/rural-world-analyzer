import io
import logging
import math
from typing import Optional, Tuple, Union

import folium
import geopandas as gpd
import osmnx as ox
import pandas as pd
import plotly.express as px
import streamlit as st
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

logging.basicConfig(level=logging.ERROR)

st.set_page_config(page_title="Rural World Analyzer", layout="wide")

RADIUS_DEFAULT = 1000
AMENITY_TYPES = [
    "all",
    "restaurant",
    "hospital",
    "school",
    "bank",
    "cafe",
    "pharmacy",
    "cinema",
    "parking",
    "fuel",
    "library",
    "post_office",
    "police",
    "fire_station",
    "marketplace",
    "place_of_worship",
    "pub",
    "fast_food",
    "bus_station",
    "bicycle_parking",
]
BIBTEX_ENTRY = """@article{martinez2025overview,
  title={An overview of civic engagement tools for rural communities},
  author={Martinez-Gil, Jorge and Pichler, Mario and Lechat, Noemi and Lentini, Gianluca and Cvar, Nina and Trilar, Jure and Bucchiarone, Antonio and Marconi, Annapaola},
  journal={Open Research Europe},
  volume={4},
  number={195},
  pages={195},
  year={2025},
  publisher={F1000 Research Limited}
}"""

example_coordinates = {
    "Hagenberg, Austria": (48.36964, 14.5128),
    "Lienz, Austria": (46.8294, 12.7687),
    "Evora, Portugal": (38.5714, -7.9135),
    "Oristano, Italy": (39.9036, 8.5920),
    "Braganca, Portugal": (41.8067, -6.7567),
    "Avila, Spain": (40.6567, -4.6810),
    "Gjirokaster, Albania": (40.0758, 20.1389),
    "Logrono, Spain": (42.4627, -2.4449),
    "Oaxaca, Mexico": (17.0732, -96.7266),
    "Mysuru, India": (12.2958, 76.6394),
    "Meknes, Morocco": (33.8935, -5.5473),
    "Arequipa, Peru": (-16.4090, -71.5375),
}

TileSpec = Union[str, dict[str, str]]

map_themes: dict[str, TileSpec] = {
    "OpenStreetMap": "OpenStreetMap",
    "CartoDB Positron": "CartoDB positron",
    "CartoDB Dark Matter": "CartoDB dark_matter",
    "Esri World Imagery": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Tiles (C) Esri",
    },
    "OpenTopoMap": {
        "tiles": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        "attr": "Map data (C) OpenStreetMap contributors, SRTM | Map style (C) OpenTopoMap",
    },
}

DEFAULT_AREA_1 = "Hagenberg, Austria"
DEFAULT_AREA_2 = "Oaxaca, Mexico"


def sync_area_selection(selection_key: str, name_key: str, lat_key: str, lon_key: str) -> None:
    area_label = st.session_state[selection_key]
    latitude, longitude = example_coordinates[area_label]
    st.session_state[name_key] = area_label
    st.session_state[lat_key] = latitude
    st.session_state[lon_key] = longitude


def sync_area_1_selection() -> None:
    sync_area_selection("area_1_label", "area_name_1", "lat_1", "lon_1")


def sync_area_2_selection() -> None:
    sync_area_selection("area_2_label", "area_name_2", "lat_2", "lon_2")


def initialize_area_state() -> None:
    defaults = (
        ("area_1_label", "area_name_1", "lat_1", "lon_1", DEFAULT_AREA_1),
        ("area_2_label", "area_name_2", "lat_2", "lon_2", DEFAULT_AREA_2),
    )
    for selection_key, name_key, lat_key, lon_key, default_area in defaults:
        st.session_state.setdefault(selection_key, default_area)
        st.session_state.setdefault(name_key, st.session_state[selection_key])
        latitude, longitude = example_coordinates[st.session_state[selection_key]]
        st.session_state.setdefault(lat_key, latitude)
        st.session_state.setdefault(lon_key, longitude)


def compute_zoom_level(radius: int) -> int:
    if radius < 500:
        return 15
    zoom = 15 - int(math.log(radius / 500, 2))
    return max(10, min(zoom, 18))


@st.cache_data(show_spinner=False)
def get_amenities(
    latitude: float,
    longitude: float,
    amenity_type: str = "all",
    radius: int = RADIUS_DEFAULT,
) -> pd.DataFrame:
    tags = {"amenity": True} if amenity_type == "all" else {"amenity": amenity_type}
    try:
        return ox.features_from_point((latitude, longitude), tags=tags, dist=radius)
    except Exception as exc:
        error_message = f"Error fetching amenities: {exc}"
        st.error(error_message)
        logging.error(error_message)
        return pd.DataFrame()


def get_amenity_series(amenities_df: pd.DataFrame) -> pd.Series:
    if amenities_df.empty or "amenity" not in amenities_df:
        return pd.Series(dtype="object")
    return amenities_df["amenity"].dropna().astype(str)


def compute_shannon_index(amenities_df: pd.DataFrame) -> float:
    """Compute Shannon entropy with the ecological natural-log convention."""
    amenity_series = get_amenity_series(amenities_df)
    if amenity_series.empty:
        return 0.0
    proportions = amenity_series.value_counts(normalize=True)
    shannon_index = -(proportions * proportions.map(math.log)).sum()
    return round(float(shannon_index), 3)


def compute_rai(amenities_df: pd.DataFrame) -> float:
    if amenities_df.empty:
        return 0.0
    amenity_series = get_amenity_series(amenities_df)
    count = int(len(amenities_df))
    unique_types = int(amenity_series.nunique()) if not amenity_series.empty else 0
    diversity_score = compute_shannon_index(amenities_df)
    return min(100, round((count * 0.4 + diversity_score * 30 + unique_types * 2), 1))


def extract_coordinates(geometry) -> Tuple[Optional[float], Optional[float]]:
    if geometry is None or getattr(geometry, "is_empty", False):
        return None, None
    if geometry.geom_type == "Point":
        return geometry.y, geometry.x
    centroid = geometry.centroid
    return centroid.y, centroid.x


def add_markers_to_map(folium_map: folium.Map, amenities: pd.DataFrame, amenity_type: str) -> None:
    marker_cluster = MarkerCluster().add_to(folium_map)
    for _, row in amenities.iterrows():
        lat, lon = extract_coordinates(row.geometry)
        if lat is None or lon is None:
            continue
        amenity_label = row.get("amenity", amenity_type)
        name = row.get("name", "N/A")
        tooltip = f"{str(amenity_label).replace('_', ' ').title()}: {name}"
        folium.CircleMarker(
            location=[lat, lon],
            radius=5,
            color="#2563eb",
            fill=True,
            fill_color="#60a5fa",
            fill_opacity=0.85,
            popup=tooltip,
            tooltip=tooltip,
        ).add_to(marker_cluster)


def add_heatmap_to_map(folium_map: folium.Map, amenities: pd.DataFrame) -> None:
    heat_data = []
    for _, row in amenities.iterrows():
        lat, lon = extract_coordinates(row.geometry)
        if lat is not None and lon is not None:
            heat_data.append([lat, lon])
    if heat_data:
        HeatMap(heat_data).add_to(folium_map)


def create_plotly_chart(amenities_df: pd.DataFrame):
    amenity_series = get_amenity_series(amenities_df)
    if amenity_series.empty:
        return None
    counts = (
        amenity_series.value_counts()
        .rename_axis("amenity")
        .reset_index(name="count")
        .sort_values("count", ascending=True)
    )
    fig = px.bar(
        counts,
        x="count",
        y="amenity",
        orientation="h",
        text="count",
        labels={"count": "Count", "amenity": "Amenity Type"},
        color="count",
        color_continuous_scale="Viridis",
    )
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
    fig.update_traces(textposition="outside")
    return fig


def prepare_export_dataframe(amenities_df: pd.DataFrame) -> pd.DataFrame:
    if amenities_df.empty:
        return pd.DataFrame(columns=["name", "amenity", "lat", "lon"])

    export_df = amenities_df.copy()
    coordinates = export_df["geometry"].apply(extract_coordinates)
    export_df["lat"] = coordinates.apply(lambda coord: coord[0])
    export_df["lon"] = coordinates.apply(lambda coord: coord[1])

    name_series = export_df["name"] if "name" in export_df else pd.Series(index=export_df.index, dtype="object")
    amenity_series = export_df["amenity"] if "amenity" in export_df else pd.Series(index=export_df.index, dtype="object")

    return pd.DataFrame(
        {
            "name": name_series.fillna("N/A"),
            "amenity": amenity_series.fillna("N/A"),
            "lat": export_df["lat"],
            "lon": export_df["lon"],
        }
    )


def build_map(
    latitude: float,
    longitude: float,
    amenities: pd.DataFrame,
    amenity_type: str,
    radius: int,
    map_theme: str,
    show_markers: bool,
    show_heatmap: bool,
) -> folium.Map:
    tile_spec = map_themes.get(map_theme, "OpenStreetMap")
    if isinstance(tile_spec, dict):
        folium_map = folium.Map(
            location=[latitude, longitude],
            zoom_start=compute_zoom_level(radius),
            tiles=tile_spec["tiles"],
            attr=tile_spec["attr"],
        )
    else:
        folium_map = folium.Map(
            location=[latitude, longitude],
            zoom_start=compute_zoom_level(radius),
            tiles=tile_spec,
        )

    folium.Circle(
        location=[latitude, longitude],
        radius=radius,
        color="#2563eb",
        fill=True,
        fill_opacity=0.1,
        popup=f"Radius: {radius} m",
    ).add_to(folium_map)

    if show_markers:
        add_markers_to_map(folium_map, amenities, amenity_type)
    if show_heatmap:
        add_heatmap_to_map(folium_map, amenities)

    return folium_map


def render_summary_metrics(amenities_df: pd.DataFrame, rai_score: float, shannon_index: float) -> None:
    summary_columns = st.columns(4)
    total_amenities = int(len(amenities_df))
    unique_types = int(get_amenity_series(amenities_df).nunique()) if not amenities_df.empty else 0
    summary_columns[0].metric("Total Amenities", total_amenities)
    summary_columns[1].metric("Unique Types", unique_types)
    summary_columns[2].metric("RAI Score", f"{rai_score}/100")
    summary_columns[3].metric("Shannon Index", shannon_index)


def render_download_buttons(amenities_df: pd.DataFrame, area_name: str, key_prefix: str) -> None:
    export_df = prepare_export_dataframe(amenities_df)
    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)
    geojson_frame = (
        amenities_df
        if isinstance(amenities_df, gpd.GeoDataFrame)
        else gpd.GeoDataFrame(amenities_df, geometry="geometry")
    )
    geojson_data = geojson_frame.to_json()

    download_columns = st.columns(2)
    download_columns[0].download_button(
        "Download CSV",
        data=csv_buffer.getvalue().encode("utf-8"),
        file_name=f"{area_name.lower().replace(' ', '_')}_amenities.csv",
        mime="text/csv",
        key=f"csv_{key_prefix}",
    )
    download_columns[1].download_button(
        "Download GeoJSON",
        data=geojson_data,
        file_name=f"{area_name.lower().replace(' ', '_')}_amenities.geojson",
        mime="application/geo+json",
        key=f"geojson_{key_prefix}",
    )


def render_area_analysis(
    area_name: str,
    latitude: float,
    longitude: float,
    amenity_type: str,
    radius: int,
    map_theme: str,
    show_markers: bool,
    show_heatmap: bool,
    key_prefix: str,
    map_width: int,
) -> None:
    st.subheader(area_name)
    amenities = get_amenities(latitude, longitude, amenity_type, radius)

    if amenities.empty:
        st.warning("No amenities found in the selected area.")
        return

    rai_score = compute_rai(amenities)
    shannon_index = compute_shannon_index(amenities)
    hero_columns = st.columns([1.4, 1])
    hero_columns[0].metric("Rural Accessibility Index (RAI)", f"{rai_score}/100")
    hero_columns[1].metric("Shannon Diversity Index", shannon_index)

    folium_map = build_map(
        latitude,
        longitude,
        amenities,
        amenity_type,
        radius,
        map_theme,
        show_markers,
        show_heatmap,
    )
    st.markdown("### Interactive Map")
    st_folium(folium_map, width=map_width, height=500, key=f"map_{key_prefix}")

    st.markdown("### Statistics Summary")
    render_summary_metrics(amenities, rai_score, shannon_index)

    st.markdown("### Export Data")
    render_download_buttons(amenities, area_name, key_prefix)

    st.markdown("### Amenity Distribution")
    chart = create_plotly_chart(amenities)
    if chart is None:
        st.info("No amenity distribution data available for charting.")
    else:
        st.plotly_chart(chart, use_container_width=True, key=f"chart_{key_prefix}")


def main() -> None:
    initialize_area_state()

    st.title("Rural World Analyzer")
    st.markdown(
        """
        Rural World Analyzer is an open-source geospatial tool for quantifying and visualizing
        the distribution and diversity of civic amenities in rural and semi-urban areas.
        It leverages OpenStreetMap data via OSMnx to support research in rural development,
        smart villages, and territorial cohesion.
        """
    )

    st.sidebar.header("Configuration")
    st.sidebar.markdown("**Select a Test Area**")
    area_1_label = st.sidebar.selectbox(
        "Example Area 1",
        list(example_coordinates.keys()),
        key="area_1_label",
        on_change=sync_area_1_selection,
    )
    area_name_1 = st.sidebar.text_input("Area Name", key="area_name_1")
    lat_1 = st.sidebar.number_input("Latitude", key="lat_1", format="%.6f")
    lon_1 = st.sidebar.number_input("Longitude", key="lon_1", format="%.6f")

    comparison_mode = st.sidebar.checkbox("Enable Area Comparison", value=False)

    area_name_2 = None
    lat_2 = None
    lon_2 = None
    if comparison_mode:
        st.sidebar.markdown("**Comparison Area**")
        st.sidebar.selectbox(
            "Example Area 2",
            list(example_coordinates.keys()),
            key="area_2_label",
            on_change=sync_area_2_selection,
        )
        area_name_2 = st.sidebar.text_input("Area Name 2", key="area_name_2")
        lat_2 = st.sidebar.number_input("Latitude 2", key="lat_2", format="%.6f")
        lon_2 = st.sidebar.number_input("Longitude 2", key="lon_2", format="%.6f")

    st.sidebar.markdown("**Choose Amenity Type**")
    amenity_type = st.sidebar.selectbox("Amenity Type", AMENITY_TYPES)

    st.sidebar.markdown("**Map Settings**")
    map_theme = st.sidebar.selectbox("Map Theme", list(map_themes.keys()))
    radius = st.sidebar.number_input(
        "Radius (meters)",
        value=RADIUS_DEFAULT,
        min_value=300,
        max_value=3000,
        step=100,
    )
    show_markers = st.sidebar.checkbox("Show Markers", value=True)
    show_heatmap = st.sidebar.checkbox("Show Heatmap", value=True)
    st.sidebar.markdown("---")
    st.sidebar.markdown("Built for rural research | [Cite this tool](#citation)")

    if "analysis_requested" not in st.session_state:
        st.session_state.analysis_requested = False

    if st.sidebar.button("Analyze Area"):
        st.session_state.analysis_requested = True

    if st.session_state.analysis_requested:
        with st.spinner("Fetching amenities and computing rural accessibility metrics..."):
            if comparison_mode and area_name_2 is not None and lat_2 is not None and lon_2 is not None:
                left_column, right_column = st.columns(2)
                with left_column:
                    render_area_analysis(
                        area_name_1,
                        lat_1,
                        lon_1,
                        amenity_type,
                        radius,
                        map_theme,
                        show_markers,
                        show_heatmap,
                        key_prefix="area_1",
                        map_width=500,
                    )
                with right_column:
                    render_area_analysis(
                        area_name_2,
                        lat_2,
                        lon_2,
                        amenity_type,
                        radius,
                        map_theme,
                        show_markers,
                        show_heatmap,
                        key_prefix="area_2",
                        map_width=500,
                    )
            else:
                render_area_analysis(
                    area_name_1,
                    lat_1,
                    lon_1,
                    amenity_type,
                    radius,
                    map_theme,
                    show_markers,
                    show_heatmap,
                    key_prefix="area_1",
                    map_width=700,
                )

    st.markdown('<div id="citation"></div>', unsafe_allow_html=True)
    with st.expander("How to cite this tool"):
        st.code(BIBTEX_ENTRY, language="bibtex")


if __name__ == "__main__":
    main()
