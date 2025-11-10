# app.py
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
    layout="wide",
)

# ---------------------------------------------------------
# Sidebar – Layer selector
# ---------------------------------------------------------
layer_options = {
    "All years": "map_data_all.csv",
    "2025": "map_data_2025.csv",
    "2024": "map_data_2024.csv",
    "2023": "map_data_2023.csv",
}
selected_layer = st.sidebar.selectbox(
    "Select data layer",
    options=list(layer_options.keys()),
    index=0,
)

# ---- TITLE -------------------------------------------------
if selected_layer == "All years":
    title_suffix = "All Years"
else:
    title_suffix = f"July {selected_layer}"

st.title(f"Massachusetts Bar Examinee Distribution Map – {title_suffix}")

st.markdown(
    """
    Hover over any area to view the ZIP Code, Area, Sub-Area, and number of Examinees.
    """
)

# ---------------------------------------------------------
# Load Examinee Data (cached per file)
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_examinee_data(csv_name: str) -> pd.DataFrame:
    df = pd.read_csv(csv_name, dtype={"zip": str})
    df["zip"] = df["zip"].str.zfill(5)

    # Aggregate in case a zip appears more than once
    agg = (
        df.groupby("zip")
        .agg(
            area=("area", lambda x: ", ".join(sorted(set(x)))),
            sub_area=("sub_area", lambda x: ", ".join(sorted(set(x)))),
            count=("examinees", "sum"),
        )
        .reset_index()
    )
    return agg


agg = load_examinee_data(layer_options[selected_layer])

# ---------------------------------------------------------
# Load Massachusetts ZIP Code GeoJSON (cached once)
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_geojson():
    url = "https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ma_massachusetts_zip_codes_geo.min.json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()


geojson_data = load_geojson()

# ---------------------------------------------------------
# Build Map using Leafmap
# ---------------------------------------------------------
def build_map(agg_df: pd.DataFrame, geojson: dict) -> leafmap.Map:
    m = leafmap.Map(
        center=[42.1, -71.7],
        zoom=8,
        locate_control=False,
        draw_control=False,
        measure_control=False,
    )

    # ---- DYNAMIC colour scale -----------------------------------------
    min_val = agg_df["count"].min()
    max_val = agg_df["count"].max()
    if max_val == min_val:               # protect against flat data
        max_val = min_val + 1
    colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
    colormap.caption = "Number of Examinees"
    colormap.add_to(m)

    # ---- Lookup dict ---------------------------------------------------
    value_dict = agg_df.set_index("zip").to_dict(orient="index")

    # ---- Style function ------------------------------------------------
    def style_function(feature):
        zip_code = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
        val = value_dict.get(zip_code, {}).get("count", 0)
        return {
            "fillColor": colormap(val) if val > 0 else "#d9d9d9",
            "color": "black",
            "weight": 0.3,
            "fillOpacity": 0.7,
        }

    # ---- Tooltip properties (unchanged) --------------------------------
    for feature in geojson["features"]:
        z = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
        if z in value_dict:
            i = value_dict[z]
            feature["properties"]["ZIP Code"] = z
            feature["properties"]["Area"] = i["area"]
            feature["properties"]["Sub_Area"] = i["sub_area"]
            feature["properties"]["Examinees"] = i["count"]
        else:
            feature["properties"]["ZIP Code"] = z
            feature["properties"]["Area"] = "No data"
            feature["properties"]["Sub_Area"] = "-"
            feature["properties"]["Examinees"] = 0

    # ---- Add choropleth ------------------------------------------------
    m.add_geojson(
        geojson,
        style_function=style_function,
        info_mode="on_hover",
        fields=["ZIP Code", "Area", "Sub_Area", "Examinees"],
        aliases=["ZIP Code", "Area", "Sub-area", "Examinees"],
    )

    m.add_layer_control()
    return m


# ---------------------------------------------------------
# Render the Map
# ---------------------------------------------------------
with st.spinner(f"Loading {selected_layer} map…"):
    m = build_map(agg, geojson_data)
    m.to_streamlit(width=1500, height=700)
