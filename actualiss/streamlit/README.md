# Actualiss Streamlit UI

A web-based user interface for importing transactions from Swiss financial institutions (ZKB, Swisscard) into Actual Budget.

## Features

- **Connection Management**: Configure and test connection to Actual Budget server
- **Account Selection**: Dynamically load and select from your Actual Budget accounts
- **File Upload**: Upload transaction files (XLSX for Swisscard/ZKB, CSV for ZKB)
- **Category Mapping Preview**: View how Cashew categories map to Actual Budget categories
- **Transaction Preview**: Review transactions before importing
- **Import Progress**: Real-time progress tracking during import
- **Dry Run Mode**: Validate transactions without importing

## Installation

Install the GUI dependencies:

```bash
# In a virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -e ".[gui]"

# Or with uv
uv pip install -e ".[gui]"
```

## Running the App

Start the Streamlit app:

```bash
streamlit run actualiss/streamlit/app.py
```

Or use the CLI:

```bash
actualiss ui
```

The app will open in your browser at `http://localhost:8501`

## Usage

### 1. Configure Connection

- Enter your Actual Budget server URL (e.g., `http://localhost:5006`)
- Enter your account password
- Enter your budget file name (case-sensitive)
- Click "Test Connection" to verify

### 2. Upload Transaction File

- Click "Choose a transaction file"
- Select XLSX (Swisscard/ZKB) or CSV (ZKB) file
- Transactions will be processed automatically

### 3. Preview Transactions

- Review transaction details in the preview table
- Check metrics (total count, amount, date range)
- Edit categories if needed (future feature)

### 4. Select Account

- Choose the Actual Budget account to import into
- Accounts are loaded from your connected budget

### 5. Review Category Mappings

- Click "Category Mappings" to see how categories map
- Verify mappings are correct for your transactions

### 6. Import

- Choose between Dry Run (validate) or actual import
- Click "Import Transactions"
- Monitor progress in real-time

## Configuration

Environment variables (optional, can be set in `.env`):

```bash
ACTUAL_SERVER_URL=http://localhost:5006
ACTUAL_PASSWORD=your_password
ACTUAL_FILE=My Budget
ACTUAL_ENCRYPTION_PASSWORD=your_encryption_password  # Optional
```

## Troubleshooting

### Connection Failed

- Verify Actual Budget server is running
- Check server URL is correct (include `http://` or `https://`)
- Verify password and budget file name (case-sensitive)

### File Processing Error

- Ensure file format is correct (XLSX for Swisscard/ZKB, CSV for ZKB)
- Check file is not corrupted
- Verify file headers match expected format

### Import Failed

- Verify account is selected
- Check for duplicate transactions
- Ensure categories exist in Actual Budget

## Screenshots

### Connection Sidebar
![Connection Sidebar](docs/screenshots/sidebar.png)

### Transaction Preview
![Transaction Preview](docs/screenshots/preview.png)

### Import Progress
![Import Progress](docs/screenshots/progress.png)
