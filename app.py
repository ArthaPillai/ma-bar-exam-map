import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from branca.colormap import LinearColormap
import base64
from io import BytesIO

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="MA Bar Exam Map", layout="wide", initial_sidebar_state="collapsed")
st.title("Massachusetts Bar Exam Takers by ZIP (July 2025)")
st.markdown("Hover for ZIP, area, and examinee count.")

# ---------------------------
# Load data (cached)
# ---------------------------
@st.cache_data
def load_data():
    data = pd.read_csv("data-ROBeC.csv")
    data["zip"] = data["zip"].astype(str).str.zfill(5)
    return data

data = load_data()

# ---------------------------
# Aggregate ZIPs
# ---------------------------
agg = (
    data.groupby("zip")
    .agg({
        "area": lambda x: ", ".join(sorted(set(x))),
        "sub_area": lambda x: ", ".join(sorted(set(x))),
        "examinees": "sum"
    })
    .reset_index()
)
zip_info = agg.set_index("zip").to_dict(orient="index")

# ---------------------------
# Load GeoJSON (cached)
# ---------------------------
@st.cache_data
def load_geojson():
    geojson_url = "https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ma_massachusetts_zip_codes_geo.min.json"
    return requests.get(geojson_url).json()

geojson_data = load_geojson()

# ---------------------------
# Add tooltips
# ---------------------------
for feature in geojson_data["features"]:
    zip_code = feature["properties"]["ZCTA5CE10"]
    if zip_code in zip_info:
        info = zip_info[zip_code]
        tooltip_html = (
            f"<b>ZIP:</b> {zip_code}<br>"
            f"<b>Area:</b> {info['area']}<br>"
            f"<b>Sub-area:</b> {info['sub_area']}<br>"
            f"<b>Examinees:</b> {info['examinees']}"
        )
    else:
        tooltip_html = f"<b>ZIP:</b> {zip_code}<br>No data"
    feature["properties"]["tooltip"] = tooltip_html

# ---------------------------
# Function to build map (used for both interactive and download)
# ---------------------------
def build_map():
    m = folium.Map(location=[42.1, -71.5], zoom_start=8, tiles="cartodbpositron")

    # Custom bins for consistent coloring
    bins = [0, 5, 10, 20, 50, agg['examinees'].max()]

    # Choropleth with NO auto legend (legend_name=None)
    choropleth = folium.Choropleth(
        geo_data=geojson_data,
        data=agg,
        columns=["zip", "examinees"],
        key_on="feature.properties.ZCTA5CE10",
        fill_color="YlOrRd",
        fill_opacity=0.85,
        line_opacity=0.25,
        nan_fill_color="lightgray",
        threshold_scale=bins,  # Custom bins for coloring
        legend_name=None,  # Disable auto legend
        highlight=False,
        show=True
    ).add_to(m)

    # Add tooltip
    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields=["tooltip"],
            aliases=[""],
            labels=False,
            sticky=True,
            style=(
                "background-color: rgba(255,255,255,0.95); "
                "border: 1px solid #aaa; "
                "border-radius: 6px; "
                "padding: 10px; "
                "font-family: Arial, sans-serif; "
                "font-size: 13px; "
                "box-shadow: 0 2px 6px rgba(0,0,0,0.2);"
            )
        )
    )

    # Add custom legend with same bins
    colormap = LinearColormap(
        colors=['#ffffb2', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#bd0026', '#800026'],
        vmin=agg['examinees'].min(),
        vmax=agg['examinees'].max()
    ).to_step(index=bins)
    colormap.caption = "Number of Examinees"
    m.add_child(colormap)

    return m

# ---------------------------
# Interactive map for Streamlit
# ---------------------------
m_interactive = build_map()
st_folium(m_interactive, width=1100, height=800, use_container_width=True)

# ---------------------------
# Download button
# ---------------------------
m_download = build_map()  # Same build function → identical map
html_bytes = BytesIO()
m_download.save(html_bytes, close_file=False)
b64 = base64.b64encode(html_bytes.getvalue()).decode()
href = f'<a href="data:text/html;base64,{b64}" download="MA_Bar_Exam_Map.html" style="display:inline-block;margin-top:10px;padding:10px 20px;background:#0068c9;color:white;border-radius:5px;text-decoration:none;">Download Map as HTML</a>'
st.markdown(href, unsafe_allow_html=True)
