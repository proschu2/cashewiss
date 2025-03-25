from datetime import date
import importlib.util
import os
from typing import Optional, List

from dotenv import load_dotenv

import polars as pl

from ..core.base import BaseTransactionProcessor, Transaction


class VisecaProcessor(BaseTransactionProcessor):
    """Processor for Viseca credit card transactions."""

    SUGGESTED_MERCHANT_MAPPING = {
        # Groceries
        "Denner": {"category": "Groceries", "subcategory": "Meal"},
        "Lidl": {"category": "Groceries", "subcategory": "Meal"},
        "Migros": {"category": "Groceries", "subcategory": "Meal"},
        "Coop": {"category": "Groceries", "subcategory": "Meal"},
        "Volg": {"category": "Groceries", "subcategory": "Meal"},
        "Alnatura": {"category": "Groceries", "subcategory": "Meal"},
        "Migrolino": {"category": "Groceries", "subcategory": "Snacks"},
        "Coop Pronto": {"category": "Groceries", "subcategory": "Snacks"},
        "Selecta": {"category": "Groceries", "subcategory": "Snacks"},
        # Restaurants & Dining
        "ZETT Restaurant": {"category": "Dining", "subcategory": "Friends"},
        "Pho Vietnam ZH": {"category": "Dining", "subcategory": "Friends"},
        "Migros Restaurant": {"category": "Dining", "subcategory": "Work"},
        "La Penisola": {"category": "Dining", "subcategory": "Friends"},
        "McDonald's": {"category": "Dining", "subcategory": "Delivery"},
        "Too Good To Go": {"category": "Dining", "subcategory": "Delivery"},
        "Restaurant Talstation Rotair": {
            "category": "Dining",
            "subcategory": "Friends",
        },
        "Stern Gastro-Imbiss Inh.M": {"category": "Dining", "subcategory": "Delivery"},
        "Escher Wyss Platz Kebap G": {"category": "Dining", "subcategory": "Delivery"},
        "Bo's Co Gastro GmbH": {"category": "Dining", "subcategory": "Friends"},
        "SV (Schweiz) AG": {"category": "Dining", "subcategory": "Work"},
        # Bakeries
        "Bäckerei Hug": {"category": "Dining", "subcategory": None},
        "St Jakob Beck im Viadukt": {"category": "Dining", "subcategory": None},
        # Bars & Entertainment
        "Plaza Klub Zürich": {"category": "Entertainment", "subcategory": "Concerts"},
        "Barmuenster": {"category": "Entertainment", "subcategory": None},
        "Moods": {"category": "Entertainment", "subcategory": "Concerts"},
        "Bar KIR ROYAL": {"category": "Entertainment", "subcategory": None},
        "Hallenstadion Zürich": {
            "category": "Entertainment",
            "subcategory": "Concerts",
        },
        "Theater 00 Zuerich": {"category": "Entertainment", "subcategory": "Concerts"},
        "Rent-a-Theater AG": {"category": "Entertainment", "subcategory": "Concerts"},
        "Wendel's Kapelle": {"category": "Entertainment", "subcategory": "Concerts"},
        "Kafi Schnaps": {"category": "Entertainment", "subcategory": None},
        "Enfant terrible Gastro Gm": {"category": "Entertainment", "subcategory": None},
        # Sports & Hobbies
        "Boulderlounge": {"category": "Hobbies", "subcategory": "Bouldern"},
        "Minimum- Boulder Bar Leut": {"category": "Hobbies", "subcategory": "Bouldern"},
        "Kraftreaktor Aarau AG": {"category": "Hobbies", "subcategory": "Bouldern"},
        "SalsaRica AG": {"category": "Hobbies", "subcategory": "Salsa"},
        # Shopping
        "Decathlon": {"category": "Shopping", "subcategory": None},
        "InMedia Haus GmbH": {"category": "Shopping", "subcategory": "Electronics"},
        "Orell Füssli": {"category": "Shopping", "subcategory": None},
        "Transa Backpacking AG": {"category": "Shopping", "subcategory": "Clothes"},
        "SportX": {"category": "Shopping", "subcategory": None},
        # Escape Rooms & Games
        "Zuerichtheescape.p": {"category": "Entertainment", "subcategory": None},
        "Live Escape Game Schwe": {"category": "Entertainment", "subcategory": None},
        "the escape GmbH": {"category": "Entertainment", "subcategory": None},
        # Beauty & Health
        "Coiffeur Tablo": {"category": "Beauty & Health", "subcategory": "Beauty"},
        "Coiffeur 0 Jallki": {"category": "Beauty & Health", "subcategory": "Beauty"},
        # Transit
        "Uber": {"category": "Transit", "subcategory": None},
        "PubliBike": {"category": "Transit", "subcategory": None},
        # Travel & Hotels
        "Hotel Sporting": {"category": "Travel", "subcategory": None},
        "Berghus Spirstock": {"category": "Travel", "subcategory": None},
        # Others/Uncategorized
        "Sujanth GmbH": {"category": "Shopping", "subcategory": None},
        "Maison Leo AG": {"category": "Shopping", "subcategory": None},
        "Genossenschaft Schweiz": {"category": "Shopping", "subcategory": None},
        "POSTFINANCE Piazza Bar B": {"category": "Shopping", "subcategory": None},
        None: {"category": "Shopping", "subcategory": None},
    }

    SUGGESTED_MERCHANT_CATEGORY_MAPPING = {
        # Food & Dining Related
        "Bakery": {"category": "Dining", "subcategory": None},
        "Bar/Club": {"category": "Entertainment", "subcategory": None},
        "Canteen": {"category": "Dining", "subcategory": "Work"},
        "Fast Food Restaurant": {"category": "Dining", "subcategory": "Delivery"},
        "Food": {"category": "Dining", "subcategory": None},
        "Restaurant": {"category": "Dining", "subcategory": None},
        "Supermarket": {"category": "Groceries", "subcategory": "Meal"},
        # Shopping & Retail
        "Book Shop": {"category": "Shopping", "subcategory": None},
        "Office Supply": {"category": "Shopping", "subcategory": None},
        "Shopping": {"category": "Shopping", "subcategory": None},
        "Sport Shop": {"category": "Shopping", "subcategory": None},
        "Tobacco Smoking Related Store": {"category": "Shopping", "subcategory": None},
        # Entertainment & Leisure
        "Amusement Park": {"category": "Entertainment", "subcategory": None},
        "Leisure Activities": {"category": "Entertainment", "subcategory": None},
        "Sport": {"category": "Hobbies", "subcategory": None},
        "Theatre/Opera/Orchestra/Ballet": {
            "category": "Entertainment",
            "subcategory": "Concerts",
        },
        # Services
        "Hairdresser": {"category": "Beauty & Health", "subcategory": "Beauty"},
        "Hotel": {"category": "Travel", "subcategory": None},
        # Transportation
        "Public Transport": {"category": "Transit", "subcategory": None},
        "Taxi": {"category": "Transit", "subcategory": None},
        # Education
        "School": {"category": "Bills & Fees", "subcategory": None},
    }

    def __init__(
        self,
        name: str = "Viseca",
        username: Optional[str] = None,
        password: Optional[str] = None,
        card_id: Optional[str] = None,
    ):
        super().__init__(name=name)
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

        # Load environment variables from .env file
        load_dotenv()

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
            mapped_categories = self._map_category(row)

            transaction = Transaction(
                date=row["date"],
                title=row["description"],
                amount=-float(
                    row["amount"]
                ),  # Negate amount since debit is positive in source
                currency=row["currency"],
                notes=self.name,
                category=mapped_categories["category"],
                subcategory=mapped_categories["subcategory"],
                account=self.name,
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
