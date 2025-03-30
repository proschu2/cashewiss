from datetime import date, datetime
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
    EssentialsSubcategory,
    ShoppingSubcategory,
    LeisureSubcategory,
    BillsSubcategory,
    PersonalCareSubcategory,
    TravelSubcategory,
)


class VisecaProcessor(BaseTransactionProcessor):
    """Processor for Viseca credit card transactions."""

    SUGGESTED_MERCHANT_CATEGORY_MAPPING = {
        # Viseca specific categories
        "Bakery": CategoryMapping(category=Category.DINING),
        "Bar/Club": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
        ),
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
        "Restaurant": CategoryMapping(category=Category.DINING),
        "Supermarket": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
        ),
        "Shopping": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.CLOTHING
        ),
        "Fast Food Restaurant": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.DELIVERY
        ),
        "Hotel": CategoryMapping(
            category=Category.TRAVEL, subcategory=TravelSubcategory.ACCOMMODATION
        ),
        "Music Festival/concert": CategoryMapping(
            category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
        ),
        "Cosmetic/Perfumery": CategoryMapping(
            category=Category.PERSONAL_CARE,
            subcategory=PersonalCareSubcategory.PERSONAL,
        ),
        "Electronics": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.ELECTRONICS
        ),
        "Taxi": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
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

        try:
            self._client = VisecaClient(self._username, self._password)
        except Exception as e:
            raise ValueError(f"Failed to initialize Viseca client: {str(e)}")

    def load_data(
        self,
        file_path: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> pl.DataFrame:
        """
        Load Viseca transaction data using the Viseca API.
        Note: file_path is kept for compatibility with BaseTransactionProcessor but is ignored.

        Args:
            file_path: Ignored. Data is always fetched from the Viseca API.
            date_from: Optional start date for filtering transactions
            date_to: Optional end date for filtering transactions

        Returns:
            A Polars DataFrame containing the transaction data
        """
        from viseca import format_transactions

        # Convert date objects to datetime if they are strings, otherwise keep as is
        date_from_dt = (
            datetime.strptime(date_from, "%Y-%m-%d")
            if isinstance(date_from, str)
            else date_from
            if date_from is not None
            else None
        )
        date_to_dt = (
            datetime.strptime(date_to, "%Y-%m-%d")
            if isinstance(date_to, str)
            else date_to
            if date_to is not None
            else None
        )

        all_transactions = []
        offset = 0
        page_size = 100

        while True:
            transactions = self._client.list_transactions(
                self._card_id,
                date_from=date_from_dt,
                date_to=date_to_dt,
                offset=offset,
                page_size=page_size,
            )
            all_transactions.extend(transactions)

            if len(transactions) < page_size:
                break

            offset += page_size

        df = format_transactions(all_transactions)
        self._df = pl.DataFrame(df).filter(
            (pl.col("PFMCategoryID") != "cv_not_categorized")
            & (pl.col("Name") != "")
            & (pl.col("Amount") > 0)
        )
        return self._df

    def transform_data(self) -> List[Transaction]:
        """Transform Viseca data into standardized Transaction objects."""
        if self._df is None:
            raise ValueError("No data loaded. Call load_data() first.")

        transactions = []

        for row in self._df.iter_rows(named=True):
            # Map categories using the row data
            mapping = self._map_category(row)
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
