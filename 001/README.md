# Module 001: Satellite Imagery Download and Detection

This module downloads satellite imagery tiles for a specified area and runs object detection to identify features (e.g., swimming pools). This script replicates the workflow from the Google Colab notebook `001_bulk_img_download_and_detect.ipynb`.

---

## Step 1: Create Your Conda Environment

Open your terminal and run these commands:

```bash
# Navigate to the 001 folder
cd 001

# Create a new conda environment named "iaac-001" with Python 3.10
conda create -n iaac-001 python=3.10 -y

# Activate the environment
conda activate iaac-001

# Install all required packages
pip install -r requirements.txt
```

**Verify your installation:**
```bash
python -c "import geopandas, mercantile, cv2; print('✓ Environment ready!')"
```

If you see "✓ Environment ready!", you're all set!

**Important:** You must activate this environment every time you want to run the script:
```bash
conda activate iaac-001
```

---

## Step 2: Prepare Your GeoJSON File

You need a GeoJSON file containing polygon(s) that define your area of interest.

### Option A: Use geojson.io (Easiest - No Software Required)

1. Go to **https://geojson.io/**
2. In the map view, use the drawing tools on the right side:
   - Click the **polygon tool** (rectangle icon)
   - Click on the map to draw your area of interest
   - Close the polygon by clicking on the first point
3. The GeoJSON will automatically appear in the right panel
4. Click **Save** → **GeoJSON** to download as `map.geojson`
5. Rename the file to something descriptive (e.g., `barcelona_area.geojson`)

**Tip:** Use the search box to find your location, then draw your polygon. You can draw multiple polygons if needed.

### Option B: Export from QGIS

1. Open QGIS
2. Create a new temporary scratch layer: **Layer → Create Layer → New Temporary Scratch Layer**
   - Geometry type: **Polygon**
   - CRS: **EPSG:4326 - WGS 84**
3. Enable editing and draw your polygon(s) over your area of interest
4. Save the layer: **Right-click layer → Export → Save Features As...**
   - Format: **GeoJSON**
   - CRS: **EPSG:4326 - WGS 84**
   - Save as: `my_area.geojson`

### Option C: Use the Interactive Map (Colab Notebook)

If you prefer the interactive Leaflet map from the original notebook:
1. Open `001_bulk_img_download_and_detect.ipynb` in Google Colab
2. Run cells 1-6 to draw your polygon on the interactive map
3. The drawn features will be saved as `interactive_geojson_data`
4. Export by adding a cell:
   ```python
   import json
   with open('my_area.geojson', 'w') as f:
       json.dump({"type": "FeatureCollection", "features": interactive_geojson_data}, f)
   from google.colab import files
   files.download('my_area.geojson')
   ```

**Important:** Your GeoJSON must use **EPSG:4326** (latitude/longitude) coordinates.

---

## Step 3: Get Your Roboflow API Key and Model

You'll need:
1. **Roboflow API Key**: Get this from your [Roboflow account settings](https://app.roboflow.com/settings/api)
2. **Model ID**: Format is `project-name/version`, for example: `swimming-pools-for-workshop/1`

---

## Step 4: Run the Script

### Replicating the Notebook Results

To get the **exact same results as the notebook**, use these parameters:

```bash
python satellite_detection.py \
  --geojson my_area.geojson \
  --output-name "Barcelona_Pools" \
  --zoom 18 \
  --roboflow-api-key "YOUR_API_KEY_HERE" \
  --roboflow-model "swimming-pools-for-workshop/1" \
  --confidence 0.05
```

**Replace:**
- `my_area.geojson` with the path to your GeoJSON file
- `YOUR_API_KEY_HERE` with your actual Roboflow API key

This will:
1. ✓ Download satellite tiles at zoom level 18 (same as notebook)
2. ✓ Stitch tiles into 512×512 pixel images
3. ✓ Run detection with 0.05 confidence threshold (same as notebook)
4. ✓ Save results in a `Barcelona_Pools` folder

### Understanding the Parameters

- `--geojson my_area.geojson` - Your area of interest (replaces the interactive map)
- `--output-name "Barcelona_Pools"` - Name of the output folder
- `--zoom 18` - Tile zoom level (18 = ~0.6m per pixel, good for detecting pools)
- `--roboflow-model "swimming-pools-for-workshop/1"` - The detection model to use
- `--confidence 0.05` - Minimum confidence score (0.05 = 5% confidence)

---

## Step 5: View Your Results

After the script completes, you'll find your results in:

```
Barcelona_Pools/
├── tiles/
│   ├── 1234_5678_18.jpg         # Downloaded satellite images (512×512 pixels)
│   ├── 1235_5678_18.jpg
│   ├── ...
│   └── tile_metadata.geojson    # Geographic coordinates for each tile
└── detections/
    ├── 1234_5678_18.jpg         # Annotated images with detection boxes
    ├── 1235_5678_18.jpg
    └── ...
```

**To view results:**
- Open images in `detections/` folder to see detected objects with bounding boxes
- Load `tile_metadata.geojson` in QGIS to see tiles on a map

---

## Advanced Usage

### Run Download and Detection Separately

**Step 1: Download tiles only (faster iteration)**
```bash
python satellite_detection.py \
  --mode download \
  --geojson my_area.geojson \
  --output-name "Barcelona_Pools" \
  --zoom 18
```

**Step 2: Run detection with different confidence levels**
```bash
# Try low confidence (finds more objects, more false positives)
python satellite_detection.py \
  --mode detect \
  --output-name "Barcelona_Pools" \
  --roboflow-api-key "YOUR_API_KEY" \
  --roboflow-model "swimming-pools-for-workshop/1" \
  --confidence 0.02

# Try high confidence (finds fewer objects, higher precision)
python satellite_detection.py \
  --mode detect \
  --output-name "Barcelona_Pools" \
  --roboflow-api-key "YOUR_API_KEY" \
  --roboflow-model "swimming-pools-for-workshop/1" \
  --confidence 0.15
```

**Why separate them?** You download tiles once (can take 10+ minutes for large areas), then experiment with different detection settings without re-downloading.

### Change Zoom Level

Different zoom levels provide different levels of detail:

- `--zoom 16` - ~2.4m per pixel (faster downloads, less detail)
- `--zoom 17` - ~1.2m per pixel (balanced)
- `--zoom 18` - ~0.6m per pixel (recommended for pools, default)
- `--zoom 19` - ~0.3m per pixel (very detailed, slower downloads)

**Example:**
```bash
python satellite_detection.py \
  --geojson my_area.geojson \
  --output-name "High_Detail_Pools" \
  --zoom 19 \
  --roboflow-api-key "YOUR_API_KEY" \
  --roboflow-model "swimming-pools-for-workshop/1"
```

### Use Different Models

If you've trained your own Roboflow model or want to detect different objects:

```bash
python satellite_detection.py \
  --geojson my_area.geojson \
  --output-name "Tennis_Courts" \
  --zoom 18 \
  --roboflow-api-key "YOUR_API_KEY" \
  --roboflow-model "tennis-courts-detector/2"
```

---

## Troubleshooting

### "conda: command not found"

You need to install Anaconda or Miniconda first:
- Download from: https://docs.conda.io/en/latest/miniconda.html
- Follow installation instructions for your operating system
- Restart your terminal after installation

### "No module named 'geopandas'" or import errors

Make sure you activated the conda environment:
```bash
conda activate iaac-001
```

You should see `(iaac-001)` at the start of your terminal prompt.

### "Error: GeoJSON file not found"

Check that:
1. Your GeoJSON file exists in the current directory
2. The filename is correct (case-sensitive)
3. You're running the script from the right folder

Try using an absolute path:
```bash
python satellite_detection.py \
  --geojson /full/path/to/my_area.geojson \
  --output-name "MyProject" \
  ...
```

### "Error: --roboflow-api-key is required for detection mode"

You need to provide your Roboflow API key. Get it from:
https://app.roboflow.com/settings/api

### Downloads are very slow

This is normal! Downloading satellite imagery can take time:
- ~150 tiles = 5-10 minutes
- ~500 tiles = 20-30 minutes

The script shows progress as it downloads. You can:
1. Reduce the area size in your GeoJSON
2. Use a lower zoom level (e.g., `--zoom 17` instead of `18`)
3. Run in `--mode download` first, then `--mode detect` later

### Detection finds nothing or too many false positives

Adjust the confidence threshold:
- **Too many false positives?** Increase confidence: `--confidence 0.1` or `0.15`
- **Missing objects?** Decrease confidence: `--confidence 0.02` or `0.03`

Experiment with different values between 0.01 and 0.5.

### "Error: Failed to load Roboflow model"

Check:
1. Your API key is correct (no extra spaces)
2. Model ID format is correct: `"project-name/version"` (e.g., `"swimming-pools-for-workshop/1"`)
3. You have access to this model in your Roboflow account

---

## Quick Reference

### Full Command (All Options)

```bash
python satellite_detection.py \
  --mode both \
  --geojson my_area.geojson \
  --output-name "MyProject" \
  --output-dir . \
  --zoom 18 \
  --confidence 0.05 \
  --roboflow-api-key "YOUR_KEY" \
  --roboflow-model "model-name/version" \
  --tile-url "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
```

### Get Help

```bash
python satellite_detection.py --help
```

### Common Values

| Parameter | Typical Values | Default |
|-----------|---------------|---------|
| `--zoom` | 16, 17, 18, 19 | 18 |
| `--confidence` | 0.02 to 0.2 | 0.05 |
| `--mode` | download, detect, both | both |

---

## Differences from the Notebook

This script does the **same thing** as the notebook, but:

✓ **Runs locally** (no Google Colab needed)
✓ **Uses a GeoJSON file** instead of interactive map
✓ **More flexible** (can run download and detection separately)
✓ **Better error handling** (continues if individual tiles fail)
✓ **Portable** (works on any computer with Python)

The **algorithms and results are identical** to the notebook.

---

## Need More Help?

- **Script documentation**: Run `python satellite_detection.py --help`
- **Technical details**: See main repository `CLAUDE.md`
- **Design decisions**: See `.claude/module_001_design.md`
- **Notebook reference**: Open `001_bulk_img_download_and_detect.ipynb`

---

## Files in This Module

- `satellite_detection.py` - Main script (run this!)
- `001_bulk_img_download_and_detect.ipynb` - Original Colab notebook
- `requirements.txt` - Python dependencies
- `README.md` - This guide
