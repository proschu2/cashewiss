#!/usr/bin/env python3
"""ZKB CSV -> cashewiss ZKBProcessor -> Sure TransactionImport.

Replaces the Actual Budget round trip. Proven import payload from the
Selma/Saxo migrations (see skill: sure-finance-integration).

Usage:
  # 1. Parse + transform + validate (nothing touches Sure)
  zkb_to_sure.py PATH_TO_CSV [--since 2026-06-20] [--dry-run]

  # 2. Same, then POST unpublished import to Sure (publish=false — review in UI)
  zkb_to_sure.py PATH_TO_CSV [--since 2026-06-20] --upload-unpublished

  # 3. Full auto-import (publish=true) — only after a green dry run
  zkb_to_sure.py PATH_TO_CSV [--since 2026-06-20] --publish
"""
import argparse
import csv
import io
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime

SURE_URL = os.environ.get("SURE_URL", "http://localhost:3000")
SURE_API_KEY = os.environ.get("MCP_SURE_API_KEY")
ZKB_ACCOUNT_ID = "baa23a18-2f91-47b7-944c-98da82a1db2d"  # Sure "ZKB" depository

# actualiss (category, subcategory) -> Sure category.
# Subcategory-aware: Bills/Donations -> Gifts & Donations, Bills/Taxes -> Taxes, etc.
# Top-level fallbacks verified against the 716 existing ZKB txns (ActualImport
# 7b0742d6, Jul 21): Groceries 209, Shopping 156, Utilities 93, Food & Drink 85, ...
PAIR_MAP = {
    ("Income", None): "Income",
    ("Income", "Salary"): "Income",
    ("Income", "Twint"): "Income",
    ("Income", "Refunds"): "Income",
    ("Bills", None): "Utilities",
    ("Bills", "Rent"): "Mortgage / Rent",
    ("Bills", "Utilities"): "Utilities",
    ("Bills", "Insurance"): "Insurance",
    ("Bills", "Telecom"): "Services",
    ("Bills", "Taxes"): "Taxes",
    ("Bills", "Fees"): "Fees",
    ("Bills", "Subscriptions"): "Subscriptions",
    ("Bills", "Donations"): "Gifts & Donations",
    ("Essentials", None): "Groceries",
    ("Essentials", "Groceries"): "Groceries",
    ("Essentials", "Transit"): "Transportation",
    ("Dining", None): "Food & Drink",
    ("Shopping", None): "Shopping",
    ("Household", None): "Home Improvement",
    ("Personal Care & Health", None): "Personal Care & Health",
    ("Leisure", None): "Entertainment",
    ("Leisure", "Events"): "Entertainment",
    ("Hobbies", None): "Entertainment",
    ("Travel", None): "Travel",
    ("Travel", "Transport"): "Travel",
    ("Financial", None): "Savings & Investments",
    ("Financial", "Investments"): "Savings & Investments",
    ("Financial", "Savings"): "Savings & Investments",
}
CATEGORY_MAP = {cat: sure for (cat, _), sure in PAIR_MAP.items()}  # top-level fallback

# Run with the actualiss venv python (needs polars):
#   ~/dev/cashewiss/actualiss/.venv/bin/python zkb_to_sure.py <csv> [opts]
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "actualiss"))
from actualiss.processors.zkb import ZKBProcessor  # noqa: E402


def sure_category(t):
    """Map a Transaction to a Sure category, preferring the (cat, subcat) pair."""
    cat = t.category.value if t.category else None
    sub = t.subcategory.value if t.subcategory else None
    if (cat, sub) in PAIR_MAP:
        return PAIR_MAP[(cat, sub)]
    if (cat, None) in PAIR_MAP:
        return PAIR_MAP[(cat, None)]
    return CATEGORY_MAP.get(cat) or ""


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--since", help="only rows with date > this (YYYY-MM-DD)")
    ap.add_argument("--account", default="ZKB", help="target Sure account name (default ZKB)")
    ap.add_argument("--dry-run", action="store_true", help="transform only, no API calls")
    ap.add_argument("--upload-unpublished", action="store_true",
                    help="POST import with publish=false (review in Sure UI)")
    ap.add_argument("--publish", action="store_true",
                    help="POST import with publish=true (imports for real)")
    return ap.parse_args()


def to_sure_csv(batch, since=None):
    """Transform TransactionBatch -> (sure_csv_string, summary_dict)."""
    rows = []
    skipped_old = 0
    unmapped_cats = set()
    for t in batch.transactions:
        if since and str(t.date) <= since:
            skipped_old += 1
            continue
        cat = t.category.value if t.category else None
        sub = t.subcategory.value if t.subcategory else None
        sure_cat = sure_category(t)
        if cat and not sure_cat:
            unmapped_cats.add(f"{cat}/{sub}")
        rows.append({
            "date": t.date.isoformat(),
            "amount": f"{t.amount:.2f}",
            "name": t.title,
            "currency": "CHF",
            "category": sure_cat or "",
            "account": "ZKB",
            "notes": t.notes or "",
        })

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["date", "amount", "name", "currency",
                                        "category", "account", "notes"],
                       lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    summary = {
        "rows": len(rows),
        "skipped_old": skipped_old,
        "unmapped_categories": sorted(unmapped_cats),
        "date_min": rows[0]["date"] if rows else None,
        "date_max": rows[-1]["date"] if rows else None,
        "total_amount": round(sum(float(r["amount"]) for r in rows), 2),
    }
    return buf.getvalue(), summary


def get_last_sure_txn_date():
    """Fetch latest ZKB transaction date currently in Sure (for --since default)."""
    req = urllib.request.Request(
        f"{SURE_URL}/api/v1/transactions?account_id={ZKB_ACCOUNT_ID}&per_page=100&page=1",
        headers={"X-Api-Key": SURE_API_KEY})
    data = json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
    dates = [t.get("date") for t in data.get("transactions", []) if t.get("date")]
    return max(dates) if dates else None


def post_import(sure_csv, publish):
    payload = {
        "raw_file_content": sure_csv,
        "type": "TransactionImport",
        "account_id": ZKB_ACCOUNT_ID,          # REQUIRED — Account column alone fails
        "publish": "true" if publish else "false",
        "date_col_label": "date",
        "amount_col_label": "amount",
        "name_col_label": "name",
        "category_col_label": "category",   # REQUIRED or the column is silently ignored
        "notes_col_label": "notes",         # carries the #twint / subcategory hashtags
        "date_format": "%Y-%m-%d",             # default is %m/%d/%Y — ISO silently invalid
        "number_format": "1,234.56",
        "signage_convention": "inflows_positive",
    }
    req = urllib.request.Request(
        f"{SURE_URL}/api/v1/imports",
        data=json.dumps(payload).encode(),
        headers={"X-Api-Key": SURE_API_KEY, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def main():
    args = parse_args()
    if (args.upload_unpublished or args.publish) and not SURE_API_KEY:
        sys.exit("MCP_SURE_API_KEY not set")

    if not args.since and (args.upload_unpublished or args.publish):
        last = get_last_sure_txn_date()
        print(f"Latest txn already in Sure: {last}")
        if last:
            args.since = last

    proc = ZKBProcessor(name="ZKB")
    batch = proc.process(args.csv_path)

    # Transactions come newest-first (ZKB export order); sort oldest-first
    batch.transactions.sort(key=lambda t: t.date)

    sure_csv, s = to_sure_csv(batch, since=args.since)
    print(json.dumps(s, indent=2))

    if s["unmapped_categories"]:
        print(f"WARNING: unmapped categories: {s['unmapped_categories']}", file=sys.stderr)

    out_path = os.path.splitext(args.csv_path)[0] + ".sure.csv"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(sure_csv)
    print(f"wrote {out_path}")

    if args.dry_run:
        print("--- dry run: first/last 3 rows ---")
        lines = sure_csv.splitlines()
        print("\n".join(lines[:4]))
        print("...")
        print("\n".join(lines[-3:]))
        return

    if args.upload_unpublished or args.publish:
        result = post_import(sure_csv, publish=args.publish)
        imp = result.get("import", result)
        print(json.dumps({
            "import_id": imp.get("id"),
            "status": imp.get("status"),
            "publish": imp.get("published_at") is not None,
            "raw_row_count": imp.get("raw_row_count"),
            "valid_rows": imp.get("valid_row_count"),
            "invalid_rows": imp.get("invalid_row_count"),
        }, indent=2))
        if not args.publish:
            print("Import created UNPUBLISHED — review in Sure: Settings → Imports, "
                  "then Publish there if it looks right.")


if __name__ == "__main__":
    main()
