from enum import Enum
from typing import Dict, Optional, Type

from pydantic import BaseModel, field_validator


class DiningSubcategory(str, Enum):
    WORK = "Work"
    DATE = "Date"
    DELIVERY = "Delivery"
    FRIENDS = "Friends & Co"


class GroceriesSubcategory(str, Enum):
    SNACKS = "Snacks"
    MEAL = "Meal"


class ShoppingSubcategory(str, Enum):
    CLOTHES = "Clothes"
    ELECTRONICS = "Electronics"
    GAMES = "Games"
    KITCHEN = "Kitchen"


class EntertainmentSubcategory(str, Enum):
    CONCERTS = "Concerts"


class BillsFeesSubcategory(str, Enum):
    TELECOM = "Telecom"
    RENT = "Rent"
    HEALTH = "Health"


class BeautyHealthSubcategory(str, Enum):
    HEALTH = "Health"
    BEAUTY = "Beauty"


class HobbiesSubcategory(str, Enum):
    BOULDERN = "Bouldern"
    SALSA = "Salsa"
    TECH = "Tech"


class HouseSubcategory(str, Enum):
    CLEANING = "Cleaning"
    GADGETS = "Gadgets"
    FURNITURE = "Furniture"


class Category(str, Enum):
    DINING = "Dining"
    GROCERIES = "Groceries"
    SHOPPING = "Shopping"
    TRANSIT = "Transit"
    ENTERTAINMENT = "Entertainment"
    BILLS_FEES = "Bills & Fees"
    GIFTS = "Gifts"
    BEAUTY_HEALTH = "Beauty & Health"
    WORK = "Work"
    TRAVEL = "Travel"
    INCOME = "Income"
    HOUSE = "House"
    INVESTMENTS = "Investments"
    HOBBIES = "Hobbies"


# Mapping categories to their subcategory enum types
SUBCATEGORY_TYPES: Dict[Category, Type[Enum]] = {
    Category.DINING: DiningSubcategory,
    Category.GROCERIES: GroceriesSubcategory,
    Category.SHOPPING: ShoppingSubcategory,
    Category.ENTERTAINMENT: EntertainmentSubcategory,
    Category.BILLS_FEES: BillsFeesSubcategory,
    Category.BEAUTY_HEALTH: BeautyHealthSubcategory,
}


class CategoryMapping(BaseModel):
    """
    Represents a mapping from a provider category to Cashew category/subcategory.

    Validates that if a subcategory is provided, it's valid for the given category.
    """

    category: Category
    subcategory: Optional[Enum] = None

    @field_validator("subcategory")
    @classmethod
    def validate_subcategory(
        cls, subcategory: Optional[Enum], values: Dict
    ) -> Optional[Enum]:
        if subcategory is None:
            return None

        category = values.get("category")
        if category is None:
            raise ValueError("Category must be provided to validate subcategory")

        subcategory_type = SUBCATEGORY_TYPES.get(category)
        if subcategory_type is None:  # Category doesn't have subcategories
            raise ValueError(
                f"Category '{category.value}' does not support subcategories"
            )

        if not isinstance(subcategory, subcategory_type):
            raise ValueError(
                f"Invalid subcategory type for category '{category.value}'. "
                f"Expected {subcategory_type.__name__}, got {type(subcategory).__name__}"
            )
        return subcategory


class ProviderCategoryMapper:
    """Helper class to manage provider category mappings with validation."""

    def __init__(self):
        self._mappings: Dict[str, CategoryMapping] = {}

    def add_mapping(
        self,
        provider_category: str,
        category: Category,
        subcategory: Optional[Enum] = None,
    ) -> None:
        """
        Add a mapping with validation.

        Args:
            provider_category: The category string from the provider
            category: The Cashew category enum value
            subcategory: Optional subcategory enum value (e.g., DiningSubcategory.WORK)
        """
        self._mappings[provider_category] = CategoryMapping(
            category=category, subcategory=subcategory
        )

    def get_mapping(self, provider_category: str) -> Optional[CategoryMapping]:
        """Get the mapping for a provider category if it exists."""
        return self._mappings.get(provider_category)

    def to_dict(self) -> Dict[str, Dict[str, Optional[str]]]:
        """Convert mappings to the format expected by BaseTransactionProcessor."""
        return {
            provider_cat: {
                "category": mapping.category.value,
                "subcategory": mapping.subcategory.value
                if mapping.subcategory
                else None,
            }
            for provider_cat, mapping in self._mappings.items()
        }
