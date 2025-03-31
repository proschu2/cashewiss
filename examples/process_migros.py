#!/usr/bin/env python3
"""Example script demonstrating Migros Bank transaction processing."""

from datetime import date
from cashewiss import MigrosProcessor, CashewClient

# Initialize processor and client
processor = MigrosProcessor(name="Migros Bank", account="My Account")
client = CashewClient()

# Process transactions with date filtering
batch = processor.process(
    "transactions.csv",
    date_from=date(2024, 1, 1),
    date_to=date(2024, 3, 31),
)

print(f"\nProcessed {len(batch.transactions)} transactions")

# Show example transaction
if batch.transactions:
    t = batch.transactions[0]
    print("\nExample transaction:")
    print(f"Date: {t.date}")
    print(f"Title: {t.title}")
    print(f"Amount: {t.amount} {t.currency}")
    print(f"Category: {t.category.value if t.category else None}")
    print(f"Subcategory: {t.subcategory.value if t.subcategory else None}")
    print(f"Account: {t.account}")
    print(f"Notes: {t.notes}")
    if t.meta:
        print("\nMeta information:")
        print(f"Reference Number: {t.meta['reference_number']}")
        print(f"Original Text: {t.meta['original_text']}")

# Export to CSV
print("\nExporting to CSV...")
client.export_to_csv(batch, "migros_transactions.csv")

# Or use API export
print("\nGenerating API URL...")
url = client.export_to_api(batch, dry_run=True)
print(f"API Import URL: {url}")
