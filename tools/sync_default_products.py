#!/usr/bin/env python3
"""Regenerate the `defaultProducts` arrays inside the HTML pages from the live
Firestore catalog, so a first visit renders the full catalog instantly from the
bundled copy instead of waiting for the network.

Usage: python3 tools/sync_default_products.py
"""
import json
import re
import urllib.request

from add_products_to_firestore import BASE

PAGES = ["index.html", "creatprogect.html"]
PATTERN = re.compile(r"(const defaultProducts = \[)(.*?)(\n\s*\];)", re.S)


def fetch_products():
    docs = json.loads(urllib.request.urlopen(
        f"{BASE}/products?pageSize=400", timeout=40).read()).get("documents", [])
    rows = []
    for d in docs:
        f = d["fields"]
        rows.append((
            int(f.get("order", {}).get("integerValue", 0)),
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
    for _, name, desc, price, img in rows:
        lines.append(
            f"            {{ name: {js(name)}, desc: {js(desc)}, price: {js(price)}, img: {js(img)} }}"
        )
    return ",\n".join(lines)


def main():
    rows = fetch_products()
    block = render(rows)
    for page in PAGES:
        with open(page, encoding="utf-8") as f:
            src = f.read()
        new, n = PATTERN.subn(lambda m: m.group(1) + "\n" + block + m.group(3), src, count=1)
        if not n:
            print(f"  ! defaultProducts not found in {page}")
            continue
        with open(page, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"  {page}: defaultProducts synced with {len(rows)} products")


if __name__ == "__main__":
    main()
