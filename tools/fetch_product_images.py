#!/usr/bin/env python3
"""Download remote product images into the site so they are self-hosted.

Each image is saved under assets/images/products/<sha1>.<ext>, keyed by the
source URL so re-runs are idempotent. The matching Firestore `img` field is
rewritten to the local path, which means customer pages never call the source
host again.

Usage: python3 tools/fetch_product_images.py chicken-products-source.json
"""
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

from add_products_to_firestore import BASE, firestore_get, panel_credentials, sign_in, update_doc

DEST_DIR = "assets/images/products"
MAGIC = {b"\xff\xd8\xff": ".jpg", b"\x89PNG": ".png", b"\x47\x49\x46": ".gif", b"RIFF": ".webp"}
UA = {"User-Agent": "Mozilla/5.0"}


def image_ext(data):
    for magic, ext in MAGIC.items():
        if data.startswith(magic):
            return ext
    return None


def download(url):
    """Return (bytes, extension) or raise with a readable message."""
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 540:
            sys.exit("Source project is PAUSED (HTTP 540). Unpause it and re-run.")
        raise RuntimeError(f"HTTP {e.code} for {url}")
    ext = image_ext(data)
    if not ext:
        raise RuntimeError(f"not an image ({data[:60]!r}) for {url}")
    return data, ext


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "products-import.json"
    with open(src, encoding="utf-8") as f:
        products = json.load(f)

    email, password, api_key = panel_credentials()
    token = sign_in(api_key, email, password)

    docs = firestore_get(f"{BASE}/products?pageSize=400", token).get("documents", [])
    by_img = {}
    for d in docs:
        key = d["fields"].get("img", {}).get("stringValue", "")
        by_img.setdefault(key, []).append(d["name"].rsplit("/", 1)[-1])

    os.makedirs(DEST_DIR, exist_ok=True)
    mapping, total = {}, 0
    for p in products:
        url = p.get("img") or p.get("image") or p.get("image_url")
        if url.startswith("/") or url.startswith("assets/"):
            continue  # already local
        if url in mapping:
            continue
        data, ext = download(url)
        dest = f"{DEST_DIR}/{hashlib.sha1(url.encode()).hexdigest()[:16]}{ext}"
        with open(dest, "wb") as f:
            f.write(data)
        mapping[url] = "/" + dest
        total += len(data)
        print(f"  {len(data):>9,} B  {dest}")

        for doc_id in by_img.get(url, []):
            update_doc(doc_id, {"img": mapping[url]}, token)
            print(f"             -> Firestore {doc_id} img updated")

    with open("image-url-map.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\n{len(mapping)} images saved to {DEST_DIR} ({total/1024/1024:.1f} MB) — map in image-url-map.json")


if __name__ == "__main__":
    main()
