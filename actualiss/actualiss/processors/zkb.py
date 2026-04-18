from datetime import date
from typing import Optional, List
import polars as pl

from actualiss.core.models import CategoryMapping
from actualiss.core.enums import (
    BillsSubcategory,
    Category,
    FinancialSubcategory,
    IncomeSubcategory,
)

from actualiss.core.base import BaseTransactionProcessor, Transaction


class ZKBProcessor(BaseTransactionProcessor):
    """Processor for ZKB (Zürcher Kantonalbank) bank account transactions."""

    def __init__(self, name: str = "ZKB", account: Optional[str] = None):
        super().__init__(name=name)
        self.account_name = account or "Montis"
        # Override default column names for ZKB format
        self.merchant_column = "Booking text"
        self.amount_column = "amount"  # Match the key used in transform_data
        # ZKB doesn't provide merchant categories
        self.merchant_category_column = None
        self.description_column = "Booking text"
        self.registered_category_column = None

        # Set up base merchant mappings
        self.set_category_mapper(
            {
                "monti sanzio & caldari serena, hohlstrasse 117": CategoryMapping(
                    category=Category.HOUSEHOLD,
                ),
                "post ch ag": CategoryMapping(
                    category=Category.INCOME, subcategory=IncomeSubcategory.SALARY
                ),
                "salary": CategoryMapping(
                    category=Category.INCOME, subcategory=IncomeSubcategory.SALARY
                ),
                # 3rd pillar pension (3. Säule)
                "terzo": CategoryMapping(
                    category=Category.FINANCIAL,
                    subcategory=FinancialSubcategory.INVESTMENTS,
                ),
                "finpension": CategoryMapping(
                    category=Category.FINANCIAL,
                    subcategory=FinancialSubcategory.INVESTMENTS,
                ),
                "sparen 3": CategoryMapping(
                    category=Category.FINANCIAL,
                    subcategory=FinancialSubcategory.INVESTMENTS,
                ),
                "caritas": CategoryMapping(
                    category=Category.BILLS, subcategory=BillsSubcategory.DONATIONS
                ),
                "wise": CategoryMapping(category=Category.TRAVEL),
                "brokers": CategoryMapping(
                    category=Category.FINANCIAL,
                    subcategory=FinancialSubcategory.INVESTMENTS,
                ),
                "revolut": CategoryMapping(category=Category.TRAVEL),
            },
            mapper_type=self.merchant_column,
        )
        self.set_default_merchant_mapping()

        # Patterns for detecting internal transfers
        self.TRANSFER_PATTERNS = [
            (r"^Debit Mobile Banking:\s*(.+)$", "external_transfer"),
            (r"^Debit Mobile Banking \(\d+\)$", "continuation"),
        ]

    def load_data(
        self,
        file_path: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> pl.DataFrame:
        """
        Load ZKB transaction data from CSV file with multi-row support.

        Expected CSV format has columns:
        Date;"Booking text";"Curr";"Amount details";"ZKB reference";"Reference number";"Debit CHF";"Credit CHF";"Value date";"Balance CHF";"Payment purpose";"Details"

        Multi-row patterns:
        - Type 1: Description override (Payment purpose column contains real description)
        - Type 2: Split payments (header row + continuation rows without dates)
        - Type 3: Internal transfers (Debit Mobile Banking prefix)
        """
        import csv

        # Step 1: State machine to parse multi-row CSV
        class ZKBStateMachine:
            def __init__(self, transfer_patterns):
                self.transactions = []
                self.current_date = None
                self.transfer_patterns = transfer_patterns

            def _parse_amount(self, row):
                """Parse amount from Debit/Credit CHF columns."""
                debit_str = row.get("Debit CHF", "").strip()
                credit_str = row.get("Credit CHF", "").strip()
                try:
                    debit = (
                        float(debit_str.replace("'", "").replace(",", ""))
                        if debit_str
                        else 0.0
                    )
                except ValueError:
                    debit = 0.0
                try:
                    credit = (
                        float(credit_str.replace("'", "").replace(",", ""))
                        if credit_str
                        else 0.0
                    )
                except ValueError:
                    credit = 0.0
                return credit - debit

            def process_row(self, row):
                # Strip BOM and quotes from keys (CSV has "Date", "Booking text", etc.)
                row = {k.strip("\ufeff").strip('"'): v for k, v in row.items()}

                date_val = row.get("Date", "").strip()
                booking_text = row.get("Booking text", "").strip()
                amount_details = row.get("Amount details", "").strip()
                payment_purpose = row.get("Payment purpose", "").strip()
                details = row.get("Details", "").strip()

                # Type 3: Internal transfer detection
                if "Mobile Banking" in booking_text and ":" in booking_text:
                    # Extract real payee after colon (e.g., "Debit Mobile Banking: SalsaRica AG")
                    real_payee = booking_text.split(":", 1)[1].strip()
                    booking_text = real_payee

                # Filter out continuation rows AFTER payee extraction
                import re

                should_skip = False
                for pattern, transfer_type in self.transfer_patterns:
                    if transfer_type == "continuation" and re.match(
                        pattern, booking_text, re.IGNORECASE
                    ):
                        should_skip = True
                        break
                if should_skip:
                    return  # Skip this continuation row

                # Type 1: Description override (single row with Payment purpose)
                if date_val and payment_purpose and "Standing order" in booking_text:
                    # Use Payment purpose as the payee, Details for notes
                    self.transactions.append(
                        {
                            "date": date_val,
                            "booking_text": payment_purpose,  # Override with Payment purpose
                            "amount": self._parse_amount(row),
                            "reference": row.get("ZKB reference", ""),
                            "details": details,
                            "is_header": False,
                        }
                    )

                # Type 2a: Split payment header (skip but remember date)
                elif date_val and "(" in booking_text and ")" in booking_text:
                    self.current_date = date_val  # Remember date for continuations

                # Type 2b: Split payment continuation (real transaction)
                elif not date_val and booking_text and amount_details:
                    # Parse amount from "CHF;123.45" format
                    if ";" in amount_details:
                        parts = amount_details.split(";")
                        currency = parts[0] if parts else ""
                        amount_str = (
                            parts[1] if len(parts) > 1 else parts[0] if parts else "0"
                        )
                    else:
                        currency = "CHF"
                        amount_str = amount_details if amount_details else "0"

                    # Convert amount string to float (Swiss format with apostrophe)
                    amount_str = amount_str.replace("'", "").replace(",", ".")
                    try:
                        amount = float(amount_str)
                    except ValueError:
                        amount = 0.0

                    self.transactions.append(
                        {
                            "date": self.current_date,  # Use header's date
                            "booking_text": booking_text,
                            "amount": -amount,  # Split payments are debits
                            "reference": "",
                            "details": f"Split payment",
                            "is_header": False,
                        }
                    )

                # Standard transaction
                elif date_val:
                    self.transactions.append(
                        {
                            "date": date_val,
                            "booking_text": booking_text,
                            "amount": self._parse_amount(row),
                            "reference": row.get("ZKB reference", ""),
                            "details": details,
                            "is_header": False,
                        }
                    )

                # else: Empty row or unrecognized continuation - skip

            def finalize(self):
                return self.transactions

        # Step 2: Process CSV with state machine
        fsm = ZKBStateMachine(self.TRANSFER_PATTERNS)

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                fsm.process_row(row)

        raw_transactions = fsm.finalize()

        # Filter out transactions without dates (edge case)
        raw_transactions = [tx for tx in raw_transactions if tx.get("date")]

        # Step 3: Convert to Polars DataFrame (like Viseca pattern)
        df = pl.DataFrame(raw_transactions)

        # Step 4: Continue with normal Polars processing (date parsing, text cleaning, etc.)
        # Convert date strings to Date type
        df = df.with_columns(
            pl.col("date").str.strptime(pl.Date, "%d.%m.%Y", strict=False).alias("date")
        )

        # Apply date filtering
        if date_from is not None:
            df = df.filter(pl.col("date") >= date_from)
        if date_to is not None:
            df = df.filter(pl.col("date") <= date_to)

        df = (
            df.with_columns(
                pl.col("booking_text")
                .str.replace_all(r"-\d{4,6}\b", "")
                .str.replace_all(r"\s{2,}", " ")
                .str.strip_chars()
                .str.replace_all(r"\bMM\b", "Migros")
                .str.replace_all(r"\bM EX\b", "Migros")
                .str.replace_all(r"\bMMM\b", "Migros")
                .str.replace_all(r"\*", " ")
                .str.replace_all(r"\s{2,}", " ")
                .str.strip_chars()
                # Remove ZKB-specific prefixes (order matters - most specific first)
                .str.replace_all(r"^Purchase ZKB Visa Debit card [Nn]o\. xxxx \d+, ", "")
                .str.replace_all(r"^Online purchase ZKB Visa Debit card no\. xxxx \d+, ", "")
                .str.replace_all(r"^Debit Mobile Banking: ", "")
                .str.replace_all(r"^Credit TWINT: ", "")
                .str.replace_all(r"^Debit TWINT: ", "")
                .str.replace_all(r"^Debit eBill: ", "")
                .str.replace_all(r"^Credit eBill: ", "")
                .str.replace_all(r"^Credit salary: ", "")
                .str.replace_all(r"^Credit Salary: ", "")
                # Generic cleanup
                .str.replace_all(r"\s{2,}", " ")
                .str.strip_chars()
                .alias("booking_text")
            )
            .rename({"booking_text": "Booking text"})
            .filter(~pl.col("Booking text").str.contains("Viseca|Swisscard"))
        )

        self._df = df
        return df

    def _parse_amount_row(self, row):
        """Parse amount from Debit/Credit CHF columns (standard row)."""
        debit_str = row.get("Debit CHF", "").strip()
        credit_str = row.get("Credit CHF", "").strip()

        # Convert and combine (Credit positive, Debit negative)
        try:
            debit = (
                float(debit_str.replace("'", "").replace(",", "")) if debit_str else 0.0
            )
        except ValueError:
            debit = 0.0

        try:
            credit = (
                float(credit_str.replace("'", "").replace(",", ""))
                if credit_str
                else 0.0
            )
        except ValueError:
            credit = 0.0

        return credit - debit

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
                    "amount": float(row["amount"]),
                }
            )

            transaction = Transaction(
                date=row["date"],
                title=row["Booking text"],
                amount=float(row["amount"]),
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
