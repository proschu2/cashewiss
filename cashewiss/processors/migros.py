from datetime import date
from typing import Optional, List
import polars as pl

from ..core.base import BaseTransactionProcessor, Transaction


class MigrosProcessor(BaseTransactionProcessor):
    """Processor for Migros Bank account transactions."""

    def __init__(self, name: str = "Migros Bank", account: Optional[str] = None):
        super().__init__(name=name)
        self.account_name = account or name
        self.merchant_column = "Buchungstext"
        self.amount_column = "Betrag"
        self.set_default_merchant_mapping()

    def load_data(
        self,
        file_path: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> pl.DataFrame:
        """
        Load Migros Bank transaction data from CSV file.

        Expected CSV format:
        - Semicolon separated
        - Header row contains 'Datum' as first column
        - Columns: Datum, Buchungstext, Mitteilung, Referenznummer, Betrag, Saldo, Valuta
        - Amount in Swiss format (e.g. -12,32)
        """
        # First determine the header row by finding the row with 'Datum' as first column
        header_row = 0

        # Check if file_path is a string path or a file-like object
        if hasattr(file_path, "read"):
            # It's a file-like object (like Streamlit's UploadedFile)
            # First, read all contents to find the header row
            file_content = file_path.getvalue().decode("utf-8")
            for i, line in enumerate(file_content.splitlines()):
                if "Buchungstext" in line:
                    header_row = i
                    break
                if line.strip().startswith('"Datum;"'):
                    header_row = i
                    break

            # Now use read_csv with a file-like object
            file_path.seek(0)
        else:
            # It's a path (string or PathLike)
            with open(file_path, "r", encoding="utf8") as f:
                for i, line in enumerate(f):
                    if line.strip().startswith("Datum;"):
                        header_row = i
                        break

        df = pl.read_csv(
            file_path,
            separator=";",
            skip_rows=header_row,
            encoding="utf8",
            try_parse_dates=False,  # Don't auto-parse dates
            truncate_ragged_lines=True,  # Handle inconsistent number of fields
        )
        # Convert Swiss date format to ISO
        df = df.with_columns(
            pl.col("Datum").str.strptime(pl.Date, format="%d.%m.%Y").alias("Datum")
        )

        # Ensure required columns exist
        required_cols = [
            "Datum",
            "Buchungstext",
            "Mitteilung",
            "Referenznummer",
            "Betrag",
            "Saldo",
            "Valuta",
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

        # Convert Betrag from Swiss format (-12,32) to standard decimal format (-12.32)
        df = df.with_columns(
            pl.when(pl.col("Betrag").cast(pl.String).str.contains(","))
            .then(pl.col("Betrag").cast(pl.String).str.replace(",", "."))
            .otherwise(pl.col("Betrag"))
            .cast(pl.Float64)
            .alias("Betrag")
        )

        # Apply date filtering if provided
        if date_from is not None:
            df = df.filter(pl.col("Datum") >= date_from)
        if date_to is not None:
            df = df.filter(pl.col("Datum") <= date_to)

        self._df = df
        return df

    def transform_data(self) -> List[Transaction]:
        """Transform Migros Bank data into standardized Transaction objects."""
        if self._df is None:
            raise ValueError("No data loaded. Call load_data() first.")

        transactions = []

        # Convert DataFrame to list of Transaction objects
        for row in self._df.iter_rows(named=True):
            if "Karte: 474124" in row["Buchungstext"]:
                continue

            # Get filtered buchungstext for merchant mapping
            merchant = row["Buchungstext"].split(",")[0]

            # Further clean merchant text by removing TWINT prefix
            if "TWINT" in merchant:
                # Handle cases like TWINT and phone number
                if "+417" in row["Buchungstext"]:
                    person_name = row["Buchungstext"].split(",")[1].strip()
                    merchant = f"TWINT {person_name}"
                else:
                    # Handle cases like "TWINT Belastung IKEA AG 0400003132762475"
                    parts = merchant.split("TWINT Belastung ")
                    if len(parts) > 1:
                        # Take everything after "TWINT Belastung" and before any numbers
                        merchant = parts[1].split(" 0")[0].strip()

            # Use Mitteilung as title if present, otherwise use filtered buchungstext
            title = row["Mitteilung"] if row["Mitteilung"] else merchant
            notes = self.name

            # Map categories using the merchant text
            mapping = self._map_category(
                {self.merchant_column: title, "Betrag": float(row["Betrag"])}
            )

            transaction = Transaction(
                date=row["Datum"],
                title=title,
                amount=float(
                    row["Betrag"]
                ),  # Already converted to standard format in load_data
                currency="CHF",  # Migros Bank transactions are in CHF
                notes=notes,
                category=mapping.category,
                subcategory=mapping.subcategory,
                account=self.account_name,
                meta={
                    "processor": self.name,
                    "reference_number": row["Referenznummer"],
                    "balance": row["Saldo"],
                    "value_date": row["Valuta"],
                    "original_text": row["Buchungstext"],
                    "original_row": row,
                },
            )
            transactions.append(transaction)

        self._transformed_data = transactions
        return transactions
