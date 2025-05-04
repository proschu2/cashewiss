from datetime import date
from typing import Optional, List
import polars as pl

from ..core.base import BaseTransactionProcessor, Transaction


class ZKBProcessor(BaseTransactionProcessor):
    """Processor for ZKB (Zürcher Kantonalbank) bank account transactions."""

    def __init__(self, name: str = "ZKB", account: Optional[str] = None):
        super().__init__(name=name)
        self.account_name = account or name
        # Override default column names for ZKB format
        self.merchant_column = "Booking text"
        # ZKB doesn't provide merchant categories
        self.merchant_category_column = None
        self.description_column = "Booking text"
        self.registered_category_column = None

        # Set up base merchant mappings
        self.set_default_merchant_mapping()

    def load_data(
        self,
        file_path: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> pl.DataFrame:
        """
        Load ZKB transaction data from CSV file.

        Expected CSV format has columns:
        Date;"Booking text";"ZKB reference";"Reference number";"Debit CHF";"Credit CHF";"Value date";"Balance CHF"
        """
        df = pl.read_csv(file_path, separator=";", try_parse_dates=True)

        # Ensure required columns exist
        required_cols = ["Date", "Booking text", "Debit CHF", "Credit CHF"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

        # Convert Debit/Credit columns to numeric, replacing empty values with 0
        df = df.with_columns(
            [
                pl.when(pl.col("Debit CHF") == "")
                .then(pl.lit(0.0))
                .otherwise(pl.col("Debit CHF"))
                .cast(pl.Float64)
                .alias("Debit CHF"),
                pl.when(pl.col("Credit CHF") == "")
                .then(pl.lit(0.0))
                .otherwise(pl.col("Credit CHF"))
                .cast(pl.Float64)
                .alias("Credit CHF"),
            ]
        )

        # Combine Debit and Credit into a single Amount column (Credit positive, Debit negative)
        df = df.with_columns(
            [
                (pl.col("Credit CHF") - pl.col("Debit CHF")).alias("Amount"),
                df["Booking text"].str.contains("TWINT").alias("is_twint"),
            ]
        )

        # Clean the booking text by removing debit/credit indicators
        df = (
            df.with_columns(pl.col("Booking text").str.split(":").list.last())
            .with_columns(
                pl.col("Booking text").str.count_matches(",").alias("tot_commas")
            )
            .with_columns(
                pl.when(pl.col("tot_commas") > 1)
                .then(pl.col("Booking text").str.split(",").list[0])
                .otherwise(pl.col("Booking text"))
                .str.strip_chars()
                .alias("Booking text")
            )
            .with_columns(
                pl.when(pl.col("is_twint"))
                .then(
                    pl.lit("TWINT")
                    + " "
                    + pl.col("Booking text")
                    .str.split(",")
                    .list.get(-1)
                    .str.strip_chars()
                    .str.to_titlecase()
                )
                .otherwise(pl.col("Booking text"))
                .alias("Booking text")
            )
        )

        # Remove Viseca and Swisscard entries
        df = df.filter(~pl.col("Booking text").str.contains("Viseca|Swisscard"))

        # Apply date filtering if provided
        if date_from is not None:
            df = df.filter(pl.col("Date") >= date_from)
        if date_to is not None:
            df = df.filter(pl.col("Date") <= date_to)

        self._df = df
        return df

    def transform_data(self) -> List[Transaction]:
        """Transform ZKB data into standardized Transaction objects."""
        if self._df is None:
            raise ValueError("No data loaded. Call load_data() first.")

        transactions = []

        # Convert DataFrame to list of Transaction objects
        for row in self._df.iter_rows(named=True):
            # Map categories using the row data
            mapping = self._map_category(
                {
                    self.merchant_column: row["Booking text"],
                    self.amount_column: float(row["Amount"]),
                }
            )

            transaction = Transaction(
                date=row["Date"],
                title=row["Booking text"],
                amount=float(row["Amount"]),
                currency="CHF",
                notes=self.name,
                category=mapping.category,
                subcategory=mapping.subcategory,
                account=self.account_name,
                meta={
                    "processor": self.name,
                    "zkb_reference": row.get("ZKB reference"),
                    "reference_number": row.get("Reference number"),
                    "value_date": row.get("Value date"),
                    "balance": row.get("Balance CHF"),
                    "original_row": row,
                },
            )
            transactions.append(transaction)

        self._transformed_data = transactions
        return transactions
