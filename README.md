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
- Export to CSV in Cashew-compatible format

## Installation

```bash
uv pip install cashewiss  # Basic installation
uv pip install 'cashewiss[viseca]'  # With Viseca support
uv pip install 'cashewiss[streamlit]'  # With Streamlit UI support
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
# Process transactions from a Swisscard XLSX file (default: CSV export)
cashewiss process transactions.xlsx --output output.csv

# Export as CSV with custom settings
cashewiss process transactions.xlsx --output output.csv --date-from 2024-01-01 --date-to 2024-03-23

# Preview CSV content (shows header + first 5 rows)
cashewiss process transactions.xlsx --dry-run

# Use API export instead of CSV
cashewiss process transactions.xlsx --method api

# API export with custom URL and dry run
cashewiss process transactions.xlsx --method api --cashew-url https://your-cashew-url.com --dry-run

# Use a custom processor name (affects transaction notes)
cashewiss process transactions.xlsx --name "MyCard"

Note: When using API export, transactions are processed in batches of 25 to handle URL length limits.
If browser opening fails, use --dry-run to get URLs and open them manually.

# Using Viseca processor with API
cashewiss process --processor viseca

# Show available category mappings
cashewiss categories

# Launch Streamlit UI
cashewiss ui (wip)
```

### Streamlit Interface

A web-based interface is available through Streamlit, providing a user-friendly way to:
- Upload and process transaction files
- Preview transaction data before export
- Configure date ranges and processing options
- Export to CSV or directly to Cashew

To use the Streamlit interface, run:
```bash
cashewiss ui
```

When using the Viseca processor, configure credentials in a .env file:
```bash
VISECA_USERNAME=your_username
VISECA_PASSWORD=your_password
VISECA_CARD_ID=your_card_id
```

### Python API

```python
from datetime import date
from cashewiss import SwisscardProcessor, CashewClient

# Initialize the processor and client
processor = SwisscardProcessor()
client = CashewClient()

# Process transactions with optional date filtering
batch = processor.process(
    "transactions.xlsx",
    date_from=date(2024, 1, 1),
    date_to=date(2024, 3, 23)
)

# Export to CSV
client.export_to_csv(batch, "output.csv")  # Creates CSV file
# Or preview CSV content
preview = client.export_to_csv(batch, "output.csv", dry_run=True)

# Or use API export
client.export_to_api(batch)  # Opens browser windows (25 transactions per batch)
# Or get URL without opening browser
url = client.export_to_api(batch, dry_run=True)
```

### CSV Export Format

The CSV export follows this format:
```
Date,Amount,Category,Title,Note,Account
23/03/2025 00:00,-50,Groceries,Fruits and Vegetables,Paid with cash,Sanzio
```

Fields:
- Date: DD/MM/YYYY HH:mm format
- Amount: Decimal number (negative for expenses)
- Category: Transaction category
- Title: Transaction description
- Note: Additional notes (optional)
- Account: Account name (optional)

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
  - Generating Cashew import URLs or CSV exports

## Supported Institutions

Currently supported financial institutions:

- Swisscard (XLSX format)
- Viseca (API access)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
