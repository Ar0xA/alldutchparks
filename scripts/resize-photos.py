#!/usr/bin/env python3
"""Shrinks source photos under assets/images/ in place before Hugo builds them.

Camera photos land here at full resolution (4000px+, several MB each) and get
committed to git as-is under assets/. Hugo's own image pipeline (see
layouts/partials/activation-images.html) only shrinks the *published* copy —
the originals in the repo stay huge. This brings the originals down to
roughly what Hugo actually serves, so the repo doesn't carry full-res camera
dumps for photos nobody ever sees at full size.

Also strips EXIF unconditionally, even on photos that are already small
enough to skip resizing — phone photos routinely embed GPS coordinates,
which have no business ending up in a public git repo.

Idempotent: a photo that's already <= MAX_WIDTH and has no EXIF left is
skipped entirely (no repeated lossy re-encoding on every run).
"""
import sys
from pathlib import Path

MAX_WIDTH = 2000
RESIZE_QUALITY = 82
STRIP_ONLY_QUALITY = 95  # higher quality when we're only stripping EXIF, not resizing
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "images"
EXTENSIONS = {".jpg", ".jpeg", ".png"}

try:
    from PIL import Image, ImageOps
except ImportError:
    print("resize-photos: Pillow not installed, skipping (pip install pillow)", file=sys.stderr)
    sys.exit(0)

if not ASSETS_DIR.is_dir():
    sys.exit(0)

for path in sorted(ASSETS_DIR.rglob("*")):
    if path.suffix.lower() not in EXTENSIONS:
        continue

    with Image.open(path) as img:
        has_exif = bool(img.info.get("exif"))
        needs_resize = img.width > MAX_WIDTH

        if not has_exif and not needs_resize:
            continue

        # Bake in EXIF rotation before dropping the rest of the EXIF block
        # (orientation tag would otherwise be lost, flipping the photo).
        img = ImageOps.exif_transpose(img)

        if needs_resize:
            height = round(img.height * (MAX_WIDTH / img.width))
            img = img.resize((MAX_WIDTH, height), Image.LANCZOS)
            quality = RESIZE_QUALITY
        else:
            quality = STRIP_ONLY_QUALITY

        original_size = path.stat().st_size
        if path.suffix.lower() == ".png":
            img.save(path, optimize=True)
        else:
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(path, quality=quality, optimize=True)

        new_size = path.stat().st_size
        action = "resized" if needs_resize else "stripped EXIF from"
        print(f"{action} {path.relative_to(ASSETS_DIR.parent.parent)}: "
              f"{original_size // 1024}KB -> {new_size // 1024}KB")
