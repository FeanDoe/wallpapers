#!/usr/bin/env python3
"""Genera _site/ con las imágenes de wallpapers/ en la raíz y un wallpapers.json
compatible con la fuente "Generic JSON" de RandomWallpaperGnome3."""
import json
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

from exif import clean_dir

BASE_URL = os.environ.get("BASE_URL", "https://wallpapers.tugurio.cl").rstrip("/")
SRC = Path(__file__).parent / "wallpapers"
OUT = Path(__file__).parent / "_site"
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".bmp", ".gif"}


def main():
    images = sorted(p for p in SRC.iterdir() if p.is_file() and p.suffix.lower() in EXTS)
    if not images:
        sys.exit(f"No hay imágenes en {SRC}")
    dirty = clean_dir(SRC, write=False)
    if dirty:
        sys.exit("Imágenes con metadata (corre `python3 exif.py` antes de hacer commit):\n"
                 + "\n".join(f"  {p.name}" for p in dirty))

    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    for img in images:
        shutil.copy2(img, OUT / img.name)

    data = [{"url": f"{BASE_URL}/{quote(img.name)}"} for img in images]
    (OUT / "wallpapers.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    shutil.copy2(Path(__file__).parent / "index.html", OUT / "index.html")
    (OUT / "CNAME").write_text("wallpapers.tugurio.cl\n")
    (OUT / ".nojekyll").touch()
    print(f"{len(images)} wallpapers -> {OUT / 'wallpapers.json'}")


if __name__ == "__main__":
    main()
