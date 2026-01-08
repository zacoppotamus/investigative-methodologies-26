# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains teaching materials for "From Afar: Investigative Methodologies" course at the Institute of Advanced Architecture of Catalunya (IAAC). The course focuses on satellite imagery analysis using machine learning and computer vision techniques.

## Project Structure

The repository uses numbered directories (001/, 002/, etc.) to organize course modules or sessions:

```
IAAC/
├── 001/          # Course module 1
├── 002/          # Course module 2 (future)
├── ...
└── .claude/      # Claude Code configuration
```

Each module directory may contain:
- Google Colab notebooks (`.ipynb` files)
- Python scripts for batch processing
- Data processing utilities
- Example datasets or outputs

## Course Workflow

The typical workflow in this course involves:

1. **Satellite Imagery Download**: Batch downloading satellite imagery from various sources
2. **Image Tiling**: Processing and tiling large satellite images for analysis
3. **Interactive Visualization**: Creating interactive Leaflet maps to explore imagery
4. **Dataset Annotation**: Using Roboflow for annotating training datasets
5. **Model Training**: Training computer vision models on annotated data
6. **Model Export**: Generating ONNX model files for deployment

## Key Technologies

- **Python**: Primary language for scripts and data processing
- **Google Colab**: Notebooks for interactive development and teaching
- **Leaflet**: JavaScript library for interactive maps (likely via folium or similar)
- **Roboflow**: Platform for dataset management and annotation
- **ONNX**: Model format for trained ML models

## Common Python Libraries

Expected dependencies for satellite imagery and ML work:
- Geospatial: `rasterio`, `gdal`, `geopandas`, `shapely`, `pyproj`
- Visualization: `folium`, `matplotlib`, `ipyleaflet`
- ML/CV: `torch`/`tensorflow`, `opencv-python`, `onnx`, `onnxruntime`
- Data: `numpy`, `pandas`, `pillow`
- Imagery: `sentinelsat`, `planet`, or similar satellite data APIs

## Development Notes

- **Notebooks**: Google Colab notebooks should be self-contained with installation cells for required packages
- **Scripts**: Python scripts should include clear docstrings and be executable from command line
- **Data Paths**: Use relative paths or environment variables for data locations to ensure portability
- **Tiling**: Satellite imagery tiling typically involves geographic coordinates (lat/lon) and zoom levels
- **Model Format**: ONNX models should be exported with clear input/output specifications documented in comments or README files within module directories

## Module 001: Satellite Imagery Download and Detection

### Overview
Module 001 contains tools for downloading satellite imagery tiles and running object detection with Roboflow models. The primary script is `satellite_detection.py`, which was converted from a Google Colab notebook.

### Files
- `001_bulk_img_download_and_detect.ipynb` - Original Google Colab notebook (reference)
- `satellite_detection.py` - Production CLI script for tile download and detection
- `requirements.txt` - Python dependencies for the module

### Environment Setup

**Create a new conda environment for Module 001:**

```bash
# Navigate to the module directory
cd 001

# Create a new conda environment with Python 3.10
conda create -n iaac-001 python=3.10 -y

# Activate the environment
conda activate iaac-001

# Install dependencies from requirements.txt
pip install -r requirements.txt

# Verify installation
python -c "import geopandas, mercantile, cv2; print('Environment ready!')"
```

**Alternative: Using an existing conda environment:**

```bash
# Activate your existing environment
conda activate your-env-name

# Install dependencies
cd 001
pip install -r requirements.txt
```

**Deactivate when done:**

```bash
conda deactivate
```

**Note:** The environment needs to be activated each time you run the script:
```bash
conda activate iaac-001
python satellite_detection.py --help
```

### Key Design Decisions

**1. Modular Pipeline Architecture**
The script is organized into two independent pipelines that can run separately or together:
- `download_tiles_pipeline()` - Downloads and stitches satellite tiles from bounding boxes
- `run_detection_pipeline()` - Runs Roboflow object detection on existing tiles

This separation allows:
- Downloading tiles once, then experimenting with different detection parameters
- Resuming from a specific step if one fails
- Better testing of individual components

**2. Execution Modes**
Three modes via `--mode` argument:
- `download` - Only download tiles, skip detection
- `detect` - Only run detection on existing tiles
- `both` (default) - Run complete pipeline

**3. Local File Operations**
All Google Drive and Colab-specific code was replaced with local file operations:
- Paths are relative to script execution directory
- Output structure: `{output_dir}/{output_name}/tiles/` and `{output_dir}/{output_name}/detections/`
- No cloud dependencies, fully portable

**4. Tile Stitching Strategy**
Downloads four 256x256 tiles and stitches them into 512x512 images:
- Uses ArcGIS World Imagery tile server by default
- Follows standard web mercator tiling scheme (XYZ)
- Saves spatial metadata as GeoJSON for each tile

**5. Input Validation**
Validates GeoJSON input files:
- Checks for valid JSON and polygon geometries
- Ensures CRS is EPSG:4326 (WGS84)
- Provides clear error messages for invalid inputs

### Usage Patterns

**Basic usage:**
```bash
python satellite_detection.py \
  --geojson area.geojson \
  --output-name "ProjectName" \
  --roboflow-api-key "KEY" \
  --roboflow-model "model-id/version"
```

**Common workflow for students:**
1. Create bounding box polygons in QGIS and export as GeoJSON
2. Run download mode to fetch tiles: `--mode download --geojson area.geojson`
3. Review downloaded tiles
4. Run detection mode with different confidence thresholds: `--mode detect --confidence 0.1`
5. Compare results

### Important CLI Arguments

Required:
- `--output-name` - Name of output folder
- `--geojson` - Path to GeoJSON file (for download mode)
- `--roboflow-api-key` - Roboflow API key (for detect mode)
- `--roboflow-model` - Model identifier like "model-name/version" (for detect mode)

Common optional:
- `--zoom` - Tile zoom level (default: 18)
- `--confidence` - Detection confidence threshold (default: 0.05)
- `--mode` - Execution mode: download, detect, or both (default: both)
- `--output-dir` - Base directory for outputs (default: current directory)

### Output Structure

```
{output_name}/
├── tiles/
│   ├── {x}_{y}_{z}.jpg          # Stitched 512x512 satellite images
│   └── tile_metadata.geojson    # Spatial metadata with tile bounds
└── detections/
    └── {x}_{y}_{z}.jpg          # Annotated images with bounding boxes
```

### Technical Notes

**Tile Coordinate System:**
- Uses web mercator projection (EPSG:3857) for tile coordinates
- Bounding boxes must be in WGS84 (EPSG:4326) lat/lon
- Downloads 2x2 grid of 256px tiles and stitches to 512px

**Detection Pipeline:**
- Uses Roboflow Inference SDK (`inference` package)
- Supports any Roboflow-trained model
- Annotates images using `supervision` library (bounding boxes + labels)
- Processes images in sequence, continues on errors

**Performance Considerations:**
- Network-bound during tile download (can be slow for large areas)
- Detection speed depends on model complexity and image count
- No parallel processing implemented (sequential for simplicity)

### Future Enhancements

When extending this module, consider:
- Adding parallel tile downloads for better performance
- Supporting additional tile servers (Sentinel, Planet, etc.)
- Batch processing with multiprocessing for detection
- Exporting detection results as GeoJSON (not just annotated images)
- Supporting other model formats beyond Roboflow
