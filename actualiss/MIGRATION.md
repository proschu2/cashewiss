# Migration Guide: Cashewiss to Actualiss

This guide helps you migrate from Cashewiss (Cashew integration) to Actualiss (Actual Budget integration).

## Overview

Actualiss is derived from Cashewiss but targets Actual Budget instead of Cashew. While the core transaction processing logic remains similar, there are important differences in APIs, data formats, and deployment.

## Key Differences

### Export Target

- **Cashewiss**: Exports to Cashew app via URL scheme or CSV
- **Actualiss**: Imports to Actual Budget via REST API

### API Client

- **Cashewiss**: Uses `CashewClient` with URL-based export
- **Actualiss**: Uses `ActualClient` from actualpy library

### Duplicate Detection

- **Cashewiss**: Basic duplicate checking
- **Actualiss**: Layered approach with `imported_id` (exact) and fuzzy matching

### Transaction Format

- **Cashewiss**: Cashew-specific CSV format
- **Actualiss**: Actual Budget API format with different field names

## Migration Steps

### Step 1: Install Actualiss

```bash
# Uninstall cashewiss (optional)
pip uninstall cashewiss

# Install actualiss
pip install actualiss

# For development mode
git clone https://github.com/yourusername/actualiss.git
cd actualiss
pip install -e ".[dev,gui]"
```

### Step 2: Update Environment Variables

Cashewiss environment variables:
```bash
# No environment variables required for cashewiss
# Cashew URL was passed via CLI or defaults
```

Actualiss environment variables:
```bash
# Required
ACTUAL_SERVER_URL=http://localhost:5006
ACTUAL_PASSWORD=your_password
ACTUAL_FILE=My Budget

# Optional
ACTUAL_ENCRYPTION_PASSWORD=  # For encrypted budgets
```

Create a `.env` file:
```bash
ACTUAL_SERVER_URL=http://localhost:5006
ACTUAL_PASSWORD=your_password
ACTUAL_FILE=My Budget
```

### Step 3: Update Import Statements

**Before (Cashewiss)**:
```python
from cashewiss import SwisscardProcessor, MigrosProcessor, CashewClient
from cashewiss import Category, ProviderCategoryMapper
```

**After (Actualiss)**:
```python
from actualiss import SwisscardProcessor, ZKBProcessor, ActualClient
from actualiss import Category, ProviderCategoryMapper
```

### Step 4: Update Client Initialization

**Before (Cashewiss)**:
```python
from cashewiss import CashewClient

client = CashewClient()
# Optional: Set custom Cashew URL
client = CashewClient(cashew_url="https://your-cashew-url.com")
```

**After (Actualiss)**:
```python
from actualiss import ActualClient

client = ActualClient(
    server_url="http://localhost:5006",
    password="your_password",
    file="My Budget"
)
```

### Step 5: Update Export Methods

**Before (Cashewiss)**:
```python
# Export to CSV
client.export_to_csv(batch, "output.csv")

# Export via API (opens browser)
client.export_to_api(batch)

# Get URL without opening browser
url = client.export_to_api(batch, dry_run=True)
```

**After (Actualiss)**:
```python
# Import to Actual Budget
with client:
    account_id = client.get_or_create_account("My Account")
    transactions = batch.to_actual_format()
    imported = client.import_transactions(transactions, account_id)
    client.commit()

# Export to CSV (for manual import)
batch.to_actual_csv("output.csv")
```

### Step 6: Update Transaction Format Methods

**Before (Cashewiss)**:
```python
# Cashewiss had internal format conversion
transactions = batch.transactions  # List of Transaction objects
```

**After (Actualiss)**:
```python
# Convert to Actual Budget format
transactions = batch.to_actual_format()  # List of dicts

# Each transaction dict has:
# {
#     'date': '2024-01-15',
#     'amount': -1000,  # in cents
#     'account': 'My Account',
#     'category': 'Groceries',
#     'imported_payee': 'Merchant Name',
#     'notes': 'Transaction notes',
#     'imported_id': 'unique_id'
# }
```

### Step 7: Update CLI Commands

**Before (Cashewiss)**:
```bash
cashewiss process transactions.xlsx --output output.csv
cashewiss process transactions.xlsx --method api --cashew-url https://...
cashewiss ui
```

**After (Actualiss)**:
```bash
actualiss process transactions.xlsx --output output.csv --method csv
actualiss process transactions.xlsx --method api
actualiss process transactions.xlsx --dry-run
actualiss accounts list
actualiss accounts create "My Account"
actualiss ui
```

## Code Comparison

### Complete Example: Cashewiss

```python
from datetime import date
from cashewiss import SwisscardProcessor, CashewClient

# Process transactions
processor = SwisscardProcessor()
batch = processor.process(
    "transactions.xlsx",
    date_from=date(2024, 1, 1),
    date_to=date(2024, 12, 31)
)

# Export to CSV
client = CashewClient()
client.export_to_csv(batch, "output.csv")

# Or export via API
client.export_to_api(batch)  # Opens browser
```

### Complete Example: Actualiss

```python
from datetime import date
from actualiss import SwisscardProcessor, ActualClient

# Process transactions
processor = SwisscardProcessor()
batch = processor.process(
    "transactions.xlsx",
    date_from=date(2024, 1, 1),
    date_to=date(2024, 12, 31)
)

# Import to Actual Budget
client = ActualClient(
    server_url="http://localhost:5006",
    password="your_password",
    file="My Budget"
)

with client:
    account_id = client.get_or_create_account("My Account")
    transactions = batch.to_actual_format()
    imported = client.import_transactions(transactions, account_id)
    client.commit()
    print(f"Imported {imported} transactions")
```

## Breaking Changes

### 1. Client Context Manager

**Cashewiss**: No context manager needed
```python
client = CashewClient()
client.export_to_api(batch)
```

**Actualiss**: Must use context manager
```python
client = ActualClient(...)
with client:
    # Perform operations
    client.import_transactions(...)
    client.commit()
```

### 2. Account Management

**Cashewiss**: Accounts specified in CSV/URL
```python
# Account name in transaction data
```

**Actualiss**: Must create or reference account
```python
account_id = client.get_or_create_account("My Account")
client.import_transactions(transactions, account_id)
```

### 3. Transaction Amount Format

**Cashewiss**: Decimal in CSV format
```python
# Amount: -50.25
```

**Actualiss**: Integer in cents
```python
# Amount: -5025 (for $50.25)
# Conversion handled automatically by to_actual_format()
```

### 4. Category Names

**Cashewiss**: Used Cashew category names
```python
Category.GROCERIES  # Mapped to "Groceries" in Cashew
```

**Actualiss**: Uses Actual Budget category names
```python
Category.GROCERIES  # Mapped to "Groceries" in Actual
# Category mappings differ between apps
```

## Common Migration Issues

### Issue 1: Missing Account

**Problem**: `ValueError: Account not found`

**Solution**: Create account before importing
```python
with client:
    account_id = client.get_or_create_account("My Account")
    # Or create manually:
    # account_id = client.create_account("My Account", type="checking")
```

### Issue 2: Category Not Found

**Problem**: Transactions not categorized correctly

**Solution**: Verify category names match Actual Budget
```python
# Check available categories
from actualiss.core.category_map import ACTUAL_CATEGORY_MAP
print(ACTUAL_CATEGORY_MAP)

# Create custom mapping
mapper = ProviderCategoryMapper()
mapper.add_mapping("MERCHANT", Category.GROCERIES)
```

### Issue 3: Connection Refused

**Problem**: Cannot connect to Actual Budget

**Solution**: Ensure Actual Budget server is running
```bash
# Using Docker
docker-compose up -d actual-budget

# Or run Actual Budget server manually
actualbudget server
```

### Issue 4: Duplicate Transactions

**Problem**: Same transactions imported multiple times

**Solution**: Actualiss has built-in duplicate detection
```python
# Duplicates are detected by:
# 1. imported_id (exact match)
# 2. Fuzzy matching (date + amount + payee)

# To skip duplicates:
# Already handled automatically by ActualClient
```

### Issue 5: SSL/TLS Errors

**Problem**: Certificate verification errors

**Solution**: Configure SSL verification (for self-signed certs)
```python
# Note: This is not recommended for production
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

## Deployment Changes

### Cashewiss Deployment

No server required. Cashewiss ran locally and opened browser windows for Cashew app.

### Actualiss Deployment

Requires Actual Budget server running:

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Services:
# - actual-budget: port 5006
# - actualiss: port 8501 (Streamlit UI)
```

## Testing Your Migration

### Step 1: Dry Run

```bash
# Validate without importing
actualiss process transactions.xlsx --dry-run
```

### Step 2: Test Connection

```bash
# List accounts to verify connection
actualiss accounts list
```

### Step 3: Small Batch Test

```python
# Process a small date range first
processor = SwisscardProcessor()
batch = processor.process(
    "transactions.xlsx",
    date_from=date(2024, 1, 1),
    date_to=date(2024, 1, 31)  # Just one month
)

# Import small batch
with client:
    account_id = client.get_or_create_account("Test Account")
    transactions = batch.to_actual_format()
    client.import_transactions(transactions, account_id)
    client.commit()
```

### Step 4: Verify in Actual Budget

1. Open Actual Budget UI
2. Navigate to the account
3. Verify transactions appear correctly
4. Check categories are mapped properly
5. Confirm no duplicates

## Rollback Plan

If you need to rollback to Cashewiss:

1. **Keep Cashewiss installed**: Don't uninstall until migration is verified
2. **Export data from Actual**: Export transactions from Actual Budget as CSV
3. **Reinstall Cashewiss**: `pip install cashewiss`
4. **Update environment variables**: Remove Actual Budget variables
5. **Update code**: Revert import statements and client usage

## Additional Resources

- [Actualiss README](README.md)
- [Actual Budget Documentation](https://actualbudget.org/docs)
- [actualpy Library](https://github.com/bjourne/actualpy)

## Getting Help

If you encounter issues during migration:

1. Check the troubleshooting section in the main README
2. Review actualiss logs: `docker-compose logs actualiss`
3. Enable verbose mode: `actualiss process transactions.xlsx --verbose`
4. Open an issue on GitHub with:
   - Your cashewiss code (before)
   - Your actualiss code (after)
   - Error messages
   - Environment details

## Summary

| Aspect | Cashewiss | Actualiss |
|--------|-----------|-----------|
| Target | Cashew app | Actual Budget |
| API | URL scheme | REST API |
| Deployment | Local only | Docker ready |
| Context Manager | No | Yes (required) |
| Account Management | In CSV/URL | Must create |
| Amount Format | Decimal | Integer (cents) |
| Duplicate Detection | Basic | Layered (exact + fuzzy) |
