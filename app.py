# # version 1

# # app.py 
# import streamlit as st
# import pandas as pd
# import requests
# import leafmap.foliumap as leafmap
# import branca.colormap as cm
# import json

# # ---------------------------------------------------------
# # Streamlit Page Setup
# # ---------------------------------------------------------
# st.set_page_config(page_title="Massachusetts Bar Examinee Map", layout="wide")

# # ---------------------------------------------------------
# # MBTA subway-served ZIP codes
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
# # Sidebar Controls
# # ---------------------------------------------------------
# layer_options = {
#     "All years": "map_data_all.csv",
#     "2025": "map_data_2025.csv",
#     "2024": "map_data_2024.csv",
#     "2023": "map_data_2023.csv",
# }
# selected_layer = st.sidebar.selectbox("Select data layer", options=list(layer_options.keys()), index=0)
# view_mode = st.sidebar.radio("Map view", ["State-wide", "Greater Boston (MBTA subway)"], index=0)

# # ---------------------------------------------------------
# # Dynamic Title
# # ---------------------------------------------------------
# title_suffix = selected_layer if selected_layer == "All years" else f"July {selected_layer}"
# st.title(f"Massachusetts Bar Examinee Distribution Map – {title_suffix}")
# st.markdown(f"**View:** *{view_mode}* | **Data:** *{title_suffix}*  \nHover over ZIPs. Click stations for details.")

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
# def build_map(agg_df: pd.DataFrame, geojson: dict, mbta_mode: bool) -> leafmap.Map:
#     m = leafmap.Map(
#         center=[42.30, -71.05],  
#         zoom=9 if mbta_mode else 8,  
#         locate_control=False,
#         draw_control=False,
#         measure_control=False,
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

#     # Add ZIP code polygons
#     for feature in geojson["features"]:
#         z = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
#         if z in value_dict:
#             i = value_dict[z]
#             feature["properties"].update({
#                 "ZIP Code": z, "Area": i["area"],
#                 "Sub_Area": i["sub_area"], "Examinees": i["count"]
#             })
#         else:
#             feature["properties"].update({
#                 "ZIP Code": z, "Area": "No data",
#                 "Sub_Area": "-", "Examinees": 0
#             })

#     m.add_geojson(
#         geojson,
#         style_function=style_function,
#         info_mode="on_hover",
#         fields=["ZIP Code", "Area", "Sub_Area", "Examinees"],
#         aliases=["ZIP Code", "Area", "Sub-area", "Examinees"],
#     )

#     # ---------------------------------------------------------
#     # ADD MBTA LINES & STATIONS (from NEW files)
#     # ---------------------------------------------------------
#     if mbta_mode:
#         line_colors = {
#             "blue": "#003DA5",
#             "orange": "#ED8B00",
#             "red": "#DA291C",
#             "green": "#00843D",
#             "green-b": "#00843D",
#             "green-c": "#00843D",
#             "green-d": "#00843D",
#             "green-e": "#00843D",
#             "silver": "#8D8D8D",
#             "sl1": "#8D8D8D",
#             "sl2": "#8D8D8D",
#             "sl4": "#8D8D8D",
#             "sl5": "#8D8D8D",
#             "mattapan": "#DA291C",
#         }

#         # === LINES: routes.geojson ===
#         try:
#             with open("routes.geojson", "r", encoding="utf-8") as f:
#                 routes = json.load(f)

#             for feat in routes["features"]:
#                 props = feat.get("properties", {})
#                 route_id = str(props.get("id") or props.get("route_id", "")).lower()
#                 name = props.get("name", "Unknown Line")
#                 color = line_colors.get(route_id, "#666666")

#                 # Wrap each feature to be valid GeoJSON
#                 m.add_geojson(
#                     {"type": "FeatureCollection", "features": [feat]},
#                     style={"color": color, "weight": 5, "opacity": 0.9},
#                     layer_name=name
#                 )
#         except Exception as e:
#             st.warning(f"MBTA lines failed: {e}")

#         # === STATIONS: stops.geojson ===
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
#                     "fillOpacity": 0.9
#                 }

#             m.add_geojson(
#                 stops,
#                 layer_name="MBTA Stations",
#                 style_callback=station_style,
#                 info_mode="on_click",
#                 fields=["name", "lines"],
#                 aliases=["Station", "Lines"]
#             )
#         except Exception as e:
#             st.warning(f"MBTA stations failed: {e}")

#     m.add_layer_control()
#     return m

# # ---------------------------------------------------------
# # Render
# # ---------------------------------------------------------
# mbta_mode = (view_mode == "Greater Boston (MBTA subway)")

# with st.spinner(f"Loading {selected_layer} – {view_mode.lower()} map…"):
#     m = build_map(agg, geojson_data, mbta_mode)
#     m.to_streamlit(width=1500, height=700)


#version 2

# # app.py 
# import streamlit as st
# import pandas as pd
# import requests
# import leafmap.foliumap as leafmap
# import branca.colormap as cm
# import json

# # ---------------------------------------------------------
# # Streamlit Page Setup
# # ---------------------------------------------------------
# st.set_page_config(page_title="Massachusetts Bar Examinee Map", layout="wide")

# # ---------------------------------------------------------
# # MBTA subway-served ZIP codes
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
# st.markdown(f"**View:** *{view_mode}* | **Data:** *{title_suffix}*  \nHover over ZIPs. Click stations/highways for details.")

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
#     # Set view for Greater Boston vs State-wide
#     if highway_mode or mbta_mode:
#         # Greater Boston view (wider zoom)
#         m = leafmap.Map(
#             center=[42.30, -71.05],
#             zoom=9,
#             locate_control=False,
#             draw_control=False,
#             measure_control=False,
#         )
#     else:
#         # State-wide view
#         m = leafmap.Map(
#             center=[42.3601, -71.0589],
#             zoom=8,
#             locate_control=False,
#             draw_control=False,
#             measure_control=False,
#         )

#     # Color scale
#     min_val = agg_df["count"].min()
#     max_val = agg_df["count"].max()
#     if max_val == min_val:
#         max_val = min_val + 1
#     colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
#     colormap.caption = "Number of Examinees"
#     colormap.add_to(m)

#     value_dict = agg_df.set_index("zip").to_dict(orient="index")

#     def style_function(feature):
#         zip_code = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
#         if (mbta_mode or highway_mode) and zip_code not in MBTA_ZIPS:
#             return {"fillColor": "transparent", "color": "transparent", "weight": 0}
#         val = value_dict.get(zip_code, {}).get("count", 0)
#         return {
#             "fillColor": colormap(val) if val > 0 else "#d9d9d9",
#             "color": "black",
#             "weight": 0.3,
#             "fillOpacity": 0.7,
#         }

#     # Add ZIP polygons
#     for feature in geojson["features"]:
#         z = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
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

#     m.add_geojson(
#         geojson,
#         style_function=style_function,
#         info_mode="on_hover",
#         fields=["ZIP Code", "Area", "Sub_Area", "Examinees"],
#         aliases=["ZIP Code", "Area", "Sub-area", "Examinees"],
#     )

#     # Add MBTA lines & stations
#     if mbta_mode:
#         line_colors = {
#             "blue": "#003DA5",
#             "orange": "#ED8B00",
#             "red": "#DA291C",
#             "green": "#00843D",
#             "green-b": "#00843D",
#             "green-c": "#00843D",
#             "green-d": "#00843D",
#             "green-e": "#00843D",
#             "silver": "#8D8D8D",
#             "sl1": "#8D8D8D",
#             "sl2": "#8D8D8D",
#             "sl4": "#8D8D8D",
#             "sl5": "#8D8D8D",
#             "mattapan": "#DA291C",
#         }

#         # === LINES: routes.geojson ===
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
#                     layer_name=name
#                 )
#         except Exception as e:
#             st.warning(f"MBTA lines failed: {e}")

#         # === STATIONS: stops.geojson ===
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
#                     "fillOpacity": 0.9
#                 }

#             m.add_geojson(
#                 stops,
#                 layer_name="MBTA Stations",
#                 style_callback=station_style,
#                 info_mode="on_click",
#                 fields=["name", "lines"],
#                 aliases=["Station", "Lines"]
#             )
#         except Exception as e:
#             st.warning(f"MBTA stations failed: {e}")

#     # Add Highways view
#     elif highway_mode:
#         try:
#             url = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-highways.json"
#             r = requests.get(url)
#             r.raise_for_status()
#             highways = r.json()

#             def highway_style(feature):
#                 name = feature["properties"].get("NAME", "")
#                 if "I-" in name:
#                     color = "#0047AB"
#                 elif "US-" in name:
#                     color = "#FF8C00"
#                 else:
#                     color = "#666666"
#                 return {"color": color, "weight": 3, "opacity": 0.8}

#             m.add_geojson(
#                 highways,
#                 layer_name="Major Highways",
#                 style_function=highway_style,
#                 info_mode="on_hover",
#                 fields=["NAME"],
#                 aliases=["Highway"]
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
#     m.to_streamlit(width=1500, height=800)

#version 3

# # app.py
# import streamlit as st
# import pandas as pd
# import requests
# import leafmap.foliumap as leafmap
# import branca.colormap as cm
# import json
# import geopandas as gpd

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
# st.markdown(f"**View:** *{view_mode}* | **Data:** *{title_suffix}*  \nHover over ZIPs. Click stations/highways for details.")

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

#     # Set view for Greater Boston vs State-wide
#     if highway_mode or mbta_mode:
#         m = leafmap.Map(center=[42.30, -71.05], zoom=9, locate_control=False, draw_control=False, measure_control=False)
#     else:
#         m = leafmap.Map(center=[42.3601, -71.0589], zoom=8, locate_control=False, draw_control=False, measure_control=False)

#     # Color scale
#     min_val = agg_df["count"].min()
#     max_val = agg_df["count"].max()
#     if max_val == min_val:
#         max_val = min_val + 1
#     colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
#     colormap.caption = "Number of Examinees"
#     colormap.add_to(m)

#     value_dict = agg_df.set_index("zip").to_dict(orient="index")

#     def style_function(feature):
#         zip_code = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
#         if (mbta_mode or highway_mode) and zip_code not in MBTA_ZIPS:
#             return {"fillColor": "transparent", "color": "transparent", "weight": 0}
#         val = value_dict.get(zip_code, {}).get("count", 0)
#         return {
#             "fillColor": colormap(val) if val > 0 else "#d9d9d9",
#             "color": "black",
#             "weight": 0.3,
#             "fillOpacity": 0.7,
#         }

#     # Add ZIP polygons
#     for feature in geojson["features"]:
#         z = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
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

#     m.add_geojson(
#         geojson,
#         style_function=style_function,
#         info_mode="on_hover",
#         fields=["ZIP Code", "Area", "Sub_Area", "Examinees"],
#         aliases=["ZIP Code", "Area", "Sub-area", "Examinees"],
#     )

#     # ------------------------
#     # Add MBTA lines & stations
#     # ------------------------
#     if mbta_mode:
#         line_colors = {
#             "blue": "#003DA5", "orange": "#ED8B00", "red": "#DA291C", "green": "#00843D",
#             "green-b": "#00843D", "green-c": "#00843D", "green-d": "#00843D", "green-e": "#00843D",
#             "silver": "#8D8D8D", "sl1": "#8D8D8D", "sl2": "#8D8D8D", "sl4": "#8D8D8D", "sl5": "#8D8D8D",
#             "mattapan": "#DA291C",
#         }

#         # LINES
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

#         # STATIONS
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
#     # Add Highway Layer
#     # ------------------------
#     elif highway_mode:
#         try:
#             import geopandas as gpd
#             gdf = gpd.read_file("ma_major_roads.geojson")
    
#             # Reproject to EPSG:4326 (lat/lon)
#             if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
#                 gdf = gdf.to_crs(epsg=4326)
    
#             # Keep only primary + secondary roads for clarity
#             gdf = gdf[gdf["FEATURE_TY"].isin(["Primary Road", "Secondary Road"])]
    
#             # Convert to GeoJSON for Leafmap
#             highways = json.loads(gdf.to_json())
    
#             def highway_style(feature):
#                 ftype = feature["properties"].get("FEATURE_TY", "")
#                 color = "#0047AB" if ftype == "Primary Road" else "#FF8C00"
#                 return {"color": color, "weight": 3, "opacity": 0.9}
    
#             m.add_geojson(
#                 highways,
#                 layer_name="Major Roads",
#                 style_function=highway_style,
#                 info_mode="on_hover",
#                 fields=["FULLNAME", "FEATURE_TY"],
#                 aliases=["Road Name", "Type"],
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
#     m.to_streamlit(width=1500, height=800)


#version 4

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

#version 5

# app.py
import streamlit as st
import pandas as pd
import requests
import leafmap.foliumap as leafmap
import branca.colormap as cm
import json
import geopandas as gpd
from shapely.geometry import shape, LineString
import re
import folium
import base64

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
# Route Shield SVG (Base64)
# ---------------------------------------------------------
def get_shield_svg(route_type: str, number: str):
    number = str(number).strip()
    if route_type == "I":
        svg = f'''
        <svg width="36" height="36" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg">
          <path d="M18 2 L2 18 L18 34 L34 18 Z" fill="#C41E3A"/>
          <path d="M18 2 L2 18 L18 34" fill="#0033A0" stroke="white" stroke-width="2"/>
          <text x="18" y="22" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="white" text-anchor="middle">{number}</text>
        </svg>
        '''
    elif route_type == "US":
        svg = f'''
        <svg width="36" height="36" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg">
          <rect x="4" y="4" width="28" height="28" rx="4" fill="white" stroke="black" stroke-width="2"/>
          <text x="18" y="22" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="black" text-anchor="middle">{number}</text>
        </svg>
        '''
    else:  # MA
        svg = f'''
        <svg width="36" height="36" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg">
          <rect x="4" y="4" width="28" height="28" rx="4" fill="#FFD700" stroke="black" stroke-width="2"/>
          <text x="18" y="22" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="black" text-anchor="middle">{number}</text>
        </svg>
        '''
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f'data:image/svg+xml;base64,{b64}'

# ---------------------------------------------------------
# Build Map
# ---------------------------------------------------------
def build_map(agg_df: pd.DataFrame, geojson: dict, mbta_mode: bool = False, highway_mode: bool = False) -> leafmap.Map:
    m = leafmap.Map(
        center=[42.3601, -71.0589],
        zoom=8,
        locate_control=False,
        draw_control=False,
        measure_control=False,
        scroll_wheel_zoom=True
    )

    # Color scale
    min_val = agg_df["count"].min()
    max_val = agg_df["count"].max()
    if max_val == min_val:
        max_val = min_val + 1
    colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
    colormap.caption = "Number of Examinees"
    colormap.add_to(m)

    value_dict = agg_df.set_index("zip").to_dict(orient="index")

    # === Filter ZIPs and compute bounds ===
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

        visible_features.append(feature)
        geom = shape(feature["geometry"])
        if geom.is_valid and not geom.is_empty:
            minx, miny, maxx, maxy = geom.bounds
            if bounds is None:
                bounds = [minx, miny, maxx, maxy]
            else:
                bounds = [min(bounds[0], minx), min(bounds[1], miny), max(bounds[2], maxx), max(bounds[3], maxy)]

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
        padding = 0.02
        padded_bounds = [
            [bounds[1] - padding, bounds[0] - padding],
            [bounds[3] + padding, bounds[2] + padding]
        ]
        m.fit_bounds(padded_bounds)

    # ------------------------
    # MBTA (unchanged)
    # ------------------------
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

    # ------------------------
    # HIGHWAYS + ROUTE SHIELDS (FIXED FOR YOUR DATA)
    # ------------------------
    elif highway_mode:
        try:
            gdf = gpd.read_file("ma_major_roads.geojson")
            if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)

            gdf = gdf[gdf["FEATURE_TY"].isin(["Primary Road", "Secondary Road"])].copy()

            # === Extract route from FULLNAME (your data format) ===
            def extract_route(fullname):
                if pd.isna(fullname):
                    return None, None
                text = str(fullname).upper()
                # Match: "I- 95", "I- 190", "I 95"
                i_match = re.search(r'\bI[-\s]+(\d+[A-Z]?)\b', text)
                if i_match:
                    return "I", i_match.group(1)
                # Match: "ROUTE 202", "RT 9", "MA 3"
                ma_match = re.search(r'\b(ROUTE|RT|MA)[-\s]+(\d+[A-Z]?)\b', text)
                if ma_match:
                    return "MA", ma_match.group(2)
                return None, None

            gdf[["ROUTE_TYPE", "ROUTE_NUM"]] = gdf["FULLNAME"].apply(
                lambda x: pd.Series(extract_route(x))
            )

            # Clean display name
            gdf["ROAD_NAME"] = gdf["FULLNAME"].fillna("Unnamed Road").str.strip()

            # Friendly type
            type_map = {
                "Primary Road": "Interstate / Major Highway",
                "Secondary Road": "State Route / Arterial"
            }
            gdf["ROAD_TYPE"] = gdf["FEATURE_TY"].map(type_map)

            highways_geojson = json.loads(gdf.to_json())

            # Add highway lines
            def highway_style(feature):
                ftype = feature["properties"].get("FEATURE_TY", "")
                color = "#0047AB" if ftype == "Primary Road" else "#00843D"
                return {"color": color, "weight": 4, "opacity": 0.9}

            m.add_geojson(
                highways_geojson,
                layer_name="Major Highways",
                style_function=highway_style,
                info_mode="on_hover",
                fields=["ROAD_NAME", "ROAD_TYPE", "ROUTE_TYPE", "ROUTE_NUM"],
                aliases=["Highway", "Type", "Route", "Number"],
            )

            # === ADD ROUTE SHIELDS ===
            shield_group = folium.FeatureGroup(name="Route Shields", show=True)
            placed_points = set()

            matched = []

            for _, row in gdf.iterrows():
                rtype = row.get("ROUTE_TYPE")
                rnum = row.get("ROUTE_NUM")
                if pd.isna(rnum) or str(rnum).strip() in ["", "nan", "0"]:
                    continue

                route_key = f"{rtype}-{rnum}"
                matched.append(f"{route_key}: {row['ROAD_NAME'][:50]}...")

                line = row.geometry
                if not isinstance(line, LineString) or line.is_empty:
                    continue

                length = line.length
                step = max(4000, length / 8)  # ~4km or 8 points
                for dist in [step * i for i in range(int(length / step) + 1)]:
                    point = line.interpolate(dist)
                    lat, lon = round(point.y, 5), round(point.x, 5)
                    key = (lat, lon, route_key)

                    if key in placed_points:
                        continue
                    placed_points.add(key)

                    icon_url = get_shield_svg(rtype, rnum)
                    icon = folium.CustomIcon(icon_url, icon_size=(36, 36), icon_anchor=(18, 18))

                    folium.Marker(
                        [lat, lon],
                        icon=icon,
                        tooltip=f"{rtype} {rnum}",
                        popup=folium.Popup(f"<b>{rtype} {rnum}</b><br>{row['ROAD_NAME']}", max_width=300)
                    ).add_to(shield_group)

            shield_group.add_to(m.get_root())

            # Debug
            with st.expander("Debug: Route Shields (Highways mode)"):
                st.success("**Using FULLNAME extraction** (e.g., 'I- 95')")
                st.write("**Sample matched routes:**")
                for line in matched[:20]:
                    st.write(line)
                if not matched:
                    st.warning("No routes found in FULLNAME. Check for 'I- 95' or 'ROUTE 9'.")

        except Exception as e:
            st.error(f"Highway layer error: {e}")

    m.add_layer_control()
    return m

# ---------------------------------------------------------
# Render
# ---------------------------------------------------------
mbta_mode = (view_mode == "Greater Boston (MBTA subway)")
highway_mode = (view_mode == "Greater Boston (Highways)")

with st.spinner(f"Loading {selected_layer} – {view_mode.lower()} map…"):
    m = build_map(agg, geojson_data, mbta_mode=mbta_mode, highway_mode=highway_mode)
    m.to_streamlit(width=1500, height=700)
