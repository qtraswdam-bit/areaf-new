#!/usr/bin/env python3
"""Give the remaining duplicate product names distinct, customer-readable titles.

The cart keys line items by `name` only (assets/js/cart.js), so two products
sharing a name collapse into a single line with mixed prices. The pairs below
differ only by size/grade, which the name did not say — folding the
distinguishing attribute into the title fixes the cart and reads better.

Usage: python3 tools/dedupe_product_names.py
"""
from add_products_to_firestore import BASE, firestore_get, panel_credentials, sign_in, update_doc

RENAMES = {
    "loesbyo7vHo9InRezI1g": "عسل السدر الكويتي المميز 500 غرام",
    "flkFwemf1bycshXSv2AJ": "عسل السدر الكويتي المميز 250 غرام",
    "xIKpzPzXEb4vyqb56tkq": "حمام زاجل - بوكس 20 حمامة",
    "p9mSIOsF32G0cilWQnvt": "حمام زاجل - بوكس 10 حمامات",
    "hL12T9KFTb15dqYivRLk": "عرض ربيان 10 كيلو - حجم متوسط",
    "NevFP4IX6CIN7N85sGhz": "عرض ربيان 10 كيلو - حجم كبير",
}


def main():
    email, password, api_key = panel_credentials()
    token = sign_in(api_key, email, password)
    docs = {d["name"].rsplit("/", 1)[-1] for d in
            firestore_get(f"{BASE}/products?pageSize=400", token).get("documents", [])}

    missing = [i for i in RENAMES if i not in docs]
    if missing:
        raise SystemExit(f"unknown document ids: {missing}")

    for doc_id, name in RENAMES.items():
        update_doc(doc_id, {"name": name}, token)
        print(f"  {doc_id} -> {name}")
    print(f"renamed {len(RENAMES)} products")


if __name__ == "__main__":
    main()
