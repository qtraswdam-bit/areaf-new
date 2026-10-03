#!/usr/bin/env python3
"""Rewrite product `img` fields from remote URLs to the self-hosted local paths
recorded in image-url-map.json.

Usage: python3 tools/localize_images.py chicken-products.json
"""
import json
import sys


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "chicken-products.json"
    with open("image-url-map.json", encoding="utf-8") as f:
        mapping = json.load(f)
    with open(src, encoding="utf-8") as f:
        products = json.load(f)

    changed = 0
    for p in products:
        url = p.get("img") or p.get("image") or p.get("image_url")
        if url in mapping:
            p["img"] = mapping[url]
            changed += 1
    missing = [p["name"] for p in products if not str(p.get("img", "")).startswith("/")]

    with open(src, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"localized {changed}/{len(products)} images in {src}")
    if missing:
        print("still remote:", missing)


if __name__ == "__main__":
    main()
