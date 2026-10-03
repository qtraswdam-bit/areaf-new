#!/usr/bin/env python3
"""Build the single dynamic product page served for every /product/<id>/<slug> URL.

The page reads the product id from the path and resolves it against Firestore,
falling back to the bundled catalog for an instant first paint. The catalog is
injected with `_id` so the page can match products and build related links.

Usage: python3 tools/build_product_page.py
"""
import json
import os
import urllib.request

from add_products_to_firestore import BASE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "tools", "product-page.template.html")
OUTPUT = os.path.join(ROOT, "product", "index.html")
MARKER = "/*__PRODUCTS__*/"


def fetch_products():
    docs = json.loads(urllib.request.urlopen(
        f"{BASE}/products?pageSize=400", timeout=40).read()).get("documents", [])
    rows = []
    for d in docs:
        f = d["fields"]
        rows.append((
            int(f.get("order", {}).get("integerValue", 0)),
            d["name"].rsplit("/", 1)[-1],
            f.get("name", {}).get("stringValue", ""),
            f.get("desc", {}).get("stringValue", ""),
            f.get("price", {}).get("stringValue", ""),
            f.get("img", {}).get("stringValue", ""),
        ))
    rows.sort()
    return rows


def js(value):
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def render(rows):
    lines = []
    for _, doc_id, name, desc, price, img in rows:
        lines.append(
            f"    {{ _id: {js(doc_id)}, name: {js(name)}, desc: {js(desc)}, "
            f"price: {js(price)}, img: {js(img)} }}"
        )
    return ",\n".join(lines)


def main():
    rows = fetch_products()
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()
    if MARKER not in html:
        raise SystemExit(f"marker {MARKER} not found in template")

    html = html.replace(MARKER, render(rows))
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  product/index.html built with {len(rows)} products ({len(html)} bytes)")


if __name__ == "__main__":
    main()
