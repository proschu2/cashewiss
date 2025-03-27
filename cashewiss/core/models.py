from typing import Dict, Optional, Any, Type
from enum import Enum
from datetime import date
from pydantic import BaseModel, Field, ValidationInfo, field_validator

from .enums import (
    Category,
    IncomeSubcategory,
    BillsSubcategory,
    EssentialsSubcategory,
    DiningSubcategory,
    ShoppingSubcategory,
    HouseholdSubcategory,
    PersonalCareSubcategory,
    LeisureSubcategory,
    HobbiesSubcategory,
    TravelSubcategory,
    FinancialSubcategory,
)

# Mapping categories to their subcategory enum types
SUBCATEGORY_TYPES: Dict[Category, Type[Enum]] = {
    Category.INCOME: IncomeSubcategory,
    Category.BILLS: BillsSubcategory,
    Category.ESSENTIALS: EssentialsSubcategory,
    Category.DINING: DiningSubcategory,
    Category.SHOPPING: ShoppingSubcategory,
    Category.HOUSEHOLD: HouseholdSubcategory,
    Category.PERSONAL_CARE: PersonalCareSubcategory,
    Category.LEISURE: LeisureSubcategory,
    Category.HOBBIES: HobbiesSubcategory,
    Category.TRAVEL: TravelSubcategory,
    Category.FINANCIAL: FinancialSubcategory,
}


class CategoryMapping(BaseModel):
    """
    Represents a mapping from a provider category to a standardized category/subcategory.
    Validates that if a subcategory is provided, it's valid for the given category.
    """

    category: Category
    subcategory: Optional[Enum] = None

    @field_validator("category", "subcategory", mode="after")
    @classmethod
    def validate_categories(
        cls, value: Optional[Enum], info: ValidationInfo
    ) -> Optional[Enum]:
        if value is None:
            return None

        field = info.field_name
        if field == "subcategory":
            category = info.data.get("category")
            if category is None:
                raise ValueError("Category must be provided to validate subcategory")

            subcategory_type = SUBCATEGORY_TYPES.get(category)
            if subcategory_type is None:
                raise ValueError(
                    f"Category '{category.value}' does not support subcategories"
                )

            if not isinstance(value, subcategory_type):
                raise ValueError(
                    f"Invalid subcategory type for category '{category.value}'. "
                    f"Expected {subcategory_type.__name__}, got {type(value).__name__}"
                )
        elif field == "category":
            if not isinstance(value, Category):
                raise ValueError(f"Expected Category enum, got {type(value).__name__}")

        return value


class MerchantCategoryMapping(BaseModel):
    """Represents a mapping from a merchant name to a category mapping."""

    merchant_name: str
    mapping: CategoryMapping


class Transaction(BaseModel):
    """
    Represents a financial transaction with strong type validation.
    """

    amount: float
    title: str
    date: date
    currency: str
    category: Optional[Category] = None
    subcategory: Optional[Enum] = None
    notes: Optional[str] = None
    account: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, value: Any) -> date:
        if isinstance(value, date):
            return value
        elif isinstance(value, str):  # Assuming ISO 8601 format
            try:
                return date.fromisoformat(value.split("T")[0])
            except ValueError:
                raise ValueError("Invalid ISO 8601 date format.")
        else:
            raise ValueError("Invalid date format. Expected a date or ISO 8601 string.")

    @field_validator("category", "subcategory", mode="after")
    @classmethod
    def validate_categories(
        cls, value: Optional[Enum], info: ValidationInfo
    ) -> Optional[Enum]:
        if value is None:
            return None

        field = info.field_name
        if field == "subcategory":
            category = info.data.get("category")
            if category is None:
                return None  # Can't validate subcategory without category

            subcategory_type = SUBCATEGORY_TYPES.get(category)
            if subcategory_type is None:
                raise ValueError(
                    f"Category '{category.value}' does not support subcategories"
                )

            if not isinstance(value, subcategory_type):
                raise ValueError(
                    f"Invalid subcategory type for category '{category.value}'. "
                    f"Expected {subcategory_type.__name__}, got {type(value).__name__}"
                )
        elif field == "category":
            if not isinstance(value, Category):
                raise ValueError(f"Expected Category enum, got {type(value).__name__}")

        return value


class ProcessorConfig(BaseModel):
    """Configuration for a transaction processor."""

    name: str
    merchant_mappings: Dict[str, CategoryMapping] = Field(default_factory=dict)
    merchant_category_mappings: Dict[str, CategoryMapping] = Field(default_factory=dict)
    registered_category_mappings: Dict[str, CategoryMapping] = Field(
        default_factory=dict
    )


class CategoryMigration(BaseModel):
    """Defines how to migrate from old categories to new ones."""

    old_category: str
    old_subcategory: Optional[str]
    new_category: Category
    new_subcategory: Optional[Enum]

    @field_validator("new_subcategory")
    @classmethod
    def validate_new_subcategory(
        cls, subcategory: Optional[Enum], values: Dict
    ) -> Optional[Enum]:
        if subcategory is None:
            return None

        category = values.get("new_category")
        if category is None:
            raise ValueError(
                "new_category must be provided to validate new_subcategory"
            )

        subcategory_type = SUBCATEGORY_TYPES.get(category)
        if subcategory_type is None:
            raise ValueError(
                f"Category '{category.value}' does not support subcategories"
            )

        if not isinstance(subcategory, subcategory_type):
            raise ValueError(
                f"Invalid subcategory type for category '{category.value}'. "
                f"Expected {subcategory_type.__name__}, got {type(subcategory).__name__}"
            )
        return subcategory
