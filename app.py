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

import streamlit as st
import leafmap.foliumap as leafmap
import geopandas as gpd
import json
from streamlit.components.v1 import html

st.set_page_config(page_title="Massachusetts Bar Examinee Distribution Map", layout="wide")

st.title("Massachusetts Bar Examinee Distribution Map – All years")

# Sidebar for map view options
view = st.sidebar.radio(
    "Select Map View:",
    ["Statewide", "Greater Boston (MBTA)", "Greater Boston (Highways)"]
)
data_choice = st.sidebar.selectbox("Select Dataset:", ["All years", "2023", "2022", "2021"])

st.info(f"View: {view} | Data: {data_choice} Hover over ZIPs. Click stations/highways for details.")

# ---------------------------------------------------
# Initialize map based on view
# ---------------------------------------------------
if view == "Statewide":
    m = leafmap.Map(center=[42.3, -71.8], zoom=7)
elif view == "Greater Boston (MBTA)":
    m = leafmap.Map(center=[42.36, -71.05], zoom=10)
elif view == "Greater Boston (Highways)":
    m = leafmap.Map(center=[42.36, -71.05], zoom=10)
else:
    m = leafmap.Map(center=[42.3, -71.8], zoom=7)

# ---------------------------------------------------
# Highway Layer
# ---------------------------------------------------
if view == "Greater Boston (Highways)":
    try:
        # ✅ Load directly from GitHub raw URL (replace with your repo if different)
        url = "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/us-states.json"
        gdf = gpd.read_file("https://raw.githubusercontent.com/ArthaPillai/ma-bar-exam-map/main/data/ma_major_roads.geojson")

        # Fix CRS
        if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)

        # Filter only main/primary roads
        gdf = gdf[gdf["FEATURE_TY"].isin(["Primary Road", "Secondary Road"])]

        # Rename road types for clarity
        gdf["ROAD_TYPE"] = gdf["FEATURE_TY"].replace({
            "Primary Road": "Highway",
            "Secondary Road": "Main Road"
        })

        # Convert GeoDataFrame to GeoJSON dict (not string!)
        highways = json.loads(gdf.to_json())

        # Style for each feature
        def style_function(feature):
            ftype = feature["properties"].get("FEATURE_TY", "")
            return {
                "color": "#0047AB" if ftype == "Primary Road" else "#008000",
                "weight": 3,
                "opacity": 0.9
            }

        # ✅ Add highway layer
        m.add_geojson(
            highways,
            layer_name="Major Roads",
            style_function=style_function,
            info_mode="on_hover",
            fields=["FULLNAME", "ROAD_TYPE"],
            aliases=["Road Name", "Road Type"]
        )

        # ✅ Add distinct route shield markers (for visual clarity)
        for _, row in gdf.iterrows():
            road_name = row.get("FULLNAME", "")
            if any(keyword in road_name for keyword in ["I-", "Route", "US"]):
                centroid = row.geometry.representative_point()
                m.add_marker(
                    location=[centroid.y, centroid.x],
                    popup=f"<b>{road_name}</b><br>{row['ROAD_TYPE']}",
                    icon="🚗",
                )

        m.zoom_to_bounds(gdf.total_bounds)

    except Exception as e:
        st.warning(f"Highway layer failed: {e}")

# ---------------------------------------------------
# MBTA Map Example (for reference)
# ---------------------------------------------------
elif view == "Greater Boston (MBTA)":
    try:
        mbta_gdf = gpd.read_file("https://raw.githubusercontent.com/ArthaPillai/ma-bar-exam-map/main/data/MBTA_Lines.geojson")
        if mbta_gdf.crs and mbta_gdf.crs.to_string() != "EPSG:4326":
            mbta_gdf = mbta_gdf.to_crs(epsg=4326)
        mbta = json.loads(mbta_gdf.to_json())

        def mbta_style(feature):
            return {"color": "#B03060", "weight": 2.5, "opacity": 0.9}

        m.add_geojson(
            mbta,
            layer_name="MBTA Lines",
            style_function=mbta_style,
            info_mode="on_hover",
            fields=["LINE", "BRANCH"],
            aliases=["Line", "Branch"]
        )
        m.zoom_to_bounds(mbta_gdf.total_bounds)
    except Exception as e:
        st.warning(f"MBTA layer failed: {e}")

# ---------------------------------------------------
# Display map
# ---------------------------------------------------
m.to_streamlit(height=700)


