from datetime import date
from cashewiss import (
    SwisscardProcessor,
    CashewClient,
    Category,
    ProviderCategoryMapper,
    DiningSubcategory,
    GroceriesSubcategory,
    ShoppingSubcategory,
    EntertainmentSubcategory,
    BillsFeesSubcategory,
    BeautyHealthSubcategory,
)


def main():
    """
    Example script showing how to process Swisscard transactions and upload them to Cashew.

    Expected XLSX format has columns:
    Transaction date, Description, Merchant, Card number, Currency, Amount,
    Foreign Currency, Amount in foreign currency, Debit/Credit, Status,
    Merchant Category, Registered Category
    """
    # Initialize the Swisscard processor
    processor = SwisscardProcessor()

    # Set up category mapping using type-safe enum values
    mapper = ProviderCategoryMapper()

    # Add mappings with validation
    mapper.add_mapping("GROCERY STORES", Category.GROCERIES, GroceriesSubcategory.MEAL)
    mapper.add_mapping(
        "CONVENIENCE STORES", Category.GROCERIES, GroceriesSubcategory.SNACKS
    )
    mapper.add_mapping("RESTAURANTS", Category.DINING, DiningSubcategory.FRIENDS)
    mapper.add_mapping(
        "FAST FOOD RESTAURANTS", Category.DINING, DiningSubcategory.DELIVERY
    )
    mapper.add_mapping("BUSINESS DINING", Category.DINING, DiningSubcategory.WORK)
    mapper.add_mapping("TRANSPORTATION", Category.TRANSIT)  # No subcategory needed
    mapper.add_mapping(
        "CLOTHING STORES", Category.SHOPPING, ShoppingSubcategory.CLOTHES
    )
    mapper.add_mapping(
        "ELECTRONICS", Category.SHOPPING, ShoppingSubcategory.ELECTRONICS
    )
    mapper.add_mapping("GAME/TOY STORES", Category.SHOPPING, ShoppingSubcategory.GAMES)
    mapper.add_mapping(
        "HOUSEHOLD APPLIANCE STORES", Category.SHOPPING, ShoppingSubcategory.KITCHEN
    )
    mapper.add_mapping(
        "TICKETING AGENCIES", Category.ENTERTAINMENT, EntertainmentSubcategory.CONCERTS
    )
    mapper.add_mapping(
        "TELECOMMUNICATION SERVICES", Category.BILLS_FEES, BillsFeesSubcategory.TELECOM
    )
    mapper.add_mapping(
        "MEDICAL SERVICES", Category.BILLS_FEES, BillsFeesSubcategory.HEALTH
    )
    mapper.add_mapping(
        "DRUG STORES", Category.BEAUTY_HEALTH, BeautyHealthSubcategory.HEALTH
    )
    mapper.add_mapping(
        "COSMETIC STORES", Category.BEAUTY_HEALTH, BeautyHealthSubcategory.BEAUTY
    )
    mapper.add_mapping("GIFT SHOPS", Category.GIFTS)  # No subcategory needed
    mapper.add_mapping("TRAVEL AGENCIES", Category.TRAVEL)  # No subcategory needed

    # Convert to format expected by processor
    processor.set_category_mapper(mapper.to_dict())

    # Initialize the Cashew client with web app URL
    client = CashewClient(base_url="https://budget-track.web.app")

    try:
        # Process transactions for a specific date range
        batch = processor.process(
            file_path="swisscard_transactions.xlsx",  # Your downloaded Swisscard XLSX file
            date_from=date(2024, 1, 1),
            date_to=date(2024, 3, 23),
        )

        print(f"Loaded {len(batch.transactions)} transactions")

        # Example of accessing transaction fields
        if batch.transactions:
            t = batch.transactions[0]
            print("\nExample transaction:")
            print(f"Date: {t.date}")
            print(f"Title: {t.title}")
            print(f"Amount: {t.amount} {t.currency}")
            print(f"Category: {t.category}")
            print(f"Subcategory: {t.subcategory}")
            print(f"Original Merchant Category: {t.meta['original_merchant_category']}")
            print(
                f"Original Registered Category: {t.meta['original_registered_category']}"
            )
            print(f"Account: {t.account}")
            print(f"Notes: {t.notes}")
            if t.meta.get("foreign_amount"):
                print(
                    f"Foreign Amount: {t.meta['foreign_amount']} {t.meta['foreign_currency']}"
                )

        # Get URL for uploading transactions to Cashew
        upload_url = client.upload_transactions(batch)
        print("\nOpen this URL in your browser to import the transactions:")
        print(upload_url)

        # Example of generating a single transaction URL
        single_url = client.get_add_transaction_url(
            amount=-42.50,
            title="Example Transaction",
            notes="Added via Python script",
            category="Shopping",
        )
        print("\nExample single transaction URL:")
        print(single_url)

    except Exception as e:
        print(f"Error processing transactions: {str(e)}")


if __name__ == "__main__":
    main()
