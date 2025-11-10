# # -------------------------------------------------
# # app.py  –  Streamlit + Folium
# # -------------------------------------------------
# import streamlit as st
# import pandas as pd
# import folium
# from streamlit_folium import st_folium
# import requests
# from branca.colormap import LinearColormap
# import base64
# from io import BytesIO

# # ---------------------------
# # Page config
# # ---------------------------
# st.set_page_config(
#     page_title="MA Bar Exam Map",
#     layout="wide",
#     initial_sidebar_state="collapsed",
# )

# st.title("Massachusetts Bar Examinees (July 2025)")
# st.markdown("Hover for ZIP, area, and examinee count.")

# # ---------------------------
# # 1. Load & cache the CSV
# # ---------------------------
# @st.cache_data
# def load_data() -> pd.DataFrame:
#     df = pd.read_csv("data-ROBeC.csv")
#     df["zip"] = df["zip"].astype(str).str.zfill(5)
#     return df

# data = load_data()

# # ---------------------------
# # 2. Aggregate duplicate ZIPs
# # ---------------------------
# agg = (
#     data.groupby("zip")
#     .agg(
#         area=("area", lambda x: ", ".join(sorted(set(x)))),
#         sub_area=("sub_area", lambda x: ", ".join(sorted(set(x)))),
#         examinees=("examinees", "sum"),
#     )
#     .reset_index()
# )
# zip_info = agg.set_index("zip").to_dict(orient="index")

# # ---------------------------
# # 3. Load & cache the GeoJSON
# # ---------------------------
# @st.cache_data
# def load_geojson():
#     url = "https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ma_massachusetts_zip_codes_geo.min.json"
#     return requests.get(url).json()

# geojson_data = load_geojson()

# # ---------------------------
# # 4. Attach tooltips to every feature
# # ---------------------------
# for f in geojson_data["features"]:
#     z = f["properties"]["ZCTA5CE10"]
#     if z in zip_info:
#         i = zip_info[z]
#         html = (
#             f"<b>ZIP:</b> {z}<br>"
#             f"<b>Area:</b> {i['area']}<br>"
#             f"<b>Sub‑area:</b> {i['sub_area']}<br>"
#             f"<b>Examinees:</b> {i['examinees']}"
#         )
#     else:
#         html = f"<b>ZIP:</b> {z}<br>No data"
#     f["properties"]["tooltip"] = html

# # ---------------------------
# # 5. Build the Folium map
# # ---------------------------
# def build_map() -> folium.Map:
#     m = folium.Map(
#         location=[42.1, -71.5],
#         zoom_start=8,
#         tiles="cartodbpositron",
#         # Leaflet‑specific options to speed up raster‑tile loading
#         attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors '
#              '&copy; <a href="https://carto.com/attributions">CARTO</a>',
#     )

#     # ---- Choropleth -------------------------------------------------
#     ch = folium.Choropleth(
#         geo_data=geojson_data,
#         data=agg,
#         columns=["zip", "examinees"],
#         key_on="feature.properties.ZCTA5CE10",
#         fill_color="YlOrRd",
#         fill_opacity=0.85,
#         line_opacity=0.25,
#         nan_fill_color="lightgray",
#         legend_name="Number of Examinees",
#         highlight=False,
#         show=True,
#     ).add_to(m)

#     # Remove Folium’s auto‑legend
#     for key in list(ch._children):
#         if key.startswith("color_map"):
#             del ch._children[key]

#     # ---- Tooltip ----------------------------------------------------
#     ch.geojson.add_child(
#         folium.features.GeoJsonTooltip(
#             fields=["tooltip"],
#             aliases=[""],
#             labels=False,
#             sticky=True,
#             style="""
#                 background-color:rgba(255,255,255,0.95);
#                 border:1px solid #aaa;
#                 border-radius:6px;
#                 padding:10px;
#                 font-family:Arial,sans-serif;
#                 font-size:13px;
#                 box-shadow:0 2px 6px rgba(0,0,0,0.2);
#             """,
#         )
#     )

#     # ---- Custom stepped legend ---------------------------------------
#     bins = [0, 5, 10, 20, 50, agg["examinees"].max()]
#     cmap = LinearColormap(
#         colors=[
#             "#ffffb2",
#             "#fed976",
#             "#feb24c",
#             "#fd8d3c",
#             "#fc4e2a",
#             "#e31a1c",
#             "#bd0026",
#             "#800026",
#         ],
#         vmin=agg["examinees"].min(),
#         vmax=agg["examinees"].max(),
#     ).to_step(index=bins)
#     cmap.caption = "Number of Examinees"
#     m.add_child(cmap)

#     return m

# # Build the map
# m = build_map()

# # ---------------------------
# # 6. Render the interactive map
# # ---------------------------
# map_obj = st_folium(m, width=1100, height=800, use_container_width=True)



import streamlit as st
import pandas as pd
import requests
import leafmap.foliumap as leafmap
import branca.colormap as cm

# ---------------------------------------------------------
# Streamlit Page Setup
# ---------------------------------------------------------
st.set_page_config(
    page_title="Massachusetts Bar Examinee Map",
    page_icon="🗺️",
    layout="wide",
)

st.title("🗺️ Massachusetts Bar Examinee Distribution Map")
st.markdown(
    """
    This interactive map visualizes the **number of bar examinees by ZIP code**
    across Massachusetts. Hover over ZIP regions to view detailed information.
    """
)

# ---------------------------------------------------------
# Load Examinee Data (Local CSV)
# ---------------------------------------------------------
@st.cache_data
def load_examinee_data():
    # Load your CSV file directly from the repo
    df = pd.read_csv("data-ROBeC.csv", dtype={"zip": str})
    df["zip"] = df["zip"].str.zfill(5)
    df = (
        df.groupby("zip")
        .agg(
            area=("area", lambda x: ", ".join(sorted(set(x)))),
            sub_area=("sub_area", lambda x: ", ".join(sorted(set(x)))),
            count=("examinees", "sum"),
        )
        .reset_index()
    )
    return df

agg = load_examinee_data()

# ---------------------------------------------------------
# Load Massachusetts ZIP Code GeoJSON
# ---------------------------------------------------------
@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ma_massachusetts_zip_codes_geo.min.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

geojson_data = load_geojson()

# ---------------------------------------------------------
# Build Map using Leafmap
# ---------------------------------------------------------
def build_map(agg, geojson_data):
    """Builds an interactive choropleth map with hover tooltips using Leafmap."""

    # Initialize Leafmap
    m = leafmap.Map(
        center=[42.1, -71.7],
        zoom=8,
        locate_control=False,
        draw_control=False,
        measure_control=False,
    )

    # Prepare color scale
    min_val = agg["count"].min()
    max_val = agg["count"].max()
    colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
    colormap.caption = "Number of Examinees"
    colormap.add_to(m)

    # Lookup for examinee counts and area info
    value_dict = agg.set_index("zip").to_dict(orient="index")

    # Define style function for polygons
    def style_function(feature):
        zip_code = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
        val = value_dict.get(zip_code, {}).get("count", 0)
        return {
            "fillColor": colormap(val) if val > 0 else "#d9d9d9",
            "color": "black",
            "weight": 0.3,
            "fillOpacity": 0.7,
        }

    # Add custom tooltip info
    for feature in geojson_data["features"]:
        z = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
        if z in value_dict:
            i = value_dict[z]
            feature["properties"]["Area"] = i["area"]
            feature["properties"]["Sub_Area"] = i["sub_area"]
            feature["properties"]["Examinees"] = i["count"]
        else:
            feature["properties"]["Area"] = "No data"
            feature["properties"]["Sub_Area"] = "-"
            feature["properties"]["Examinees"] = 0

    # Add GeoJSON with hover tooltips
    m.add_geojson(
        geojson_data,
        style_function=style_function,
        info_mode="on_hover",  # enables hover tooltips
        fields=["ZCTA5CE10", "Area", "Sub_Area", "Examinees"],
        aliases=["ZIP Code", "Area", "Sub-area", "Examinees"],
    )

    # Add layer control
    m.add_layer_control()
    return m

# ---------------------------------------------------------
# Render the Map
# ---------------------------------------------------------
with st.spinner("Loading Massachusetts Bar Examinee Map..."):
    m = build_map(agg, geojson_data)
    m.to_streamlit(width=1100, height=800)
