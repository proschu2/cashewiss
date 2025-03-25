from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, Dict, Any, List

import polars as pl
from pydantic import BaseModel


class Transaction(BaseModel):
    """
    Represents a financial transaction with all possible parameters.

    Attributes:
        amount (float): The amount of the transaction. Negative for expenses, positive for income.
        title (str): The title/description of the transaction.
        notes (Optional[str]): Additional notes about the transaction.
        date (date): The date of the transaction.
        category (Optional[str]): Category name (case-insensitive search).
        subcategory (Optional[str]): Subcategory name (case-insensitive search).
        account (Optional[str]): Account name (case-insensitive search).
        currency (str): The currency of the transaction.
        meta (Dict[str, Any]): Additional metadata about the transaction.
    """

    amount: float
    title: str
    date: date
    currency: str
    notes: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    account: Optional[str] = None
    meta: Dict[str, Any] = {}


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
                "category": t.category,
                "subcategory": t.subcategory,
                "account": t.account,
                "notes": t.notes,
            }
            for t in self.transactions
        ]


class BaseTransactionProcessor(ABC):
    def __init__(self, name: str):
        self.name = name
        self._df: Optional[pl.DataFrame] = None
        self._loaded_data: Optional[pl.DataFrame] = None
        self._transformed_data: Optional[List[Transaction]] = None

        # Default column names that can be overridden by processors
        self.merchant_column: str = "Merchant"
        self.merchant_category_column: str = "Merchant Category"
        self.description_column: str = "Description"
        self.registered_category_column: str = "Registered Category"
        self._category_mappers: Dict[str, Dict[str, Dict[str, str]]] = {}

    def set_category_mapper(
        self, mapper: dict[str, dict[str, str]], mapper_type: str
    ) -> None:
        """
        Set the category mapping dictionary.

        Args:
            mapper: A nested dictionary where:
                   - First level key is the provider's category
                   - Second level is a dict with 'category' and 'subcategory' keys
                   Example:
                   {
                       "GROCERY_STORES": {
                           "category": "Food & Dining",
                           "subcategory": "Groceries"
                       }
                   }
        """
        if mapper_type is None:
            raise ValueError("mapper_type cannot be None")
        self._category_mappers[mapper_type] = mapper

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

    def _map_category(self, row: Dict[str, Any]) -> dict[str, Optional[str]]:
        """
        Map transaction data to standardized category and subcategory using multiple strategies.

        Args:
            row: The transaction row data

        Returns:
            Dictionary with 'category' and 'subcategory' keys
        """
        for col in zip(
            [
                self.merchant_column,
                self.description_column,
                self.registered_category_column,
                self.merchant_category_column,
            ]
        ):
            if col is None:
                continue
            if row.get(col) in self._category_mappers[col]:
                return self._category_mappers[col][row[col]]

        return {"category": None, "subcategory": None}

    def process(
        self,
        file_path: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> TransactionBatch:
        """Process the transaction file and return a TransactionBatch."""
        self._df = self.load_data(file_path, date_from, date_to)
        self._transformed_data = self.transform_data()
        return TransactionBatch(
            transactions=self._transformed_data, source=self.__class__.__name__
        )
