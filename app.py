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
import leafmap.foliumap as leafmap
import pandas as pd

st.set_page_config(page_title="MA Bar Exam Map", layout="wide")

st.title("📍 Massachusetts Bar Exam Data by Area")

# ---------------------------
# Load datasets
# ---------------------------
data_files = {
    "2025": "map_data_2025.csv",
    "2024": "map_data_2024.csv",
    "2023": "map_data_2023.csv"
}

data_dict = {}
for year, path in data_files.items():
    try:
        df = pd.read_csv(path)
        df["Year"] = year
        data_dict[year] = df
    except FileNotFoundError:
        st.warning(f"⚠️ {path} not found. Skipping {year} data.")

# Combine all three years if available
if data_dict:
    combined_data = pd.concat(data_dict.values(), ignore_index=True)
else:
    st.error("No data files found!")
    st.stop()

# ---------------------------
# Sidebar selector
# ---------------------------
st.sidebar.header("🗂️ Select Dataset")
option = st.sidebar.radio(
    "Choose which dataset to view:",
    ["Combined (All Years)", "2025", "2024", "2023"],
    index=0
)

# ---------------------------
# Select data based on choice
# ---------------------------
if option == "Combined (All Years)":
    selected_data = combined_data
elif option in data_dict:
    selected_data = data_dict[option]
else:
    st.error(f"No data found for {option}")
    st.stop()

# ---------------------------
# Create the Leafmap map
# ---------------------------
m = leafmap.Map(center=[42.3, -71.8], zoom=8, draw_control=False, measure_control=True)
m.add_basemap("CartoDB.Positron")

# ---------------------------
# Add data layer
# ---------------------------
def add_data_layer(map_obj, data, name):
    """Adds a choropleth layer with hover tooltips for a given dataset."""
    if "ZCTA5CE10" not in data.columns:
        st.warning(f"Skipping {name}: missing 'ZCTA5CE10' column.")
        return

    # Rename Zip Code field for display
    data = data.rename(columns={"ZCTA5CE10": "Zip Code"})

    # Build tooltip
    tooltip_fields = []
    for col in ["Area", "Sub-Area", "Zip Code"]:
        if col in data.columns:
            tooltip_fields.append(col)

    map_obj.add_data(
        geojson=data,
        name=name,
        tooltip=tooltip_fields,
        style={
            "fillColor": "#3182bd",
            "color": "black",
            "weight": 0.5,
            "fillOpacity": 0.6
        },
        layer_type="geojson"
    )

add_data_layer(m, selected_data, option)

# ---------------------------
# Display map in Streamlit
# ---------------------------
m.to_streamlit(width=1100, height=700)

