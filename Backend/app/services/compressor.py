import os
from PIL import Image

# Target size in KB — anything above this gets compressed
COMPRESS_THRESHOLD_KB = 500
JPEG_QUALITY_START    = 85
JPEG_QUALITY_MIN      = 40
MAX_DIMENSION         = 2048   # max width or height in pixels


def compress_image(file_path: str) -> str:
    """
    Compress a JPEG or PNG image in-place.
    - Resizes if any dimension exceeds MAX_DIMENSION
    - Reduces JPEG quality progressively until under COMPRESS_THRESHOLD_KB
    - Converts PNG to JPEG for better compression (saves as .jpg)
    - Returns the final file path (may differ if PNG → JPG conversion happened)
    """
    ext = os.path.splitext(file_path)[1].lower()
    size_kb = os.path.getsize(file_path) / 1024

    if size_kb <= COMPRESS_THRESHOLD_KB:
        return file_path  # already small enough, skip

    img = Image.open(file_path)

    # Convert RGBA/P mode to RGB (required for JPEG save)
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    # Resize if too large
    w, h = img.size
    if w > MAX_DIMENSION or h > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    # PNG → convert to JPEG path
    if ext == ".png":
        new_path = file_path.replace(".png", ".jpg")
    else:
        new_path = file_path

    # Progressive quality reduction until under threshold
    quality = JPEG_QUALITY_START
    while quality >= JPEG_QUALITY_MIN:
        img.save(new_path, format="JPEG", quality=quality, optimize=True)
        if os.path.getsize(new_path) / 1024 <= COMPRESS_THRESHOLD_KB:
            break
        quality -= 10

    # If PNG was converted, remove the original .png
    if ext == ".png" and new_path != file_path:
        os.remove(file_path)

    return new_path


def compress_pdf(file_path: str) -> str:
    """
    PDFs are not compressed by Pillow.
    Ghostscript would be needed for PDF compression — skip for now,
    just return the path unchanged.
    Placeholder for future Ghostscript integration.
    """
    return file_path


def compress_file(file_path: str) -> str:
    """
    Entry point — routes to the right compressor based on file extension.
    Returns the (possibly new) file path after compression.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext in (".jpg", ".jpeg", ".png"):
        return compress_image(file_path)
    elif ext == ".pdf":
        return compress_pdf(file_path)
    return file_path  # unknown type, pass through