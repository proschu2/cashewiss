from datetime import date
import importlib.util
import os
from typing import Optional, List

from dotenv import load_dotenv

import polars as pl

from ..core.base import BaseTransactionProcessor, Transaction
from ..core.models import CategoryMapping
from ..core.enums import (
    Category,
    DiningSubcategory,
    ShoppingSubcategory,
    LeisureSubcategory,
    BillsSubcategory,
    PersonalCareSubcategory,
)


class VisecaProcessor(BaseTransactionProcessor):
    """Processor for Viseca credit card transactions."""

    # Empty since merchant mappings are now in base class
    SUGGESTED_MERCHANT_MAPPING = {}

    SUGGESTED_MERCHANT_CATEGORY_MAPPING = {
        # Viseca specific categories
        "Bakery": CategoryMapping(category=Category.DINING),
        "Bar/Club": CategoryMapping(category=Category.LEISURE),
        "Canteen": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.WORK
        ),
        "Book Shop": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.MEDIA
        ),
        "Office Supply": CategoryMapping(category=Category.SHOPPING),
        "Sport Shop": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.CLOTHING
        ),
        "Tobacco Smoking Related Store": CategoryMapping(category=Category.SHOPPING),
        "Amusement Park": CategoryMapping(
            category=Category.LEISURE, subcategory=LeisureSubcategory.ACTIVITIES
        ),
        "Leisure Activities": CategoryMapping(
            category=Category.LEISURE, subcategory=LeisureSubcategory.ACTIVITIES
        ),
        "Sport": CategoryMapping(category=Category.LEISURE),
        "Theatre/Opera/Orchestra/Ballet": CategoryMapping(
            category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
        ),
        "Hairdresser": CategoryMapping(
            category=Category.PERSONAL_CARE,
            subcategory=PersonalCareSubcategory.PERSONAL,
        ),
        "School": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.FEES
        ),
    }

    def __init__(
        self,
        name: str = "Viseca",
        username: Optional[str] = None,
        password: Optional[str] = None,
        card_id: Optional[str] = None,
        account: Optional[str] = None,
    ):
        super().__init__(name=name)
        self.account_name = account or name
        # Override default column names for Viseca format
        self.merchant_column = "Name"
        self.merchant_category_column = "PFMCategoryName"
        self.description_column = "Merchant"
        self.registered_category_column = (
            None  # Viseca doesn't have registered categories
        )

        self.set_category_mapper(self.SUGGESTED_MERCHANT_MAPPING, self.merchant_column)
        self.set_category_mapper(
            self.SUGGESTED_MERCHANT_CATEGORY_MAPPING, self.merchant_category_column
        )
        load_dotenv()

        # Use either provided credentials or environment variables
        self._username = username or os.environ.get("VISECA_USERNAME")
        self._password = password or os.environ.get("VISECA_PASSWORD")
        self._card_id = card_id or os.environ.get("VISECA_CARD_ID")

        if not all([self._username, self._password, self._card_id]):
            raise ValueError(
                "Missing credentials. Provide either through constructor or environment variables: "
                "VISECA_USERNAME, VISECA_PASSWORD, VISECA_CARD_ID"
            )

        # Check if viseca package is installed
        if importlib.util.find_spec("viseca") is None:
            raise ImportError(
                "viseca package is not installed. Install it with: pip install cashewiss[viseca]"
            )

        # Initialize the Viseca client
        from viseca import VisecaClient

        self._client = VisecaClient(self._username, self._password)

    def load_data(
        self,
        file_path: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> pl.DataFrame:
        """
        Load Viseca transaction data using the Viseca API.
        Note: file_path is ignored as data is fetched directly from the API.
        """
        # Fetch transactions from Viseca API
        from viseca import format_transactions

        transactions = self._client.list_transactions(self._card_id)
        df = format_transactions(transactions)

        # Convert to Polars DataFrame
        df = pl.DataFrame(df)

        # Apply date filtering if provided
        if date_from is not None:
            df = df.filter(pl.col("date") >= date_from)
        if date_to is not None:
            df = df.filter(pl.col("date") <= date_to)

        self._df = df
        return df

    def transform_data(self) -> List[Transaction]:
        """Transform Viseca data into standardized Transaction objects."""
        if self._df is None:
            raise ValueError("No data loaded. Call load_data() first.")

        transactions = []

        for row in self._df.iter_rows(named=True):
            # Map categories using the row data
            mapping = self._map_category(row)
            print(row, mapping)
            transaction = Transaction(
                date=row["Date"],
                title=row[self.merchant_column],
                amount=-float(
                    row["Amount"]
                ),  # Negate amount since debit is positive in source
                currency=row["Currency"],
                notes=self.name,
                category=mapping.category,
                subcategory=mapping.subcategory,
                account=self.account_name,
                meta={
                    "processor": self.name,
                    "original_merchant_category": row.get(
                        self.merchant_category_column
                    ),
                    "original_row": row,
                },
            )
            transactions.append(transaction)

        self._transformed_data = transactions
        return transactions
