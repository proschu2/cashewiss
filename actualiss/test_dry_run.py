#!/usr/bin/env python3

# Simple test to verify dry-run functionality
from actualiss.core.base import Transaction
from datetime import date
from actualiss.core.base import TransactionBatch

# Create sample transactions
transactions = [
    Transaction(
        date=date(2025, 3, 23),
        title="Fruits and Vegetables",
        amount=-50.0,
        currency="CHF",
        category="GROCERIES",
        notes="Paid with cash",
        account="Sanzio",
    ),
    Transaction(
        date=date(2025, 3, 22),
        title="Restaurant Dinner",
        amount=-25.0,
        currency="CHF",
        category="DINING",
        notes="Weekend dinner",
        account="Visa",
    ),
    Transaction(
        date=date(2025, 3, 21),
        title="Clothing Store",
        amount=-100.0,
        currency="CHF",
        category="SHOPPING",
        notes="New clothes",
        account="Mastercard",
    ),
    Transaction(
        date=date(2025, 3, 20),
        title="Salary March 2025",
        amount=2000.0,
        currency="CHF",
        category="INCOME",
        notes="Monthly salary",
        account="Checking",
    ),
]

# Create a batch
batch = TransactionBatch(transactions=transactions, source="test")


# Test dry-run validation
def test_dry_run_process(file_path, processor, batch):
    """Test the dry-run validation logic"""
    print("\n" + "=" * 60)
    print("🔍 DRY-RUN VALIDATION RESULTS")
    print("=" * 60)

    # 1. Show transaction preview (first 10 transactions)
    transactions = batch.to_actual_format()
    preview_count = min(10, len(transactions))

    print(
        f"\n📊 TRANSACTION PREVIEW (first {preview_count} of {len(transactions)} transactions):"
    )
    print("-" * 80)
    for i, tx in enumerate(transactions[:preview_count], 1):
        print(
            f"{i:2d}. {tx['date']} | {tx['amount']:8d} | {tx['account']:15} | {tx['category']:15} | {tx['imported_payee']}"
        )

    # 2. Check for missing accounts
    accounts_found = set()
    categories_found = set()
    uncategorized_count = 0

    for tx in transactions:
        accounts_found.add(tx["account"])
        categories_found.add(tx["category"])
        if tx["category"] == "Uncategorized":
            uncategorized_count += 1

    missing_accounts = []
    # Common account names that might exist in Actual Budget
    common_accounts = [
        "Default Account",
        "Checking Account",
        "Savings Account",
        "Credit Card",
    ]
    for account in sorted(accounts_found):
        if account not in common_accounts:
            missing_accounts.append(account)

    print(f"\n🏦 ACCOUNT ANALYSIS:")
    print(f"   Total unique accounts found: {len(accounts_found)}")
    if missing_accounts:
        print(f"   ⚠️  Accounts not in common list (may need manual setup):")
        for account in missing_accounts:
            print(f"      - {account}")
    else:
        print("   ✅ All accounts found in common reference list")

    # 3. Check for missing categories
    print(f"\n📋 CATEGORY ANALYSIS:")
    print(f"   Total unique categories found: {len(categories_found)}")
    if uncategorized_count > 0:
        print(f"   ⚠️  Uncategorized transactions: {uncategorized_count}")
        print("      These may need manual category assignment in Actual Budget")
    else:
        print("   ✅ All transactions have categories assigned")

    # 4. Validation summary
    print(f"\n📋 VALIDATION SUMMARY:")
    print("-" * 40)
    print(f"   Total transactions: {len(transactions)}")
    print(f"   Date range: {transactions[0]['date']} to {transactions[-1]['date']}")
    print(f"   Processor used: {processor}")
    print(f"   Source file: {file_path}")

    # 5. Issues and recommendations
    issues = []
    if missing_accounts:
        issues.append(f"Missing accounts: {len(missing_accounts)}")
    if uncategorized_count > 0:
        issues.append(f"Uncategorized transactions: {uncategorized_count}")

    if issues:
        print(f"\n⚠️  POTENTIAL ISSUES:")
        for issue in issues:
            print(f"   • {issue}")
        print("\n💡 RECOMMENDATIONS:")
        print("   • Review and update category mappings in processor configuration")
        print("   • Ensure accounts exist in Actual Budget before importing")
        print("   • Consider adding custom merchant mappings for better categorization")
    else:
        print(f"\n✅ ALL VALIDATIONS PASSED")
        print("   Ready for import to Actual Budget")


# Test the dry-run function
test_dry_run_process("test_file.csv", "zkb", batch)
