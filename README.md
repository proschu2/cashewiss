# Cashewiss

A Python library for processing and uploading transactions from Swiss financial institutions to the Cashew budget app.

## Features

- Process transaction data from various Swiss financial institutions
- Support for CSV and XLSX file formats
- Automatic category mapping with subcategories
- Date range filtering for transactions
- Easy integration with Cashew API
- Built with Polars for efficient data processing
- Type-safe category and subcategory enums

## Installation

```bash
uv pip install cashewiss
```

Or install in development mode:

```bash
git clone https://github.com/proschu2/cashewiss.git
cd cashewiss
uv pip install -e ".[dev]"
```

## Usage

### Command Line Interface

Process transactions from the command line:

```bash
# Process transactions from a Swisscard XLSX file
cashewiss process transactions.xlsx

# Process transactions for a specific date range
cashewiss process transactions.xlsx --date-from 2024-01-01 --date-to 2024-03-23

# Use a different Cashew web app URL
cashewiss process transactions.xlsx --cashew-url https://your-cashew-url.com

# Use a custom processor name (affects transaction notes)
cashewiss process transactions.xlsx --name "MyCard"

# Show URLs without attempting to open browser (dry run mode)
cashewiss process transactions.xlsx --dry-run

Note: Transactions are processed in batches of 25 to handle URL length limits.
If browser opening fails, use --dry-run to get URLs and open them manually.

# Show available category mappings
cashewiss categories
```

### Python API

```python
from datetime import date
from cashewiss import SwisscardProcessor, CashewClient

# Initialize the processor and client
processor = SwisscardProcessor()
client = CashewClient(api_key="your-cashew-api-key")

# Process transactions with optional date filtering
transactions = processor.process(
    "transactions.csv",
    date_from=date(2024, 1, 1),
    date_to=date(2024, 3, 23)
)

# Upload to Cashew
client.upload_transactions(transactions)  # Opens browser windows (25 transactions per batch)
# Or get URL without opening browser
url = client.upload_transactions(transactions, dry_run=True)
```

### Category Mapping

The library provides type-safe category mapping with subcategories:

```python
from cashewiss import (
    Category, ProviderCategoryMapper,
    DiningSubcategory, GroceriesSubcategory
)

# Initialize category mapper
mapper = ProviderCategoryMapper()

# Add mappings with validation
mapper.add_mapping("GROCERY STORES", Category.GROCERIES, GroceriesSubcategory.MEAL)
mapper.add_mapping("CONVENIENCE STORES", Category.GROCERIES, GroceriesSubcategory.SNACKS)
mapper.add_mapping("RESTAURANTS", Category.DINING, DiningSubcategory.FRIENDS)
mapper.add_mapping("FAST FOOD", Category.DINING, DiningSubcategory.DELIVERY)

# Set mapper in processor
processor.set_category_mapper(mapper.to_dict())
```

Available categories:
- GROCERIES (subcategories: MEAL, SNACKS)
- DINING (subcategories: FRIENDS, DELIVERY, WORK)
- SHOPPING (subcategories: CLOTHES, ELECTRONICS, GAMES, KITCHEN)
- ENTERTAINMENT (subcategories: CONCERTS)
- BILLS_FEES (subcategories: TELECOM, HEALTH)
- BEAUTY_HEALTH (subcategories: HEALTH, BEAUTY)
- GIFTS
- TRAVEL
- TRANSIT

### Creating Custom Processors

You can create custom processors for other financial institutions by extending the `BaseTransactionProcessor` class:

```python
from cashewiss import BaseTransactionProcessor, Transaction
import polars as pl

class MyBankProcessor(BaseTransactionProcessor):
    def load_data(self, file_path, date_from=None, date_to=None):
        # Load and filter your data
        df = pl.read_csv(file_path)

        if date_from:
            df = df.filter(pl.col("Date") >= date_from)
        if date_to:
            df = df.filter(pl.col("Date") <= date_to)

        return df

    def transform_data(self):
        # Transform your data into Transaction objects
        transactions = []
        for row in self._df.iter_rows(named=True):
            transaction = Transaction(
                date=row["Date"],
                description=row["Description"],
                amount=float(row["Amount"]),
                currency=row["Currency"]
            )
            transactions.append(transaction)
        return transactions
```

## Examples

Check out the `examples/` directory for complete working examples:

- `examples/process_swisscard.py`: Shows how to process Swisscard transactions including:
  - Category mapping setup
  - Date range filtering
  - Transaction batch processing
  - Accessing transaction details
  - Generating Cashew import URLs

## Supported Institutions

Currently supported financial institutions:

- Swisscard (XLSX format)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
