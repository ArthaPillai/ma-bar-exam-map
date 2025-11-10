#first version
# # app.py
# import streamlit as st
# import pandas as pd
# import requests
# import leafmap.foliumap as leafmap
# import branca.colormap as cm

# # ---------------------------------------------------------
# # Streamlit Page Setup
# # ---------------------------------------------------------
# st.set_page_config(
#     page_title="Massachusetts Bar Examinee Map",
#     layout="wide",
# )

# # ---------------------------------------------------------
# # Sidebar – Layer selector
# # ---------------------------------------------------------
# layer_options = {
#     "All years": "map_data_all.csv",
#     "2025": "map_data_2025.csv",
#     "2024": "map_data_2024.csv",
#     "2023": "map_data_2023.csv",
# }
# selected_layer = st.sidebar.selectbox(
#     "Select data layer",
#     options=list(layer_options.keys()),
#     index=0,
# )

# # ---- TITLE -------------------------------------------------
# if selected_layer == "All years":
#     title_suffix = "All Years"
# else:
#     title_suffix = f"July {selected_layer}"

# st.title(f"Massachusetts Bar Examinee Distribution Map – {title_suffix}")

# st.markdown(
#     """
#     Hover over any area to view the ZIP Code, Area, Sub-Area, and number of Examinees.
#     """
# )

# # ---------------------------------------------------------
# # Load Examinee Data (cached per file)
# # ---------------------------------------------------------
# @st.cache_data(show_spinner=False)
# def load_examinee_data(csv_name: str) -> pd.DataFrame:
#     df = pd.read_csv(csv_name, dtype={"zip": str})
#     df["zip"] = df["zip"].str.zfill(5)

#     # Aggregate in case a zip appears more than once
#     agg = (
#         df.groupby("zip")
#         .agg(
#             area=("area", lambda x: ", ".join(sorted(set(x)))),
#             sub_area=("sub_area", lambda x: ", ".join(sorted(set(x)))),
#             count=("examinees", "sum"),
#         )
#         .reset_index()
#     )
#     return agg


# agg = load_examinee_data(layer_options[selected_layer])

# # ---------------------------------------------------------
# # Load Massachusetts ZIP Code GeoJSON (cached once)
# # ---------------------------------------------------------
# @st.cache_data(show_spinner=False)
# def load_geojson():
#     url = "https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ma_massachusetts_zip_codes_geo.min.json"
#     r = requests.get(url)
#     r.raise_for_status()
#     return r.json()


# geojson_data = load_geojson()

# # ---------------------------------------------------------
# # Build Map using Leafmap
# # ---------------------------------------------------------
# def build_map(agg_df: pd.DataFrame, geojson: dict) -> leafmap.Map:
#     m = leafmap.Map(
#         center=[42.1, -71.7],
#         zoom=8,
#         locate_control=False,
#         draw_control=False,
#         measure_control=False,
#     )

#     # ---- DYNAMIC colour scale -----------------------------------------
#     min_val = agg_df["count"].min()
#     max_val = agg_df["count"].max()
#     if max_val == min_val:               # protect against flat data
#         max_val = min_val + 1
#     colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
#     colormap.caption = "Number of Examinees"
#     colormap.add_to(m)

#     # ---- Lookup dict ---------------------------------------------------
#     value_dict = agg_df.set_index("zip").to_dict(orient="index")

#     # ---- Style function ------------------------------------------------
#     def style_function(feature):
#         zip_code = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
#         val = value_dict.get(zip_code, {}).get("count", 0)
#         return {
#             "fillColor": colormap(val) if val > 0 else "#d9d9d9",
#             "color": "black",
#             "weight": 0.3,
#             "fillOpacity": 0.7,
#         }

#     # ---- Tooltip properties (unchanged) --------------------------------
#     for feature in geojson["features"]:
#         z = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
#         if z in value_dict:
#             i = value_dict[z]
#             feature["properties"]["ZIP Code"] = z
#             feature["properties"]["Area"] = i["area"]
#             feature["properties"]["Sub_Area"] = i["sub_area"]
#             feature["properties"]["Examinees"] = i["count"]
#         else:
#             feature["properties"]["ZIP Code"] = z
#             feature["properties"]["Area"] = "No data"
#             feature["properties"]["Sub_Area"] = "-"
#             feature["properties"]["Examinees"] = 0

#     # ---- Add choropleth ------------------------------------------------
#     m.add_geojson(
#         geojson,
#         style_function=style_function,
#         info_mode="on_hover",
#         fields=["ZIP Code", "Area", "Sub_Area", "Examinees"],
#         aliases=["ZIP Code", "Area", "Sub-area", "Examinees"],
#     )

#     m.add_layer_control()
#     return m


# # ---------------------------------------------------------
# # Render the Map
# # ---------------------------------------------------------
# with st.spinner(f"Loading {selected_layer} map…"):
#     m = build_map(agg, geojson_data)
#     m.to_streamlit(width=1500, height=700)


#second version
# # app.py
# import streamlit as st
# import pandas as pd
# import requests
# import leafmap.foliumap as leafmap
# import branca.colormap as cm

# # ---------------------------------------------------------
# # Streamlit Page Setup
# # ---------------------------------------------------------
# st.set_page_config(
#     page_title="Massachusetts Bar Examinee Map",
#     layout="wide",
# )

# # ---------------------------------------------------------
# # MBTA subway-served ZIP codes (covers all subway stations)
# # ---------------------------------------------------------
# MBTA_ZIPS = {
#     "02108", "02109", "02110", "02111", "02113", "02114", "02115", "02116",
#     "02118", "02119", "02120", "02121", "02122", "02124", "02125", "02126",
#     "02127", "02128", "02129", "02130", "02131", "02132", "02134", "02135",
#     "02136", "02138", "02139", "02140", "02141", "02142", "02143", "02144",
#     "02145", "02148", "02149", "02151", "02152", "02155", "02163", "02169",
#     "02171", "02176", "02180", "02184", "02186", "02188", "02190", "02191",
#     "02215", "02445", "02446", "02453", "02458", "02459", "02467", "02472",
# }

# # ---------------------------------------------------------
# # Sidebar – Layer selector
# # ---------------------------------------------------------
# layer_options = {
#     "All years": "map_data_all.csv",
#     "2025": "map_data_2025.csv",
#     "2024": "map_data_2024.csv",
#     "2023": "map_data_2023.csv",
# }
# selected_layer = st.sidebar.selectbox(
#     "Select data layer",
#     options=list(layer_options.keys()),
#     index=0,
# )

# # ---------------------------------------------------------
# # Sidebar – View selector
# # ---------------------------------------------------------
# view_mode = st.sidebar.radio(
#     "Map view",
#     options=["State-wide", "Greater Boston (MBTA subway)"],
#     index=0,
# )

# # ---------------------------------------------------------
# # Dynamic Title
# # ---------------------------------------------------------
# if selected_layer == "All years":
#     title_suffix = selected_layer
# else:
#     title_suffix = f"July {selected_layer}"

# st.title(f"Massachusetts Bar Examinee Distribution Map – {title_suffix}")
# st.markdown(
#     f"**Current view:** *{view_mode}*  |  **Data:** *{title_suffix}*  \n"
#     "Hover over any area to view ZIP Code, Area, Sub-Area, and number of Examinees."
# )

# # ---------------------------------------------------------
# # Load Examinee Data (cached per file)
# # ---------------------------------------------------------
# @st.cache_data(show_spinner=False)
# def load_examinee_data(csv_name: str) -> pd.DataFrame:
#     df = pd.read_csv(csv_name, dtype={"zip": str})
#     df["zip"] = df["zip"].str.zfill(5)

#     agg = (
#         df.groupby("zip")
#         .agg(
#             area=("area", lambda x: ", ".join(sorted(set(x)))),
#             sub_area=("sub_area", lambda x: ", ".join(sorted(set(x)))),
#             count=("examinees", "sum"),
#         )
#         .reset_index()
#     )
#     return agg

# agg = load_examinee_data(layer_options[selected_layer])

# # ---------------------------------------------------------
# # Load Massachusetts ZIP Code GeoJSON (cached once)
# # ---------------------------------------------------------
# @st.cache_data(show_spinner=False)
# def load_geojson():
#     url = "https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ma_massachusetts_zip_codes_geo.min.json"
#     r = requests.get(url)
#     r.raise_for_status()
#     return r.json()

# geojson_data = load_geojson()

# # ---------------------------------------------------------
# # Build Map with MBTA masking & dynamic zoom
# # ---------------------------------------------------------
# def build_map(agg_df: pd.DataFrame, geojson: dict, mbta_mode: bool) -> leafmap.Map:
#     # Base map – zoom/center changes with mode
#     center = [42.3601, -71.0589]  # Downtown Boston
#     zoom = 11 if mbta_mode else 8
#     m = leafmap.Map(
#         center=center,
#         zoom=zoom,
#         locate_control=False,
#         draw_control=False,
#         measure_control=False,
#     )

#     # Dynamic color scale
#     min_val = agg_df["count"].min()
#     max_val = agg_df["count"].max()
#     if max_val == min_val:
#         max_val = min_val + 1
#     colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
#     colormap.caption = "Number of Examinees"
#     colormap.add_to(m)

#     # Lookup dict
#     value_dict = agg_df.set_index("zip").to_dict(orient="index")

#     # Style function – hide non-MBTA ZIPs in subway mode
#     def style_function(feature):
#         zip_code = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)

#         if mbta_mode and zip_code not in MBTA_ZIPS:
#             return {"fillColor": "transparent", "color": "transparent", "weight": 0}

#         val = value_dict.get(zip_code, {}).get("count", 0)
#         return {
#             "fillColor": colormap(val) if val > 0 else "#d9d9d9",
#             "color": "black",
#             "weight": 0.3,
#             "fillOpacity": 0.7,
#         }

#     # Add tooltip data
#     for feature in geojson["features"]:
#         z = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
#         if z in value_dict:
#             i = value_dict[z]
#             feature["properties"]["ZIP Code"] = z
#             feature["properties"]["Area"] = i["area"]
#             feature["properties"]["Sub_Area"] = i["sub_area"]
#             feature["properties"]["Examinees"] = i["count"]
#         else:
#             feature["properties"]["ZIP Code"] = z
#             feature["properties"]["Area"] = "No data"
#             feature["properties"]["Sub_Area"] = "-"
#             feature["properties"]["Examinees"] = 0

#     # Add choropleth
#     m.add_geojson(
#         geojson,
#         style_function=style_function,
#         info_mode="on_hover",
#         fields=["ZIP Code", "Area", "Sub_Area", "Examinees"],
#         aliases=["ZIP Code", "Area", "Sub-area", "Examinees"],
#     )

#     m.add_layer_control()
#     return m

# # ---------------------------------------------------------
# # Render the Map
# # ---------------------------------------------------------
# mbta_mode = (view_mode == "Greater Boston (MBTA subway)")

# with st.spinner(f"Loading {selected_layer} – {view_mode.lower()} map…"):
#     m = build_map(agg, geojson_data, mbta_mode)
#     m.to_streamlit(width=1500, height=800)


#3rd version

# app.py
import streamlit as st
import pandas as pd
import requests
import leafmap.foliumap as leafmap
import branca.colormap as cm
import json
import pyproj  # pip install pyproj

# ---------------------------------------------------------
# Coordinate transformer: EPSG:26986 → WGS84
# ---------------------------------------------------------
transformer = pyproj.Transformer.from_crs("EPSG:26986", "EPSG:4326", always_xy=True)

def transform_coords(x, y):
    lon, lat = transformer.transform(x, y)
    return [lon, lat]

# ---------------------------------------------------------
# Streamlit Setup
# ---------------------------------------------------------
st.set_page_config(page_title="Massachusetts Bar Examinee Map", layout="wide")

MBTA_ZIPS = { ... }  # (your list)

# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------
layer_options = { "All years": "map_data_all.csv", "2025": "map_data_2025.csv", ... }
selected_layer = st.sidebar.selectbox("Select data layer", options=list(layer_options.keys()), index=0)
view_mode = st.sidebar.radio("Map view", ["State-wide", "Greater Boston (MBTA subway)"], index=0)

title_suffix = selected_layer if selected_layer == "All years" else f"July {selected_layer}"
st.title(f"Massachusetts Bar Examinee Distribution Map – {title_suffix}")
st.markdown(f"**View:** *{view_mode}* | **Data:** *{title_suffix}*")

# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_examinee_data(csv_name): ...
agg = load_examinee_data(layer_options[selected_layer])

@st.cache_data(show_spinner=False)
def load_geojson(): ...
geojson_data = load_geojson()

# ---------------------------------------------------------
# Build Map
# ---------------------------------------------------------
def build_map(agg_df, geojson, mbta_mode):
    m = leafmap.Map(center=[42.3601, -71.0589], zoom=11 if mbta_mode else 8, ...)

    # ... (choropleth code same as before) ...

    # ---------------------------------------------------------
    # ADD MBTA LINES & STATIONS (only in subway mode)
    # ---------------------------------------------------------
    if mbta_mode:
        line_colors = {"RED": "#DA291C", "ORANGE": "#ED8B00", "BLUE": "#003DA5", "GREEN": "#00843D", "SILVER": "#8D8D8D"}

        # Load and project ARC (lines)
        try:
            with open("GISDATA.MBTA_ARC.json", "r") as f:
                arcs = json.load(f)
            for feat in arcs["features"]:
                line = feat["properties"].get("line", "").upper()
                if line in line_colors:
                    coords = feat["geometry"]["coordinates"]
                    projected = [transform_coords(x, y) for x, y in coords]
                    feat["geometry"]["coordinates"] = projected
                    m.add_geojson(
                        feat,
                        style={"color": line_colors[line], "weight": 4, "opacity": 0.9},
                        layer_name=line
                    )
        except Exception as e:
            st.warning(f"Lines failed: {e}")

        # Load and project NODE (stations)
        try:
            with open("GISDATA.MBTA_NODE.json", "r") as f:
                nodes = json.load(f)
            station_features = []
            for feat in nodes["features"]:
                x, y = feat["geometry"]["coordinates"]
                lon, lat = transform_coords(x, y)
                station = feat["properties"].get("station", "Unknown")
                line = feat["properties"].get("line", "")
                color = line_colors.get(line, "#333")
                station_features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {"name": station, "line": line, "color": color}
                })
            m.add_geojson(
                {"type": "FeatureCollection", "features": station_features},
                layer_name="MBTA Stations",
                style={"color": "color", "radius": 6, "fillOpacity": 0.8, "weight": 1},
                info_mode="on_click",
                fields=["name", "line"],
                aliases=["Station", "Line"]
            )
        except Exception as e:
            st.warning(f"Stations failed: {e}")

    m.add_layer_control()
    return m

# ---------------------------------------------------------
# Render
# ---------------------------------------------------------
mbta_mode = (view_mode == "Greater Boston (MBTA subway)")
with st.spinner("Loading map…"):
    m = build_map(agg, geojson_data, mbta_mode)
    m.to_streamlit(width=1500, height=800)
