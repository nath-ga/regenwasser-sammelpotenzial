# 02_calc_rooftop_area.py 

import geopandas as gpd
from config import NAME_SHORT, RAINFALL_MM_PER_YEAR

# Gebäudedaten laden
gdf = gpd.read_file(f"data/interim/{NAME_SHORT}_buildings.geojson")

# Berechnung: Liter pro Jahr
gdf["rain_liter_per_year"] = gdf["area_m2"] * RAINFALL_MM_PER_YEAR

# Speichern
gdf.to_file(f"data/interim/{NAME_SHORT}_buildings.geojson", driver="GeoJSON")

# Ausgabe
total_liters = gdf["rain_liter_per_year"].sum()
print(f"Gesamte Regenwassermenge für alle Dächer: {total_liters:,.0f} Liter pro Jahr")
print(gdf[["area_m2", "rain_liter_per_year"]].describe())
