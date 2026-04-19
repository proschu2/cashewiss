#!/usr/bin/env python3
"""
Migrate Cashewiss transaction history to Actual Budget.

This script loads your existing Cashewiss transactions and imports them to Actual Budget.
"""

import sys
from pathlib import Path
from datetime import date

# Add actualiss to path
sys.path.insert(0, str(Path(__file__).parent))

from actualiss import ZKBProcessor, SwisscardProcessor
from actualiss.core.actual_client import ActualClient


def migrate_cashess_to_actual(
    file_path: str,
    processor_type: str = "zkb",
    account_name: str = "Imported from Cashewiss",
):
    """
    Migrate transactions from Cashewiss to Actual Budget.

    Args:
        file_path: Path to transaction file (CSV/XLSX)
        processor_type: 'zkb' or 'swisscard'
        account_name: Account name in Actual Budget
    """
    print(f"🚀 Migrating {processor_type.upper()} transactions to Actual Budget...")

    # Load transactions using Cashewiss processor
    if processor_type.lower() == "zkb":
        processor = ZKBProcessor(name="Cashewiss ZKB")
    else:
        processor = SwisscardProcessor(name="Cashewiss Swisscard")

    print(f"📂 Loading transactions from {file_path}...")
    processor.load_data(file_path)
    transactions = processor.transform_data()

    print(f"✅ Loaded {len(transactions)} transactions")

    # Connect to Actual Budget
    print(f"\n🔌 Connecting to Actual Budget...")
    client = ActualClient(
        server_url="http://localhost:5006",
        password="Thieving-Croon-Quarrel-Lantern7-Fretful-Elope",
        file="MontisBudget",
    )

    with client:
        # Get or create account
        print(f"🏦 Getting/creating account: {account_name}")
        account_id = client.get_or_create_account(account_name)
        print(f"   Account ID: {account_id}")

        # Convert to Actual format
        print(f"🔄 Converting to Actual Budget format...")
        batch = processor.get_batch()
        actual_transactions = batch.to_actual_format()

        print(f"   Converted {len(actual_transactions)} transactions")

        # Import transactions
        print(f"📥 Importing {len(actual_transactions)} transactions...")

        imported = 0
        for tx in actual_transactions:
            try:
                # Import transaction
                client.create_transaction(
                    account_id=account_id,
                    date=tx["date"],
                    amount=tx["amount"],
                    payee_name=tx.get("payee_name", ""),
                    imported_payee=tx.get("imported_payee", ""),
                    notes=tx.get("notes", ""),
                    category=tx.get("category"),
                    imported_id=tx.get("imported_id"),
                    cleared=False,
                )
                imported += 1
            except Exception as e:
                print(f"   ⚠️  Failed to import transaction: {e}")
                continue

        print(
            f"\n✅ Successfully imported {imported}/{len(actual_transactions)} transactions"
        )

        # Commit changes
        print(f"💾 Committing changes...")
        client.commit()
        print(f"✅ Migration complete!")


def main():
    """Main migration function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate Cashewiss transactions to Actual Budget"
    )
    parser.add_argument("file_path", help="Path to transaction file (CSV or XLSX)")
    parser.add_argument(
        "--processor",
        choices=["zkb", "swisscard"],
        default="zkb",
        help="Processor type (default: zkb)",
    )
    parser.add_argument(
        "--account",
        default="Migrated from Cashewiss",
        help="Account name in Actual Budget (default: 'Migrated from Cashewiss')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without importing (just show preview)",
    )

    args = parser.parse_args()

    if args.dry_run:
        # Dry run - just show preview
        print("🔍 DRY RUN MODE - Preview only (no actual import)")
        print("=" * 60)

        # Load transactions
        if args.processor == "zkb":
            processor = ZKBProcessor(name="Cashewiss ZKB")
        else:
            processor = SwisscardProcessor(name="Cashess Swisscard")

        processor.load_data(args.file_path)
        transactions = processor.transform_data()

        print(f"\n📊 Preview: {len(transactions)} transactions")
        print("\nFirst 10 transactions:")
        for i, t in enumerate(transactions[:10], 1):
            print(
                f"  {i:2d}. {t.date} | {t.title:40s} | {t.amount:8.2f} CHF | {t.category}"
            )

        if len(transactions) > 10:
            print(f"\n  ... and {len(transactions) - 10} more transactions")

        print(f"\n📋 Summary:")
        print(f"   Total: {len(transactions)} transactions")
        print(f"   Processor: {args.processor}")
        print(f"   Account: {args.account}")
        print(f"\n💡 To actually import, run WITHOUT --dry-run flag")

    else:
        # Actual migration
        migrate_cashess_to_actual(
            file_path=args.file_path,
            processor_type=args.processor,
            account_name=args.account,
        )


if __name__ == "__main__":
    main()
