import json
import urllib.parse
import subprocess
import platform
from typing import Optional, List
from datetime import date
import time
from .base import TransactionBatch, Transaction


def _open_url(url: str):
    """Open URL in browser based on OS."""
    system = platform.system().lower()
    try:
        if system == "darwin":  # macOS
            subprocess.run(["open", url])
        elif system == "windows":
            subprocess.run(["start", url], shell=True)
        elif system == "linux":
            subprocess.run(["xdg-open", url])
        else:
            raise OSError(f"Unsupported operating system: {system}")
    except Exception as e:
        raise RuntimeError(f"Failed to open URL: {str(e)}")


class CashewClient:
    """Client for interacting with Cashew web app."""

    def __init__(self, base_url: str = "https://budget-track.web.app"):
        """
        Initialize the Cashew web app client.

        Args:
            base_url: The base URL for the Cashew web app.
                     Use https://budget-track.web.app for web app
                     or https://cashewapp.web.app for mobile app
        """
        self.base_url = base_url.rstrip("/")

    def get_add_transaction_url(
        self,
        batch: Optional[TransactionBatch] = None,
        amount: Optional[float] = None,
        title: Optional[str] = None,
        notes: Optional[str] = None,
        date: Optional[date] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        account: Optional[str] = None,
        route_only: bool = False,
    ) -> str:
        """
        Get URL for adding transaction(s) in Cashew.

        Args:
            batch: Optional TransactionBatch for bulk import
            amount: Amount of the transaction (negative for expense)
            title: Title of the transaction
            notes: Additional notes
            date: Transaction date
            category: Category name (case-insensitive)
            subcategory: Subcategory name (case-insensitive)
            account: Account name (case-insensitive)
            route_only: If True, uses /addTransactionRoute instead of /addTransaction

        Returns:
            URL string that can be opened in a browser or mobile app
        """
        endpoint = "/addTransactionRoute" if route_only else "/addTransaction"

        if batch is not None:
            # Format batch transactions as JSON parameter
            transactions_data = {"transactions": batch.to_cashew_format()}
            json_str = json.dumps(transactions_data, separators=(",", ":"))
            encoded_json = urllib.parse.quote(json_str)
            return f"{self.base_url}{endpoint}?JSON={encoded_json}"

        # Build URL parameters for single transaction
        params = {}
        if amount is not None:
            params["amount"] = str(amount)
        if title:
            params["title"] = title
        if notes:
            params["notes"] = notes
        if date:
            params["date"] = date.isoformat()
        if category:
            params["category"] = category
        if subcategory:
            params["subcategory"] = subcategory
        if account:
            params["account"] = account

        query_string = urllib.parse.urlencode(params)
        return f"{self.base_url}{endpoint}?{query_string}"

    def _split_batch(
        self, transactions: List[Transaction], max_size: int = 10
    ) -> List[List[Transaction]]:
        """Split transactions into smaller batches to handle URL length limits."""
        return [
            transactions[i : i + max_size]
            for i in range(0, len(transactions), max_size)
        ]

    def export_to_csv(
        self, batch: TransactionBatch, output_path: str, dry_run: bool = False
    ) -> Optional[str]:
        """
        Export transactions to CSV file in Cashew format.

        Args:
            batch: TransactionBatch to export
            output_path: Path to save the CSV file
            dry_run: If True, return preview of first 5 rows instead of writing file

        Returns:
            Preview string if dry_run=True, otherwise None
        """
        # Create header and rows for CSV
        header = "Date,Amount,Category,Subcategory,Title,Note,Account"
        rows = []
        for t in batch.transactions:
            # Format date as DD/MM/YYYY HH:mm
            date_str = t.date.strftime("%d/%m/%Y 00:00")
            # Create comma-separated row
            row = f"{date_str},{t.amount},{t.category.value if t.category else ''},{t.subcategory.value if t.subcategory else ''},{t.title},{t.notes or ''},{t.account or ''}"
            rows.append(row)

        if dry_run:
            # Return preview of header and first 5 rows
            preview_rows = rows[:5]
            return header + "\n" + "\n".join(preview_rows)

        # Write header and all rows to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header + "\n" + "\n".join(rows))
        return None

    def export_to_api(
        self, batch: TransactionBatch, dry_run: bool = False, debug: bool = False
    ) -> Optional[str]:
        """
        Export transactions via Cashew API.

        Args:
            batch: TransactionBatch to export
            dry_run: If True, return URL instead of opening browser
            debug: If True, print debug information

        Returns:
            URL string if dry_run=True, otherwise None
        """
        import logging

        # Setup logging if needed
        if debug:
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s - %(levelname)s - %(message)s",
                force=True,
            )

        logging.debug(f"Starting export of {len(batch.transactions)} transactions")

        # Validate transactions before proceeding
        for i, transaction in enumerate(batch.transactions):
            try:
                # Check for required fields
                if not hasattr(transaction, "date") or transaction.date is None:
                    logging.error(f"Transaction {i} missing date field")
                    raise ValueError(f"Transaction {i} missing date field")

                if not hasattr(transaction, "amount") or transaction.amount is None:
                    logging.error(f"Transaction {i} missing amount field")
                    raise ValueError(f"Transaction {i} missing amount field")

                if not hasattr(transaction, "title") or not transaction.title:
                    logging.error(f"Transaction {i} missing title field")
                    raise ValueError(f"Transaction {i} missing title field")

                # Validate category and subcategory
                if transaction.category is not None:
                    try:
                        category_value = transaction.category.value
                        logging.debug(f"Transaction {i} has category: {category_value}")
                    except AttributeError:
                        logging.error(
                            f"Transaction {i} has invalid category type: {type(transaction.category)}"
                        )
                        transaction.category = None

                if transaction.subcategory is not None:
                    try:
                        subcategory_value = transaction.subcategory.value
                        logging.debug(
                            f"Transaction {i} has subcategory: {subcategory_value}"
                        )
                    except AttributeError:
                        logging.error(
                            f"Transaction {i} has invalid subcategory type: {type(transaction.subcategory)}"
                        )
                        transaction.subcategory = None

                # For Viseca transactions, handle special case
                if batch.source == "VisecaProcessor" or (
                    hasattr(transaction, "meta")
                    and transaction.meta
                    and transaction.meta.get("processor") == "Viseca"
                ):
                    logging.debug(f"Special handling for Viseca transaction {i}")
                    # Ensure values are properly formatted for Cashew
                    if hasattr(transaction, "amount"):
                        # Ensure amount is negative for expenses
                        if transaction.amount > 0:
                            transaction.amount = -transaction.amount
                            logging.debug(
                                f"Converted positive amount to negative for Viseca transaction {i}"
                            )

            except Exception as e:
                logging.error(f"Validation error for transaction {i}: {str(e)}")
                raise ValueError(f"Invalid transaction at index {i}: {str(e)}")

        # Split transactions into smaller batches
        batches = self._split_batch(batch.transactions, max_size=25)
        logging.debug(f"Split into {len(batches)} batches of max 25 transactions each")

        if dry_run:
            # Return first batch URL for testing
            first_batch = TransactionBatch(transactions=batches[0], source=batch.source)
            url = self.get_add_transaction_url(batch=first_batch)
            logging.debug(f"Generated dry-run URL: {url}")
            return url

        # Process each batch
        for i, transactions in enumerate(batches):
            logging.debug(
                f"Processing batch {i + 1}/{len(batches)} with {len(transactions)} transactions"
            )
            sub_batch = TransactionBatch(transactions=transactions, source=batch.source)
            try:
                url = self.get_add_transaction_url(batch=sub_batch)
                logging.debug(f"Opening URL for batch {i + 1}: {url[:100]}...")
                _open_url(url)
                logging.debug(
                    f"Successfully opened batch {i + 1}. Waiting 10 seconds before next batch."
                )
                time.sleep(10)
            except Exception as e:
                logging.error(f"Failed to open batch {i + 1} in browser: {str(e)}")
                raise RuntimeError(f"Failed to open batch {i + 1} in browser: {str(e)}")

        logging.debug("Export completed successfully")
        return None
