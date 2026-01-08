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
