#!/usr/bin/env python3
"""
Module 002 - Script 02: Filtering and Attribute Operations
==========================================================

Learn how to filter spatial data and compute geometric properties.

Key concepts:
- Selecting columns and rows
- Filtering with boolean conditions and .query()
- Computing geometric properties: area, perimeter, centroid
- Adding new computed columns to a GeoDataFrame

Data: Barcelona neighborhoods (73 barris).
"""

# --- Google Colab Setup ---
# If running in Google Colab, uncomment and run these lines first:
# !pip install geopandas
# !git clone https://github.com/zacoppotamus/investigative-methodologies-26
# %cd investigative-methodologies-26/002
# ---

from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

try:
    BASE_DIR = Path(__file__).parent
except NameError:
    BASE_DIR = Path.cwd()  # Colab: use current working directory
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Load neighborhoods
barris = gpd.read_file(DATA_DIR / "barris.geojson")

print(f"Loaded {len(barris)} neighborhoods")
print(f"CRS: {barris.crs}")


# --- Section 1: Selecting Columns ---

print("\n" + "=" * 60)
print("SECTION 1: Selecting Columns")
print("=" * 60)

# Select just the columns we care about for a cleaner view.
# NOM = name, DISTRICTE = district number, AREA = area attribute from source
barris_simple = barris[["NOM", "DISTRICTE", "AREA", "geometry"]].copy()
print("\nSimplified DataFrame:")
print(barris_simple.head())

# Note: selecting columns that include 'geometry' keeps it as a GeoDataFrame.
print(f"\nType after selection: {type(barris_simple)}")


# --- Section 2: Filtering Rows ---

print("\n" + "=" * 60)
print("SECTION 2: Filtering Rows")
print("=" * 60)

# Filter neighborhoods in District 1 (Ciutat Vella - the old city)
ciutat_vella = barris_simple[barris_simple["DISTRICTE"] == "01"]
print(f"\nNeighborhoods in Ciutat Vella (District 01): {len(ciutat_vella)}")
for _, row in ciutat_vella.iterrows():
    print(f"  - {row['NOM']}")

# Using .query() for more readable filtering
eixample = barris_simple.query("DISTRICTE == '02'")
print(f"\nNeighborhoods in Eixample (District 02): {len(eixample)}")
for _, row in eixample.iterrows():
    print(f"  - {row['NOM']}")


# --- Section 3: Computing Area in Proper Units ---

print("\n" + "=" * 60)
print("SECTION 3: Computing Area (with proper CRS)")
print("=" * 60)

# IMPORTANT: Area computed in EPSG:4326 (degrees) is meaningless!
# We must project to a metric CRS first.
print(f"\nCurrent CRS: {barris_simple.crs}")
print("Area in degrees (WRONG):")
print(f"  First neighborhood: {barris_simple.geometry.area.iloc[0]:.8f} square degrees")

# Project to EPSG:25831 (UTM zone 31N) -- the standard metric CRS for Barcelona.
barris_metric = barris_simple.to_crs(epsg=25831)
print(f"\nProjected CRS: {barris_metric.crs}")

# Now compute area in square meters
barris_metric["area_m2"] = barris_metric.geometry.area
barris_metric["area_km2"] = barris_metric["area_m2"] / 1_000_000
barris_metric["area_ha"] = barris_metric["area_m2"] / 10_000

print("\nArea (correct, in metric units):")
print(barris_metric[["NOM", "area_m2", "area_km2", "area_ha"]].head(10).to_string(index=False))


# --- Section 4: Computing Perimeter ---

print("\n" + "=" * 60)
print("SECTION 4: Computing Perimeter")
print("=" * 60)

barris_metric["perimeter_m"] = barris_metric.geometry.length
barris_metric["perimeter_km"] = barris_metric["perimeter_m"] / 1000

print("\nPerimeter of neighborhoods:")
print(barris_metric[["NOM", "perimeter_m", "perimeter_km"]].head(10).to_string(index=False))


# --- Section 5: Finding Extremes ---

print("\n" + "=" * 60)
print("SECTION 5: Finding Extremes")
print("=" * 60)

# Largest neighborhood
largest = barris_metric.loc[barris_metric["area_km2"].idxmax()]
print(f"\nLargest neighborhood: {largest['NOM']} ({largest['area_km2']:.2f} km2)")

# Smallest neighborhood
smallest = barris_metric.loc[barris_metric["area_km2"].idxmin()]
print(f"Smallest neighborhood: {smallest['NOM']} ({smallest['area_km2']:.2f} km2)")

# Most compact (lowest perimeter-to-area ratio = most circle-like)
barris_metric["compactness"] = (4 * np.pi * barris_metric["area_m2"]) / (barris_metric["perimeter_m"] ** 2)
most_compact = barris_metric.loc[barris_metric["compactness"].idxmax()]
print(f"Most compact: {most_compact['NOM']} (compactness={most_compact['compactness']:.3f}, 1.0=circle)")

least_compact = barris_metric.loc[barris_metric["compactness"].idxmin()]
print(f"Least compact: {least_compact['NOM']} (compactness={least_compact['compactness']:.3f})")


# --- Section 6: Summary Statistics by District ---

print("\n" + "=" * 60)
print("SECTION 6: Summary Statistics by District")
print("=" * 60)

district_stats = barris_metric.groupby("DISTRICTE").agg(
    num_neighborhoods=("NOM", "count"),
    total_area_km2=("area_km2", "sum"),
    avg_area_km2=("area_km2", "mean"),
    avg_compactness=("compactness", "mean"),
).round(3)

print("\nDistrict-level summary:")
print(district_stats.to_string())


# --- Section 7: Centroid Computation ---

print("\n" + "=" * 60)
print("SECTION 7: Computing Centroids")
print("=" * 60)

# Centroids are the geometric center of each polygon.
barris_metric["centroid"] = barris_metric.geometry.centroid

# Show centroid coordinates for first few neighborhoods
print("\nNeighborhood centroids (UTM coordinates):")
for _, row in barris_metric.head(5).iterrows():
    print(f"  {row['NOM']}: ({row['centroid'].x:.1f}, {row['centroid'].y:.1f})")


# --- Section 8: Visualization of Computed Properties ---

print("\n" + "=" * 60)
print("SECTION 8: Visualizing Computed Properties")
print("=" * 60)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Plot 1: Area choropleth
barris_metric.plot(ax=axes[0], column="area_km2", cmap="YlOrRd", edgecolor="white",
                   linewidth=0.5, legend=True,
                   legend_kwds={"label": "Area (km2)", "shrink": 0.6})
axes[0].set_title("Neighborhood Area")
axes[0].set_axis_off()

# Plot 2: Compactness choropleth
barris_metric.plot(ax=axes[1], column="compactness", cmap="RdYlGn", edgecolor="white",
                   linewidth=0.5, legend=True,
                   legend_kwds={"label": "Compactness", "shrink": 0.6})
axes[1].set_title("Shape Compactness (1.0 = circle)")
axes[1].set_axis_off()

# Plot 3: Centroids overlaid on neighborhoods
barris_metric.plot(ax=axes[2], edgecolor="gray", facecolor="lightyellow", linewidth=0.5)
centroid_gdf = gpd.GeoDataFrame(barris_metric[["NOM"]], geometry=barris_metric["centroid"],
                                crs=barris_metric.crs)
centroid_gdf.plot(ax=axes[2], color="red", markersize=15, zorder=5)
axes[2].set_title("Neighborhood Centroids")
axes[2].set_axis_off()

plt.tight_layout()
output_path = OUTPUT_DIR / "02_attributes.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"\nPlot saved to: {output_path}")
plt.close("all")

print("\n" + "=" * 60)
print("DONE! You've learned filtering and geometric computations.")
print("Next: 03_coordinate_systems.py")
print("=" * 60)
