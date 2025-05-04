from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, Dict, Any, List

import polars as pl

from .models import Transaction, ProcessorConfig, CategoryMapping
from .enums import (
    BillsSubcategory,
    Category,
    DiningSubcategory,
    EssentialsSubcategory,
    HouseholdSubcategory,
    IncomeSubcategory,
    ShoppingSubcategory,
    LeisureSubcategory,
    PersonalCareSubcategory,
    HobbiesSubcategory,
    TravelSubcategory,
)


class TransactionBatch:
    def __init__(self, transactions: List[Transaction], source: str):
        self.transactions = transactions
        self.source = source

    def to_cashew_format(self) -> List[Dict[str, Any]]:
        """Convert transactions to Cashew API format."""
        return [
            {
                "date": t.date.isoformat(),
                "title": t.title,
                "amount": t.amount,
                "currency": t.currency,
                "category": t.category.value if t.category else None,
                "subcategory": t.subcategory.value if t.subcategory else None,
                "account": t.account,
                "notes": t.notes,
            }
            for t in self.transactions
        ]


class BaseTransactionProcessor(ABC):
    """Base class for transaction processors with shared merchant mappings."""

    # Shared merchant mappings for all processors
    SUGGESTED_MERCHANT_MAPPING = {
        "boulderlounge": CategoryMapping(
            category=Category.HOBBIES, subcategory=HobbiesSubcategory.BOULDERN
        ),
        "publibike": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
        ),
        "salsarica": CategoryMapping(
            category=Category.HOBBIES, subcategory=HobbiesSubcategory.SALSA
        ),
        "theater": CategoryMapping(
            category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
        ),
        "kir": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
        ),
        "minimum": CategoryMapping(
            category=Category.HOBBIES, subcategory=HobbiesSubcategory.BOULDERN
        ),
        "minimum-": CategoryMapping(
            category=Category.HOBBIES, subcategory=HobbiesSubcategory.BOULDERN
        ),
        "gastro technopark zh": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.WORK
        ),
        "sv": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.WORK
        ),
        "plaza": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
        ),
        "too good to go": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.DATE
        ),
        "toogoodt": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.DATE
        ),
        "google": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.MEDIA
        ),
        "blue tomato": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.CLOTHING
        ),
        "burger king": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.DELIVERY
        ),
        "mcdonald's": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.DELIVERY
        ),
        "coiffeur": CategoryMapping(
            category=Category.PERSONAL_CARE,
            subcategory=PersonalCareSubcategory.PERSONAL,
        ),
        "ikea": CategoryMapping(
            category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.DECOR
        ),
        "pub": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
        ),
        "lokal": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
        ),
        "nelson": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
        ),
        "paddy's": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
        ),
        "mobility": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
        ),
        "sbb": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
        ),
        "zvv": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
        ),
        "swiss post": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.WORK
        ),
        "uber eats": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.DELIVERY
        ),
        "openair": CategoryMapping(
            category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
        ),
        "hallenstadion": CategoryMapping(
            category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
        ),
        "gomore.ch": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
        ),
        "helvetia": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.INSURANCE
        ),
        "jumbo": CategoryMapping(
            category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.DECOR
        ),
        "jysk": CategoryMapping(
            category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.FURNITURE
        ),
        "bett0.ch": CategoryMapping(
            category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.FURNITURE
        ),
        "kkl": CategoryMapping(
            category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
        ),
        "swiss international air lines": CategoryMapping(
            category=Category.TRAVEL, subcategory=TravelSubcategory.TRANSPORT
        ),
        "booking.com": CategoryMapping(
            category=Category.TRAVEL, subcategory=TravelSubcategory.ACCOMMODATION
        ),
        "ticketino": CategoryMapping(
            category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
        ),
        "netflix": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.SUBSCRIPTIONS
        ),
        "spotify": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.SUBSCRIPTIONS
        ),
        "sky": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.SUBSCRIPTIONS
        ),
        "amavita": CategoryMapping(
            category=Category.PERSONAL_CARE, subcategory=PersonalCareSubcategory.MEDICAL
        ),
        "vitality": CategoryMapping(
            category=Category.PERSONAL_CARE, subcategory=PersonalCareSubcategory.MEDICAL
        ),
        "see tickets": CategoryMapping(
            category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
        ),
        "gelateria": CategoryMapping(category=Category.DINING),
        "apotheke": CategoryMapping(
            category=Category.PERSONAL_CARE, subcategory=PersonalCareSubcategory.MEDICAL
        ),
        "microsoft": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.MEDIA
        ),
        "home 24": CategoryMapping(
            category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.DECOR
        ),
        "just eat": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.DELIVERY
        ),
        "swiss": CategoryMapping(
            category=Category.TRAVEL, subcategory=TravelSubcategory.TRANSPORT
        ),
        "easyjet": CategoryMapping(
            category=Category.TRAVEL, subcategory=TravelSubcategory.TRANSPORT
        ),
        "bitwarden.com": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.SUBSCRIPTIONS
        ),
        "xlch": CategoryMapping(
            category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.FURNITURE
        ),
        "aliexpress": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.ELECTRONICS
        ),
        "sunrise": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.TELECOM
        ),
        "elektrizitätswerk": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.UTILITIES
        ),
        "salär": CategoryMapping(
            category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.CLEANING
        ),
        "baugenossenschaft": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.RENT
        ),
        "serafe": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.UTILITIES
        ),
        "touring": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.INSURANCE
        ),
        "mensile": CategoryMapping(category=Category.INCOME),
        "sva": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.INSURANCE
        ),
        "helsana": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.INSURANCE
        ),
    }

    def __init__(self, name: str):
        self.name = name
        self._df: Optional[pl.DataFrame] = None
        self._loaded_data: Optional[pl.DataFrame] = None
        self._transformed_data: Optional[List[Transaction]] = None
        self._config = ProcessorConfig(name=name)

        # Default column names that can be overridden by processors
        self.merchant_column: str = "Merchant"
        self.merchant_category_column: str = "Merchant Category"
        self.description_column: str = "Description"
        self.registered_category_column: str = "Registered Category"
        self.amount_column: str = "Amount"

        # Initialize base mappings with shared merchant mappings
        self.set_category_mapper(self.SUGGESTED_MERCHANT_MAPPING, self.merchant_column)

    def set_default_merchant_mapping(self):
        """
        Set default merchant mapping for the processor.

        This method should be overridden by subclasses to provide specific
        merchant mappings.
        """
        self.set_category_mapper(self.SUGGESTED_MERCHANT_MAPPING, self.merchant_column)

    def set_category_mapper(
        self, mapper: Dict[str, CategoryMapping], mapper_type: str
    ) -> None:
        """
        Update the category mapping dictionary with validation.

        Args:
            mapper: A dictionary mapping merchant names to CategoryMapping objects
            mapper_type: The type of mapper to update (merchant, merchant_category, or registered_category)
        """
        if mapper_type == self.merchant_column:
            target_mappings = self._config.merchant_mappings
        elif mapper_type == self.merchant_category_column:
            target_mappings = self._config.merchant_category_mappings
        elif mapper_type == self.registered_category_column:
            target_mappings = self._config.registered_category_mappings
        else:
            raise ValueError(f"Unknown mapper type: {mapper_type}")

        # Store all keys as lowercase
        for key, value in mapper.items():
            # Convert key to lowercase for case-insensitive matching
            key_lower = key.lower()
            # If value is already a CategoryMapping, use it directly
            if isinstance(value, CategoryMapping):
                target_mappings[key_lower] = value
            else:
                # Otherwise, create a new CategoryMapping from the dict
                target_mappings[key_lower] = CategoryMapping(
                    category=value["category"], subcategory=value.get("subcategory")
                )

    def _map_category(self, row: Dict[str, Any]) -> CategoryMapping:
        """
        Map transaction data to standardized category and subcategory using multiple strategies.

        Args:
            row: The transaction row data

        Returns:
            CategoryMapping object with category and optional subcategory
        """
        # Try merchant mapping first
        if self.merchant_column and row.get(self.merchant_column):
            merchant = row[self.merchant_column]

            # First try exact match
            merchant_lower = merchant.lower()
            if mapping := self._config.merchant_mappings.get(merchant_lower):
                return mapping

            # Then try matching any word in the merchant name
            merchant_words = set(merchant_lower.split())
            for word in merchant_words:
                if mapping := self._config.merchant_mappings.get(word):
                    return mapping

        # Try merchant category mapping (case-insensitive)
        if self.merchant_category_column and row.get(self.merchant_category_column):
            category_lower = row[self.merchant_category_column].lower()
            if mapping := self._config.merchant_category_mappings.get(category_lower):
                return mapping

        # Try registered category mapping (case-insensitive)
        if self.registered_category_column and row.get(self.registered_category_column):
            registered_lower = row[self.registered_category_column].lower()
            if mapping := self._config.registered_category_mappings.get(
                registered_lower
            ):
                return mapping

        # For default categorization, check if it's a credit (positive amount)
        is_twint = "twint" in row.get(self.merchant_column, "").lower()
        if self.amount_column in row and float(row[self.amount_column]) > 0:
            return CategoryMapping(
                category=Category.INCOME,
                subcategory=IncomeSubcategory.TWINT if is_twint else None,
            )
        return (
            CategoryMapping(
                category=Category.DINING, subcategory=DiningSubcategory.TWINT
            )
            if is_twint
            else CategoryMapping(category=Category.SHOPPING, subcategory=None)
        )

    @abstractmethod
    def load_data(
        self,
        file_path: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> pl.DataFrame:
        """Load transaction data from file with optional date filtering."""
        pass

    @abstractmethod
    def transform_data(self) -> List[Transaction]:
        """Transform the loaded data into Transaction objects."""
        pass

    def process(
        self,
        file_path: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> TransactionBatch:
        """Process the transaction file and return a TransactionBatch."""
        # Load and transform data
        self._df = self.load_data(file_path, date_from, date_to)
        self._transformed_data = self.transform_data()
        return TransactionBatch(
            transactions=self._transformed_data, source=self.__class__.__name__
        )
