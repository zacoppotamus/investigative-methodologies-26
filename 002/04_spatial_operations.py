#!/usr/bin/env python3
"""
Module 002 - Script 04: Spatial Operations
==========================================

Learn fundamental spatial operations that make GIS powerful.

Key concepts:
- Downloading real-world data from OpenStreetMap via osmnx
- Buffer: creating zones around features
- Intersection: finding where geometries overlap
- Spatial join (sjoin): linking data based on location
- Dissolve: merging geometries by attribute
- Overlay: combining layers with set operations

Data: Barcelona neighborhoods + OSM parks and metro stations.

NOTE: This script requires internet access to download OSM data.
"""

from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import osmnx as ox
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Load and project neighborhoods to UTM for metric operations
barris = gpd.read_file(DATA_DIR / "barris.geojson")
barris_utm = barris[["NOM", "DISTRICTE", "geometry"]].to_crs(epsg=25831)

# Barcelona bounding box for OSM queries
BCN_BBOX = barris.total_bounds  # (minx, miny, maxx, maxy)
BCN_PLACE = "Barcelona, Spain"


# --- Section 1: Downloading Data from OpenStreetMap ---

print("=" * 60)
print("SECTION 1: Downloading Data from OpenStreetMap")
print("=" * 60)

print("\nDownloading parks from OSM (this may take a moment)...")
# osmnx.features_from_place downloads tagged features from OSM
parks = ox.features_from_place(BCN_PLACE, tags={"leisure": "park"})
# Keep only polygons (parks can also be tagged as points/lines)
parks = parks[parks.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()
parks = parks[["name", "geometry"]].reset_index(drop=True)
parks = parks.to_crs(epsg=25831)
print(f"  Found {len(parks)} parks")

print("\nDownloading metro stations from OSM...")
metro = ox.features_from_place(BCN_PLACE, tags={"railway": "station", "station": "subway"})
# Keep only points
metro = metro[metro.geometry.type == "Point"].copy()
metro = metro[["name", "geometry"]].reset_index(drop=True)
metro = metro.to_crs(epsg=25831)
print(f"  Found {len(metro)} metro stations")


# --- Section 2: Buffer ---

print("\n" + "=" * 60)
print("SECTION 2: Buffer Operations")
print("=" * 60)

# Create a 400m buffer around each metro station (approx. 5-minute walk)
metro_buffer_400 = metro.copy()
metro_buffer_400["geometry"] = metro.geometry.buffer(400)
print(f"\nCreated 400m buffers around {len(metro_buffer_400)} metro stations")

# Create a 50m buffer around parks (adjacent/accessible zone)
parks_buffer_50 = parks.copy()
parks_buffer_50["geometry"] = parks.geometry.buffer(50)
print(f"Created 50m buffers around {len(parks_buffer_50)} parks")

# Visualize buffers
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

barris_utm.plot(ax=axes[0], edgecolor="gray", facecolor="lightyellow", linewidth=0.3)
metro_buffer_400.plot(ax=axes[0], facecolor="blue", alpha=0.2, edgecolor="blue", linewidth=0.3)
metro.plot(ax=axes[0], color="blue", markersize=10, zorder=5)
axes[0].set_title("Metro Stations with 400m Buffer")
axes[0].set_axis_off()

barris_utm.plot(ax=axes[1], edgecolor="gray", facecolor="lightyellow", linewidth=0.3)
parks_buffer_50.plot(ax=axes[1], facecolor="green", alpha=0.3, edgecolor="green", linewidth=0.3)
parks.plot(ax=axes[1], facecolor="green", alpha=0.5, edgecolor="darkgreen", linewidth=0.5)
axes[1].set_title("Parks with 50m Buffer")
axes[1].set_axis_off()

plt.tight_layout()
output_path = OUTPUT_DIR / "04_buffers.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"\nPlot saved to: {output_path}")


# --- Section 3: Spatial Join (sjoin) ---

print("\n" + "=" * 60)
print("SECTION 3: Spatial Join (sjoin)")
print("=" * 60)

# Which neighborhood is each metro station in?
# sjoin matches rows from two GeoDataFrames based on spatial relationship
metro_with_barri = gpd.sjoin(metro, barris_utm, how="left", predicate="within")
print("\nMetro stations with their neighborhood:")
for _, row in metro_with_barri.head(10).iterrows():
    station_name = row.get("name_left", "Unknown")
    barri_name = row.get("NOM", "Unknown")
    print(f"  {station_name} -> {barri_name}")

# Count metro stations per neighborhood
stations_per_barri = metro_with_barri.groupby("NOM").size().reset_index(name="num_stations")
print(f"\nNeighborhoods with most metro stations:")
top_metro = stations_per_barri.sort_values("num_stations", ascending=False).head(5)
for _, row in top_metro.iterrows():
    print(f"  {row['NOM']}: {row['num_stations']} stations")

# Neighborhoods with NO metro stations
barris_with_metro = set(stations_per_barri["NOM"])
barris_without = [n for n in barris_utm["NOM"] if n not in barris_with_metro]
print(f"\nNeighborhoods with NO metro stations: {len(barris_without)}")


# --- Section 4: Dissolve ---

print("\n" + "=" * 60)
print("SECTION 4: Dissolve (Merge by Attribute)")
print("=" * 60)

# Dissolve neighborhoods into districts (merge geometries that share the same DISTRICTE)
districts_dissolved = barris_utm.dissolve(by="DISTRICTE", as_index=False)
print(f"\nDissolved {len(barris_utm)} neighborhoods into {len(districts_dissolved)} districts")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

barris_utm.plot(ax=axes[0], edgecolor="black", facecolor="lightblue", linewidth=0.3)
axes[0].set_title(f"Neighborhoods ({len(barris_utm)})")
axes[0].set_axis_off()

districts_dissolved.plot(ax=axes[1], edgecolor="black", facecolor="lightcoral",
                         linewidth=1, column="DISTRICTE", cmap="tab10")
axes[1].set_title(f"Dissolved into Districts ({len(districts_dissolved)})")
axes[1].set_axis_off()

plt.tight_layout()
output_path = OUTPUT_DIR / "04_dissolve.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"Plot saved to: {output_path}")


# --- Section 5: Intersection and Overlay ---

print("\n" + "=" * 60)
print("SECTION 5: Intersection and Overlay")
print("=" * 60)

# Find the area of parks within each neighborhood using overlay
# overlay(how="intersection") clips one layer by another
parks_in_barris = gpd.overlay(parks, barris_utm, how="intersection")
print(f"\nIntersected parks with neighborhoods: {len(parks_in_barris)} fragments")

# Calculate park area per neighborhood
parks_in_barris["park_area_m2"] = parks_in_barris.geometry.area
park_area_by_barri = parks_in_barris.groupby("NOM")["park_area_m2"].sum().reset_index()

# Merge back to get percentages
barris_with_parks = barris_utm.copy()
barris_with_parks["barri_area_m2"] = barris_with_parks.geometry.area
barris_with_parks = barris_with_parks.merge(park_area_by_barri, on="NOM", how="left")
barris_with_parks["park_area_m2"] = barris_with_parks["park_area_m2"].fillna(0)
barris_with_parks["park_pct"] = (barris_with_parks["park_area_m2"] / barris_with_parks["barri_area_m2"]) * 100

print("\nNeighborhoods with most park coverage:")
top_parks = barris_with_parks.sort_values("park_pct", ascending=False).head(5)
for _, row in top_parks.iterrows():
    print(f"  {row['NOM']}: {row['park_pct']:.1f}%")

print("\nNeighborhoods with least park coverage:")
bottom_parks = barris_with_parks.sort_values("park_pct").head(5)
for _, row in bottom_parks.iterrows():
    print(f"  {row['NOM']}: {row['park_pct']:.1f}%")


# --- Section 6: Unary Union ---

print("\n" + "=" * 60)
print("SECTION 6: Unary Union (Merge All)")
print("=" * 60)

# Merge all metro buffers into a single geometry
metro_coverage = metro_buffer_400.geometry.union_all()
print(f"\nMerged {len(metro_buffer_400)} metro buffers into a single geometry")
print(f"  Type: {metro_coverage.geom_type}")

# What percentage of Barcelona is within 400m of a metro station?
bcn_outline = barris_utm.geometry.union_all()
bcn_area = bcn_outline.area
metro_in_bcn = metro_coverage.intersection(bcn_outline)
metro_coverage_pct = (metro_in_bcn.area / bcn_area) * 100
print(f"  Barcelona area: {bcn_area/1_000_000:.2f} km2")
print(f"  Metro coverage area: {metro_in_bcn.area/1_000_000:.2f} km2")
print(f"  Coverage: {metro_coverage_pct:.1f}% of Barcelona within 400m of metro")


# --- Section 7: Summary Visualization ---

print("\n" + "=" * 60)
print("SECTION 7: Park Coverage Map")
print("=" * 60)

fig, ax = plt.subplots(figsize=(10, 10))
barris_with_parks.plot(ax=ax, column="park_pct", cmap="Greens", edgecolor="white",
                       linewidth=0.5, legend=True,
                       legend_kwds={"label": "Park Coverage (%)", "shrink": 0.6})
ax.set_title("Park Coverage by Neighborhood (%)")
ax.set_axis_off()

output_path = OUTPUT_DIR / "04_park_coverage.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"Plot saved to: {output_path}")
plt.close("all")

print("\n" + "=" * 60)
print("DONE! You've learned key spatial operations.")
print("Next: 05_visualization.py")
print("=" * 60)
