#!/usr/bin/env python3
"""Move base64 data-URI images out of Firestore and into real files.

Products created through the admin form store their image inline as
`data:image/...;base64,...`. That bloats every page that embeds the catalog
(the homepage reached 1.4 MB). Each payload is decoded, compressed to WebP under
assets/images/products/, and the Firestore field is repointed at the file.

Usage: python3 tools/externalize_inline_images.py
"""
import base64
import hashlib
import io
import os

from PIL import Image

from add_products_to_firestore import BASE, firestore_get, panel_credentials, sign_in, update_doc

DEST_DIR = "assets/images/products"
MAX_SIZE = (900, 900)
QUALITY = 82


def main():
    email, password, api_key = panel_credentials()
    token = sign_in(api_key, email, password)
    docs = firestore_get(f"{BASE}/products?pageSize=400", token).get("documents", [])

    os.makedirs(DEST_DIR, exist_ok=True)
    count = 0
    for d in docs:
        img = d["fields"].get("img", {}).get("stringValue", "")
        if not img.startswith("data:image"):
            continue
        raw = base64.b64decode(img.split(",", 1)[1])
        dest = f"{DEST_DIR}/{hashlib.sha1(raw).hexdigest()[:16]}.webp"
        with Image.open(io.BytesIO(raw)) as im:
            im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
            im.thumbnail(MAX_SIZE, Image.LANCZOS)
            im.save(dest, "WEBP", quality=QUALITY, method=6)
        update_doc(d["name"].rsplit("/", 1)[-1], {"img": "/" + dest}, token)
        count += 1
        print(f"  {len(img)/1024/1024:.1f} MB inline -> /{dest}")

    print(f"externalized {count} inline images")


if __name__ == "__main__":
    main()
