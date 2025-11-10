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



# -------------------------------------------------
# app.py – Streamlit + Leafmap (Optimized Version)
# -------------------------------------------------
import streamlit as st
import pandas as pd
import leafmap.foliumap as leafmap
import requests
from branca.colormap import LinearColormap

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="MA Bar Exam Map",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Massachusetts Bar Examinees (July 2025)")
st.markdown("Hover over ZIP areas to see details.")

# ---------------------------
# 1. Load & cache the CSV
# ---------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("data-ROBeC.csv")
    df["zip"] = df["zip"].astype(str).str.zfill(5)
    return df

data = load_data()

# ---------------------------
# 2. Aggregate duplicate ZIPs
# ---------------------------
agg = (
    data.groupby("zip")
    .agg(
        area=("area", lambda x: ", ".join(sorted(set(x)))),
        sub_area=("sub_area", lambda x: ", ".join(sorted(set(x)))),
        examinees=("examinees", "sum"),
    )
    .reset_index()
)
zip_info = agg.set_index("zip").to_dict(orient="index")

# ---------------------------
# 3. Load & filter GeoJSON
# ---------------------------
@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ma_massachusetts_zip_codes_geo.min.json"
    geo = requests.get(url).json()
    geo["features"] = [
        f for f in geo["features"]
        if f["properties"]["ZCTA5CE10"] in zip_info
    ]
    return geo

geojson_data = load_geojson()

# ---------------------------
# 4. Prepare legend & colormap
# ---------------------------
bins = [0, 5, 10, 20, 50, agg["examinees"].max()]
cmap = LinearColormap(
    colors=[
        "#ffffb2",
        "#fed976",
        "#feb24c",
        "#fd8d3c",
        "#fc4e2a",
        "#e31a1c",
        "#bd0026",
        "#800026",
    ],
    vmin=agg["examinees"].min(),
    vmax=agg["examinees"].max(),
).to_step(index=bins)
cmap.caption = "Number of Examinees"

# ---------------------------
# 5. Build map using Leafmap
# ---------------------------
@st.cache_resource
def build_map(agg, geojson_data):
    m = leafmap.Map(center=[42.1, -71.5], zoom=8, tiles="CartoDB.Positron")

    # Convert aggregated data to dict for quick lookup
    value_dict = dict(zip(agg["zip"], agg["examinees"]))

    # Function for styling polygons dynamically
    def style_function(feature):
        zip_code = feature["properties"]["ZCTA5CE10"]
        val = value_dict.get(zip_code, 0)
        color = cmap(val) if val > 0 else "#cccccc"
        return {
            "fillColor": color,
            "color": "black",
            "weight": 0.5,
            "fillOpacity": 0.85,
        }

    # Function for tooltips
    def tooltip_function(feature):
        z = feature["properties"]["ZCTA5CE10"]
        if z in zip_info:
            info = zip_info[z]
            return (
                f"<b>ZIP:</b> {z}<br>"
                f"<b>Area:</b> {info['area']}<br>"
                f"<b>Sub-area:</b> {info['sub_area']}<br>"
                f"<b>Examinees:</b> {info['examinees']}"
            )
        else:
            return f"<b>ZIP:</b> {z}<br>No data"

    # Add polygons
    m.add_geojson(
        geojson_data,
        style_function=style_function,
        tooltip=tooltip_function,
    )

    # Add legend manually using colormap
    m.add_colorbar(
        cmap=cmap,
        label="Number of Examinees",
        orientation="horizontal",
    )

    return m

# ---------------------------
# 6. Render map efficiently
# ---------------------------
with st.spinner("Loading Massachusetts Bar Examinee Map..."):
    m = build_map(agg, geojson_data)
    m.to_streamlit(width=1100, height=800)

st.markdown(
    """
    <style>
    .leaflet-container {
        font-family: Arial, sans-serif;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
