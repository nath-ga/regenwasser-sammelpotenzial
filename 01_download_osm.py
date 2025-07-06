# 01_download_osm.py
# Häuserdaten aus OSM extrahieren mit Overpass API / osmnx Version 1.3.0 (!)


import osmnx as ox
import geopandas as gpd
import os
from config import PLACE_NAME, NAME_SHORT

# Gebäudedaten laden
gdf_buildings = ox.geometries_from_place(PLACE_NAME, tags={"building": True})

# Nur Polygone behalten
gdf_buildings = gdf_buildings[gdf_buildings.geometry.type.isin(["Polygon", "MultiPolygon"])]

# Fläche berechnen (m², EPSG:32632 für BW)
gdf_buildings["area_m2"] = gdf_buildings.geometry.to_crs(epsg=32632).area

# Sicherstellen, dass Ordner existiert
os.makedirs("data/interim", exist_ok=True)

# Speichern
gdf_buildings.to_file(f"data/interim/{NAME_SHORT}_buildings.geojson", driver="GeoJSON")
