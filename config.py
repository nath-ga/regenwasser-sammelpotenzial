# config.py

PLACE_NAME = "Denkendorf, Baden-Württemberg, Deutschland"
NAME_SHORT = "denkendorf"

# Jahresniederschlag automatisch laden
try:
    with open("data/interim/precip_mm_2023.txt") as f:
        RAINFALL_MM_PER_YEAR = float(f.read().strip())
except FileNotFoundError:
    RAINFALL_MM_PER_YEAR = 900.0  # Fallback-Wert in mm
