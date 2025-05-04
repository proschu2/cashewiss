from cashewiss.processors import ZKBProcessor


def main():
    # Initialize the ZKB processor
    processor = ZKBProcessor(account="ZKB Main Account")

    # Process transactions
    # Replace with your actual CSV file path
    transactions = processor.process(
        file_path="path/to/your/zkb_transactions.csv",
        # Optionally filter by date
        # date_from=date(2025, 1, 1),
        # date_to=date(2025, 12, 31),
    )

    # Print processed transactions
    for transaction in transactions.transactions:
        print(
            f"{transaction.date}: {transaction.title} - "
            f"{transaction.amount} {transaction.currency} "
            f"({transaction.category.value if transaction.category else 'Uncategorized'})"
        )


if __name__ == "__main__":
    main()
