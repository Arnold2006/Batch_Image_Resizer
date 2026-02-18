# Image Resizer

A 1-click Pinokio launcher for [Image Resizer](https://github.com/Arnold2006/Image_Resizer) — a Python desktop GUI application that batch-resizes images to a target size on the longest side while preserving aspect ratio.

## What the App Does

Image Resizer lets you select multiple images at once and resize them all to a chosen width/height (512, 768, or 1024 pixels on the longest side). It uses Lanczos resampling for high quality output and saves results to a folder of your choice without modifying the originals.

**Supported formats:** JPG, JPEG, PNG, BMP, GIF, TIFF, WebP

## How to Use

### Installation
1. Install [Pinokio](https://pinokio.computer/) if you haven't already.
2. In Pinokio, click **Download** and paste this repository URL.
3. Click **Install** — this clones the app and sets up the Python environment automatically.

### Running
1. Click **Start** in the Pinokio sidebar. A desktop window will open.
2. Select your target size (512, 768, or 1024 px) from the dropdown.
3. Click **Select Images** and pick the files you want to resize.
4. Choose an output folder.
5. The app processes your images and shows a live status log with progress.

### Output
- Resized files are saved as `<original_name>_resized.<ext>` in the chosen folder.
- Original files are never modified.

### Example
| Original | Target | Output |
|---|---|---|
| 1920 × 1080 | 1024 px | 1024 × 576 |
| 800 × 1200 | 1024 px | 683 × 1024 |
| 512 × 512 | 768 px | 768 × 768 |

## Launcher File Overview

| File | Purpose |
|---|---|
| `install.js` | Clones the app repo and installs Pillow into a venv |
| `start.js` | Launches `app.py` inside the venv |
| `update.js` | Pulls the latest changes for both launcher and app |
| `reset.js` | Deletes the `app/` folder to restore a clean state |
| `link.js` | Deduplicates library files to save disk space |
| `pinokio.js` | Builds the dynamic Pinokio sidebar UI |
| `pinokio.json` | App metadata (title, description, icon) |

## API / Programmatic Access

This app is a local desktop GUI (tkinter) and does not expose an HTTP server or API endpoints. To batch-resize images programmatically using the same logic, you can call the core resize function directly:

### Python

```python
from PIL import Image
import os

def resize_image(input_path, output_path, target_size=1024):
    img = Image.open(input_path)
    w, h = img.size
    if w > h:
        new_w, new_h = target_size, int(h * target_size / w)
    else:
        new_h, new_w = target_size, int(w * target_size / h)
    img.resize((new_w, new_h), Image.Resampling.LANCZOS).save(output_path, quality=95, optimize=True)

# Example
resize_image("photo.jpg", "photo_resized.jpg", target_size=1024)
```

### Command Line (using the same venv)

```bash
# Activate the venv created by the installer (adjust path as needed)
source app/env/bin/activate   # Linux / macOS
app\env\Scripts\activate      # Windows

python - <<'EOF'
from PIL import Image
img = Image.open("input.jpg")
w, h = img.size
scale = 1024 / max(w, h)
img.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS).save("output.jpg", quality=95)
EOF
```

## Requirements

- Python 3.7+
- [Pillow](https://python-pillow.org/) (installed automatically by the launcher)

## License

MIT — see the [upstream repository](https://github.com/Arnold2006/Image_Resizer) for details.
