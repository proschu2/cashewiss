"""
Cashewiss - Swiss Financial Institution Transaction Processor for Cashew
"""

from .core.base import Transaction, TransactionBatch, BaseTransactionProcessor
from .core.models import (
    CategoryMapping,
    ProcessorConfig,
    MerchantCategoryMapping,
    CategoryMigration,
)
from .core.enums import (
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
from .core.client import CashewClient
from .processors.swisscard import SwisscardProcessor
from .processors.viseca import VisecaProcessor

__version__ = "0.1.0"
__all__ = [
    "Transaction",
    "TransactionBatch",
    "BaseTransactionProcessor",
    "CashewClient",
    "SwisscardProcessor",
    "VisecaProcessor",
    # Category Enums
    "Category",
    "IncomeSubcategory",
    "BillsSubcategory",
    "EssentialsSubcategory",
    "DiningSubcategory",
    "ShoppingSubcategory",
    "HouseholdSubcategory",
    "PersonalCareSubcategory",
    "LeisureSubcategory",
    "HobbiesSubcategory",
    "TravelSubcategory",
    "FinancialSubcategory",
    # Models
    "CategoryMapping",
    "ProcessorConfig",
    "MerchantCategoryMapping",
    "CategoryMigration",
]
