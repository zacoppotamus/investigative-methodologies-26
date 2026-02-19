#!/usr/bin/env python3
"""
Module 002 - Script 01: Loading Spatial Data with GeoPandas
==========================================================

Learn the fundamentals of loading and inspecting geospatial data using GeoPandas.
We'll work with Barcelona's administrative boundaries (districts and neighborhoods).

Key concepts:
- Reading GeoJSON files into GeoDataFrames
- Inspecting the structure of spatial data (shape, dtypes, head)
- Understanding geometry types (Point, LineString, Polygon, MultiPolygon)
- Creating basic plots with .plot()

Data: Barcelona districts (10) and neighborhoods (73) from bcn-geodata.
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

# Portable path resolution -- works in scripts and Colab
try:
    BASE_DIR = Path(__file__).parent
except NameError:
    BASE_DIR = Path.cwd()  # Colab: use current working directory
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


# --- Section 1: Loading a GeoJSON file ---

print("=" * 60)
print("SECTION 1: Loading a GeoJSON File")
print("=" * 60)

# gpd.read_file() can read GeoJSON, Shapefile, GeoPackage, and many more formats.
districts = gpd.read_file(DATA_DIR / "districtes.geojson")

# A GeoDataFrame is just like a pandas DataFrame, but with a special 'geometry' column.
print(f"\nType: {type(districts)}")
print(f"Shape: {districts.shape}  (rows={districts.shape[0]}, columns={districts.shape[1]})")

# The .head() method shows the first few rows, just like pandas.
print("\n--- First 3 rows ---")
print(districts[["NOM", "DISTRICTE", "AREA", "geometry"]].head(3))


# --- Section 2: Inspecting Column Types ---

print("\n" + "=" * 60)
print("SECTION 2: Inspecting Column Types")
print("=" * 60)

# .dtypes tells us the data type of each column.
# Notice that the 'geometry' column has a special type.
print("\nKey column types:")
for col in ["NOM", "DISTRICTE", "AREA", "geometry"]:
    print(f"  {col}: {districts[col].dtype}")

# .columns lists all available columns
print(f"\nAll columns ({len(districts.columns)}):")
print(list(districts.columns))


# --- Section 3: Understanding the Geometry Column ---

print("\n" + "=" * 60)
print("SECTION 3: Understanding the Geometry Column")
print("=" * 60)

# The geometry column contains Shapely geometry objects.
print(f"\nGeometry column name: {districts.geometry.name}")
print(f"Geometry type(s): {districts.geom_type.unique()}")

# Each row's geometry is a Shapely object. Let's look at one.
first_geom = districts.geometry.iloc[0]
print(f"\nFirst district: {districts['NOM'].iloc[0]}")
print(f"  Geometry type: {first_geom.geom_type}")
print(f"  Number of vertices: {len(first_geom.exterior.coords)}")
print(f"  Bounds (minx, miny, maxx, maxy): {first_geom.bounds}")

# Total bounds of the entire dataset
print(f"\nTotal bounds of all districts: {districts.total_bounds}")


# --- Section 4: Loading the Neighborhoods Dataset ---

print("\n" + "=" * 60)
print("SECTION 4: Loading Neighborhoods")
print("=" * 60)

neighborhoods = gpd.read_file(DATA_DIR / "barris.geojson")

print(f"Number of neighborhoods: {len(neighborhoods)}")
print(f"Geometry types: {neighborhoods.geom_type.unique()}")

# Let's see a few neighborhood names
print("\nSample neighborhoods:")
for _, row in neighborhoods.head(5).iterrows():
    print(f"  {row['NOM']} (District: {row['DISTRICTE']})")


# --- Section 5: The Coordinate Reference System (CRS) ---

print("\n" + "=" * 60)
print("SECTION 5: Coordinate Reference System (CRS)")
print("=" * 60)

# Every GeoDataFrame has a CRS that tells us how coordinates map to locations on Earth.
print(f"\nDistricts CRS: {districts.crs}")
print(f"Neighborhoods CRS: {neighborhoods.crs}")

# EPSG:4326 = WGS84 = the GPS coordinate system (latitude/longitude in degrees)
# This is the most common CRS for web mapping and GeoJSON files.


# --- Section 6: Basic Plotting ---

print("\n" + "=" * 60)
print("SECTION 6: Basic Plotting")
print("=" * 60)

# .plot() creates a quick matplotlib figure.
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Plot 1: Districts
districts.plot(ax=axes[0], edgecolor="black", facecolor="lightblue", linewidth=1)
axes[0].set_title("Barcelona Districts (10)")
axes[0].set_xlabel("Longitude")
axes[0].set_ylabel("Latitude")

# Plot 2: Neighborhoods
neighborhoods.plot(ax=axes[1], edgecolor="black", facecolor="lightyellow", linewidth=0.5)
axes[1].set_title("Barcelona Neighborhoods (73)")
axes[1].set_xlabel("Longitude")
axes[1].set_ylabel("Latitude")

plt.tight_layout()

# Save the figure (in Colab, you would use plt.show() instead)
output_path = OUTPUT_DIR / "01_basic_maps.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"\nPlot saved to: {output_path}")
# plt.show()  # Uncomment in Colab or interactive environments

# Plot 3: Neighborhoods colored by district
fig, ax = plt.subplots(figsize=(10, 8))
neighborhoods.plot(ax=ax, column="DISTRICTE", cmap="tab10", edgecolor="white",
                   linewidth=0.5, legend=True, legend_kwds={"title": "District"})
ax.set_title("Barcelona Neighborhoods Colored by District")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")

output_path = OUTPUT_DIR / "01_neighborhoods_by_district.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"Plot saved to: {output_path}")

plt.close("all")

print("\n" + "=" * 60)
print("DONE! You've learned how to load and inspect spatial data.")
print("Next: 02_filtering_and_attributes.py")
print("=" * 60)
