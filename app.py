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

# app.py
import streamlit as st
import pandas as pd
import requests
import leafmap.foliumap as leafmap
import branca.colormap as cm
import json
import geopandas as gpd

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
st.markdown(f"**View:** *{view_mode}* | **Data:** *{title_suffix}*  \nHover over ZIPs. Click stations/highways for details.")

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
# Build Map
# ---------------------------------------------------------
def build_map(agg_df: pd.DataFrame, geojson: dict, mbta_mode: bool = False, highway_mode: bool = False) -> leafmap.Map:

    # Set view for Greater Boston vs State-wide
    if highway_mode or mbta_mode:
        m = leafmap.Map(center=[42.30, -71.05], zoom=9, locate_control=False, draw_control=False, measure_control=False)
    else:
        m = leafmap.Map(center=[42.3601, -71.0589], zoom=8, locate_control=False, draw_control=False, measure_control=False)

    # Color scale
    min_val = agg_df["count"].min()
    max_val = agg_df["count"].max()
    if max_val == min_val:
        max_val = min_val + 1
    colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
    colormap.caption = "Number of Examinees"
    colormap.add_to(m)

    value_dict = agg_df.set_index("zip").to_dict(orient="index")

    def style_function(feature):
        zip_code = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
        if (mbta_mode or highway_mode) and zip_code not in MBTA_ZIPS:
            return {"fillColor": "transparent", "color": "transparent", "weight": 0}
        val = value_dict.get(zip_code, {}).get("count", 0)
        return {
            "fillColor": colormap(val) if val > 0 else "#d9d9d9",
            "color": "black",
            "weight": 0.3,
            "fillOpacity": 0.7,
        }

    # Add ZIP polygons
    for feature in geojson["features"]:
        z = str(feature["properties"].get("ZCTA5CE10", "")).zfill(5)
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

    m.add_geojson(
        geojson,
        style_function=style_function,
        info_mode="on_hover",
        fields=["ZIP Code", "Area", "Sub_Area", "Examinees"],
        aliases=["ZIP Code", "Area", "Sub-area", "Examinees"],
    )

    # ------------------------
    # Add MBTA lines & stations
    # ------------------------
    if mbta_mode:
        line_colors = {
            "blue": "#003DA5", "orange": "#ED8B00", "red": "#DA291C", "green": "#00843D",
            "green-b": "#00843D", "green-c": "#00843D", "green-d": "#00843D", "green-e": "#00843D",
            "silver": "#8D8D8D", "sl1": "#8D8D8D", "sl2": "#8D8D8D", "sl4": "#8D8D8D", "sl5": "#8D8D8D",
            "mattapan": "#DA291C",
        }

        # LINES
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

        # STATIONS
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
    # Add Highway Layer – highlighted lines + ONE shield per route
    # ------------------------
    elif highway_mode:
        try:
            import geopandas as gpd, shapely.geometry as sg, re, json
    
            # --------------------------------------------------------------
            # 1. Load & reproject roads
            # --------------------------------------------------------------
            gdf = gpd.read_file("ma_major_roads.geojson")
            if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)
    
            gdf = gdf[gdf["FEATURE_TY"].isin(["Primary Road", "Secondary Road"])]
    
            # --------------------------------------------------------------
            # 2. Extract route label (I-90, US-1, MA-2, Route 9 …)
            # --------------------------------------------------------------
            route_rx = re.compile(r"\b(I-|US-|MA-|Route\s?)(\d+[A-Z]?)\b", re.I)
    
            def extract_route(txt):
                if not txt: return None
                m = route_rx.search(txt)
                return m.group(0).upper() if m else None
    
            gdf["route_label"] = gdf["FULLNAME"].apply(extract_route)
    
            # --------------------------------------------------------------
            # 3. Colour palette (line + shield)
            # --------------------------------------------------------------
            line_colors = {
                "I-":   "#FFD700",   # gold
                "US-":  "#FF8C00",   # orange
                "MA-":  "#32CD32",   # lime green
                "ROUTE": "#32CD32",
            }
    
            # --------------------------------------------------------------
            # 4. ROAD LINES (highlighted)
            # --------------------------------------------------------------
            highways_geojson = json.loads(gdf.to_json())
    
            def line_style(feature):
                route = feature["properties"].get("route_label")
                if route and any(route.startswith(p) for p in line_colors):
                    col = line_colors[next(p for p in line_colors if route.startswith(p))]
                    return {"color": col, "weight": 5, "opacity": 1.0}
                col = "#0047AB" if feature["properties"]["FEATURE_TY"] == "Primary Road" else "#666666"
                return {"color": col, "weight": 3, "opacity": 0.9}
    
            m.add_geojson(
                highways_geojson,
                layer_name="Major Roads",
                style_function=line_style,
                info_mode="on_hover",
                fields=["FULLNAME", "FEATURE_TY", "route_label"],
                aliases=["Road Name", "Type", "Route"],
            )
    
            # --------------------------------------------------------------
            # 5. ONE SHIELD PER ROUTE – placed on the *longest* segment
            # --------------------------------------------------------------
            # Keep only rows that have a route label
            routes_gdf = gdf.dropna(subset=["route_label"]).copy()
    
            # Compute length of each segment (in degrees – fine for placement)
            routes_gdf["seg_len"] = routes_gdf.geometry.length
    
            # For each route keep the **longest** segment
            longest_gdf = (
                routes_gdf.loc[routes_gdf.groupby("route_label")["seg_len"].idxmax()]
                .reset_index(drop=True)
            )
    
            shield_features = []
            for _, row in longest_gdf.iterrows():
                route = row["route_label"]
                line  = row["geometry"]
    
                # ---- midpoint of the chosen (longest) segment ----------------
                if isinstance(line, sg.LineString):
                    coords = line.coords
                elif isinstance(line, sg.MultiLineString):
                    longest_sub = max(line.geoms, key=lambda l: l.length)
                    coords = longest_sub.coords
                else:
                    continue
    
                mid_idx = len(coords) // 2
                lon, lat = coords[mid_idx]
    
                # ---- colour -------------------------------------------------
                bg = next((c for p, c in line_colors.items() if route.startswith(p)), "#666666")
    
                # ---- HTML shield --------------------------------------------
                html = f"""
                <div style="
                    background:{bg};
                    color:white;
                    font-weight:bold;
                    font-family:Arial,Helvetica,sans-serif;
                    font-size:11px;
                    padding:2px 5px;
                    border-radius:4px;
                    border:1px solid #333;
                    white-space:nowrap;
                    box-shadow:0 1px 3px rgba(0,0,0,0.4);
                ">{route}</div>
                """
    
                shield_features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {"icon_html": html, "route": route}
                })
    
            if shield_features:
                shields_geojson = {"type": "FeatureCollection", "features": shield_features}
    
                m.add_geojson(
                    shields_geojson,
                    layer_name="Route Shields",
                    marker_type="divicon",
                    icon_html="icon_html",
                    # optional: click popup
                    info_mode="on_click",
                    fields=["route"],
                    aliases=["Route"]
                )
    
        except Exception as e:
            st.warning(f"Highway layer failed: {e}")
   
        
    m.add_layer_control()
    return m

# ---------------------------------------------------------
# Render
# ---------------------------------------------------------
mbta_mode = (view_mode == "Greater Boston (MBTA subway)")
highway_mode = (view_mode == "Greater Boston (Highways)")

with st.spinner(f"Loading {selected_layer} – {view_mode.lower()} map…"):
    m = build_map(agg, geojson_data, mbta_mode=mbta_mode, highway_mode=highway_mode)
    m.to_streamlit(width=1500, height=800)
