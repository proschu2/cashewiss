"""
Actualiss - Swiss Financial Institution Transaction Processor for Actual Budget
"""

import os
from .logging_config import setup_logging, get_logger

# Initialize logging with environment-based defaults
# CLI options will override these defaults when available
setup_logging(
    verbose=os.getenv("ACTUALISS_VERBOSE", "false").lower() == "true",
    log_file=os.getenv("ACTUALISS_LOG_FILE"),
)

from .core.base import Transaction, TransactionBatch, BaseTransactionProcessor
from .core.actual_client import ActualClient
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
from .processors.zkb import ZKBProcessor
from .processors.swisscard import SwisscardProcessor

__version__ = "0.1.0"
__all__ = [
    "Transaction",
    "TransactionBatch",
    "BaseTransactionProcessor",
    "ActualClient",
    # Processors
    "ZKBProcessor",
    "SwisscardProcessor",
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
