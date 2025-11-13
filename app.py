# # app.py
# import streamlit as st
# import pandas as pd
# import requests
# import leafmap.foliumap as leafmap
# import branca.colormap as cm
# import json
# import geopandas as gpd
# from shapely.geometry import shape
# import numpy as np

# # ---------------------------------------------------------
# # Streamlit Page Setup
# # ---------------------------------------------------------
# st.set_page_config(page_title="Massachusetts Bar Examinee Map", layout="wide")

# # ---------------------------------------------------------
# # MBTA subway-served ZIP codes
# # ---------------------------------------------------------
# MBTA_ZIPS = {
#     "02108", "02109", "02110", "02111", "02113", "02114", "02115", "02116", "02118", "02119", "02120", "02121",
#     "02122", "02124", "02125", "02126", "02127", "02128", "02129", "02130", "02131", "02132", "02134", "02135",
#     "02136", "02138", "02139", "02140", "02141", "02142", "02143", "02144", "02145", "02148", "02149", "02151",
#     "02152", "02155", "02163", "02169", "02171", "02176", "02180", "02184", "02186", "02188", "02190", "02191",
#     "02215", "02445", "02446", "02453", "02458", "02459", "02467", "02472"
# }

# # ---------------------------------------------------------
# # Sidebar Controls
# # ---------------------------------------------------------
# layer_options = {
#     "All years": "map_data_all.csv",
#     "2025": "map_data_2025.csv",
#     "2024": "map_data_2024.csv",
#     "2023": "map_data_2023.csv",
# }
# selected_layer = st.sidebar.selectbox("Select data layer", options=list(layer_options.keys()), index=0)
# view_mode = st.sidebar.radio(
#     "Map view",
#     ["State-wide", "Greater Boston (MBTA subway)", "Greater Boston (Highways)"],
#     index=0
# )

# # ---------------------------------------------------------
# # Dynamic Title
# # ---------------------------------------------------------
# title_suffix = selected_layer if selected_layer == "All years" else f"July {selected_layer}"
# st.title(f"Massachusetts Bar Examinee Distribution Map – {title_suffix}")
# st.markdown(f"**View:** *{view_mode}* | **Data:** *{title_suffix}* \nHover over ZIPs. Hover highways for details.")

# # ---------------------------------------------------------
# # Load Examinee Data
# # ---------------------------------------------------------
# @st.cache_data(show_spinner=False)
# def load_examinee_data(csv_name: str) -> pd.DataFrame:
#     df = pd.read_csv(csv_name, dtype={"zip": str})
#     df["zip"] = df["zip"].str.zfill(5)
#     agg = df.groupby("zip").agg(
#         area=("area", lambda x: ", ".join(sorted(set(x)))),
#         sub_area=("sub_area", lambda x: ", ".join(sorted(set(x)))),
#         count=("examinees", "sum"),
#     ).reset_index()
#     return agg

# agg = load_examinee_data(layer_options[selected_layer])

# # ---------------------------------------------------------
# # Load MA ZIP GeoJSON
# # ---------------------------------------------------------
# @st.cache_data(show_spinner=False)
# def load_geojson():
#     url = "https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ma_massachusetts_zip_codes_geo.min.json"
#     r = requests.get(url)
#     r.raise_for_status()
#     return r.json()

# geojson_data = load_geojson()

# # ---------------------------------------------------------
# # Build Map
# # ---------------------------------------------------------
# def build_map(agg_df: pd.DataFrame, geojson: dict, mbta_mode: bool = False, highway_mode: bool = False) -> leafmap.Map:
#     # Start map with default view
#     m = leafmap.Map(
#         center=[42.3601, -71.0589],
#         zoom=8,
#         locate_control=False,
#         draw_control=False,
#         measure_control=False,
#         scroll_wheel_zoom=True
#     )

#     # Color scale
#     min_val = agg_df["count"].min()
#     max_val = agg_df["count"].max()
#     if max_val == min_val:
#         max_val = min_val + 1
#     colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
#     colormap.caption = "Number of Examinees"
#     colormap.add_to(m)

#     value_dict = agg_df.set_index("zip").to_dict(orient="index")

#     # === Filter and prepare visible ZIPs ===
#     visible_features = []
#     bounds = None

#     for feature in geojson["features"]:
#         z = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
#         is_mbta_area = z in MBTA_ZIPS

#         # In Greater Boston modes: only show MBTA ZIPs
#         if (mbta_mode or highway_mode) and not is_mbta_area:
#             continue  # Skip non-MBTA ZIPs

#         # Update properties
#         if z in value_dict:
#             i = value_dict[z]
#             feature["properties"].update({
#                 "ZIP Code": z,
#                 "Area": i["area"],
#                 "Sub_Area": i["sub_area"],
#                 "Examinees": i["count"]
#             })
#         else:
#             feature["properties"].update({
#                 "ZIP Code": z,
#                 "Area": "No data",
#                 "Sub_Area": "-",
#                 "Examinees": 0
#             })

#         visible_features.append(feature)

#         # Compute bounds for auto-fit
#         geom = shape(feature["geometry"])
#         if geom.is_valid and not geom.is_empty:
#             minx, miny, maxx, maxy = geom.bounds
#             if bounds is None:
#                 bounds = [minx, miny, maxx, maxy]
#             else:
#                 bounds = [
#                     min(bounds[0], minx),
#                     min(bounds[1], miny),
#                     max(bounds[2], maxx),
#                     max(bounds[3], maxy)
#                 ]

#     # Define style function
#     def style_function(feature):
#         zip_code = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
#         val = value_dict.get(zip_code, {}).get("count", 0)
#         return {
#             "fillColor": colormap(val) if val > 0 else "#d9d9d9",
#             "color": "black",
#             "weight": 0.3,
#             "fillOpacity": 0.7,
#         }

#     # Add only visible ZIPs
#     visible_geojson = {"type": "FeatureCollection", "features": visible_features}
#     m.add_geojson(
#         visible_geojson,
#         style_function=style_function,
#         info_mode="on_hover",
#         fields=["ZIP Code", "Area", "Sub_Area", "Examinees"],
#         aliases=["ZIP Code", "Area", "Sub-area", "Examinees"],
#     )

#     # === Auto-fit to Greater Boston ZIPs on first load ===
#     if (mbta_mode or highway_mode) and bounds:
#         # Add small padding
#         padding = 0.01
#         padded_bounds = [
#             [bounds[1] - padding, bounds[0] - padding],
#             [bounds[3] + padding, bounds[2] + padding]
#         ]
#         m.fit_bounds(padded_bounds)

#     # ------------------------
#     # MBTA Lines & Stations
#     # ------------------------
#     if mbta_mode:
#         line_colors = {
#             "blue": "#003DA5", "orange": "#ED8B00", "red": "#DA291C", "green": "#00843D",
#             "green-b": "#00843D", "green-c": "#00843D", "green-d": "#00843D", "green-e": "#00843D",
#             "silver": "#8D8D8D", "sl1": "#8D8D8D", "sl2": "#8D8D8D", "sl4": "#8D8D8D", "sl5": "#8D8D8D",
#             "mattapan": "#DA291C",
#         }

#         try:
#             with open("routes.geojson", "r", encoding="utf-8") as f:
#                 routes = json.load(f)
#             for feat in routes["features"]:
#                 props = feat.get("properties", {})
#                 route_id = str(props.get("id") or props.get("route_id", "")).lower()
#                 name = props.get("name", "Unknown Line")
#                 color = line_colors.get(route_id, "#666666")
#                 m.add_geojson(
#                     {"type": "FeatureCollection", "features": [feat]},
#                     style={"color": color, "weight": 5, "opacity": 0.9},
#                     layer_name=name,
#                 )
#         except Exception as e:
#             st.warning(f"MBTA lines failed: {e}")

#         try:
#             with open("stops.geojson", "r", encoding="utf-8") as f:
#                 stops = json.load(f)

#             def station_style(feature):
#                 lines = feature["properties"].get("lines", [])
#                 primary = next((l for l in lines if l in line_colors), "silver")
#                 return {
#                     "fillColor": line_colors.get(primary, "#666666"),
#                     "color": "white",
#                     "weight": 1.5,
#                     "radius": 6,
#                     "fillOpacity": 0.9,
#                 }

#             m.add_geojson(
#                 stops,
#                 layer_name="MBTA Stations",
#                 style_callback=station_style,
#                 info_mode="on_click",
#                 fields=["name", "lines"],
#                 aliases=["Station", "Lines"],
#             )
#         except Exception as e:
#             st.warning(f"MBTA stations failed: {e}")

#     # ------------------------
#     # Highway Layer (Green Secondary, Auto-Fit)
#     # ------------------------
#     elif highway_mode:
#         try:
#             gdf = gpd.read_file("ma_major_roads.geojson")
#             if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
#                 gdf = gdf.to_crs(epsg=4326)

#             gdf = gdf[gdf["FEATURE_TY"].isin(["Primary Road", "Secondary Road"])]

#             # Friendly labels
#             type_map = {
#                 "Primary Road": "Interstate / Major Highway",
#                 "Secondary Road": "State Route / Arterial"
#             }
#             gdf["ROAD_TYPE"] = gdf["FEATURE_TY"].map(type_map)
#             gdf["ROAD_NAME"] = (
#                 gdf["FULLNAME"]
#                 .str.replace(r"\s+(E|W|N|S|East|West|North|South)$", "", regex=True)
#                 .str.strip()
#                 .fillna("Unnamed Road")
#             )

#             highways = json.loads(gdf.to_json())

#             def highway_style(feature):
#                 ftype = feature["properties"].get("FEATURE_TY", "")
#                 color = "#0047AB" if ftype == "Primary Road" else "#00843D"  # GREEN
#                 return {"color": color, "weight": 4, "opacity": 0.9}

#             m.add_geojson(
#                 highways,
#                 layer_name="Major Highways",
#                 style_function=highway_style,
#                 info_mode="on_hover",
#                 fields=["ROAD_NAME", "ROAD_TYPE"],
#                 aliases=["Highway", "Type"],
#             )
#         except Exception as e:
#             st.warning(f"Highway layer failed: {e}")

#     m.add_layer_control()
#     return m

# # ---------------------------------------------------------
# # Render
# # ---------------------------------------------------------
# mbta_mode = (view_mode == "Greater Boston (MBTA subway)")
# highway_mode = (view_mode == "Greater Boston (Highways)")

# with st.spinner(f"Loading {selected_layer} – {view_mode.lower()} map…"):
#     m = build_map(agg, geojson_data, mbta_mode=mbta_mode, highway_mode=highway_mode)
#     m.to_streamlit(width=1500, height=700)


#version 2

# app.py
import streamlit as st
import pandas as pd
import requests
import leafmap.foliumap as leafmap
import branca.colormap as cm
import json
import geopandas as gpd
from shapely.geometry import shape
import numpy as np
from io import BytesIO

# ---------------------------------------------------------
# Streamlit Page Setup
# ---------------------------------------------------------
st.set_page_config(page_title="Massachusetts Bar Examinee Map", layout="wide")

# ---------------------------------------------------------
# MBTA subway-served ZIP codes
# ---------------------------------------------------------
MBTA_ZIPS = {
    "02108", "02109", "02110", "02111", "02113", "02114", "02115", "02116", "02118", "02119", "02120", "02121",
    "02122", "02124", "02125", "02126", "02127", "02128", "02129", "02130", "02131", "02132", "02134", "02135",
    "02136", "02138", "02139", "02140", "02141", "02142", "02143", "02144", "02145", "02148", "02149", "02151",
    "02152", "02155", "02163", "02169", "02171", "02176", "02180", "02184", "02186", "02188", "02190", "02191",
    "02215", "02445", "02446", "02453", "02458", "02459", "02467", "02472"
}

# ---------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------
layer_options = {
    "All years": "map_data_all.csv",
    "2025": "map_data_2025.csv",
    "2024": "map_data_2024.csv",
    "2023": "map_data_2023.csv",
}
selected_layer = st.sidebar.selectbox("Select data layer", options=list(layer_options.keys()), index=0)
view_mode = st.sidebar.radio(
    "Map view",
    ["State-wide", "Greater Boston (MBTA subway)", "Greater Boston (Highways)"],
    index=0
)

# ---------------------------------------------------------
# Dynamic Title
# ---------------------------------------------------------
title_suffix = selected_layer if selected_layer == "All years" else f"July {selected_layer}"
st.title(f"Massachusetts Bar Examinee Distribution Map – {title_suffix}")
st.markdown(f"**View:** *{view_mode}* | **Data:** *{title_suffix}* \nHover over ZIPs. Hover highways for details.")

# ---------------------------------------------------------
# Load Examinee Data
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_examinee_data(csv_name: str) -> pd.DataFrame:
    df = pd.read_csv(csv_name, dtype={"zip": str})
    df["zip"] = df["zip"].str.zfill(5)
    agg = df.groupby("zip").agg(
        area=("area", lambda x: ", ".join(sorted(set(x)))),
        sub_area=("sub_area", lambda x: ", ".join(sorted(set(x)))),
        count=("examinees", "sum"),
    ).reset_index()
    return agg

agg = load_examinee_data(layer_options[selected_layer])

# ---------------------------------------------------------
# Load MA ZIP GeoJSON
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_geojson():
    url = "https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ma_massachusetts_zip_codes_geo.min.json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

geojson_data = load_geojson()

# ---------------------------------------------------------
# Build Map (leafmap version - for display)
# ---------------------------------------------------------
def build_leafmap(agg_df: pd.DataFrame, geojson: dict, mbta_mode: bool = False, highway_mode: bool = False) -> leafmap.Map:
    m = leafmap.Map(
        center=[42.3601, -71.0589],
        zoom=8,
        locate_control=False,
        draw_control=False,
        measure_control=False,
        scroll_wheel_zoom=True
    )

    min_val = agg_df["count"].min()
    max_val = agg_df["count"].max()
    if max_val == min_val:
        max_val = min_val + 1
    colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
    colormap.caption = "Number of Examinees"
    colormap.add_to(m)

    value_dict = agg_df.set_index("zip").to_dict(orient="index")
    visible_features = []
    bounds = None

    for feature in geojson["features"]:
        z = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
        is_mbta_area = z in MBTA_ZIPS
        if (mbta_mode or highway_mode) and not is_mbta_area:
            continue

        if z in value_dict:
            i = value_dict[z]
            feature["properties"].update({
                "ZIP Code": z,
                "Area": i["area"],
                "Sub_Area": i["sub_area"],
                "Examinees": i["count"]
            })
        else:
            feature["properties"].update({
                "ZIP Code": z,
                "Area": "No data",
                "Sub_Area": "-",
                "Examinees": 0
            })

        geom = shape(feature["geometry"])
        if geom.is_valid and not geom.is_empty:
            minx, miny, maxx, maxy = geom.bounds
            if bounds is None:
                bounds = [minx, miny, maxx, maxy]
            else:
                bounds = [min(bounds[0], minx), min(bounds[1], miny), max(bounds[2], maxx), max(bounds[3], maxy)]
        visible_features.append(feature)

    def style_function(feature):
        zip_code = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
        val = value_dict.get(zip_code, {}).get("count", 0)
        return {
            "fillColor": colormap(val) if val > 0 else "#d9d9d9",
            "color": "black",
            "weight": 0.3,
            "fillOpacity": 0.7,
        }

    visible_geojson = {"type": "FeatureCollection", "features": visible_features}
    m.add_geojson(
        visible_geojson,
        style_function=style_function,
        info_mode="on_hover",
        fields=["ZIP Code", "Area", "Sub_Area", "Examinees"],
        aliases=["ZIP Code", "Area", "Sub-area", "Examinees"],
    )

    if (mbta_mode or highway_mode) and bounds:
        padding = 0.01
        padded_bounds = [[bounds[1] - padding, bounds[0] - padding], [bounds[3] + padding, bounds[2] + padding]]
        m.fit_bounds(padded_bounds)

    # MBTA
    if mbta_mode:
        line_colors = {
            "blue": "#003DA5", "orange": "#ED8B00", "red": "#DA291C", "green": "#00843D",
            "green-b": "#00843D", "green-c": "#00843D", "green-d": "#00843D", "green-e": "#00843D",
            "silver": "#8D8D8D", "sl1": "#8D8D8D", "sl2": "#8D8D8D", "sl4": "#8D8D8D", "sl5": "#8D8D8D",
            "mattapan": "#DA291C",
        }
        try:
            with open("routes.geojson", "r", encoding="utf-8") as f:
                routes = json.load(f)
            for feat in routes["features"]:
                props = feat.get("properties", {})
                route_id = str(props.get("id") or props.get("route_id", "")).lower()
                name = props.get("name", "Unknown Line")
                color = line_colors.get(route_id, "#666666")
                m.add_geojson(
                    {"type": "FeatureCollection", "features": [feat]},
                    style={"color": color, "weight": 5, "opacity": 0.9},
                    layer_name=name,
                )
        except Exception as e:
            st.warning(f"MBTA lines failed: {e}")

        try:
            with open("stops.geojson", "r", encoding="utf-8") as f:
                stops = json.load(f)
            def station_style(feature):
                lines = feature["properties"].get("lines", [])
                primary = next((l for l in lines if l in line_colors), "silver")
                return {
                    "fillColor": line_colors.get(primary, "#666666"),
                    "color": "white",
                    "weight": 1.5,
                    "radius": 6,
                    "fillOpacity": 0.9,
                }
            m.add_geojson(
                stops,
                layer_name="MBTA Stations",
                style_callback=station_style,
                info_mode="on_click",
                fields=["name", "lines"],
                aliases=["Station", "Lines"],
            )
        except Exception as e:
            st.warning(f"MBTA stations failed: {e}")

    # Highways
    elif highway_mode:
        try:
            gdf = gpd.read_file("ma_major_roads.geojson")
            if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)
            gdf = gdf[gdf["FEATURE_TY"].isin(["Primary Road", "Secondary Road"])]
            type_map = {"Primary Road": "Interstate / Major Highway", "Secondary Road": "State Route / Arterial"}
            gdf["ROAD_TYPE"] = gdf["FEATURE_TY"].map(type_map)
            gdf["ROAD_NAME"] = (
                gdf["FULLNAME"]
                .str.replace(r"\s+(E|W|N|S|East|West|North|South)$", "", regex=True)
                .str.strip()
                .fillna("Unnamed Road")
            )
            highways = json.loads(gdf.to_json())
            def highway_style(feature):
                ftype = feature["properties"].get("FEATURE_TY", "")
                color = "#0047AB" if ftype == "Primary Road" else "#00843D"
                return {"color": color, "weight": 4, "opacity": 0.9}
            m.add_geojson(
                highways,
                layer_name="Major Highways",
                style_function=highway_style,
                info_mode="on_hover",
                fields=["ROAD_NAME", "ROAD_TYPE"],
                aliases=["Highway", "Type"],
            )
        except Exception as e:
            st.warning(f"Highway layer failed: {e}")

    m.add_layer_control()
    return m

# ---------------------------------------------------------
# Convert leafmap → folium (for HTML export only)
# ---------------------------------------------------------
def leafmap_to_folium(leafmap_obj) -> 'folium.Map':
    """Extract underlying folium map from leafmap"""
    return leafmap_obj._folium_map

# ---------------------------------------------------------
# Render in Streamlit
# ---------------------------------------------------------
mbta_mode = (view_mode == "Greater Boston (MBTA subway)")
highway_mode = (view_mode == "Greater Boston (Highways)")

with st.spinner(f"Loading {selected_layer} – {view_mode.lower()} map…"):
    m_leaf = build_leafmap(agg, geojson_data, mbta_mode=mbta_mode, highway_mode=highway_mode)
    m_leaf.to_streamlit(width=1500, height=700)

# ---------------------------------------------------------
# DOWNLOAD AS HTML (Preserves leafmap look!)
# ---------------------------------------------------------
st.markdown("---")
if st.button("Download Current Map as HTML (Offline)"):
    with st.spinner("Generating HTML with original style..."):
        # Reuse the same map object
        folium_map = leafmap_to_folium(m_leaf)
        
        output = BytesIO()
        folium_map.save(output, close_file=False)
        html_bytes = output.getvalue()

        filename = f"ma_bar_exam_map_{selected_layer.lower().replace(' ', '_')}_{view_mode.lower().replace(' ', '_').replace('(', '').replace(')', '')}.html"

        st.download_button(
            label="Download HTML File",
            data=html_bytes,
            file_name=filename,
            mime="text/html",
            help="Preserves your original map style. Works offline (except base tiles)."
        )
        st.success("HTML ready! Click to download.")
        st.info("Your map style is 100% preserved!")
