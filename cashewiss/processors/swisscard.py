from datetime import date
from typing import Optional, List
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
    HouseholdSubcategory,
)


class SwisscardProcessor(BaseTransactionProcessor):
    """Processor for Swisscard credit card transactions."""

    SUGGESTED_MERCHANT_CATEGORY_MAPPING = {
        # Swisscard specific categories
        "Auto": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
        ),
        "Family and Household": CategoryMapping(category=Category.HOUSEHOLD),
        "Food and Drink": CategoryMapping(category=Category.DINING),
        "Health and Beauty": CategoryMapping(category=Category.PERSONAL_CARE),
        "Groceries": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
        ),
        "Entertainment": CategoryMapping(category=Category.LEISURE),
        "Travel": CategoryMapping(category=Category.TRAVEL),
    }

    SUGGESTED_REGISTERED_CATEGORY_MAPPING = {
        # Shopping
        "MEN & WOMEN'S CLOTHING": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.CLOTHING
        ),
        "SHOE STORES": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.CLOTHING
        ),
        "SPORTING GOODS STORES": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.CLOTHING
        ),
        "CATALOG MERCHANTS": CategoryMapping(category=Category.SHOPPING),
        "DUTY FREE STORES": CategoryMapping(category=Category.SHOPPING),
        "LEATHER GOODS AND LUGGAGE STORES": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.CLOTHING
        ),
        # Restaurant Dining
        "EATING PLACES, RESTAURANTS": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
        ),
        "FAST FOOD RESTAURANTS": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.DELIVERY
        ),
        "BARS, LOUNGES": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
        ),
        # Groceries
        "GROCERY STORES, SUPERMARKETS": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
        ),
        "MISCELLANEOUS FOOD STORES, MARKETS": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
        ),
        # Transit and Travel
        "LODGING NOT SPECIFIED": CategoryMapping(category=Category.TRAVEL),
        "PASSENGER RAILWAYS": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
        ),
        "AUTOMOBILE RENTAL": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
        ),
        "TRANSPORTATION SERVICES, NOT SPECIFIED": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
        ),
        # Entertainment
        "AMUSEMENT AND RECREATION SERVICES": CategoryMapping(
            category=Category.LEISURE, subcategory=LeisureSubcategory.ACTIVITIES
        ),
        "DIGITAL GOODS - MEDIA, BOOKS, MOVIES, MUSIC": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.MEDIA
        ),
        # Game stores
        "GAME, TOY, AND HOBBY STORES": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.MEDIA
        ),
        # Health and Beauty
        "DRUG STORES and Pharmacies": CategoryMapping(
            category=Category.PERSONAL_CARE, subcategory=PersonalCareSubcategory.MEDICAL
        ),
        "BARBER AND BEAUTY SHOPS": CategoryMapping(
            category=Category.PERSONAL_CARE,
            subcategory=PersonalCareSubcategory.PERSONAL,
        ),
        "DENTAL, HOSPITAL, LAB EQUIPMENT AND SUPPLIES": CategoryMapping(
            category=Category.PERSONAL_CARE, subcategory=PersonalCareSubcategory.MEDICAL
        ),
        # Bills & Fees
        "TELECOMMUNICATION SERVICE": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.TELECOM
        ),
        # Household
        "EQUIPMENT, FURNITURE STORES": CategoryMapping(
            category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.FURNITURE
        ),
    }

    def __init__(self, name: str = "SwissCard", account: Optional[str] = None):
        # Set both category and merchant mappings by default
        super().__init__(name=name)
        self.account_name = account or name
        # Override default column names for Swisscard format
        self.merchant_column = "Merchant"
        self.merchant_category_column = "Merchant Category"
        self.description_column = "Description"
        self.registered_category_column = "Registered Category"
        self.set_category_mapper(
            self.SUGGESTED_MERCHANT_CATEGORY_MAPPING, self.merchant_category_column
        )
        self.set_category_mapper(
            self.SUGGESTED_REGISTERED_CATEGORY_MAPPING, self.registered_category_column
        )

    def load_data(
        self,
        file_path: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> pl.DataFrame:
        """
        Load Swisscard transaction data from XLSX file.

        Expected XLSX format has columns:
        Transaction date, Description, Merchant, Card number, Currency, Amount,
        Foreign Currency, Amount in foreign currency, Debit/Credit, Status,
        Merchant Category, Registered Category
        """
        df = pl.read_excel(file_path)

        # Ensure required columns exist
        required_cols = [
            "Transaction date",
            self.description_column,
            "Amount",
            "Currency",
            self.merchant_category_column,
            self.registered_category_column,
            "Status",
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

        # Apply date filtering if provided
        if date_from is not None:
            df = df.filter(pl.col("Transaction date") >= date_from)
        if date_to is not None:
            df = df.filter(pl.col("Transaction date") <= date_to)
        self._df = df
        return df

    def transform_data(self) -> List[Transaction]:
        """Transform Swisscard data into standardized Transaction objects."""
        if self._df is None:
            raise ValueError("No data loaded. Call load_data() first.")

        transactions = []

        # Convert DataFrame to list of Transaction objects
        for row in self._df.iter_rows(named=True):
            # Only include posted transactions that are debits
            if row["Status"] != "Posted" or row["Debit/Credit"] == "Credit":
                continue

            # Map categories using the row data
            mapping = self._map_category(row)

            transaction = Transaction(
                date=row["Transaction date"],
                title=row.get(self.merchant_column) or row[self.description_column],
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
                    "card_number": row["Card number"],
                    "foreign_currency": row.get("Foreign Currency"),
                    "foreign_amount": row.get("Amount in foreign currency"),
                    "original_merchant_category": row.get(
                        self.merchant_category_column
                    ),
                    "original_registered_category": row.get(
                        self.registered_category_column
                    )
                    if self.registered_category_column
                    else None,
                    "original_row": row,
                },
            )
            transactions.append(transaction)

        self._transformed_data = transactions
        return transactions
