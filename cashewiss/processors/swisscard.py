from datetime import date
from typing import Optional, List
import polars as pl

from ..core.base import BaseTransactionProcessor, Transaction


class SwisscardProcessor(BaseTransactionProcessor):
    """Processor for Swisscard credit card transactions."""

    SUGGESTED_MERCHANT_CATEGORY_MAPPING = {
        "Auto": {"category": "Transit", "subcategory": None},
        "Entertainment": {"category": "Entertainment", "subcategory": None},
        "Family and Household": {"category": "House", "subcategory": None},
        "Food and Drink": {"category": "Dining", "subcategory": None},
        "Groceries": {"category": "Groceries", "subcategory": None},
        "Health and Beauty": {"category": "Beauty & Health", "subcategory": None},
        "Shopping": {"category": "Shopping", "subcategory": None},
        "Travel": {"category": "Travel", "subcategory": None},
    }

    SUGGESTED_REGISTERED_CATEGORY_MAPPING = {
        # Shopping
        "MEN & WOMEN'S CLOTHING": {"category": "Shopping", "subcategory": "Clothes"},
        "SHOE STORES": {"category": "Shopping", "subcategory": "Clothes"},
        "SPORTING GOODS STORES": {"category": "Shopping", "subcategory": "Clothes"},
        "CATALOG MERCHANTS": {
            "category": "Shopping",
            "subcategory": "Clothes",  # Default to clothes for catalog merchants
        },
        "DUTY FREE STORES": {"category": "Shopping", "subcategory": None},
        "LEATHER GOODS AND LUGGAGE STORES": {
            "category": "Shopping",
            "subcategory": "Clothes",
        },
        # Restaurant Dining
        "EATING PLACES, RESTAURANTS": {
            "category": "Dining",
            "subcategory": "Friends & Co",  # Default to Friends & Co
        },
        "FAST FOOD RESTAURANTS": {"category": "Dining", "subcategory": "Delivery"},
        "BARS, LOUNGES": {"category": "Dining", "subcategory": "Friends & Co"},
        # Groceries
        "GROCERY STORES, SUPERMARKETS": {
            "category": "Groceries",
            "subcategory": "Meal",
        },
        "MISCELLANEOUS FOOD STORES, MARKETS": {
            "category": "Groceries",
            "subcategory": "Meal",
        },
        # Transit and Travel
        "LODGING NOT SPECIFIED": {"category": "Travel", "subcategory": None},
        "PASSENGER RAILWAYS": {"category": "Transit", "subcategory": None},
        "AUTOMOBILE RENTAL": {"category": "Transit", "subcategory": None},
        "TRANSPORTATION SERVICES, NOT SPECIFIED": {
            "category": "Transit",
            "subcategory": None,
        },
        # Entertainment
        "AMUSEMENT AND RECREATION SERVICES": {
            "category": "Entertainment",
            "subcategory": None,
        },
        "DIGITAL GOODS - MEDIA, BOOKS, MOVIES, MUSIC": {
            "category": "Entertainment",
            "subcategory": None,
        },
        # Game stores
        "GAME, TOY, AND HOBBY STORES": {"category": "Shopping", "subcategory": "Games"},
        # Health and Beauty
        "DRUG STORES and Pharmacies": {
            "category": "Beauty & Health",
            "subcategory": "Health",
        },
        "BARBER AND BEAUTY SHOPS": {
            "category": "Beauty & Health",
            "subcategory": "Beauty",
        },
        "DENTAL, HOSPITAL, LAB EQUIPMENT AND SUPPLIES": {
            "category": "Beauty & Health",
            "subcategory": "Health",
        },
        # Bills & Fees
        "TELECOMMUNICATION SERVICE": {
            "category": "Bills & Fees",
            "subcategory": "Telecom",
        },
    }

    SUGGESTED_MERCHANT_MAPPING = {
        # Groceries
        "Coop": {"category": "Groceries", "subcategory": None},
        "Coop Pronto": {"category": "Groceries", "subcategory": "Snacks"},
        "Coop City": {"category": "Groceries", "subcategory": None},
        "Migros": {"category": "Groceries", "subcategory": None},
        "Denner": {"category": "Groceries", "subcategory": None},
        "Lidl": {"category": "Groceries", "subcategory": None},
        "k kiosk": {"category": "Groceries", "subcategory": "Snacks"},
        "Selecta": {"category": "Groceries", "subcategory": "Snacks"},
        # Dining - Restaurants
        "Holy Cow!": {"category": "Dining", "subcategory": "Friends & Co"},
        "GIRO DITALIA": {"category": "Dining", "subcategory": "Friends & Co"},
        "La Penisola": {"category": "Dining", "subcategory": "Friends & Co"},
        "La Penisola 3 Puls 5": {"category": "Dining", "subcategory": "Friends & Co"},
        "La Piadina": {"category": "Dining", "subcategory": "Friends & Co"},
        "Marché": {"category": "Dining", "subcategory": "Friends & Co"},
        "Peking Garden": {"category": "Dining", "subcategory": "Friends & Co"},
        "RESTAURANT PEKING GARDEN": {
            "category": "Dining",
            "subcategory": "Friends & Co",
        },
        "RISTORANTE GALLO D'ORO": {"category": "Dining", "subcategory": "Friends & Co"},
        "Restaurant EAU": {"category": "Dining", "subcategory": "Friends & Co"},
        "Rice Up!": {"category": "Dining", "subcategory": "Work"},
        "Ristorante Toscano": {"category": "Dining", "subcategory": "Friends & Co"},
        "Sapori D'Italia": {"category": "Dining", "subcategory": "Friends & Co"},
        "Tokyo Tapas Markthalle": {"category": "Dining", "subcategory": "Friends & Co"},
        "GASTRO TECHNOPARK ZH": {"category": "Dining", "subcategory": "Work"},
        # Dining - Delivery
        "McDonald's": {"category": "Dining", "subcategory": "Delivery"},
        "Burger King": {"category": "Dining", "subcategory": "Delivery"},
        "Subway": {"category": "Dining", "subcategory": "Delivery"},
        "Too Good To Go": {"category": "Dining", "subcategory": "Delivery"},
        "Uber Eats": {"category": "Dining", "subcategory": "Delivery"},
        "Pizza Kurier Piratino": {"category": "Dining", "subcategory": "Delivery"},
        # Dining - Bars
        "Bar KIR ROYAL": {"category": "Dining", "subcategory": "Friends & Co"},
        "Kir Royal": {"category": "Dining", "subcategory": "Friends & Co"},
        "FAT TONY BAR": {"category": "Dining", "subcategory": "Friends & Co"},
        "El Lokal": {"category": "Dining", "subcategory": "Friends & Co"},
        "Oliver Twist Pub": {"category": "Dining", "subcategory": "Friends & Co"},
        "Paddy Reilly's": {"category": "Dining", "subcategory": "Friends & Co"},
        # House
        "IKEA": {"category": "House", "subcategory": "Furniture"},
        "XLCH AG": {"category": "House", "subcategory": "Furniture"},
        # Shopping
        "WOMO STORE": {"category": "Shopping", "subcategory": "Clothes"},
        "Deichmann": {"category": "Shopping", "subcategory": "Clothes"},
        "FREITAG Geroldstrasse": {"category": "Shopping", "subcategory": "Clothes"},
        "Blue Tomato": {"category": "Shopping", "subcategory": "Clothes"},
        "geschenkidee.ch": {"category": "Gifts", "subcategory": None},
        "Sprüngli": {"category": "Groceries", "subcategory": "Snacks"},
        # Beauty & Health
        "Coop Vitality": {"category": "Beauty & Health", "subcategory": "Health"},
        "Medbase Apotheke": {"category": "Beauty & Health", "subcategory": "Health"},
        "Coiffeur 4 Jallki": {"category": "Beauty & Health", "subcategory": "Beauty"},
        "Akademischer Sportverband Zürich": {
            "category": "Beauty & Health",
            "subcategory": "Health",
        },
        # Entertainment
        "ZÜRICH OPENAIR": {"category": "Entertainment", "subcategory": "Concerts"},
        "ZO Festival AG": {"category": "Entertainment", "subcategory": "Concerts"},
        "Ticketcorner": {"category": "Entertainment", "subcategory": "Concerts"},
        "Sky": {"category": "Entertainment", "subcategory": None},
        "Netflix": {"category": "Entertainment", "subcategory": None},
        "Spotify": {"category": "Entertainment", "subcategory": None},
        # Hobbies
        "Google Cloud": {"category": "Hobbies", "subcategory": "Tech"},
        "Salsarica": {"category": "Hobbies", "subcategory": "Salsa"},
        "Boulderlounge": {"category": "Hobbies", "subcategory": "Bouldern"},
        # Transit
        "SBB CFF FFS": {"category": "Transit", "subcategory": None},
        "ZVV": {"category": "Transit", "subcategory": None},
        "HOTEL ALPINA": {"category": "Travel", "subcategory": None},
        "Mobility": {"category": "Transit", "subcategory": None},
        "GoMore": {"category": "Transit", "subcategory": None},
        "WWW.GOMORE.CH": {"category": "Transit", "subcategory": None},
        "PubliBike": {"category": "Transit", "subcategory": None},
        "Uber": {"category": "Transit", "subcategory": None},
        "Shell": {"category": "Transit", "subcategory": None},
        "Socar": {"category": "Transit", "subcategory": None},
        # Bills & Fees
        "Google": {"category": "Bills & Fees", "subcategory": "Telecom"},
        # Work
        "Swiss Post": {"category": "Work", "subcategory": None},
        "UPS_CH": {"category": "Work", "subcategory": None},
        "PRINTFUL, INC.": {"category": "Work", "subcategory": None},
        "Printful": {"category": "Work", "subcategory": None},
    }

    def __init__(self, name: str = "SwissCard"):
        # Set both category and merchant mappings by default
        super().__init__(name=name)
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
        self.set_category_mapper(self.SUGGESTED_MERCHANT_MAPPING, self.merchant_column)

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
            mapped_categories = self._map_category(row)

            transaction = Transaction(
                date=row["Transaction date"],
                title=row.get(self.merchant_column) or row[self.description_column],
                amount=-float(
                    row["Amount"]
                ),  # Negate amount since debit is positive in source
                currency=row["Currency"],
                notes=self.name,
                category=mapped_categories["category"],
                subcategory=mapped_categories["subcategory"],
                account="Sanzio",
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
