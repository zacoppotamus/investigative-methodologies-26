#!/usr/bin/env python3
"""
Module 002 - Script 03: Coordinate Reference Systems (CRS)
==========================================================

Understand how coordinate systems work and why they matter for spatial analysis.

Key concepts:
- What is a CRS and why it matters
- EPSG:4326 (WGS84) vs EPSG:25831 (UTM 31N) vs EPSG:3857 (Web Mercator)
- Reprojecting data with to_crs()
- Measuring real-world distances
- Creating point geometries from coordinates

Data: Barcelona neighborhoods + manually created landmark points.
"""

# --- Google Colab Setup ---
# If running in Google Colab, uncomment and run these lines first:
# !pip install geopandas
# !git clone https://github.com/zacharias1219/IAAC.git
# %cd IAAC/002
# ---

from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
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


# --- Section 1: What is a CRS? ---

print("=" * 60)
print("SECTION 1: What is a CRS?")
print("=" * 60)

print("""
A Coordinate Reference System (CRS) defines how 2D coordinates on a map
relate to real locations on Earth. Different CRS are optimized for
different purposes:

  EPSG:4326 (WGS84)
    - Units: degrees (latitude/longitude)
    - Used by: GPS, GeoJSON, web APIs
    - Good for: storing/exchanging data worldwide
    - Bad for: measuring distances or areas (degrees != meters)

  EPSG:25831 (UTM Zone 31N)
    - Units: meters
    - Used by: Spanish/Catalan official cartography
    - Good for: accurate measurements in Barcelona area
    - Bad for: data far from the UTM zone

  EPSG:3857 (Web Mercator)
    - Units: meters (but distorted!)
    - Used by: Google Maps, OpenStreetMap tiles, Mapbox
    - Good for: web map display
    - Bad for: area/distance calculations (severe distortion)
""")

print(f"Our data's CRS: {barris.crs}")
print(f"EPSG code: {barris.crs.to_epsg()}")


# --- Section 2: Creating Point Data from Coordinates ---

print("\n" + "=" * 60)
print("SECTION 2: Creating Point Data from Coordinates")
print("=" * 60)

# Barcelona landmarks with WGS84 coordinates (lat/lon from Google Maps)
landmarks = {
    "Sagrada Familia": (2.1744, 41.4036),
    "IAAC (Pujades)": (2.1942, 41.3976),
    "Park Guell": (2.1527, 41.4145),
    "Camp Nou": (2.1228, 41.3809),
    "La Boqueria": (2.1718, 41.3816),
    "Torre Glories": (2.1896, 41.4035),
    "Barceloneta Beach": (2.1899, 41.3783),
}

# Create a GeoDataFrame from the dictionary
# Note: Point takes (x, y) = (longitude, latitude), NOT (lat, lon)!
points = gpd.GeoDataFrame(
    {"name": list(landmarks.keys())},
    geometry=[Point(lon, lat) for lon, lat in landmarks.values()],
    crs="EPSG:4326",
)

print("\nLandmark points (WGS84):")
for _, row in points.iterrows():
    print(f"  {row['name']}: ({row.geometry.x:.4f}, {row.geometry.y:.4f})")


# --- Section 3: Reprojecting Data ---

print("\n" + "=" * 60)
print("SECTION 3: Reprojecting Data")
print("=" * 60)

# Reproject everything to UTM 31N for accurate measurements
barris_utm = barris.to_crs(epsg=25831)
points_utm = points.to_crs(epsg=25831)

print("\nSagrada Familia coordinates in different CRS:")
sf_4326 = points[points["name"] == "Sagrada Familia"].geometry.iloc[0]
sf_utm = points_utm[points_utm["name"] == "Sagrada Familia"].geometry.iloc[0]

print(f"  WGS84 (EPSG:4326): x={sf_4326.x:.6f}, y={sf_4326.y:.6f}  (degrees)")
print(f"  UTM 31N (EPSG:25831): x={sf_utm.x:.2f}, y={sf_utm.y:.2f}  (meters)")

# Also show Web Mercator for comparison
points_mercator = points.to_crs(epsg=3857)
sf_merc = points_mercator[points_mercator["name"] == "Sagrada Familia"].geometry.iloc[0]
print(f"  Web Mercator (EPSG:3857): x={sf_merc.x:.2f}, y={sf_merc.y:.2f}  (pseudo-meters)")


# --- Section 4: Measuring Distances ---

print("\n" + "=" * 60)
print("SECTION 4: Measuring Distances")
print("=" * 60)

# Distance from IAAC to each landmark
iaac_utm = points_utm[points_utm["name"] == "IAAC (Pujades)"].geometry.iloc[0]

print("\nDistances from IAAC (Pujades) to landmarks:")
distances = []
for _, row in points_utm.iterrows():
    if row["name"] == "IAAC (Pujades)":
        continue
    dist_m = iaac_utm.distance(row.geometry)
    distances.append({"name": row["name"], "distance_m": dist_m})
    print(f"  {row['name']}: {dist_m:.0f} m ({dist_m/1000:.2f} km)")

# What if we made the MISTAKE of computing distance in WGS84?
print("\nWARNING - Distance in WGS84 (WRONG!):")
iaac_4326 = points[points["name"] == "IAAC (Pujades)"].geometry.iloc[0]
sf_4326 = points[points["name"] == "Sagrada Familia"].geometry.iloc[0]
wrong_dist = iaac_4326.distance(sf_4326)
print(f"  IAAC to Sagrada Familia: {wrong_dist:.6f} degrees (meaningless!)")
print(f"  Correct distance: {iaac_utm.distance(points_utm[points_utm['name'] == 'Sagrada Familia'].geometry.iloc[0]):.0f} meters")


# --- Section 5: CRS and Area Comparison ---

print("\n" + "=" * 60)
print("SECTION 5: CRS and Area Comparison")
print("=" * 60)

# Compare area computation across CRS
print("\nTotal Barcelona area by CRS:")

barris_3857 = barris.to_crs(epsg=3857)

area_4326 = barris.geometry.area.sum()
area_utm = barris_utm.geometry.area.sum() / 1_000_000  # to km2
area_3857 = barris_3857.geometry.area.sum() / 1_000_000  # to km2

print(f"  EPSG:4326: {area_4326:.6f} square degrees (not useful)")
print(f"  EPSG:25831 (UTM): {area_utm:.2f} km2 (CORRECT)")
print(f"  EPSG:3857 (Mercator): {area_3857:.2f} km2 (distorted!)")
print(f"\n  Mercator overestimates area by {((area_3857/area_utm)-1)*100:.1f}%")


# --- Section 6: Visual Comparison of Projections ---

print("\n" + "=" * 60)
print("SECTION 6: Visual Comparison of Projections")
print("=" * 60)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# WGS84
barris.plot(ax=axes[0], edgecolor="black", facecolor="lightblue", linewidth=0.3)
points.plot(ax=axes[0], color="red", markersize=40, zorder=5)
axes[0].set_title("EPSG:4326 (WGS84)\nUnits: degrees")
axes[0].set_xlabel("Longitude")
axes[0].set_ylabel("Latitude")

# UTM
barris_utm.plot(ax=axes[1], edgecolor="black", facecolor="lightgreen", linewidth=0.3)
points_utm.plot(ax=axes[1], color="red", markersize=40, zorder=5)
axes[1].set_title("EPSG:25831 (UTM 31N)\nUnits: meters")
axes[1].set_xlabel("Easting (m)")
axes[1].set_ylabel("Northing (m)")

# Web Mercator
barris_3857.plot(ax=axes[2], edgecolor="black", facecolor="lightyellow", linewidth=0.3)
points_mercator.plot(ax=axes[2], color="red", markersize=40, zorder=5)
axes[2].set_title("EPSG:3857 (Web Mercator)\nUnits: pseudo-meters")
axes[2].set_xlabel("X")
axes[2].set_ylabel("Y")

plt.tight_layout()
output_path = OUTPUT_DIR / "03_crs_comparison.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"\nPlot saved to: {output_path}")

# Plot landmarks on neighborhoods
fig, ax = plt.subplots(figsize=(10, 10))
barris_utm.plot(ax=ax, edgecolor="gray", facecolor="lightyellow", linewidth=0.3)
points_utm.plot(ax=ax, color="red", markersize=60, zorder=5, edgecolor="black", linewidth=0.5)

# Label each point
for _, row in points_utm.iterrows():
    ax.annotate(row["name"], xy=(row.geometry.x, row.geometry.y),
                xytext=(5, 5), textcoords="offset points",
                fontsize=8, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))

ax.set_title("Barcelona Landmarks (UTM 31N)")
ax.set_axis_off()

output_path = OUTPUT_DIR / "03_landmarks.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"Plot saved to: {output_path}")
plt.close("all")

print("\n" + "=" * 60)
print("DONE! You understand CRS and why it matters for measurements.")
print("Next: 04_spatial_operations.py")
print("=" * 60)
