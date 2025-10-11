import json
import urllib.parse
import subprocess
import platform
from typing import Optional, List, Union
from datetime import date
import time
from .base import TransactionBatch, Transaction


def _open_url(url: str):
    """Open URL in browser based on OS."""
    import webbrowser
    import logging

    logging.info(f"Attempting to open URL: {url[:100]}...")

    # Try using webbrowser module first (more reliable)
    try:
        result = webbrowser.open(url, new=2)  # new=2 opens in new tab if possible
        if result:
            logging.info("Successfully opened URL using webbrowser module")
            return True
        else:
            logging.warning(
                "webbrowser.open() returned False - browser may not have opened"
            )
    except Exception as webbrowser_error:
        logging.warning(f"webbrowser module failed: {webbrowser_error}")

    # Fallback to subprocess method
    system = platform.system().lower()
    try:
        if system == "darwin":  # macOS
            subprocess.run(["open", url], check=True)
        elif system == "windows":
            subprocess.run(["start", url], shell=True, check=True)
        elif system == "linux":
            subprocess.run(["xdg-open", url], check=True)
        else:
            raise OSError(f"Unsupported operating system: {system}")
        logging.info("Successfully opened URL using subprocess method")
        return True
    except Exception as e:
        logging.error(f"All browser opening methods failed: {str(e)}")
        return False


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
    ) -> Union[str, List[str], None]:
        """
        Export transactions via Cashew API.

        Args:
            batch: TransactionBatch to export
            dry_run: If True, return URL(s) instead of opening browser
            debug: If True, print debug information

        Returns:
            Single URL string if dry_run=True and only one batch,
            List of URLs if dry_run=True and multiple batches,
            None if dry_run=False
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
            # Return all batch URLs for testing
            batch_urls = []
            for i, transactions in enumerate(batches):
                sub_batch = TransactionBatch(
                    transactions=transactions, source=batch.source
                )
                url = self.get_add_transaction_url(batch=sub_batch)
                batch_urls.append(url)
                logging.debug(
                    f"Generated dry-run URL for batch {i + 1}: {url[:100]}..."
                )

            # Return single URL if only one batch, otherwise return list
            if len(batch_urls) == 1:
                return batch_urls[0]
            return batch_urls

        # Process each batch
        failed_batches = []
        for i, transactions in enumerate(batches):
            logging.debug(
                f"Processing batch {i + 1}/{len(batches)} with {len(transactions)} transactions"
            )
            sub_batch = TransactionBatch(transactions=transactions, source=batch.source)
            try:
                url = self.get_add_transaction_url(batch=sub_batch)
                logging.debug(f"Opening URL for batch {i + 1}: {url[:100]}...")
                success = _open_url(url)
                if success:
                    logging.info(f"Successfully opened batch {i + 1} in browser")
                    logging.debug(
                        f"Successfully opened batch {i + 1}. Waiting 10 seconds before next batch."
                    )
                    time.sleep(10)
                else:
                    logging.warning(
                        f"Browser opening may have failed for batch {i + 1}"
                    )
                    failed_batches.append((i + 1, url))
                    # Continue with next batch even if this one failed
                    time.sleep(5)  # Shorter delay for failed batches
            except Exception as e:
                error_msg = f"Failed to open batch {i + 1} in browser: {str(e)}"
                logging.error(error_msg)
                logging.error(f"URL that failed: {url}")
                failed_batches.append((i + 1, url))
                # Continue with next batch even if this one failed
                time.sleep(5)  # Shorter delay for failed batches

        if failed_batches:
            logging.warning(
                f"{len(failed_batches)} batch(es) failed to open automatically"
            )
            # Return the failed URLs so they can be displayed for manual opening
            failed_urls = [url for _, url in failed_batches]
            if len(failed_urls) == 1:
                return failed_urls[0]
            return failed_urls

        logging.info(f"Export completed successfully - opened {len(batches)} batch(es)")
        return None
