# Actualiss

Python library for importing Swiss financial transactions to Actual Budget.

## Features

- Import ZKB and Swisscard transactions to Actual Budget
- Automatic category mapping from Cashew to Actual Budget
- Duplicate detection with exact and fuzzy matching
- CLI and Streamlit UI interfaces
- Docker deployment ready
- Type-safe category enums with subcategories
- Built with Polars for efficient data processing

## Installation

```bash
pip install actualiss
```

For development mode with all dependencies:

```bash
git clone https://github.com/yourusername/actualiss.git
cd actualiss
pip install -e ".[dev,gui]"
```

## Quick Start

### CLI Usage

```bash
# Set environment variables
export ACTUAL_SERVER_URL=http://localhost:5006
export ACTUAL_PASSWORD=your_password
export ACTUAL_FILE="My Budget"

# Import transactions
actualiss process transactions.xlsx --processor swisscard

# Dry run to validate before importing
actualiss process transactions.xlsx --dry-run

# Export to CSV instead
actualiss process transactions.xlsx --output output.csv --method csv
```

### Python API

```python
from actualiss import SwisscardProcessor, ActualClient

# Load transactions
processor = SwisscardProcessor()
batch = processor.process("transactions.xlsx")

# Import to Actual
client = ActualClient(server_url=..., password=..., file=...)
with client:
    account_id = client.get_or_create_account("My Account")
    transactions = batch.to_actual_format()
    client.import_transactions(transactions, account_id)
    client.commit()
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| ACTUAL_SERVER_URL | Yes | Actual Budget server URL |
| ACTUAL_PASSWORD | Yes | Actual Budget password |
| ACTUAL_FILE | Yes | Budget file name |
| ACTUAL_ENCRYPTION_PASSWORD | No | Encryption password for encrypted budgets |

### .env File

Create a `.env` file in your project directory:

```bash
ACTUAL_SERVER_URL=http://localhost:5006
ACTUAL_PASSWORD=your_password
ACTUAL_FILE=My Budget
ACTUAL_ENCRYPTION_PASSWORD=  # Leave empty if no encryption
```

## Category Mapping

Actualiss automatically maps Cashew categories to Actual Budget categories:

| Cashew | Actual |
|--------|--------|
| GROCERIES | Groceries |
| DINING | Dining Out |
| SHOPPING | Shopping |
| ENTERTAINMENT | Entertainment |
| BILLS_FEES | Regular Bills |
| BEAUTY_HEALTH | Personal Care |
| GIFTS | Gifts |
| TRAVEL | Vacation |
| TRANSIT | Transportation |

### Custom Category Mapping

You can create custom category mappings:

```python
from actualiss import Category, ProviderCategoryMapper

mapper = ProviderCategoryMapper()
mapper.add_mapping("MERCHANT NAME", Category.GROCERIES)
processor.set_category_mapper(mapper.to_dict())
```

## CLI Commands

### Process Transactions

```bash
# Basic usage
actualiss process transactions.xlsx

# With processor selection
actualiss process transactions.xlsx --processor zkb

# With date filtering
actualiss process transactions.xlsx --date-from 2024-01-01 --date-to 2024-12-31

# Dry run for validation
actualiss process transactions.xlsx --dry-run

# Export to CSV
actualiss process transactions.xlsx --output output.csv --method csv

# Specify account name
actualiss process transactions.xlsx --account "My Credit Card"

# Enable verbose logging
actualiss process transactions.xlsx --verbose
```

### Account Management

```bash
# List all accounts
actualiss accounts list

# Create a new account
actualiss accounts create "My Account" --type checking
```

### Category Mappings

```bash
# Show all category mappings
actualiss categories
```

### Streamlit UI

```bash
# Launch the web interface
actualiss ui
```

## Docker Deployment

### Using Docker Compose

The easiest way to run Actualiss with Actual Budget is using Docker Compose:

```bash
# Start both Actual Budget and Actualiss
docker-compose up -d

# View logs
docker-compose logs -f actualiss

# Stop services
docker-compose down
```

### Access the Services

- Actual Budget: http://localhost:5006
- Actualiss UI: http://localhost:8501

### Docker Configuration

The `docker-compose.yml` file includes:

- **actual-budget**: Official Actual Budget server on port 5006
- **actualiss**: Actualiss Streamlit UI on port 8501

Both services include health checks and automatic restart policies.

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to Actual Budget

**Solutions**:
- Verify ACTUAL_SERVER_URL is correct
- Check Actual Budget server is running
- Verify password is correct
- Check firewall settings
- Ensure ports are not blocked

**Example**:
```bash
# Test connection
curl http://localhost:5006

# Check Actual Budget logs
docker-compose logs actual-budget
```

### Import Issues

**Problem**: Transactions not importing

**Solutions**:
- Use `--dry-run` to validate data format first
- Check account exists in Actual Budget
- Verify category mappings are correct
- Check for duplicates with `actualiss process transactions.xlsx --dry-run`
- Review logs for error messages: `docker-compose logs actualiss`

**Example**:
```bash
# Validate before importing
actualiss process transactions.xlsx --dry-run --verbose

# Check if account exists
actualiss accounts list
```

### Docker Issues

**Problem**: Containers won't start

**Solutions**:
- Check port conflicts (8501, 5006)
- Verify docker-compose.yml is correct
- Check logs: `docker-compose logs actualiss`
- Ensure Docker daemon is running
- Try rebuilding: `docker-compose up -d --build`

**Example**:
```bash
# Check port usage
netstat -tuln | grep -E '8501|5006'

# Rebuild containers
docker-compose down
docker-compose up -d --build
```

### Category Mapping Issues

**Problem**: Transactions not categorized correctly

**Solutions**:
- Review category mappings: `actualiss categories`
- Check merchant names in your transaction file
- Create custom mappings for specific merchants
- Verify category names match Actual Budget categories exactly

**Example**:
```python
# Create custom mapping
from actualiss import ProviderCategoryMapper, Category

mapper = ProviderCategoryMapper()
mapper.add_mapping("MY MERCHANT", Category.GROCERIES)
```

## Streamlit UI

The web interface provides an easy way to:

- Upload transaction files
- Preview transaction data
- Configure date ranges and options
- Import directly to Actual Budget

To start the UI:

```bash
actualiss ui
```

Then open http://localhost:8501 in your browser.

## Examples

### CLI Usage

Import Swisscard transactions:
```bash
actualiss process transactions.xlsx --processor swisscard --dry-run
actualiss process transactions.xlsx --processor swisscard --account "Checking Account"
```

### Docker Usage

Start with custom config:
```bash
cp docker-compose.override.yml.example docker-compose.override.yml
docker-compose up -d
```

## Examples

### Process Swisscard Transactions

```python
from datetime import date
from actualiss import SwisscardProcessor, ActualClient

# Process transactions
processor = SwisscardProcessor()
batch = processor.process(
    "swisscard_transactions.xlsx",
    date_from=date(2024, 1, 1),
    date_to=date(2024, 12, 31)
)

# Import to Actual
client = ActualClient(
    server_url="http://localhost:5006",
    password="your_password",
    file="My Budget"
)

with client:
    account_id = client.get_or_create_account("Swisscard")
    transactions = batch.to_actual_format()
    imported = client.import_transactions(transactions, account_id)
    client.commit()
    print(f"Imported {imported} transactions")
```

### Process ZKB Transactions

```python
from actualiss import ZKBProcessor, ActualClient

# Process transactions
processor = ZKBProcessor()
batch = processor.process("zkb_transactions.xlsx")

# Import to Actual
client = ActualClient(
    server_url="http://localhost:5006",
    password="your_password",
    file="My Budget"
)

with client:
    account_id = client.get_or_create_account("ZKB Account")
    transactions = batch.to_actual_format()
    client.import_transactions(transactions, account_id)
    client.commit()
```

### Custom Category Mapping

```python
from actualiss import SwisscardProcessor, Category, ProviderCategoryMapper

# Create custom mapper
mapper = ProviderCategoryMapper()

# Add specific merchant mappings
mapper.add_mapping("COOP", Category.GROCERIES)
mapper.add_mapping("MIGROS", Category.GROCERIES)
mapper.add_mapping("UBER", Category.DINING)
mapper.add_mapping("AMAZON", Category.SHOPPING)

# Apply to processor
processor = SwisscardProcessor()
processor.set_category_mapper(mapper.to_dict())

# Process with custom mappings
batch = processor.process("transactions.xlsx")
```

## Supported Institutions

- Swisscard (XLSX format)
- ZKB (XLSX format)

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black actualiss/
isort actualiss/
```

### Type Checking

```bash
mypy actualiss/
```

## License

MIT License - see LICENSE file for details
