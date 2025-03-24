from datetime import datetime
import click
from typing import Optional

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


def setup_category_mapper():
    """Create and configure the default category mapper"""
    mapper = ProviderCategoryMapper()

    # Add default mappings
    mapper.add_mapping("GROCERY STORES", Category.GROCERIES, GroceriesSubcategory.MEAL)
    mapper.add_mapping(
        "CONVENIENCE STORES", Category.GROCERIES, GroceriesSubcategory.SNACKS
    )
    mapper.add_mapping("RESTAURANTS", Category.DINING, DiningSubcategory.FRIENDS)
    mapper.add_mapping(
        "FAST FOOD RESTAURANTS", Category.DINING, DiningSubcategory.DELIVERY
    )
    mapper.add_mapping("BUSINESS DINING", Category.DINING, DiningSubcategory.WORK)
    mapper.add_mapping("TRANSPORTATION", Category.TRANSIT)
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
    mapper.add_mapping("GIFT SHOPS", Category.GIFTS)
    mapper.add_mapping("TRAVEL AGENCIES", Category.TRAVEL)

    return mapper


@click.group()
def main():
    """Cashewiss - Process Swiss financial transactions for Cashew budget app"""
    pass


@main.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--date-from", type=click.STRING, help="Start date (YYYY-MM-DD)")
@click.option("--date-to", type=click.STRING, help="End date (YYYY-MM-DD)")
@click.option(
    "--method",
    type=click.Choice(["csv", "api"]),
    default="csv",
    help="Export method (default: csv)",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file path (required for CSV export unless --dry-run)",
)
@click.option(
    "--cashew-url",
    default="https://budget-track.web.app",
    help="Cashew web app URL (API only)",
)
@click.option(
    "--name",
    default="SwissCard",
    help="Custom name for the processor (affects transaction notes)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview mode (shows first 5 rows for CSV, shows URL for API)",
)
def process(
    file_path: str,
    date_from: Optional[str],
    date_to: Optional[str],
    method: str,
    output: Optional[str],
    cashew_url: str,
    name: str,
    dry_run: bool,
):
    """Process transactions from a Swisscard XLSX file"""
    try:
        # Parse dates if provided
        from_date = (
            datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
        )
        to_date = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None

        # Initialize processor with custom name and default category mappings
        processor = SwisscardProcessor(name=name)

        # Process transactions
        batch = processor.process(
            file_path=file_path, date_from=from_date, date_to=to_date
        )

        click.echo(f"Loaded {len(batch.transactions)} transactions")

        # Show example transaction if available
        if batch.transactions:
            t = batch.transactions[0]
            click.echo("\nExample transaction:")
            click.echo(f"Date: {t.date}")
            click.echo(f"Title: {t.title}")
            click.echo(f"Amount: {t.amount} {t.currency}")
            click.echo(f"Category: {t.category}")
            click.echo(f"Subcategory: {t.subcategory}")
            click.echo(f"Account: {t.account}")
            if t.meta and t.meta.get("original_merchant_category"):
                click.echo("Original Categories:")
                click.echo(
                    f"  Merchant Category: {t.meta['original_merchant_category']}"
                )
                click.echo(
                    f"  Registered Category: {t.meta['original_registered_category']}"
                )

            if t.meta and t.meta.get("foreign_amount"):
                click.echo("\nForeign Currency Info:")
                click.echo(
                    f"  Amount: {t.meta['foreign_amount']} {t.meta['foreign_currency']}"
                )

        # Export using selected method
        client = CashewClient(base_url=cashew_url)

        if method == "csv":
            if not dry_run and not output:
                raise click.UsageError(
                    "--output is required for CSV export unless --dry-run is used"
                )

            if dry_run:
                preview = client.export_to_csv(
                    batch, output or "preview.csv", dry_run=True
                )
                click.echo("\nCSV Preview (first 5 rows):")
                click.echo(preview)
            else:
                client.export_to_csv(batch, output)
                click.echo(
                    f"\nExported {len(batch.transactions)} transactions to {output}"
                )
        else:  # api
            if dry_run:
                preview = client.export_to_api(batch, dry_run=True)
                click.echo("\nAPI Import URL:")
                click.echo(preview)
                click.echo(
                    f"\nNote: {len(batch.transactions)} transactions will be processed in batches of 25"
                )
            else:
                click.echo("\nOpening browser windows to import transactions...")
                try:
                    client.export_to_api(batch)
                    click.echo(
                        f"Done! Processed {len(batch.transactions)} transactions in batches of 25."
                    )
                except RuntimeError as e:
                    click.echo(f"Error: {str(e)}")
                    click.echo(
                        "\nAs an alternative, you can use --dry-run to get the URLs and open them manually."
                    )

    except Exception as e:
        click.echo(f"Error processing transactions: {str(e)}", err=True)


@main.command()
def categories():
    """Show available category mappings"""
    mapper = setup_category_mapper()
    mappings = mapper.to_dict()

    click.echo("Available category mappings:")
    for merchant_category, (category, subcategory) in mappings.items():
        subcategory_str = f" -> {subcategory}" if subcategory else ""
        click.echo(f"{merchant_category}: {category}{subcategory_str}")


if __name__ == "__main__":
    main()
