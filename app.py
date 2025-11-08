# -------------------------------------------------
# app.py  –  Streamlit + Folium (one legend, download button, fast zoom)
# -------------------------------------------------
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
st.set_page_config(
    page_title="MA Bar Exam Map",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Massachusetts Bar Exam Takers by ZIP (July 2025)")
st.markdown("Hover for ZIP, area, and examinee count.")

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
# 3. Load & cache the GeoJSON (once per session)
# ---------------------------
@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ma_massachusetts_zip_codes_geo.min.json"
    return requests.get(url).json()

geojson_data = load_geojson()

# ---------------------------
# 4. Attach tooltips to every feature
# ---------------------------
for f in geojson_data["features"]:
    z = f["properties"]["ZCTA5CE10"]
    if z in zip_info:
        i = zip_info[z]
        html = (
            f"<b>ZIP:</b> {z}<br>"
            f"<b>Area:</b> {i['area']}<br>"
            f"<b>Sub‑area:</b> {i['sub_area']}<br>"
            f"<b>Examinees:</b> {i['examinees']}"
        )
    else:
        html = f"<b>ZIP:</b> {z}<br>No data"
    f["properties"]["tooltip"] = html

# ---------------------------
# 5. Build the Folium map (NO @st.cache_data!)
# ---------------------------
def build_map() -> folium.Map:
    m = folium.Map(
        location=[42.1, -71.5],
        zoom_start=8,
        tiles="cartodbpositron",
        # Leaflet‑specific options to speed up raster‑tile loading
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors '
             '&copy; <a href="https://carto.com/attributions">CARTO</a>',
    )

    # ---- Choropleth -------------------------------------------------
    ch = folium.Choropleth(
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
        show=True,
    ).add_to(m)

    # Remove Folium’s auto‑legend (the “color_map_…” child)
    for key in list(ch._children):
        if key.startswith("color_map"):
            del ch._children[key]

    # ---- Tooltip ----------------------------------------------------
    ch.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields=["tooltip"],
            aliases=[""],
            labels=False,
            sticky=True,
            style="""
                background-color:rgba(255,255,255,0.95);
                border:1px solid #aaa;
                border-radius:6px;
                padding:10px;
                font-family:Arial,sans-serif;
                font-size:13px;
                box-shadow:0 2px 6px rgba(0,0,0,0.2);
            """,
        )
    )

    # ---- Custom stepped legend ---------------------------------------
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
    m.add_child(cmap)

    return m

# Build the map (executed on every interaction – fast because data is cached)
m = build_map()

# ---------------------------
# 6. Render the interactive map
# ---------------------------
map_obj = st_folium(m, width=1100, height=800, use_container_width=True)

# ---------------------------
# 7. DOWNLOAD BUTTON (HTML file)
# ---------------------------
def map_to_html_bytes(fmap: folium.Map) -> bytes:
    """Return the map as UTF‑8 encoded HTML bytes."""
    # folium saves to a temporary file → read it back
    tmp = BytesIO()
    fmap.save(tmp, close_file=False)
    return tmp.getvalue()

html_bytes = map_to_html_bytes(m)

b64 = base64.b64encode(html_bytes).decode()
href = f'<a href="data:text/html;base64,{b64}" download="MA_Bar_Exam_Map.html">Download map as HTML</a>'
st.markdown(href, unsafe_allow_html=True)

# ---------------------------
# 8. OPTIONAL: Speed‑up tips (shown to the user)
# ---------------------------
with st.expander("Why does zoom feel a bit slow?"):
    st.write(
        """
        * The map is **fully interactive** – every zoom/pan redraws ~500 ZIP polygons.
        * The heavy work (CSV + GeoJSON) is cached, so the first load is the only slow one.
        * For **instant** zoom you could switch to a vector‑tile base map (e.g., Mapbox) – requires an API key.
        """
    )
