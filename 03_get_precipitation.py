# 03_get_precipitation.py

import os
import requests
import pandas as pd
from config import PLACE_NAME

# Koordinaten Denkendorf (fix für dieses Projekt)
lat = 48.7039
lon = 9.3190

# Sicherstellen, dass Ordner existiert
os.makedirs("data/interim", exist_ok=True)

# Open-Meteo API URL
url = (
    "https://archive-api.open-meteo.com/v1/archive"
    f"?latitude={lat}&longitude={lon}"
    "&start_date=2023-01-01"
    "&end_date=2023-12-31"
    "&daily=precipitation_sum"
    "&timezone=Europe%2FBerlin"
)

# Anfrage senden
response = requests.get(url)
data = response.json()

# In DataFrame umwandeln
df = pd.DataFrame(data["daily"])
df["precipitation_sum"] = df["precipitation_sum"].astype(float)

# Gesamtjahresniederschlag in mm
total_precip_mm = df["precipitation_sum"].sum()

# Niederschlag speichern
with open("data/interim/precip_mm_2023.txt", "w") as f:
    f.write(str(round(total_precip_mm, 1)))

print(f"Jahresniederschlag 2023 gespeichert: {total_precip_mm:.1f} mm")

