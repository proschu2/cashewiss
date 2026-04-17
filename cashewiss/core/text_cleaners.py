"""
Text cleaning utilities for normalizing merchant names.
"""

import re
from typing import List, Tuple


MERCHANT_CLEANING_PATTERNS: List[Tuple[str, str]] = [
    (r"-\d{4,6}\b", ""),
    (r"\s{2,}", " "),
    (r"\bMM\b", "Migros"),
    (r"\bM EX\b", "Migros"),
    (r"\bMMM\b", "Migros"),
    (r"\*", " "),
    (r"\s{2,}", " "),
]


def clean_merchant_name(merchant: str) -> str:
    """
    Clean merchant name by applying all normalization patterns.
    """
    if not merchant:
        return merchant

    cleaned = merchant
    for pattern, replacement in MERCHANT_CLEANING_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned)

    return cleaned.strip()


__all__ = [
    "MERCHANT_CLEANING_PATTERNS",
    "clean_merchant_name",
]


def clean_merchant_name(merchant: str) -> str:
    """
    Clean merchant name by applying all normalization patterns.

    Args:
        merchant: Raw merchant name from transaction

    Returns:
        Cleaned merchant name

    Examples:
        >>> clean_merchant_name("coop-4922 zh bleicherweg")
        'coop zh bleicherweg'
        >>> clean_merchant_name("MM  zh")
        'Migros zh'
    """
    if not merchant:
        return merchant

    cleaned = merchant
    for pattern, replacement in MERCHANT_CLEANING_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned)

    return cleaned.strip()


__all__ = [
    "MERCHANT_CLEANING_PATTERNS",
    "clean_merchant_name",
]
