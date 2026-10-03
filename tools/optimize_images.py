#!/usr/bin/env python3
"""Compress the self-hosted product images to WebP and point Firestore at them.

Product cards render at a few hundred pixels, so full-resolution PNGs (some over
1.9 MB) are wasted bytes on every first paint. Images are resized to fit
MAX_SIZE and re-encoded as WebP; the original files are removed once the new
path is stored in Firestore.

Usage: python3 tools/optimize_images.py
"""
import glob
import json
import os
import sys

from PIL import Image

from add_products_to_firestore import BASE, firestore_get, panel_credentials, sign_in, update_doc

DEST_DIR = "assets/images/products"
MAX_SIZE = (900, 900)
QUALITY = 82


def main():
    email, password, api_key = panel_credentials()
    token = sign_in(api_key, email, password)

    docs = firestore_get(f"{BASE}/products?pageSize=400", token).get("documents", [])
    old_to_new = {}
    before = after = 0

    for path in sorted(glob.glob(f"{DEST_DIR}/*.png") + glob.glob(f"{DEST_DIR}/*.jpg")):
        before += os.path.getsize(path)
        dest = os.path.splitext(path)[0] + ".webp"
        with Image.open(path) as im:
            im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
            im.thumbnail(MAX_SIZE, Image.LANCZOS)
            im.save(dest, "WEBP", quality=QUALITY, method=6)
        after += os.path.getsize(dest)
        old_to_new["/" + path] = "/" + dest
        os.remove(path)

    for d in docs:
        old = d["fields"].get("img", {}).get("stringValue", "")
        if old in old_to_new:
            update_doc(d["name"].rsplit("/", 1)[-1], {"img": old_to_new[old]}, token)

    print(f"{len(old_to_new)} images -> WebP  {before/1024/1024:.1f} MB -> {after/1024/1024:.1f} MB "
          f"({100 - after * 100 / before:.0f}% smaller)")


if __name__ == "__main__":
    main()
