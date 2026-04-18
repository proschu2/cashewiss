"""
Category mapping module for Cashew to Actual Budget integration.

Maps Cashew categories to Actual Budget categories with appropriate fallbacks.
"""

from typing import Optional, Union
from actualiss.core.enums import Category


ACTUAL_CATEGORY_MAP = {
    Category.INCOME: "Income",
    Category.BILLS: "Bills",
    Category.ESSENTIALS: "Essentials",
    Category.DINING: "Dining",
    Category.SHOPPING: "Shopping",
    Category.HOUSEHOLD: "Household",
    Category.PERSONAL_CARE: "Personal Care",
    Category.LEISURE: "Leisure",
    Category.HOBBIES: "Hobbies",
    Category.TRAVEL: "Travel",
    Category.FINANCIAL: "Financial",
}


def get_actual_category(category: Optional[Union[Category, str]]) -> str:
    """
    Get the corresponding Actual Budget category name for a Cashew category.

    Args:
        category: Cashew Category enum or string representation

    Returns:
        str: Actual Budget category name or "Uncategorized" if not found
    """
    if category is None:
        return "Uncategorized"

    # If it's already a Category enum, look it up directly
    if isinstance(category, Category):
        return ACTUAL_CATEGORY_MAP.get(category, "Uncategorized")

    # Handle string input (for backward compatibility)
    if isinstance(category, str):
        try:
            # Try to parse string back to enum
            category = Category(category.upper())
            return ACTUAL_CATEGORY_MAP.get(category, "Uncategorized")
        except ValueError:
            return "Uncategorized"

    return "Uncategorized"


def get_or_create_actual_category(
    session: Optional[object] = None,
    category: Optional[Union[Category, str]] = None,
    group_name: Optional[str] = None,
    strict_group: bool = False,
) -> str:
    """
    Wrapper function for get_or_create_category from actualpy.

    This function will be implemented when actualpy dependency is available.
    For now, it provides the interface and returns the category name directly.

    Args:
        session: actualpy Session object (will be passed from ActualClient)
        category: Cashew Category enum or string representation
        group_name: Optional group name for the category
        strict_group: Whether to enforce strict group matching

    Returns:
        str: Actual Budget category name
    """
    # This is a placeholder implementation
    # When actualpy is available, this will call:
    # from actual.queries import get_or_create_category
    # return get_or_create_category(session, actual_category, group_name, strict_group)

    # For now, just return the mapped category name
    actual_category = get_actual_category(category)
    return actual_category


# Export commonly used functions and constants
__all__ = [
    "ACTUAL_CATEGORY_MAP",
    "get_actual_category",
    "get_or_create_actual_category",
]
