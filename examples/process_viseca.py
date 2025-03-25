"""Example script showing how to use the Viseca processor."""

from datetime import date
from dotenv import load_dotenv
from cashewiss import VisecaProcessor, CashewClient


def main():
    # Load environment variables from .env file
    load_dotenv()

    """
    Create a .env file with your credentials:
    
    VISECA_USERNAME=your_username
    VISECA_PASSWORD=your_password
    VISECA_CARD_ID=your_card_id
    """

    # Initialize processor (will use credentials from .env file)
    processor = VisecaProcessor()

    # Process transactions with optional date filtering
    batch = processor.process(
        None,  # No file needed - fetches directly from API
        date_from=date(2024, 1, 1),
        date_to=date(2024, 3, 23),
    )

    # Initialize the Cashew client for exporting
    client = CashewClient()

    # Export to CSV
    client.export_to_csv(batch, "viseca_transactions.csv")

    # Or use API export (opens browser with batches of 25 transactions)
    client.export_to_api(batch)


if __name__ == "__main__":
    main()
