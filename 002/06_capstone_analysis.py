#!/usr/bin/env python3
"""
Module 002 - Script 06: Capstone Analysis
==========================================

"Which Barcelona neighborhoods have the best walkability?"

This capstone combines everything from the previous scripts to answer
a real urban planning question relevant to architecture students at IAAC.

Analysis:
1. Download metro stations and parks from OpenStreetMap
2. Create 400m buffers around metro stations (5-minute walk)
3. Create 50m buffers around parks (adjacent/accessible)
4. Find zones with BOTH metro AND park access
5. Calculate % coverage per neighborhood
6. Produce a ranked choropleth map (static + interactive)

NOTE: This script requires internet access to download OSM data.
"""

# --- Google Colab Setup ---
# If running in Google Colab, uncomment and run these lines first:
# !pip install geopandas osmnx folium mapclassify
# !git clone https://github.com/zacoppotamus/investigative-methodologies-26
# %cd investigative-methodologies-26/002
# ---

from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import osmnx as ox
import folium
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

try:
    BASE_DIR = Path(__file__).parent
except NameError:
    BASE_DIR = Path.cwd()  # Colab: use current working directory
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

BCN_PLACE = "Barcelona, Spain"


# --- Section 1: Load Base Data ---

print("=" * 60)
print("CAPSTONE: Which neighborhoods have the best walkability?")
print("=" * 60)

print("\nLoading neighborhood boundaries...")
barris = gpd.read_file(DATA_DIR / "barris.geojson")
barris = barris[["NOM", "DISTRICTE", "geometry"]].copy()
barris_utm = barris.to_crs(epsg=25831)
barris_utm["area_m2"] = barris_utm.geometry.area
print(f"  Loaded {len(barris)} neighborhoods")


# --- Section 2: Download OSM Data ---

print("\n" + "=" * 60)
print("SECTION 2: Downloading OSM Data")
print("=" * 60)

print("\nDownloading metro stations...")
metro = ox.features_from_place(BCN_PLACE, tags={"railway": "station", "station": "subway"})
metro = metro[metro.geometry.type == "Point"].copy()
metro = metro[["name", "geometry"]].reset_index(drop=True)
metro_utm = metro.to_crs(epsg=25831)
print(f"  Found {len(metro_utm)} metro stations")

print("\nDownloading parks...")
parks = ox.features_from_place(BCN_PLACE, tags={"leisure": "park"})
parks = parks[parks.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()
parks = parks[["name", "geometry"]].reset_index(drop=True)
parks_utm = parks.to_crs(epsg=25831)
print(f"  Found {len(parks_utm)} parks")


# --- Section 3: Create Buffers ---

print("\n" + "=" * 60)
print("SECTION 3: Creating Buffers")
print("=" * 60)

# 400m buffer around metro stations (~5 minute walk)
METRO_BUFFER_M = 400
metro_buffers = metro_utm.copy()
metro_buffers["geometry"] = metro_utm.geometry.buffer(METRO_BUFFER_M)
print(f"  Created {METRO_BUFFER_M}m buffers around metro stations")

# 50m buffer around parks (park-adjacent zone)
PARK_BUFFER_M = 50
park_buffers = parks_utm.copy()
park_buffers["geometry"] = parks_utm.geometry.buffer(PARK_BUFFER_M)
print(f"  Created {PARK_BUFFER_M}m buffers around parks")

# Merge all buffers into single geometries
metro_coverage = metro_buffers.geometry.union_all()
park_coverage = park_buffers.geometry.union_all()
print("  Merged individual buffers into unified coverage areas")


# --- Section 4: Find Walkable + Green Zones ---

print("\n" + "=" * 60)
print("SECTION 4: Finding Walkable + Green Zones")
print("=" * 60)

# The intersection of metro coverage AND park coverage gives us
# areas that are both near transit AND near green space.
walkable_green = metro_coverage.intersection(park_coverage)
print(f"  Combined coverage type: {walkable_green.geom_type}")
print(f"  Combined coverage area: {walkable_green.area / 1_000_000:.2f} km2")

# Also compute individual coverages for comparison
bcn_outline = barris_utm.geometry.union_all()
bcn_area = bcn_outline.area

metro_in_bcn = metro_coverage.intersection(bcn_outline)
park_in_bcn = park_coverage.intersection(bcn_outline)
walkable_in_bcn = walkable_green.intersection(bcn_outline)

print(f"\n  Barcelona total area: {bcn_area / 1_000_000:.2f} km2")
print(f"  Metro coverage (400m): {metro_in_bcn.area / bcn_area * 100:.1f}%")
print(f"  Park coverage (50m): {park_in_bcn.area / bcn_area * 100:.1f}%")
print(f"  Both (walkable + green): {walkable_in_bcn.area / bcn_area * 100:.1f}%")


# --- Section 5: Calculate Per-Neighborhood Scores ---

print("\n" + "=" * 60)
print("SECTION 5: Neighborhood Walkability Scores")
print("=" * 60)

# For each neighborhood, compute what % is covered by the walkable+green zone
results = []
for _, row in barris_utm.iterrows():
    barri_geom = row.geometry
    barri_area = barri_geom.area

    # Metro coverage in this neighborhood
    metro_clip = metro_coverage.intersection(barri_geom)
    metro_pct = (metro_clip.area / barri_area) * 100

    # Park coverage in this neighborhood
    park_clip = park_coverage.intersection(barri_geom)
    park_pct = (park_clip.area / barri_area) * 100

    # Combined: walkable + green
    combined_clip = walkable_green.intersection(barri_geom)
    combined_pct = (combined_clip.area / barri_area) * 100

    results.append({
        "NOM": row["NOM"],
        "DISTRICTE": row["DISTRICTE"],
        "area_km2": barri_area / 1_000_000,
        "metro_pct": metro_pct,
        "park_pct": park_pct,
        "walkable_green_pct": combined_pct,
    })

# Create results DataFrame and merge with geometry
import pandas as pd
results_df = pd.DataFrame(results)
barris_results = barris_utm.merge(results_df, on=["NOM", "DISTRICTE"])

# Print top 15
print("\nTop 15 Neighborhoods by Walkable + Green Coverage:")
print("-" * 65)
top15 = results_df.sort_values("walkable_green_pct", ascending=False).head(15)
for i, (_, row) in enumerate(top15.iterrows(), 1):
    print(f"  {i:2d}. {row['NOM']:<30s} {row['walkable_green_pct']:5.1f}%  "
          f"(metro: {row['metro_pct']:4.1f}%, parks: {row['park_pct']:4.1f}%)")

print("\nBottom 5 Neighborhoods:")
print("-" * 65)
bottom5 = results_df.sort_values("walkable_green_pct").head(5)
for i, (_, row) in enumerate(bottom5.iterrows(), 1):
    print(f"  {i:2d}. {row['NOM']:<30s} {row['walkable_green_pct']:5.1f}%  "
          f"(metro: {row['metro_pct']:4.1f}%, parks: {row['park_pct']:4.1f}%)")

# Average
avg_score = results_df["walkable_green_pct"].mean()
median_score = results_df["walkable_green_pct"].median()
print(f"\n  Average walkability score: {avg_score:.1f}%")
print(f"  Median walkability score: {median_score:.1f}%")


# --- Section 6: Static Choropleth Map ---

print("\n" + "=" * 60)
print("SECTION 6: Static Choropleth Map")
print("=" * 60)

fig, axes = plt.subplots(1, 3, figsize=(22, 8))

# Panel 1: Metro coverage
barris_results.plot(ax=axes[0], column="metro_pct", cmap="Blues", edgecolor="white",
                    linewidth=0.5, legend=True,
                    legend_kwds={"label": "Coverage (%)", "shrink": 0.5})
axes[0].set_title("Metro Access (400m buffer)", fontsize=13, fontweight="bold")
axes[0].set_axis_off()

# Panel 2: Park coverage
barris_results.plot(ax=axes[1], column="park_pct", cmap="Greens", edgecolor="white",
                    linewidth=0.5, legend=True,
                    legend_kwds={"label": "Coverage (%)", "shrink": 0.5})
axes[1].set_title("Park Access (50m buffer)", fontsize=13, fontweight="bold")
axes[1].set_axis_off()

# Panel 3: Combined walkability score
barris_results.plot(ax=axes[2], column="walkable_green_pct", cmap="RdYlGn",
                    edgecolor="white", linewidth=0.5, legend=True,
                    legend_kwds={"label": "Coverage (%)", "shrink": 0.5})
axes[2].set_title("Walkable + Green (both)", fontsize=13, fontweight="bold")
axes[2].set_axis_off()

plt.suptitle("Barcelona Neighborhood Walkability Analysis",
             fontsize=16, fontweight="bold", y=1.02)
plt.tight_layout()

output_path = OUTPUT_DIR / "06_walkability_panels.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"Plot saved to: {output_path}")
plt.close()

# Detailed walkability map with labels
fig, ax = plt.subplots(figsize=(14, 14))

barris_results.plot(ax=ax, column="walkable_green_pct", cmap="RdYlGn",
                    edgecolor="white", linewidth=0.8, legend=True,
                    legend_kwds={"label": "Walkable + Green Coverage (%)",
                                 "shrink": 0.4, "orientation": "horizontal", "pad": 0.02})

# Label neighborhoods with their score
for _, row in barris_results.iterrows():
    centroid = row.geometry.centroid
    score = row["walkable_green_pct"]
    ax.annotate(
        f"{score:.0f}%",
        xy=(centroid.x, centroid.y),
        ha="center", va="center",
        fontsize=6, fontweight="bold",
        path_effects=[pe.withStroke(linewidth=2, foreground="white")],
    )

ax.set_title("Barcelona Walkability: % Near Metro AND Parks",
             fontsize=16, fontweight="bold")
ax.set_axis_off()

output_path = OUTPUT_DIR / "06_walkability_labeled.png"
plt.savefig(output_path, dpi=200, bbox_inches="tight")
print(f"Plot saved to: {output_path}")
plt.close("all")


# --- Section 7: Interactive Folium Map ---

print("\n" + "=" * 60)
print("SECTION 7: Interactive Folium Map")
print("=" * 60)

# Prepare WGS84 data for Folium
barris_wgs = barris_results.to_crs(epsg=4326)
metro_wgs = metro_utm.to_crs(epsg=4326)
parks_wgs = parks_utm.to_crs(epsg=4326)

bcn_center = [41.3874, 2.1686]
m = folium.Map(location=bcn_center, zoom_start=13, tiles="cartodbpositron")

# Walkability choropleth
folium.Choropleth(
    geo_data=barris_wgs.__geo_interface__,
    data=barris_wgs,
    columns=["NOM", "walkable_green_pct"],
    key_on="feature.properties.NOM",
    fill_color="RdYlGn",
    fill_opacity=0.7,
    line_opacity=0.5,
    legend_name="Walkable + Green Coverage (%)",
    name="Walkability Score",
).add_to(m)

# Tooltips with details
folium.GeoJson(
    barris_wgs.__geo_interface__,
    name="Details",
    style_function=lambda x: {"fillOpacity": 0, "color": "transparent", "weight": 0},
    tooltip=folium.GeoJsonTooltip(
        fields=["NOM", "DISTRICTE", "walkable_green_pct", "metro_pct", "park_pct"],
        aliases=["Neighborhood:", "District:", "Walkability (%):", "Metro (%):", "Parks (%):"],
        localize=True,
    ),
).add_to(m)

# Metro stations as markers
metro_layer = folium.FeatureGroup(name="Metro Stations")
for _, row in metro_wgs.iterrows():
    station_name = row.get("name", "Metro Station")
    if pd.isna(station_name):
        station_name = "Metro Station"
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=5,
        color="blue",
        fill=True,
        fill_opacity=0.8,
        popup=station_name,
    ).add_to(metro_layer)
metro_layer.add_to(m)

# Parks
park_layer = folium.FeatureGroup(name="Parks", show=False)
folium.GeoJson(
    parks_wgs.__geo_interface__,
    style_function=lambda x: {
        "fillColor": "green",
        "fillOpacity": 0.4,
        "color": "darkgreen",
        "weight": 1,
    },
).add_to(park_layer)
park_layer.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

output_path = OUTPUT_DIR / "06_walkability_interactive.html"
m.save(str(output_path))
print(f"Interactive map saved to: {output_path}")
print("  Open this file in a browser to explore!")


# --- Section 8: Summary ---

print("\n" + "=" * 60)
print("SECTION 8: Analysis Summary")
print("=" * 60)

print(f"""
FINDINGS:
=========

Data sources:
  - {len(barris)} neighborhoods from Barcelona open data
  - {len(metro_utm)} metro stations from OpenStreetMap
  - {len(parks_utm)} parks from OpenStreetMap

Methodology:
  - Metro accessibility: {METRO_BUFFER_M}m buffer (~5 min walk)
  - Park accessibility: {PARK_BUFFER_M}m buffer (adjacent access)
  - Walkability score: % of neighborhood area within BOTH buffers

City-wide:
  - Average walkability score: {avg_score:.1f}%
  - Median walkability score: {median_score:.1f}%

Top 3 most walkable neighborhoods:
""")

for i, (_, row) in enumerate(top15.head(3).iterrows(), 1):
    print(f"  {i}. {row['NOM']} ({row['walkable_green_pct']:.1f}%)")

print(f"""
Outputs:
  - 06_walkability_panels.png: Three-panel static comparison
  - 06_walkability_labeled.png: Detailed labeled choropleth
  - 06_walkability_interactive.html: Interactive Folium map
""")

print("=" * 60)
print("CAPSTONE COMPLETE!")
print("You've performed a full spatial analysis workflow.")
print("=" * 60)
