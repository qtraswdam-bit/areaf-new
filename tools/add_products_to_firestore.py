#!/usr/bin/env python3
"""Add converted products to the site's live Firestore `products` collection.

Existing documents are never modified or deleted: new products are appended at
the end of the `order` sequence. Prints the created document ids so the import
can be rolled back with tools/remove_products_from_firestore.py.

Usage: python3 tools/add_products_to_firestore.py products-import.json
"""
import json
import random
import string
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

PROJECT = "kuwait-me"
BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"
CLIENT_JS = "assets/js/firebase-client.js"

ALPHABET = string.ascii_letters + string.digits


def panel_credentials():
    """Read the panel account the site itself uses (firebase-client.js)."""
    with open(CLIENT_JS, encoding="utf-8") as f:
        src = f.read()
    email = src.split("PANEL_EMAIL = '", 1)[1].split("'", 1)[0]
    password = src.split("PANEL_PASSWORD = '", 1)[1].split("'", 1)[0]
    api_key = src.split('apiKey: "', 1)[1].split('"', 1)[0]
    return email, password, api_key


def request(method, url, payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")


def post(url, payload, token=None):
    return request("POST", url, payload, token)


def patch(url, payload, token=None):
    return request("PATCH", url, payload, token)


def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"{}")


def firestore_get(url, token):
    return get(url, token)


def update_doc(doc_id, fields, token):
    """Patch a single document, touching only the given fields.

    Values are encoded by Python type: int -> integerValue, str -> stringValue.
    """
    def encode(v):
        if isinstance(v, bool):
            return {"booleanValue": v}
        if isinstance(v, int):
            return {"integerValue": str(v)}
        return {"stringValue": v}

    mask = "&".join(f"updateMask.fieldPaths={k}" for k in fields)
    return patch(f"{BASE}/products/{doc_id}?{mask}",
                 {"fields": {k: encode(v) for k, v in fields.items()}}, token)


def sign_in(api_key, email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    res = post(url, {"email": email, "password": password, "returnSecureToken": True})
    return res["idToken"]


def new_doc_id():
    return "".join(random.choice(ALPHABET) for _ in range(20))


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "products-import.json"
    with open(src, encoding="utf-8") as f:
        products = json.load(f)

    email, password, api_key = panel_credentials()
    token = sign_in(api_key, email, password)

    existing = get(f"{BASE}/products?pageSize=300", token).get("documents", [])
    next_order = max(
        (int(d["fields"].get("order", {}).get("integerValue", 0)) for d in existing),
        default=-1,
    ) + 1
    print(f"existing products: {len(existing)} — appending from order {next_order}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    created = []
    writes = []
    for i, p in enumerate(products):
        doc_id = new_doc_id()
        created.append(doc_id)
        writes.append({
            "update": {
                "name": f"projects/{PROJECT}/databases/(default)/documents/products/{doc_id}",
                "fields": {
                    "name": {"stringValue": p["name"]},
                    "desc": {"stringValue": p["desc"]},
                    "price": {"stringValue": p["price"]},
                    "img": {"stringValue": p["img"]},
                    "order": {"integerValue": str(next_order + i)},
                    "createdAt": {"timestampValue": now},
                    "updatedAt": {"timestampValue": now},
                },
            }
        })

    post(f"{BASE}:commit", {"writes": writes}, token)
    print(f"created {len(created)} documents")
    with open("firestore-import-result.json", "w", encoding="utf-8") as f:
        json.dump({"createdIds": created, "startOrder": next_order}, f, indent=2)
        f.write("\n")
    print("created ids saved to firestore-import-result.json")


if __name__ == "__main__":
    main()
