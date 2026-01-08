# Module 001: Design Document

**Created:** 2026-01-08
**Script:** `001/satellite_detection.py`
**Original Notebook:** `001/001_bulk_img_download_and_detect.ipynb`

## Conversion Context

This document captures the design decisions and conversion process from the Google Colab notebook to the CLI script.

### Conversion Requirements

The user requested conversion of a Colab notebook with these specifications:

1. **Expose as CLI arguments:**
   - Confidence threshold for detection model
   - GeoJSON bounding box input (replacing interactive Leaflet map)
   - Zoom level for image tiling
   - Output folder name (was hardcoded to 'Barcelona Pools')
   - Roboflow API key, project, and model identifiers

2. **Replace Google Drive/Colab dependencies:**
   - Remove `drive.mount()` calls
   - Remove interactive Leaflet map widgets
   - Replace all Google Drive paths with local filesystem paths
   - Make paths relative to script execution directory

3. **Create well-organized structure:**
   - Single entry point with argparse
   - Clean function organization
   - Proper error handling

### Original Notebook Structure

**Key cells and their purpose:**
- Cell 1: Package installation (pip installs)
- Cell 2: Imports
- Cell 3: Google Drive mount (removed)
- Cell 5: Interactive Leaflet map (removed)
- Cell 6: Extract features from interactive map (replaced with GeoJSON file input)
- Cell 8: Constants (TILE_URL, OUTPUT_FILE)
- Cell 10: Utility functions (get_tiles_for_bbox, download_tile, stitch_tiles, create_folder_if_not_exists)
- Cell 12: Load geometries and calculate tiles
- Cell 13: Download and stitch tiles, save metadata
- Cell 15-16: Initialize Roboflow model
- Cell 19: Run detection on tiles

### Architecture Decisions

#### 1. Two-Pipeline Design

**Decision:** Separate download and detection into independent pipelines.

**Rationale:**
- Students may want to download tiles once, then experiment with different detection parameters
- Allows resuming from detection step if download completes but detection fails
- Better separation of concerns (data acquisition vs. inference)
- Enables testing each component independently

**Implementation:**
```python
download_tiles_pipeline(geojson_path, zoom, output_dir, output_name, tile_url) -> Path
run_detection_pipeline(tiles_dir, detections_dir, model_id, api_key, confidence) -> None
```

#### 2. Mode-Based Execution

**Decision:** Add `--mode` argument with choices: download, detect, both.

**Rationale:**
- Maximum flexibility for users
- Supports iterative workflows (download once, detect many times)
- Clear and explicit about what the script will do

**Not chosen alternatives:**
- Separate scripts for download and detection (rejected: increases maintenance burden)
- Always run both pipelines (rejected: inflexible for experimentation)
- Auto-detect what to run based on arguments (rejected: implicit behavior is confusing)

#### 3. Local File Structure

**Decision:** Create `{output_dir}/{output_name}/tiles/` and `{output_dir}/{output_name}/detections/` structure.

**Rationale:**
- Mirrors original notebook's logical separation
- Easy to navigate and understand
- Keeps raw tiles separate from processed results
- Students can easily compare input/output

**File naming:** Preserved original `{x}_{y}_{z}.jpg` format for traceability between tiles and detections.

#### 4. Validation Strategy

**Decision:** Validate GeoJSON upfront with clear error messages.

**Rationale:**
- Fail fast if input is invalid
- Educational context: students need clear feedback on what's wrong
- Prevents wasting time on tile downloads before discovering invalid input

**Validations implemented:**
- File exists
- Valid GeoJSON/JSON syntax
- Contains polygon geometries
- CRS is WGS84 (EPSG:4326)
- At least one feature present

#### 5. Error Handling Philosophy

**Decision:** Continue processing on individual failures, log errors, report summary.

**Rationale:**
- Tile download failures shouldn't stop entire pipeline (network hiccups common)
- Detection failures on individual images shouldn't abort batch
- Users get maximum results even with partial failures
- Summary statistics show overall success rate

**Implementation:**
- Try/except blocks around individual tile downloads
- Try/except blocks around individual image detection
- Progress indicators show success/failure counts
- Final summary reports total successes

### Code Organization

#### Function Categories

**Utility Functions** (from notebook, minimal changes):
- `get_tiles_for_bbox()` - Calculate tiles for bounding box
- `download_tile()` - Fetch single tile from server
- `stitch_tiles()` - Combine 2x2 grid into 512x512 image

**Validation Functions** (new):
- `validate_geojson()` - Load and validate GeoJSON input
- `validate_detection_args()` - Ensure required detection args present

**Pipeline Functions** (refactored from notebook):
- `download_tiles_pipeline()` - Complete download workflow (cells 12-13)
- `run_detection_pipeline()` - Complete detection workflow (cells 15-19)

**CLI Functions** (new):
- `parse_args()` - argparse configuration
- `main()` - Entry point with mode switching

#### Type Hints

Added type hints throughout for:
- Better IDE support
- Documentation
- Catching errors early
- Teaching good Python practices to students

#### Constants

Module-level constants:
- `DEFAULT_TILE_URL` - ArcGIS World Imagery (can be overridden via CLI)
- `TILE_SIZE = 256` - Individual tile size
- `STITCHED_SIZE = 512` - Final stitched image size

### Dependencies

**Kept from notebook:**
- geopandas (geospatial operations)
- mercantile (tile coordinate math)
- requests (tile downloads)
- rasterio (implicit via geopandas)
- pillow (image operations)
- roboflow (model context, optional)
- inference (Roboflow inference SDK)
- supervision (detection visualization)
- opencv-python (image I/O for detection)
- shapely (geometry operations)

**Removed from notebook:**
- leafmap (Colab widget, replaced with GeoJSON input)
- ultralytics (not directly used, inference SDK handles it)

### Testing Considerations

**Manual testing checklist for future modifications:**

1. **Download mode:**
   - Valid GeoJSON with single polygon
   - Valid GeoJSON with multiple polygons
   - Invalid GeoJSON (malformed JSON, wrong geometry type, wrong CRS)
   - Missing GeoJSON file
   - Network failures during download

2. **Detect mode:**
   - Existing tiles directory
   - Missing tiles directory
   - Invalid Roboflow credentials
   - Invalid model ID
   - Images that fail detection

3. **Both mode:**
   - Complete end-to-end pipeline
   - Partial failures in download or detection

4. **CLI:**
   - Missing required arguments
   - Invalid argument combinations
   - Help text display

### Performance Notes

**Current implementation:**
- Sequential tile downloads (simple, but slow)
- Sequential detection (simple, but slow)
- No caching (downloads same tiles if run twice)

**For future optimization:**
- Add concurrent tile downloads with `concurrent.futures.ThreadPoolExecutor`
- Add detection batching if model supports it
- Add tile cache to skip re-downloading existing tiles
- Consider tqdm for better progress bars

### Educational Considerations

**Script design supports course pedagogy:**

1. **Exploration:** Students can easily adjust confidence threshold and compare results
2. **Iteration:** Download once, detect many times with different parameters
3. **Understanding:** Clear separation between data acquisition and ML inference
4. **Debugging:** Detailed progress output helps students understand what's happening
5. **Flexibility:** Can work with any GeoJSON from QGIS or other tools

### Future Module Development

**When creating subsequent modules (002, 003, etc.):**

1. **Similar patterns to follow:**
   - CLI scripts over notebooks when possible
   - Modular pipeline design
   - Clear error messages
   - Local file operations
   - Type hints and docstrings

2. **Potential new modules:**
   - 002: Model training pipeline (Roboflow → ONNX export)
   - 003: Detection result analysis (GeoJSON export, statistics)
   - 004: Multi-source imagery (Sentinel, Planet integration)
   - 005: Time-series analysis (change detection)

3. **Shared utilities:**
   - Consider creating a `common/` directory for shared geospatial utilities
   - Reusable validation functions
   - Standard output formats

### Known Limitations

1. **Tile server:** Only supports single tile URL, hardcoded format
2. **Parallelization:** No concurrent downloads or detection
3. **Caching:** Re-downloads tiles on every run
4. **Detection output:** Only annotated images, no structured data export
5. **Progress indicators:** Basic print statements, no progress bars
6. **Roboflow project:** Project argument not currently used (model ID is sufficient)

### Changelog

**2026-01-08 - Initial conversion:**
- Converted notebook to CLI script
- Added mode-based execution
- Implemented validation
- Added comprehensive documentation

**2026-01-09 - Documentation additions:**
- Added Environment Setup section to CLAUDE.md with conda instructions
- Rewrote 001/README.md as comprehensive student-focused guide with:
  - Step-by-step conda environment setup
  - Detailed GeoJSON creation instructions (QGIS and Colab methods)
  - Exact command to replicate notebook results
  - Explanations of all parameters with typical values
  - Advanced usage patterns (separate download/detect, zoom levels)
  - Extensive troubleshooting section
  - Quick reference table
  - Comparison to notebook workflow

**2026-01-09 - Code improvements (logging):**
- Added proper logging throughout satellite_detection.py
  - Configured logging in main() with timestamps and level indicators
  - Replaced all print() statements with appropriate logger calls
  - INFO level for progress and informational messages
  - WARNING level for non-fatal issues (failed tile downloads, missing images)
  - ERROR level for fatal errors before sys.exit()
- Removed unnecessary import (json was unused)
- Log format: `%(asctime)s - %(levelname)s - %(message)s`

**2026-01-09 - Output visibility improvements:**
- Fixed logging configuration to ensure terminal output:
  - Added explicit `stream=sys.stdout` to logging config
  - Added `force=True` to override any existing logging configs
  - Configured module logger with `logger.setLevel(logging.INFO)`
  - Enabled line buffering with `sys.stdout.reconfigure(line_buffering=True)`
- Progress reporting improvements:
  - Progress updates every 5 tiles/images (was 10)
  - Percentage completion displayed in progress messages
  - Immediate feedback for images with detections
- Output format improvements:
  - Clear section headers with banners
  - Real-time progress: `Progress: 15/153 tiles (9%)`
  - Detection feedback: `[5/20] filename.jpg - 3 detection(s)`
  - Summary statistics at end of each pipeline
- Removed duplicate print statements after verifying logger works correctly

**2026-01-09 - Documentation improvements:**
- Added geojson.io (https://geojson.io/) as primary method for creating GeoJSON files:
  - Updated 001/README.md to include geojson.io as Option A (easiest method)
  - No software installation required, web-based interface
  - Included step-by-step instructions for drawing polygons
  - Reordered options: geojson.io → QGIS → Colab notebook
- Updated CLAUDE.md to mention geojson.io in student workflow
