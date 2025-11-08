import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from branca.colormap import LinearColormap

# ---------------------------
# Streamlit page setup
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
# Add tooltips to GeoJSON
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
# Create map — DO NOT CACHE THIS!
# ---------------------------
def create_map():
    m = folium.Map(location=[42.1, -71.5], zoom_start=8, tiles="cartodbpositron")

    choropleth = folium.Choropleth(
        geo_data=geojson_data,
        data=agg,
        columns=["zip", "examinees"],
        key_on="feature.properties.ZCTA5CE10",
        fill_color="YlOrRd",
        fill_opacity=0.85,
        line_opacity=0.25,
        nan_fill_color="lightgray",
        legend_name="Number of Examinees",
        highlight=False,
        show=True
    ).add_to(m)

    # Remove auto legend
    for key in choropleth._children:
        if key.startswith('color_map'):
            del choropleth._children[key]

    # Add tooltip
    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields=["tooltip"],
            aliases=[""],
            labels=False,
            sticky=True,
            style="""
                background-color: rgba(255,255,255,0.95);
                border: 1px solid #aaa;
                border-radius: 6px;
                padding: 10px;
                font-family: Arial, sans-serif;
                font-size: 13px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.2);
            """
        )
    )

    # Add custom legend
    bins = [0, 1, 2, 5, 10, 20, 50, agg['examinees'].max()]
    colormap = LinearColormap(
        colors=['#ffffb2', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#bd0026', '#800026'],
        vmin=agg['examinees'].min(),
        vmax=agg['examinees'].max()
    ).to_step(index=bins)
    colormap.caption = "Number of Examinees"
    m.add_child(colormap)

    return m

# Build map (no caching!)
m = create_map()

# ---------------------------
# Display map
# ---------------------------
st_folium(m, width=1100, height=800, use_container_width=True)
