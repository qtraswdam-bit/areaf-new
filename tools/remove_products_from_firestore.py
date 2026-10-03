#!/usr/bin/env python3
"""Roll back an import made by tools/add_products_to_firestore.py.

Deletes only the document ids recorded in firestore-import-result.json, so
pre-existing products are never touched.

Usage: python3 tools/remove_products_from_firestore.py firestore-import-result.json
"""
import json
import sys
import urllib.request

PROJECT = "kuwait-me"
BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"
CLIENT_JS = "assets/js/firebase-client.js"


def panel_credentials():
    with open(CLIENT_JS, encoding="utf-8") as f:
        src = f.read()
    email = src.split("PANEL_EMAIL = '", 1)[1].split("'", 1)[0]
    password = src.split("PANEL_PASSWORD = '", 1)[1].split("'", 1)[0]
    api_key = src.split('apiKey: "', 1)[1].split('"', 1)[0]
    return email, password, api_key


def post(url, payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"{}")


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "firestore-import-result.json"
    with open(src, encoding="utf-8") as f:
        ids = json.load(f)["createdIds"]

    email, password, api_key = panel_credentials()
    token = post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
        {"email": email, "password": password, "returnSecureToken": True},
    )["idToken"]

    post(f"{BASE}:commit", {"writes": [
        {"delete": f"projects/{PROJECT}/databases/(default)/documents/products/{i}"}
        for i in ids
    ]}, token)
    print(f"deleted {len(ids)} imported documents")


if __name__ == "__main__":
    main()
