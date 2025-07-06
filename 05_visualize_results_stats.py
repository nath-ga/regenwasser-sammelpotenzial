# 05_visualize_results_stats.py
import pandas as pd
import geopandas as gpd
import folium
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from config import NAME_SHORT, RAINFALL_MM_PER_YEAR

# Eingabedatei
gdf = gpd.read_file(f"data/interim/{NAME_SHORT}_buildings.geojson")

# Nicht-serialisierbare Spalten entfernen
for col in gdf.columns:
    if pd.api.types.is_datetime64_any_dtype(gdf[col]):
        print(f"Entferne Spalte '{col}' (nicht JSON-kompatibel)")
        gdf = gdf.drop(columns=[col])

print(f"Analysiere {len(gdf)} Gebäude...")

# =============================================================================
# STATISTIKEN BERECHNEN
# =============================================================================

# Grundstatistiken
total_area = gdf['area_m2'].sum()
total_rainwater = gdf['rain_liter_per_year'].sum()
avg_area = gdf['area_m2'].mean()
avg_rainwater = gdf['rain_liter_per_year'].mean()

# Kategorien für Dächer basierend auf Quartilen (bessere Verteilung)
quartiles = gdf['rain_liter_per_year'].quantile([0.25, 0.5, 0.75]).values
print(f"Quartile: 25%={quartiles[0]:.0f}L, 50%={quartiles[1]:.0f}L, 75%={quartiles[2]:.0f}L")

gdf['potenzial_kategorie'] = pd.cut(
    gdf['rain_liter_per_year'], 
    bins=[0, quartiles[0], quartiles[1], quartiles[2], float('inf')], 
    labels=[f'Niedrig (<{quartiles[0]:.0f}L)', 
            f'Mittel ({quartiles[0]:.0f}-{quartiles[1]:.0f}L)', 
            f'Hoch ({quartiles[1]:.0f}-{quartiles[2]:.0f}L)', 
            f'Sehr hoch (>{quartiles[2]:.0f}L)']
)

# Farbkodierung für bessere Unterscheidung
def get_color(potenzial):
    if potenzial < quartiles[0]:
        return '#ffffcc'  # Helles Gelb
    elif potenzial < quartiles[1]:
        return '#a1dab4'  # Helles Grün
    elif potenzial < quartiles[2]:
        return '#41b6c4'  # Mittelblau
    else:
        return '#253494'  # Dunkles Blau

# Statistiken ausgeben
print("\n" + "="*50)
print("REGENWASSER-POTENZIAL STATISTIKEN")
print("="*50)
print(f"Gesamtanzahl Gebäude: {len(gdf):,}")
print(f"Gesamte Dachfläche: {total_area:,.0f} m²")
print(f"Gesamtes Regenwasser-Potenzial: {total_rainwater:,.0f} L/Jahr")
print(f"Das entspricht: {total_rainwater/1000:,.0f} m³/Jahr")
print(f"Durchschnittliche Dachfläche: {avg_area:.1f} m²")
print(f"Durchschnittliches Potenzial: {avg_rainwater:.0f} L/Jahr")

print(f"\nVerteilung nach Potenzial-Kategorien:")
kategorie_stats = gdf.groupby('potenzial_kategorie').agg({
    'rain_liter_per_year': ['count', 'sum'],
    'area_m2': 'sum'
}).round(0)

for kategorie in gdf['potenzial_kategorie'].cat.categories:
    count = kategorie_stats.loc[kategorie, ('rain_liter_per_year', 'count')]
    total = kategorie_stats.loc[kategorie, ('rain_liter_per_year', 'sum')]
    prozent = (count / len(gdf)) * 100
    print(f"  {kategorie}: {count:,.0f} Gebäude ({prozent:.1f}%) - {total:,.0f} L/Jahr")

# Top 10 Gebäude
print(f"\nTop 10 Gebäude mit höchstem Potenzial:")
top_10 = gdf.nlargest(10, 'rain_liter_per_year')[['area_m2', 'rain_liter_per_year', 'building', 'name']]
for i, (_, row) in enumerate(top_10.iterrows(), 1):
    name = row['name'] if pd.notna(row['name']) else f"{row['building']} Gebäude"
    print(f"  {i:2d}. {name[:30]:<30} {row['area_m2']:>6.0f} m² → {row['rain_liter_per_year']:>8.0f} L/Jahr")

# Umwelt-Impact berechnen
print(f"\n" + "="*50)
print("UMWELT-IMPACT")
print("="*50)
# Annahmen für Berechnungen
liter_per_person_per_day = 120  # Durchschnittlicher Wasserverbrauch
co2_kg_per_m3_water = 0.7  # CO2-Äquivalent für Wasseraufbereitung

personen_versorgt = total_rainwater / (liter_per_person_per_day * 365)
co2_einsparung = (total_rainwater / 1000) * co2_kg_per_m3_water

print(f"Könnte {personen_versorgt:.0f} Personen ein Jahr lang mit Wasser versorgen")
print(f"CO2-Einsparung: {co2_einsparung:.0f} kg/Jahr")
print(f"Äquivalent zu: {co2_einsparung/2300:.1f} weniger Autofahrten (je 10.000 km)")

# =============================================================================
# INTERAKTIVE KARTE ERSTELLEN
# =============================================================================

# Karte zentrieren
map_center = gdf.geometry.union_all().centroid.coords[0][::-1]
karte = folium.Map(location=map_center, zoom_start=15, tiles="cartodbpositron")

# Gebäude einzeln hinzufügen mit individuellen Farben
for _, building in gdf.iterrows():
    color = get_color(building['rain_liter_per_year'])
    
    # Popup-Text erstellen
    popup_text = f"""
    <b>Gebäude-Info:</b><br>
    Typ: {building.get('building', 'Unbekannt')}<br>
    Dachfläche: {building['area_m2']:.0f} m²<br>
    Regenwasser-Potenzial: {building['rain_liter_per_year']:.0f} L/Jahr<br>
    Kategorie: {building['potenzial_kategorie']}<br>
    """
    
    folium.GeoJson(
        building['geometry'],
        style_function=lambda x, color=color: {
            'fillColor': color,
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.7
        },
        popup=folium.Popup(popup_text, max_width=300),
        tooltip=f"{building['rain_liter_per_year']:.0f} L/Jahr"
    ).add_to(karte)

# Legende mit dynamischen Werten hinzufügen
legend_html = f'''
<div style="position: fixed; 
     bottom: 50px; left: 50px; width: 220px; height: 140px; 
     background-color: white; border:2px solid grey; z-index:9999; 
     font-size:12px; padding: 10px">
<p><b>Regenwasser-Potenzial</b></p>
<p><i class="fa fa-square" style="color:#ffffcc"></i> Niedrig (&lt;{quartiles[0]:.0f}L)</p>
<p><i class="fa fa-square" style="color:#a1dab4"></i> Mittel ({quartiles[0]:.0f}-{quartiles[1]:.0f}L)</p>
<p><i class="fa fa-square" style="color:#41b6c4"></i> Hoch ({quartiles[1]:.0f}-{quartiles[2]:.0f}L)</p>
<p><i class="fa fa-square" style="color:#253494"></i> Sehr hoch (&gt;{quartiles[2]:.0f}L)</p>
</div>
'''
karte.get_root().html.add_child(folium.Element(legend_html))

# Ausgabe
os.makedirs("outputs/figures", exist_ok=True)
karte.save("outputs/figures/regenkarte_enhanced.html")
print(f"\nVerbesserte Karte gespeichert unter outputs/figures/regenkarte_enhanced.html")

# =============================================================================
# ZUSÄTZLICHE DIAGRAMME ERSTELLEN
# =============================================================================

# Matplotlib für Diagramme
plt.style.use('seaborn-v0_8')
fig, axes = plt.subplots(2, 2, figsize=(15, 12))
fig.suptitle(f'Regenwasser-Potenzial Analyse - {NAME_SHORT}', fontsize=16, fontweight='bold')

# 1. Histogramm der Potenziale
axes[0,0].hist(gdf['rain_liter_per_year'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
axes[0,0].set_title('Verteilung des Regenwasser-Potenzials')
axes[0,0].set_xlabel('Liter pro Jahr')
axes[0,0].set_ylabel('Anzahl Gebäude')
axes[0,0].axvline(avg_rainwater, color='red', linestyle='--', label=f'Durchschnitt: {avg_rainwater:.0f}L')
axes[0,0].legend()

# 2. Scatter Plot: Fläche vs Potenzial
axes[0,1].scatter(gdf['area_m2'], gdf['rain_liter_per_year'], alpha=0.6, s=30)
axes[0,1].set_title('Dachfläche vs. Regenwasser-Potenzial')
axes[0,1].set_xlabel('Dachfläche (m²)')
axes[0,1].set_ylabel('Regenwasser-Potenzial (L/Jahr)')

# 3. Balkendiagramm Kategorien
kategorie_counts = gdf['potenzial_kategorie'].value_counts()
axes[1,0].bar(range(len(kategorie_counts)), kategorie_counts.values, 
              color=['#ffffcc', '#a1dab4', '#41b6c4', '#2c7fb8'])
axes[1,0].set_title('Gebäude nach Potenzial-Kategorien')
axes[1,0].set_xlabel('Kategorie')
axes[1,0].set_ylabel('Anzahl Gebäude')
axes[1,0].set_xticks(range(len(kategorie_counts)))
axes[1,0].set_xticklabels(kategorie_counts.index, rotation=45)

# 4. Kumulative Verteilung
sorted_potenzial = np.sort(gdf['rain_liter_per_year'])
cumulative = np.cumsum(sorted_potenzial)
axes[1,1].plot(range(len(cumulative)), cumulative/1000, linewidth=2)
axes[1,1].set_title('Kumulatives Regenwasser-Potenzial')
axes[1,1].set_xlabel('Gebäude (sortiert)')
axes[1,1].set_ylabel('Kumulatives Potenzial (m³/Jahr)')

plt.tight_layout()
plt.savefig('outputs/figures/regenwasser_statistiken.png', dpi=300, bbox_inches='tight')
print("Statistik-Diagramme gespeichert unter outputs/figures/regenwasser_statistiken.png")

print("\n Analyse abgeschlossen! Öffne die HTML-Datei für die interaktive Karte.")