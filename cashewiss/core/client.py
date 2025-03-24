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
        self, transactions: List[Transaction], max_size: int = 25
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
        header = "Date,Amount,Category,Title,Note,Account"
        rows = []
        for t in batch.transactions:
            # Format date as DD/MM/YYYY HH:mm
            date_str = t.date.strftime("%d/%m/%Y 00:00")
            # Create comma-separated row
            row = f"{date_str},{t.amount},{t.category or ''},{t.title},{t.notes or ''},{t.account or ''}"
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
        self, batch: TransactionBatch, dry_run: bool = False
    ) -> Optional[str]:
        """
        Export transactions via Cashew API.

        Args:
            batch: TransactionBatch to export
            dry_run: If True, return URL instead of opening browser

        Returns:
            URL string if dry_run=True, otherwise None
        """
        # Split transactions into smaller batches
        batches = self._split_batch(batch.transactions)

        if dry_run:
            # Return first batch URL for testing
            first_batch = TransactionBatch(transactions=batches[0], source=batch.source)
            return self.get_add_transaction_url(batch=first_batch)

        # Process each batch
        for transactions in batches:
            sub_batch = TransactionBatch(transactions=transactions, source=batch.source)
            try:
                url = self.get_add_transaction_url(batch=sub_batch)
                _open_url(url)
                time.sleep(10)
            except Exception as e:
                raise RuntimeError(f"Failed to open batch in browser: {str(e)}")

        return None
