#!/usr/bin/env python3
"""Convert a Supabase products export (id/title/description/image_url/price/active)
into the site's product JSON format (name/desc/price/img), matching the schema
used by assets/js/products-store.js and the defaultProducts arrays.

Usage: python3 tools/convert-products.py supabase-export.json products-import.json
"""
import json
import sys


def convert(rows):
    """Accepts either a Supabase lamb export (title/description/image_url/price/active)
    or a Mazzraty catalog export (title/description/image/price)."""
    products = []
    for r in rows:
        if not r.get("active", True):
            continue
        image = r.get("image_url") or r.get("image")
        if not image:
            print(f"skip (no image): id={r.get('id')} {r.get('title')}", file=sys.stderr)
            continue
        products.append({
            "name": r["title"],
            "desc": r.get("description") or "",
            "price": f"{float(r.get('price') or 0):.3f}",
            "img": image,
        })
    return products


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "supabase-export.json"
    dst = sys.argv[2] if len(sys.argv) > 2 else "products-import.json"
    with open(src, encoding="utf-8") as f:
        rows = json.load(f)
    products = convert(rows)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{len(products)} products -> {dst}")


if __name__ == "__main__":
    main()
