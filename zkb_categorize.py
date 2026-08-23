#!/usr/bin/env python3
"""Bulk-assign Sure categories to ZKB transactions imported today.

After publishing a TransactionImport, the CSV category column is ignored by
Sure (only dates/amounts/names stick). This patches each imported txn's
category from the transformed .sure.csv, matching on (date, signed amount).

Run with the actualiss venv python:
  actualiss/.venv/bin/python zkb_categorize.py <file.sure.csv> [--since YYYY-MM-DD]
"""
import argparse
import csv
import os
import sys
import urllib.request
import json

SURE_URL = os.environ.get("SURE_URL", "http://localhost:3000")
SURE_API_KEY = os.environ.get("MCP_SURE_API_KEY")
ZKB_ACCOUNT_ID = "baa23a18-2f91-47b7-944c-98da82a1db2d"


def get_categories():
    req = urllib.request.Request(f"{SURE_URL}/api/v1/categories",
                                 headers={"X-Api-Key": SURE_API_KEY})
    data = json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
    cats = data.get("categories", data if isinstance(data, list) else [])
    return {c["name"]: c["id"] for c in cats}


def all_zkb_txns():
    out, page = {}, 1
    while True:
        req = urllib.request.Request(
            f"{SURE_URL}/api/v1/transactions?account_id={ZKB_ACCOUNT_ID}&per_page=100&page={page}",
            headers={"X-Api-Key": SURE_API_KEY})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
        txns = data.get("transactions", [])
        if not txns:
            break
        for t in txns:
            out[t["id"]] = t
        if len(txns) < 100:
            break
        page += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--since", default="2026-06-19")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not SURE_API_KEY:
        sys.exit("MCP_SURE_API_KEY not set")

    cat_id = get_categories()
    txns = all_zkb_txns()

    # index existing txns by (date, signed_amount_cents)
    index = {}
    for t in txns.values():
        amt = t.get("signed_amount_cents")
        if amt is not None:
            index.setdefault((t["date"], int(amt)), []).append(t)

    with open(args.csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    def cents(a):
        return int(round(float(a) * 100))

    patched, skipped_old, no_match, no_cat = [], 0, 0, 0
    for r in rows:
        if r["date"] <= args.since:
            skipped_old += 1
            continue
        key = (r["date"], cents(r["amount"]))
        cands = index.get(key, [])
        cand = next((c for c in cands if c.get("category") is None), None) or \
               (cands[0] if cands else None)
        if not cand:
            no_match += 1
            print(f"  ? no txn for {r['date']} {r['amount']:>9} {r['name'][:30]}")
            continue
        sure_cat = r["category"]
        if not sure_cat:
            no_cat += 1
            continue
        cid = cat_id.get(sure_cat)
        if not cid:
            print(f"  ! unknown Sure category '{sure_cat}' — create it first")
            no_cat += 1
            continue
        if args.dry_run:
            patched.append((r["date"], sure_cat))
            continue
        req = urllib.request.Request(
            f"{SURE_URL}/api/v1/transactions/{cand['id']}",
            data=json.dumps({"transaction": {"category_id": cid}}).encode(),
            headers={"X-Api-Key": SURE_API_KEY, "Content-Type": "application/json"},
            method="PATCH")
        try:
            urllib.request.urlopen(req, timeout=15)
            patched.append((r["date"], sure_cat))
        except Exception as e:
            print(f"  ! PATCH {cand['id'][:8]} {r['name'][:25]}: {str(e)[:50]}")

    print(f"\nwould patch / patched: {len(patched)}  (rows of {len(rows)}, skipped_old={skipped_old}, no_match={no_match}, no_cat={no_cat})")
    from collections import Counter
    for cat, n in Counter(c for _, c in patched).most_common(12):
        print(f"  {cat:24s} {n}")


if __name__ == "__main__":
    main()
