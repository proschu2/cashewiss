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
        - Header starts at row 14
        - Columns: Datum, Buchungstext, Mitteilung, Referenznummer, Betrag, Saldo, Valuta
        - Amount in Swiss format (e.g. -12,32)
        """
        # Skip first 13 rows, header is on row 14
        # Read CSV with Swiss date format (dd.mm.yyyy)
        df = pl.read_csv(
            file_path,
            separator=";",
            skip_rows=13,
            encoding="utf8",
            try_parse_dates=False,  # Don't auto-parse dates
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
            pl.col("Betrag").str.replace(",", ".").cast(pl.Float64).alias("Betrag")
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
            # Skip Viseca card entries
            if "Karte: 474124" in row["Buchungstext"]:
                continue

            # Skip TWINT entries with +417
            if "TWINT" in row["Buchungstext"] and "+417" in row["Buchungstext"]:
                continue

            # Get filtered buchungstext for merchant mapping
            merchant = row["Buchungstext"].split(",")[0]
            
            # Further clean merchant text by removing TWINT prefix
            if "TWINT" in merchant:
                # Handle cases like "TWINT Belastung IKEA AG 0400003132762475"
                parts = merchant.split("TWINT Belastung ")
                if len(parts) > 1:
                    # Take everything after "TWINT Belastung" and before any numbers
                    merchant = parts[1].split(" 0")[0].strip()


            # Use Mitteilung as title if present, otherwise use filtered buchungstext
            title = row["Mitteilung"] if row["Mitteilung"] else merchant
            notes = self.name

            # Map categories using the merchant text
            mapping = self._map_category({self.merchant_column: title})

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
