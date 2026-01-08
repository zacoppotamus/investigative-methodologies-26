#!/usr/bin/env python3
"""
Satellite Imagery Download and Object Detection Script

This script downloads satellite imagery tiles for specified bounding boxes
and optionally runs object detection using Roboflow models.

Usage:
    python satellite_detection.py --geojson area.geojson --output-name "MyProject" \\
        --roboflow-api-key "YOUR_KEY" --roboflow-model "model-id/version"
"""

import argparse
import glob
import io
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import geopandas as gpd
import mercantile
import requests
import supervision as sv
from inference import get_model
from PIL import Image
from shapely.geometry import box

# Logger
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TILE_URL = "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
TILE_SIZE = 256
STITCHED_SIZE = 512


# ============================================================================
# Utility Functions
# ============================================================================

def get_tiles_for_bbox(bounds: Tuple[float, float, float, float], zoom: int) -> List[mercantile.Tile]:
    """
    Get mercantile tiles for a bounding box at a given zoom level.

    Args:
        bounds: Tuple of (min_lon, min_lat, max_lon, max_lat)
        zoom: Zoom level for tiles

    Returns:
        List of mercantile.Tile objects
    """
    min_lon, min_lat, max_lon, max_lat = bounds
    tiles = list(mercantile.tiles(min_lon, min_lat, max_lon, max_lat, zoom))
    return tiles


def download_tile(tile: mercantile.Tile, tile_url: str) -> Optional[Image.Image]:
    """
    Download a single tile from the tile server.

    Args:
        tile: Mercantile tile object
        tile_url: URL template for tile server

    Returns:
        PIL Image object or None if download fails
    """
    url = tile_url.format(x=tile.x, y=tile.y, z=tile.z)

    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        else:
            logger.warning(f"Failed to download tile {tile.x}, {tile.y}, {tile.z}: HTTP {response.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Error downloading tile {tile.x}, {tile.y}, {tile.z}: {e}")
        return None


def stitch_tiles(tiles: List[Optional[Image.Image]]) -> Image.Image:
    """
    Stitch four 256x256 tiles into a single 512x512 image.

    Args:
        tiles: List of 4 PIL Image objects (or None)

    Returns:
        Stitched 512x512 PIL Image
    """
    stitched = Image.new("RGB", (STITCHED_SIZE, STITCHED_SIZE))
    for i, tile in enumerate(tiles):
        if tile:
            x, y = (i % 2) * TILE_SIZE, (i // 2) * TILE_SIZE
            stitched.paste(tile, (x, y))
    return stitched


# ============================================================================
# Validation Functions
# ============================================================================

def validate_geojson(geojson_path: str) -> gpd.GeoDataFrame:
    """
    Validate and load a GeoJSON file.

    Args:
        geojson_path: Path to GeoJSON file

    Returns:
        GeoDataFrame with validated geometries

    Raises:
        SystemExit if validation fails
    """
    if not os.path.exists(geojson_path):
        logger.error(f"GeoJSON file not found: {geojson_path}")
        sys.exit(1)

    try:
        gdf = gpd.read_file(geojson_path)
    except Exception as e:
        logger.error(f"Failed to read GeoJSON file: {e}")
        sys.exit(1)

    if len(gdf) == 0:
        logger.error("GeoJSON file contains no features")
        sys.exit(1)

    # Ensure CRS is WGS84
    if gdf.crs is None:
        logger.warning("No CRS defined, assuming EPSG:4326")
        gdf.set_crs(epsg=4326, inplace=True)
    elif gdf.crs.to_epsg() != 4326:
        logger.info(f"Converting from {gdf.crs} to EPSG:4326")
        gdf = gdf.to_crs(epsg=4326)

    # Check for polygon geometries
    if not all(gdf.geometry.geom_type.isin(['Polygon', 'MultiPolygon'])):
        logger.error("GeoJSON must contain only Polygon or MultiPolygon geometries")
        sys.exit(1)

    return gdf


def validate_detection_args(args: argparse.Namespace) -> None:
    """
    Validate that required detection arguments are present.

    Args:
        args: Parsed command-line arguments

    Raises:
        SystemExit if validation fails
    """
    if args.mode in ['detect', 'both']:
        if not args.roboflow_api_key:
            logger.error("--roboflow-api-key is required for detection mode")
            sys.exit(1)
        if not args.roboflow_model:
            logger.error("--roboflow-model is required for detection mode")
            sys.exit(1)


# ============================================================================
# Pipeline Functions
# ============================================================================

def download_tiles_pipeline(
    geojson_path: str,
    zoom: int,
    output_dir: Path,
    output_name: str,
    tile_url: str
) -> Path:
    """
    Download and stitch satellite imagery tiles.

    Args:
        geojson_path: Path to GeoJSON file with bounding boxes
        zoom: Zoom level for tiles
        output_dir: Base output directory
        output_name: Name of output folder
        tile_url: Tile server URL template

    Returns:
        Path to tiles directory
    """
    logger.info("="*60)
    logger.info("TILE DOWNLOAD PIPELINE")
    logger.info("="*60)

    # Load and validate GeoJSON
    logger.info(f"Loading GeoJSON from: {geojson_path}")
    gdf = validate_geojson(geojson_path)
    logger.info(f"Loaded {len(gdf)} polygon(s)")

    # Get tiles for each polygon
    logger.info(f"Calculating tiles at zoom level {zoom}...")
    gdf["tiles"] = gdf["geometry"].apply(lambda geom: get_tiles_for_bbox(geom.bounds, zoom))

    total_tiles = sum(len(row["tiles"]) for _, row in gdf.iterrows())
    logger.info(f"Total tiles to download: {total_tiles}")

    # Create output directories
    project_dir = output_dir / output_name
    tiles_dir = project_dir / "tiles"
    tiles_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {tiles_dir}")

    # Download and stitch tiles
    metadata_list = []
    downloaded = 0

    logger.info("Downloading and stitching tiles...")
    for poly_idx, row in gdf.iterrows():
        for tile_idx, tile in enumerate(row["tiles"]):
            # Download 4 subtiles for stitching
            subtiles = [
                download_tile(mercantile.Tile(tile.x, tile.y, tile.z), tile_url),
                download_tile(mercantile.Tile(tile.x + 1, tile.y, tile.z), tile_url),
                download_tile(mercantile.Tile(tile.x, tile.y + 1, tile.z), tile_url),
                download_tile(mercantile.Tile(tile.x + 1, tile.y + 1, tile.z), tile_url)
            ]

            # Stitch tiles together
            stitched = stitch_tiles(subtiles)
            filename = f"{tile.x}_{tile.y}_{tile.z}.jpg"
            stitched.save(tiles_dir / filename, "JPEG")

            # Get bounding box of tile
            tile_bounds = mercantile.bounds(tile)
            tile_geom = box(tile_bounds.west, tile_bounds.south, tile_bounds.east, tile_bounds.north)

            # Store metadata
            metadata_list.append({
                "filename": filename,
                "geometry": tile_geom
            })

            downloaded += 1
            # More frequent progress updates (every 5 tiles or at completion)
            if downloaded % 5 == 0 or downloaded == total_tiles:
                progress_pct = (downloaded * 100) // total_tiles if total_tiles > 0 else 0
                progress_msg = f"Progress: {downloaded}/{total_tiles} tiles ({progress_pct}%)"
                logger.info(progress_msg)

    # Save metadata as GeoJSON
    metadata_gdf = gpd.GeoDataFrame(metadata_list, crs="EPSG:4326")
    metadata_path = tiles_dir / "tile_metadata.geojson"
    metadata_gdf.to_file(metadata_path, driver="GeoJSON")
    logger.info(f"Saved metadata to: {metadata_path}")
    logger.info(f"Downloaded {downloaded} tiles successfully")

    return tiles_dir


def run_detection_pipeline(
    tiles_dir: Path,
    detections_dir: Path,
    model_id: str,
    api_key: str,
    confidence: float
) -> None:
    """
    Run object detection on downloaded tiles.

    Args:
        tiles_dir: Directory containing tile images
        detections_dir: Directory for detection outputs
        model_id: Roboflow model identifier
        api_key: Roboflow API key
        confidence: Confidence threshold for detections
    """
    logger.info("="*60)
    logger.info("OBJECT DETECTION PIPELINE")
    logger.info("="*60)

    # Create detections directory
    detections_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {detections_dir}")

    # Load model
    logger.info(f"Loading Roboflow model: {model_id}")
    try:
        model = get_model(model_id=model_id, api_key=api_key)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Roboflow model: {e}")
        sys.exit(1)

    # Find all tile images
    tile_images = sorted(glob.glob(str(tiles_dir / "*.jpg")))

    if not tile_images:
        logger.warning(f"No tile images found in {tiles_dir}")
        return

    logger.info(f"Processing {len(tile_images)} images...")
    logger.info(f"Confidence threshold: {confidence}")

    # Process each image
    processed = 0
    total_detections = 0

    for image_path in tile_images:
        filename = os.path.basename(image_path)

        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                logger.warning(f"Failed to read {filename}")
                continue

            # Run inference
            results = model.infer(image, confidence=confidence)[0]

            # Load results into supervision
            detections = sv.Detections.from_inference(results)

            # Create annotators
            bounding_box_annotator = sv.BoxAnnotator()
            label_annotator = sv.LabelAnnotator()

            # Annotate image
            annotated_image = bounding_box_annotator.annotate(scene=image, detections=detections)
            annotated_image = label_annotator.annotate(scene=annotated_image, detections=detections)

            # Save annotated image
            output_path = detections_dir / filename
            cv2.imwrite(str(output_path), annotated_image)

            processed += 1
            num_detections = len(detections)
            total_detections += num_detections

            # Show progress more frequently (every image with detections, or every 5 images)
            if num_detections > 0 or processed % 5 == 0:
                msg = f"[{processed}/{len(tile_images)}] {filename}"
                if num_detections > 0:
                    msg += f" - {num_detections} detection(s)"
                logger.info(msg)

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            continue

    logger.info(f"Processed {processed}/{len(tile_images)} images")
    logger.info(f"Total detections: {total_detections}")
    logger.info(f"Saved annotated images to: {detections_dir}")


# ============================================================================
# CLI and Main
# ============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Download satellite imagery and run object detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download tiles only
  python satellite_detection.py --mode download --geojson area.geojson \\
      --output-name "MyProject" --zoom 18

  # Run detection on existing tiles
  python satellite_detection.py --mode detect --output-name "MyProject" \\
      --roboflow-api-key "KEY" --roboflow-model "model/1"

  # Full pipeline
  python satellite_detection.py --geojson area.geojson --output-name "MyProject" \\
      --roboflow-api-key "KEY" --roboflow-model "model/1"
        """
    )

    # Mode selection
    parser.add_argument(
        '--mode',
        choices=['download', 'detect', 'both'],
        default='both',
        help='Execution mode (default: both)'
    )

    # Download arguments
    parser.add_argument(
        '--geojson',
        type=str,
        help='Path to GeoJSON file with polygon bounding boxes (required for download mode)'
    )

    parser.add_argument(
        '--zoom',
        type=int,
        default=18,
        help='Zoom level for tile downloads (default: 18)'
    )

    parser.add_argument(
        '--tile-url',
        type=str,
        default=DEFAULT_TILE_URL,
        help='Tile server URL template (default: ArcGIS World Imagery)'
    )

    # Output arguments
    parser.add_argument(
        '--output-name',
        type=str,
        required=True,
        help='Name of output folder (required)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='Base directory for outputs (default: current directory)'
    )

    # Detection arguments
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.05,
        help='Detection confidence threshold (default: 0.05)'
    )

    parser.add_argument(
        '--roboflow-api-key',
        type=str,
        help='Roboflow API key (required for detection mode)'
    )

    parser.add_argument(
        '--roboflow-project',
        type=str,
        help='Roboflow project identifier (optional)'
    )

    parser.add_argument(
        '--roboflow-model',
        type=str,
        help='Roboflow model identifier, e.g., "model-name/version" (required for detection mode)'
    )

    args = parser.parse_args()

    # Validate required arguments based on mode
    if args.mode in ['download', 'both']:
        if not args.geojson:
            parser.error("--geojson is required for download and both modes")

    validate_detection_args(args)

    return args


def main() -> None:
    """Main entry point."""
    # Configure logging with explicit stdout and force refresh
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout,  # Explicitly use stdout
        force=True  # Override any existing config
    )

    # Configure module logger
    logger.setLevel(logging.INFO)

    # Ensure line buffering for immediate output
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True)

    args = parse_args()

    # Convert output_dir to Path
    output_dir = Path(args.output_dir).resolve()
    project_dir = output_dir / args.output_name
    tiles_dir = project_dir / "tiles"
    detections_dir = project_dir / "detections"

    logger.info("="*60)
    logger.info("SATELLITE IMAGERY DETECTION PIPELINE")
    logger.info("="*60)
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Output directory: {project_dir}")

    # Execute based on mode
    if args.mode in ['download', 'both']:
        tiles_dir = download_tiles_pipeline(
            geojson_path=args.geojson,
            zoom=args.zoom,
            output_dir=output_dir,
            output_name=args.output_name,
            tile_url=args.tile_url
        )

    if args.mode in ['detect', 'both']:
        # Check if tiles directory exists
        if not tiles_dir.exists():
            logger.error(f"Tiles directory not found: {tiles_dir}")
            logger.error("Please run with --mode download first or check --output-name")
            sys.exit(1)

        run_detection_pipeline(
            tiles_dir=tiles_dir,
            detections_dir=detections_dir,
            model_id=args.roboflow_model,
            api_key=args.roboflow_api_key,
            confidence=args.confidence
        )

    logger.info("="*60)
    logger.info("PIPELINE COMPLETE")
    logger.info("="*60)


if __name__ == "__main__":
    main()
