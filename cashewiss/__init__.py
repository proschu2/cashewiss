"""
Cashewiss - Swiss Financial Institution Transaction Processor for Cashew
"""

from .core.base import Transaction, TransactionBatch, BaseTransactionProcessor
from .core.categories import (
    Category,
    ProviderCategoryMapper,
    DiningSubcategory,
    GroceriesSubcategory,
    ShoppingSubcategory,
    EntertainmentSubcategory,
    BillsFeesSubcategory,
    BeautyHealthSubcategory,
)
from .core.client import CashewClient
from .processors.swisscard import SwisscardProcessor

__version__ = "0.1.0"
__all__ = [
    "Transaction",
    "TransactionBatch",
    "BaseTransactionProcessor",
    "CashewClient",
    "SwisscardProcessor",
    "Category",
    "ProviderCategoryMapper",
    "DiningSubcategory",
    "GroceriesSubcategory",
    "ShoppingSubcategory",
    "EntertainmentSubcategory",
    "BillsFeesSubcategory",
    "BeautyHealthSubcategory",
]
