"""
Actual Budget client for interacting with Actual Budget API via actualpy.

This module provides the ActualClient class which handles:
- Connection management to Actual Budget server
- Account management (list, get, create with confirmation)
- Transaction import
- Error handling and logging
"""

import hashlib
import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, List, Dict, Any, Callable, Type

logger = logging.getLogger(__name__)
from ..logging_config import log_api_call, log_api_success, log_api_error


def retry_on_transient_error(
    max_retries: int = 3,
    base_delay: float = 1.0,
    retryable_exceptions: tuple = (ConnectionError, TimeoutError),
) -> Callable:
    """
    Decorator that implements exponential backoff retry logic for transient errors.

    This decorator retries functions that raise retryable exceptions with
    exponential backoff (base_delay * 2^attempt). Non-retryable exceptions
    are raised immediately without retrying.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds before first retry (default: 1.0)
        retryable_exceptions: Tuple of exception types to retry on (default: ConnectionError, TimeoutError)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_on_transient_error(max_retries=3, base_delay=1.0)
        def fetch_data():
            # Network operation that might fail transiently
            return requests.get("https://api.example.com")
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            from actual.exceptions import ActualError, AuthorizationError

            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2**attempt)
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {delay:.1f}s: {type(e).__name__}: {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: "
                            f"{type(e).__name__}: {e}"
                        )
                except AuthorizationError as e:
                    # Authorization errors are not retryable - wrong credentials
                    logger.error(
                        f"{func.__name__} failed due to authorization: {e}. "
                        f"Check your credentials and try again."
                    )
                    raise
                except (ActualError, ValueError, KeyError, TypeError) as e:
                    # These are non-retryable errors - they'll keep failing
                    log_api_error(
                        logger,
                        func.__name__,
                        e,
                        context={"error_type": "non_retryable"},
                    )
                    raise
                except Exception as e:
                    # Unexpected errors - don't retry
                    log_api_error(
                        logger, func.__name__, e, context={"error_type": "unexpected"}
                    )
                    raise

            # If we exhausted all retries, raise the last error
            if last_error:
                raise last_error

        return wrapper

    return decorator


class ActualClient:
    """
    Client for interacting with Actual Budget API.

    This client wraps the actualpy.Actual class and provides a convenient
    interface for importing transactions into Actual Budget.

    Example:
        >>> client = ActualClient(
        ...     server_url="http://localhost:5006",
        ...     password="my_password",
        ...     file="My Budget"
        ... )
        >>> with client:
        ...     accounts = client.get_accounts()
        ...     client.import_transactions(transactions, account_id)
        ...     client.commit()
    """

    def __init__(
        self,
        server_url: str,
        password: str,
        file: str,
        encryption_password: Optional[str] = None,
    ):
        """
        Initialize the Actual Budget client.

        Args:
            server_url: URL of the Actual Budget server (e.g., "http://localhost:5006")
            password: Password for Actual Budget server authentication
            file: Name or ID of the budget file to work with
            encryption_password: Optional password for encrypted budget files
        """
        self.server_url = server_url
        self.password = password
        self.file = file
        self.encryption_password = encryption_password

        # These will be set when entering context manager
        self._actual = None
        self._session = None

        # Cache for imported_id lookups to improve performance
        self._imported_id_cache: Dict[str, Dict[str, Any]] = {}

        logger.debug(f"ActualClient initialized: server_url={server_url}, file={file}")

    @retry_on_transient_error(max_retries=3, base_delay=1.0)
    def _connect(self):
        """
        Establish connection to Actual Budget server.

        This method is wrapped with retry logic to handle transient network errors.

        Raises:
            ActualError: If connection or authentication fails
            AuthorizationError: If credentials are invalid
            ConnectionError: If network connection fails (retryable)
            TimeoutError: If connection times out (retryable)
        """
        from actual import Actual
        from actual.exceptions import ActualError, AuthorizationError

        log_api_call(logger, "_connect", server_url=self.server_url, file=self.file)
        logger.info(f"Connecting to Actual Budget at {self.server_url}...")

        # Use actualpy context manager to establish connection
        self._actual = Actual(
            base_url=self.server_url,
            password=self.password,
            file=self.file,
            encryption_password=self.encryption_password,
        )

        # Enter the context manager to establish connection
        self._actual.__enter__()
        self._session = self._actual.session

        log_api_success(
            logger, "_connect", result_summary=f"Connected to budget: {self.file}"
        )
        logger.info(f"Successfully connected to budget: {self.file}")

    def __enter__(self):
        """
        Enter context manager and connect to Actual Budget.

        Returns:
            ActualClient: The client instance with active connection

        Raises:
            ActualError: If connection or authentication fails
            AuthorizationError: If credentials are invalid
        """
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager and close connection.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        if self._actual is not None:
            try:
                self._actual.__exit__(exc_type, exc_val, exc_tb)
                logger.debug("Connection to Actual Budget closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}", exc_info=True)

        self._session = None
        self._actual = None

    def generate_imported_id(self, transaction: Dict[str, Any]) -> str:
        """
        Generate a unique imported_id for a transaction.

        The imported_id is an MD5 hash of date+amount+payee, which provides
        a consistent identifier for duplicate detection.

        Args:
            transaction: Transaction dict with 'date', 'amount', and 'imported_payee' keys

        Returns:
            str: 16-character hexadecimal hash (32 hex chars / 2 for display)

        Example:
            >>> transaction = {
            ...     'date': '2026-01-15',
            ...     'amount': -5050,
            ...     'imported_payee': 'Coffee Shop'
            ... }
            >>> imported_id = client.generate_imported_id(transaction)
            >>> print(f'Generated ID: {imported_id}')
        """
        date = transaction["date"]
        amount = str(abs(transaction["amount"]))
        payee = transaction.get("imported_payee", "")
        return hashlib.md5(f"{date}{amount}{payee}".encode()).hexdigest()

    def check_duplicates(
        self, transactions: List[Dict[str, Any]], account_id: str
    ) -> List[Dict[str, Any]]:
        """
        Check for duplicate transactions using layered detection approach.

        Layer 1: Exact match via imported_id lookup (fast)
        Layer 2: Fuzzy match via actualpy.match_transaction() (7-day window)

        Args:
            transactions: List of transaction dicts to check for duplicates
            account_id: ID of the account to check against

        Returns:
            List[Dict[str, Any]]: List of duplicate transactions found.
                Each duplicate dict includes:
                - 'transaction': The duplicate transaction
                - 'existing': The existing transaction it matches
                - 'match_type': 'imported_id' or 'fuzzy'
                - 'match_details': Description of the match

        Example:
            >>> duplicates = client.check_duplicates(transactions, account_id)
            >>> if duplicates:
            ...     for dup in duplicates:
            ...         print(f"Duplicate found: {dup['transaction']['imported_payee']}")
            ...         print(f"  Match type: {dup['match_type']}")
            ...         print(f"  Existing: {dup['existing'].date} - {dup['existing'].payee.name}")
        """
        try:
            from actual.queries import get_transactions, match_transaction
            from actual.exceptions import ActualError

            if self._session is None:
                raise RuntimeError(
                    "Not connected to Actual Budget. Use 'with client:' context manager."
                )

            logger.debug(f"Checking {len(transactions)} transactions for duplicates...")
            duplicates = []

            # Build imported_id cache from existing transactions if not already cached
            if not self._imported_id_cache:
                logger.debug("Building imported_id cache from existing transactions...")
                existing_transactions = get_transactions(
                    self._session, account=account_id
                )
                for txn in existing_transactions:
                    if txn.imported_id:
                        self._imported_id_cache[txn.imported_id] = {
                            "transaction": txn,
                            "date": txn.date,
                            "amount": txn.amount,
                            "payee": txn.payee.name if txn.payee else None,
                        }
                logger.debug(f"Cached {len(self._imported_id_cache)} imported_ids")

            # Check each transaction for duplicates
            for transaction in transactions:
                txn_date = datetime.strptime(transaction["date"], "%Y-%m-%d").date()
                txn_amount = transaction["amount"]
                txn_payee = transaction.get("imported_payee")
                imported_id = transaction.get("imported_id")

                # Layer 1: Exact match via imported_id
                if imported_id and imported_id in self._imported_id_cache:
                    existing = self._imported_id_cache[imported_id]["transaction"]
                    duplicates.append(
                        {
                            "transaction": transaction,
                            "existing": existing,
                            "match_type": "imported_id",
                            "match_details": f"Exact imported_id match: {imported_id}",
                        }
                    )
                    logger.debug(
                        f"Duplicate found via imported_id: {txn_payee} on {transaction['date']}"
                    )
                    continue

                # Layer 2: Fuzzy match using match_transaction()
                try:
                    # Build kwargs dict, only include payee if it exists
                    match_kwargs = {
                        "s": self._session,
                        "date": txn_date,
                        "account": account_id,
                        "amount": txn_amount / 100,  # Convert cents to dollars
                    }
                    if txn_payee:
                        match_kwargs["payee"] = txn_payee
                    if imported_id:
                        match_kwargs["imported_id"] = imported_id

                    matched_txn = match_transaction(**match_kwargs)

                    if matched_txn:
                        duplicates.append(
                            {
                                "transaction": transaction,
                                "existing": matched_txn,
                                "match_type": "fuzzy",
                                "match_details": (
                                    f"Fuzzy match: {matched_txn.date}, "
                                    f"amount={matched_txn.amount}, "
                                    f"payee={matched_txn.payee.name if matched_txn.payee else 'N/A'}"
                                ),
                            }
                        )
                        logger.debug(
                            f"Duplicate found via fuzzy match: {txn_payee} on {transaction['date']}"
                        )

                except ActualError as e:
                    logger.warning(f"Error during fuzzy matching for {txn_payee}: {e}")

            if duplicates:
                logger.info(f"Found {len(duplicates)} duplicate transactions")
                for i, dup in enumerate(duplicates[:5], 1):
                    logger.warning(
                        f"  Duplicate {i}: {dup['transaction'].get('imported_payee', 'Unknown')} "
                        f"on {dup['transaction']['date']} - {dup['match_type']} match"
                    )
                if len(duplicates) > 5:
                    logger.warning(f"  ... and {len(duplicates) - 5} more duplicates")

            return duplicates

        except ActualError as e:
            log_api_error(
                logger, "check_duplicates", e, context={"account_id": account_id}
            )
            raise
        except Exception as e:
            log_api_error(
                logger,
                "check_duplicates",
                e,
                context={
                    "account_id": account_id,
                    "transaction_count": len(transactions),
                },
            )
            raise

    @retry_on_transient_error(max_retries=3, base_delay=1.0)
    def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Get list of all accounts from Actual Budget.

        This method is wrapped with retry logic to handle transient network errors.

        Returns:
            List of dicts containing account information:
                - id: Account ID
                - name: Account name
                - balance: Current balance
                - type: Account type (checking, savings, credit, etc.)

        Raises:
            ActualError: If query fails
            RuntimeError: If not connected to Actual Budget
            ConnectionError: If network connection fails (retryable)
            TimeoutError: If query times out (retryable)
        """
        from actual.queries import get_accounts
        from actual.exceptions import ActualError

        if self._session is None:
            raise RuntimeError(
                "Not connected to Actual Budget. Use 'with client:' context manager."
            )

        log_api_call(logger, "get_accounts")
        logger.debug("Fetching accounts from Actual Budget...")
        accounts = get_accounts(self._session)

        # Convert account objects to dicts for easier handling
        account_list = []
        for account in accounts:
            account_dict = {
                "id": account.id,
                "name": account.name,
                "balance": account.balance,
                "type": getattr(account, "type", "unknown"),
            }
            account_list.append(account_dict)

        log_api_success(
            logger,
            "get_accounts",
            result_summary=f"Retrieved {len(account_list)} accounts",
        )
        logger.info(f"Retrieved {len(account_list)} accounts")
        return account_list

    @retry_on_transient_error(max_retries=3, base_delay=1.0)
    def _create_account(self, name: str, account_type: str) -> str:
        """
        Create a new account in Actual Budget.

        This method is wrapped with retry logic to handle transient network errors.

        Args:
            name: Account name to create
            account_type: Type of account to create (checking, savings, credit)

        Returns:
            str: Account ID

        Raises:
            ActualError: If account creation fails
            ConnectionError: If network connection fails (retryable)
            TimeoutError: If creation times out (retryable)
        """
        from actual.queries import get_or_create_account
        from actual.exceptions import ActualError

        log_api_call(logger, "_create_account", name=name, account_type=account_type)
        logger.info(f"Creating new account: {name} (type: {account_type})")
        account = get_or_create_account(self._session, name, type=account_type)
        log_api_success(
            logger,
            "_create_account",
            result_summary=f"Created account: {name} (ID: {account.id})",
        )
        logger.info(f"Successfully created account: {name} (ID: {account.id})")
        return account.id

    def get_or_create_account(self, name: str, account_type: str = "checking") -> str:
        """
        Get existing account or create new one with user confirmation.

        Args:
            name: Account name to search for or create
            account_type: Type of account to create (checking, savings, credit)
                         Default: "checking"

        Returns:
            str: Account ID

        Raises:
            ActualError: If account creation fails
            RuntimeError: If not connected to Actual Budget
            ValueError: If user cancels account creation
        """
        if self._session is None:
            raise RuntimeError(
                "Not connected to Actual Budget. Use 'with client:' context manager."
            )

        # First, check if account already exists
        accounts = self.get_accounts()
        existing_account = None
        for account in accounts:
            if account["name"].lower() == name.lower():
                existing_account = account
                break

        if existing_account:
            logger.info(
                f"Found existing account: {name} (ID: {existing_account['id']})"
            )
            return existing_account["id"]

        # Account doesn't exist, prompt user for confirmation
        print(f"\nAccount '{name}' not found in Actual Budget.")
        response = input(f"Create new account '{name}' (type: {account_type})? [y/N]: ")

        if response.lower() != "y":
            logger.info(f"Account creation cancelled by user for: {name}")
            raise ValueError(f"Account '{name}' not found and creation was cancelled")

        # Create the account (with retry logic)
        return self._create_account(name, account_type)

    @retry_on_transient_error(max_retries=3, base_delay=1.0)
    def commit(self) -> None:
        """
        Commit all pending changes to Actual Budget.

        This persists locally made changes and syncs them to the server.
        This method is wrapped with retry logic to handle transient network errors.

        Raises:
            ActualError: If commit fails
            RuntimeError: If not connected to Actual Budget
            ConnectionError: If network connection fails (retryable)
            TimeoutError: If commit times out (retryable)
        """
        from actual.exceptions import ActualError

        if self._actual is None:
            raise RuntimeError(
                "Not connected to Actual Budget. Use 'with client:' context manager."
            )

        log_api_call(logger, "commit")
        logger.info("Committing changes to Actual Budget...")
        self._actual.commit()
        log_api_success(
            logger, "commit", result_summary="Changes committed successfully"
        )
        logger.info("Changes committed successfully")

    def import_transactions(
        self,
        transactions: List[Dict[str, Any]],
        account_id: str,
        skip_duplicates: bool = False,
    ) -> int:
        """
        Import transactions into Actual Budget.

        Args:
            transactions: List of transaction dicts in Actual Budget format
                         (from TransactionBatch.to_actual_format())
            account_id: ID of the account to import transactions into
            skip_duplicates: If True, check for duplicates and skip them.
                            Defaults to False (duplicates not checked by default).

        Returns:
            int: Number of transactions successfully imported

        Raises:
            ActualError: If import fails
            RuntimeError: If not connected to Actual Budget
        """
        try:
            from actual.queries import create_transaction
            from actual.exceptions import ActualError

            if self._session is None:
                raise RuntimeError(
                    "Not connected to Actual Budget. Use 'with client:' context manager."
                )

            log_api_call(
                logger,
                "import_transactions",
                account_id=account_id,
                transaction_count=len(transactions),
            )
            logger.info(
                f"Importing {len(transactions)} transactions to account {account_id}..."
            )

            # Check for duplicates if requested
            transactions_to_import = transactions
            if skip_duplicates:
                duplicates = self.check_duplicates(transactions, account_id)
                if duplicates:
                    duplicate_ids = {
                        dup["transaction"].get("imported_id") for dup in duplicates
                    }
                    transactions_to_import = [
                        txn
                        for txn in transactions
                        if txn.get("imported_id") not in duplicate_ids
                    ]
                    logger.info(
                        f"Skipping {len(duplicates)} duplicates, "
                        f"importing {len(transactions_to_import)} transactions"
                    )

            imported_count = 0
            failed_transactions = []

            for i, transaction in enumerate(transactions_to_import):
                try:
                    # Create transaction using actualpy
                    create_transaction(
                        self._session,
                        account_id=account_id,
                        date=transaction["date"],
                        amount=transaction["amount"],
                        notes=transaction.get("notes", ""),
                        category=transaction.get("category"),
                        imported_id=transaction.get("imported_id"),
                        imported_payee=transaction.get("imported_payee"),
                    )
                    imported_count += 1

                    # Log progress every 10 transactions
                    if (i + 1) % 10 == 0:
                        logger.debug(
                            f"Imported {i + 1}/{len(transactions)} transactions..."
                        )

                except ActualError as e:
                    logger.warning(
                        f"Failed to import transaction {i + 1}: {transaction.get('imported_payee', 'Unknown')} - {e}"
                    )
                    failed_transactions.append((i, transaction, str(e)))

            if imported_count > 0:
                log_api_success(
                    logger,
                    "import_transactions",
                    result_summary=f"Successfully imported {imported_count}/{len(transactions_to_import)} transactions",
                )
                logger.info(
                    f"Successfully imported {imported_count}/{len(transactions_to_import)} transactions"
                )

            if failed_transactions:
                logger.warning(
                    f"Failed to import {len(failed_transactions)} transactions"
                )
                for idx, txn, error in failed_transactions[:5]:  # Log first 5 failures
                    logger.warning(
                        f"  Transaction {idx + 1}: {txn.get('imported_payee', 'Unknown')} - Error: {error}"
                    )
                if len(failed_transactions) > 5:
                    logger.warning(
                        f"  ... and {len(failed_transactions) - 5} more failures"
                    )

            return imported_count

        except ActualError as e:
            log_api_error(
                logger, "import_transactions", e, context={"account_id": account_id}
            )
            raise
        except Exception as e:
            log_api_error(
                logger,
                "import_transactions",
                e,
                context={
                    "account_id": account_id,
                    "transaction_count": len(transactions),
                },
            )
            raise
