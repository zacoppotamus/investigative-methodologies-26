#!/usr/bin/env python3
"""
Module 002 - Script 05: Visualization
======================================

Create publication-quality static maps and interactive web maps.

Key concepts:
- Matplotlib choropleth maps with custom styling
- Adding labels, legends, and north arrows
- Folium interactive maps with multiple layers
- Combining static and interactive approaches

Data: Barcelona neighborhoods + computed attributes.
"""

# --- Google Colab Setup ---
# If running in Google Colab, uncomment and run these lines first:
# !pip install geopandas folium mapclassify
# !git clone https://github.com/zacharias1219/IAAC.git
# %cd IAAC/002
# ---

from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import folium

try:
    BASE_DIR = Path(__file__).parent
except NameError:
    BASE_DIR = Path.cwd()  # Colab: use current working directory
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Load data
barris = gpd.read_file(DATA_DIR / "barris.geojson")
districts = gpd.read_file(DATA_DIR / "districtes.geojson")

# Compute area in metric CRS for choropleth data
barris_utm = barris[["NOM", "DISTRICTE", "geometry"]].to_crs(epsg=25831)
barris_utm["area_km2"] = barris_utm.geometry.area / 1_000_000
barris_utm["perimeter_km"] = barris_utm.geometry.length / 1000
barris_utm["compactness"] = (4 * np.pi * barris_utm.geometry.area) / (barris_utm.geometry.length ** 2)

# Keep WGS84 version for Folium (needs lat/lon)
barris_wgs = barris[["NOM", "DISTRICTE", "geometry"]].copy()
barris_wgs["area_km2"] = barris_utm["area_km2"].values
barris_wgs["compactness"] = barris_utm["compactness"].values


# --- Section 1: Basic Choropleth Map ---

print("=" * 60)
print("SECTION 1: Basic Choropleth Map")
print("=" * 60)

fig, ax = plt.subplots(figsize=(12, 10))

barris_utm.plot(
    ax=ax,
    column="area_km2",
    cmap="YlOrRd",
    edgecolor="white",
    linewidth=0.5,
    legend=True,
    legend_kwds={
        "label": "Area (km²)",
        "shrink": 0.5,
        "orientation": "horizontal",
        "pad": 0.05,
    },
)
ax.set_title("Barcelona Neighborhoods by Area", fontsize=16, fontweight="bold")
ax.set_axis_off()

output_path = OUTPUT_DIR / "05_basic_choropleth.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"Plot saved to: {output_path}")
plt.close()


# --- Section 2: Styled Choropleth with Labels ---

print("\n" + "=" * 60)
print("SECTION 2: Styled Choropleth with Labels")
print("=" * 60)

fig, ax = plt.subplots(figsize=(14, 12))

# Plot neighborhoods colored by district
barris_utm.plot(
    ax=ax,
    column="DISTRICTE",
    cmap="Paired",
    edgecolor="white",
    linewidth=0.8,
    alpha=0.7,
)

# Add district outlines
districts_utm = districts[["NOM", "geometry"]].to_crs(epsg=25831)
districts_utm.boundary.plot(ax=ax, edgecolor="black", linewidth=2)

# Label each neighborhood at its centroid
for _, row in barris_utm.iterrows():
    centroid = row.geometry.centroid
    # Shorten long names
    name = row["NOM"]
    if len(name) > 20:
        name = name[:18] + "..."
    ax.annotate(
        name,
        xy=(centroid.x, centroid.y),
        ha="center", va="center",
        fontsize=5,
        fontweight="bold",
        path_effects=[pe.withStroke(linewidth=2, foreground="white")],
    )

# Label districts
for _, row in districts_utm.iterrows():
    centroid = row.geometry.centroid
    ax.annotate(
        row["NOM"],
        xy=(centroid.x, centroid.y),
        ha="center", va="center",
        fontsize=9,
        fontweight="bold",
        color="darkred",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor="darkred"),
    )

ax.set_title("Barcelona Districts and Neighborhoods", fontsize=16, fontweight="bold")
ax.set_axis_off()

output_path = OUTPUT_DIR / "05_labeled_map.png"
plt.savefig(output_path, dpi=200, bbox_inches="tight")
print(f"Plot saved to: {output_path}")
plt.close()


# --- Section 3: Multi-Panel Figure ---

print("\n" + "=" * 60)
print("SECTION 3: Multi-Panel Figure")
print("=" * 60)

fig, axes = plt.subplots(1, 3, figsize=(20, 7))

# Panel 1: Area
barris_utm.plot(ax=axes[0], column="area_km2", cmap="YlOrRd", edgecolor="white",
                linewidth=0.3, legend=True,
                legend_kwds={"label": "km²", "shrink": 0.5})
axes[0].set_title("Area", fontsize=14, fontweight="bold")
axes[0].set_axis_off()

# Panel 2: Perimeter
barris_utm.plot(ax=axes[1], column="perimeter_km", cmap="Blues", edgecolor="white",
                linewidth=0.3, legend=True,
                legend_kwds={"label": "km", "shrink": 0.5})
axes[1].set_title("Perimeter", fontsize=14, fontweight="bold")
axes[1].set_axis_off()

# Panel 3: Compactness
barris_utm.plot(ax=axes[2], column="compactness", cmap="RdYlGn", edgecolor="white",
                linewidth=0.3, legend=True,
                legend_kwds={"label": "Ratio", "shrink": 0.5})
axes[2].set_title("Compactness (1.0 = circle)", fontsize=14, fontweight="bold")
axes[2].set_axis_off()

plt.suptitle("Barcelona Neighborhood Metrics", fontsize=18, fontweight="bold", y=1.02)
plt.tight_layout()

output_path = OUTPUT_DIR / "05_multi_panel.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"Plot saved to: {output_path}")
plt.close()


# --- Section 4: Classification Schemes ---

print("\n" + "=" * 60)
print("SECTION 4: Classification Schemes")
print("=" * 60)

# Instead of continuous color, classify into categories
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Quantiles: equal number of features in each class
barris_utm.plot(ax=axes[0], column="area_km2", cmap="YlOrRd", edgecolor="white",
                linewidth=0.3, legend=True, scheme="quantiles", k=5,
                legend_kwds={"title": "Area (km²)", "fontsize": 8})
axes[0].set_title("Quantiles (equal count per class)", fontsize=12)
axes[0].set_axis_off()

# Equal intervals: equal range in each class
barris_utm.plot(ax=axes[1], column="area_km2", cmap="YlOrRd", edgecolor="white",
                linewidth=0.3, legend=True, scheme="equal_interval", k=5,
                legend_kwds={"title": "Area (km²)", "fontsize": 8})
axes[1].set_title("Equal Intervals (equal range per class)", fontsize=12)
axes[1].set_axis_off()

plt.suptitle("Classification Schemes Comparison", fontsize=14, fontweight="bold")
plt.tight_layout()

output_path = OUTPUT_DIR / "05_classification.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"Plot saved to: {output_path}")
plt.close()


# --- Section 5: Interactive Map with Folium ---

print("\n" + "=" * 60)
print("SECTION 5: Interactive Map with Folium")
print("=" * 60)

# Folium creates interactive Leaflet.js maps.
# It needs data in WGS84 (EPSG:4326) -- which is our barris_wgs.

# Center the map on Barcelona
bcn_center = [41.3874, 2.1686]

m = folium.Map(location=bcn_center, zoom_start=13, tiles="cartodbpositron")

# Add a choropleth layer
folium.Choropleth(
    geo_data=barris_wgs.__geo_interface__,
    data=barris_wgs,
    columns=["NOM", "area_km2"],
    key_on="feature.properties.NOM",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.5,
    legend_name="Area (km²)",
    name="Area Choropleth",
).add_to(m)

# Add neighborhood names as tooltips using GeoJson
folium.GeoJson(
    barris_wgs.__geo_interface__,
    name="Neighborhoods",
    style_function=lambda x: {
        "fillOpacity": 0,
        "color": "transparent",
        "weight": 0,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["NOM", "DISTRICTE", "area_km2"],
        aliases=["Neighborhood:", "District:", "Area (km²):"],
        localize=True,
    ),
).add_to(m)

# Add layer control
folium.LayerControl().add_to(m)

output_path = OUTPUT_DIR / "05_interactive_map.html"
m.save(str(output_path))
print(f"Interactive map saved to: {output_path}")
print("  Open this file in a browser to explore!")


# --- Section 6: Multi-Layer Interactive Map ---

print("\n" + "=" * 60)
print("SECTION 6: Multi-Layer Interactive Map")
print("=" * 60)

m2 = folium.Map(location=bcn_center, zoom_start=13, tiles="cartodbpositron")

# Layer 1: Neighborhoods
neighborhood_layer = folium.FeatureGroup(name="Neighborhoods")
folium.GeoJson(
    barris_wgs.__geo_interface__,
    style_function=lambda x: {
        "fillColor": "#3388ff",
        "fillOpacity": 0.1,
        "color": "#3388ff",
        "weight": 1,
    },
    tooltip=folium.GeoJsonTooltip(fields=["NOM"], aliases=["Neighborhood:"]),
).add_to(neighborhood_layer)
neighborhood_layer.add_to(m2)

# Layer 2: Districts (thicker borders)
districts_wgs = districts[["NOM", "geometry"]].copy()
district_layer = folium.FeatureGroup(name="Districts")
folium.GeoJson(
    districts_wgs.__geo_interface__,
    style_function=lambda x: {
        "fillOpacity": 0,
        "color": "red",
        "weight": 3,
    },
    tooltip=folium.GeoJsonTooltip(fields=["NOM"], aliases=["District:"]),
).add_to(district_layer)
district_layer.add_to(m2)

# Layer 3: Compactness choropleth (added directly to map -- Choropleth requires Map parent)
folium.Choropleth(
    geo_data=barris_wgs.__geo_interface__,
    data=barris_wgs,
    columns=["NOM", "compactness"],
    key_on="feature.properties.NOM",
    fill_color="RdYlGn",
    fill_opacity=0.6,
    line_opacity=0.3,
    legend_name="Compactness",
    name="Compactness",
    overlay=True,
    show=False,
).add_to(m2)

folium.LayerControl(collapsed=False).add_to(m2)

output_path = OUTPUT_DIR / "05_multi_layer_map.html"
m2.save(str(output_path))
print(f"Multi-layer map saved to: {output_path}")

plt.close("all")

print("\n" + "=" * 60)
print("DONE! You've created static and interactive visualizations.")
print("Next: 06_capstone_analysis.py")
print("=" * 60)
