# import streamlit as st
# import pandas as pd
# import requests
# import leafmap.foliumap as leafmap
# import branca.colormap as cm

# # ---------------------------------------------------------
# # Streamlit Page Setup
# # ---------------------------------------------------------
# st.set_page_config(
#     page_title="Massachusetts Bar Examinee Map (July 2025)",
#     layout="wide",
# )

# st.title("Massachusetts Bar Examinee Distribution Map")
# st.markdown(
#     """
#     Hover over any area to view the ZIP Code, Area, Sub-Area, and number of Examinees.
#     """
# )

# # ---------------------------------------------------------
# # Load Examinee Data (Local CSV)
# # ---------------------------------------------------------
# @st.cache_data
# def load_examinee_data():
#     # Load your CSV file directly from the repo
#     df = pd.read_csv("map_data_2025.csv", dtype={"zip": str})
#     df["zip"] = df["zip"].str.zfill(5)
#     df = (
#         df.groupby("zip")
#         .agg(
#             area=("area", lambda x: ", ".join(sorted(set(x)))),
#             sub_area=("sub_area", lambda x: ", ".join(sorted(set(x)))),
#             count=("examinees", "sum"),
#         )
#         .reset_index()
#     )
#     return df

# agg = load_examinee_data()

# # ---------------------------------------------------------
# # Load Massachusetts ZIP Code GeoJSON
# # ---------------------------------------------------------
# @st.cache_data
# def load_geojson():
#     url = "https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ma_massachusetts_zip_codes_geo.min.json"
#     response = requests.get(url)
#     response.raise_for_status()
#     return response.json()

# geojson_data = load_geojson()

# # ---------------------------------------------------------
# # Build Map using Leafmap
# # ---------------------------------------------------------
# def build_map(agg, geojson_data):
#     """Builds an interactive choropleth map with hover tooltips using Leafmap."""

#     # Initialize Leafmap
#     m = leafmap.Map(
#         center=[42.1, -71.7],
#         zoom=8,
#         locate_control=False,
#         draw_control=False,
#         measure_control=False,
#     )

#     # Prepare color scale
#     min_val = agg["count"].min()
#     max_val = agg["count"].max()
#     colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
#     colormap.caption = "Number of Examinees"
#     colormap.add_to(m)

#     # Lookup for examinee counts and area info
#     value_dict = agg.set_index("zip").to_dict(orient="index")

#     # Define style function for polygons
#     def style_function(feature):
#         zip_code = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
#         val = value_dict.get(zip_code, {}).get("count", 0)
#         return {
#             "fillColor": colormap(val) if val > 0 else "#d9d9d9",
#             "color": "black",
#             "weight": 0.3,
#             "fillOpacity": 0.7,
#         }

#     # Add custom tooltip info
#     for feature in geojson_data["features"]:
#         z = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
#         if z in value_dict:
#             i = value_dict[z]
#             feature["properties"]["ZIP Code"] = z  # ✅ renamed key
#             feature["properties"]["Area"] = i["area"]
#             feature["properties"]["Sub_Area"] = i["sub_area"]
#             feature["properties"]["Examinees"] = i["count"]
#         else:
#             feature["properties"]["ZIP Code"] = z
#             feature["properties"]["Area"] = "No data"
#             feature["properties"]["Sub_Area"] = "-"
#             feature["properties"]["Examinees"] = 0

#     # Add GeoJSON with hover tooltips (updated field name)
#     m.add_geojson(
#         geojson_data,
#         style_function=style_function,
#         info_mode="on_hover",  # enables hover tooltips
#         fields=["ZIP Code", "Area", "Sub_Area", "Examinees"],  # ✅ fixed here
#         aliases=["ZIP Code", "Area", "Sub-area", "Examinees"],
#     )

#     # Add layer control
#     m.add_layer_control()
#     return m

# # ---------------------------------------------------------
# # Render the Map
# # ---------------------------------------------------------
# with st.spinner("Loading Massachusetts Bar Examinee Map..."):
#     m = build_map(agg, geojson_data)
#     m.to_streamlit(width=1500, height=800)



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

st.title("Massachusetts Bar Examinee Distribution Map")
st.markdown(
    """
    Hover over any area to view the ZIP Code, Area, Sub-Area, and number of Examinees.
    Use the **layer control button (top-right)** to switch between Combined, 2025, 2024, and 2023 data.
    """
)

# ---------------------------------------------------------
# Load Examinee Data (Local CSV)
# ---------------------------------------------------------
@st.cache_data
def load_examinee_data(file_path):
    df = pd.read_csv(file_path, dtype={"zip": str})
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

# Combined dataset
@st.cache_data
def load_combined_data():
    files = ["map_data_2025.csv", "map_data_2024.csv", "map_data_2023.csv"]
    dfs = []
    for f in files:
        try:
            dfs.append(load_examinee_data(f))
        except FileNotFoundError:
            st.warning(f"⚠️ Missing: {f}")
    if not dfs:
        st.error("No data files found!")
        st.stop()
    combined = pd.concat(dfs, ignore_index=True)
    combined = (
        combined.groupby("zip")
        .agg(
            area=("area", lambda x: ", ".join(sorted(set(x)))),
            sub_area=("sub_area", lambda x: ", ".join(sorted(set(x)))),
            count=("count", "sum"),
        )
        .reset_index()
    )
    return combined

# Load all dataframes
agg_combined = load_combined_data()
agg_2025 = load_examinee_data("map_data_2025.csv")
agg_2024 = load_examinee_data("map_data_2024.csv")
agg_2023 = load_examinee_data("map_data_2023.csv")

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
def add_layer(m, agg, geojson_data, layer_name):
    """Adds a single year/layer to the map using identical visual settings."""

    # Prepare color scale
    min_val = agg["count"].min()
    max_val = agg["count"].max()
    colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
    colormap.caption = "Number of Examinees"

    # Lookup for examinee counts and area info
    value_dict = agg.set_index("zip").to_dict(orient="index")

    # Style function for polygons
    def style_function(feature):
        zip_code = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
        val = value_dict.get(zip_code, {}).get("count", 0)
        return {
            "fillColor": colormap(val) if val > 0 else "#d9d9d9",
            "color": "black",
            "weight": 0.3,
            "fillOpacity": 0.7,
        }

    # Prepare tooltip info
    for feature in geojson_data["features"]:
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

    # Add layer
    m.add_geojson(
        geojson_data,
        style_function=style_function,
        info_mode="on_hover",
        fields=["ZIP Code", "Area", "Sub_Area", "Examinees"],
        aliases=["ZIP Code", "Area", "Sub-area", "Examinees"],
        name=layer_name,
    )

# ---------------------------------------------------------
# Render Map
# ---------------------------------------------------------
with st.spinner("Loading Massachusetts Bar Examinee Map..."):
    m = leafmap.Map(
        center=[42.1, -71.7],
        zoom=8,
        locate_control=False,
        draw_control=False,
        measure_control=False,
    )

    # Add layers
    add_layer(m, agg_combined, geojson_data, "Combined (All Years)")
    add_layer(m, agg_2025, geojson_data, "2025")
    add_layer(m, agg_2024, geojson_data, "2024")
    add_layer(m, agg_2023, geojson_data, "2023")

    # Add layer control (user can toggle visibility)
    m.add_layer_control()

    # Show map
    m.to_streamlit(width=1500, height=800)
