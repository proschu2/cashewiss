from datetime import datetime
import click
import importlib.util
from typing import Optional, Dict

from dotenv import load_dotenv

from cashewiss import (
    SwisscardProcessor,
    VisecaProcessor,
    CashewClient,
    CategoryMapping,
    Category,
    EssentialsSubcategory,
    DiningSubcategory,
    ShoppingSubcategory,
    LeisureSubcategory,
    BillsSubcategory,
    PersonalCareSubcategory,
    HouseholdSubcategory,
    HobbiesSubcategory,
)


def setup_category_mapper() -> Dict[str, CategoryMapping]:
    """Create and configure the default category mapper for merchant categories"""
    default_mappings = {
        # Groceries and Dining
        "GROCERY STORES": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
        ),
        "CONVENIENCE STORES": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.GROCERIES
        ),
        "RESTAURANTS": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.SOCIAL
        ),
        "FAST FOOD RESTAURANTS": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.DELIVERY
        ),
        "BUSINESS DINING": CategoryMapping(
            category=Category.DINING, subcategory=DiningSubcategory.WORK
        ),
        # Transit
        "TRANSPORTATION": CategoryMapping(
            category=Category.ESSENTIALS, subcategory=EssentialsSubcategory.TRANSIT
        ),
        # Shopping
        "CLOTHING STORES": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.CLOTHING
        ),
        "ELECTRONICS": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.ELECTRONICS
        ),
        "GAME/TOY STORES": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.MEDIA
        ),
        # Household
        "HOUSEHOLD APPLIANCE STORES": CategoryMapping(
            category=Category.HOUSEHOLD, subcategory=HouseholdSubcategory.APPLIANCES
        ),
        # Entertainment and Leisure
        "TICKETING AGENCIES": CategoryMapping(
            category=Category.LEISURE, subcategory=LeisureSubcategory.EVENTS
        ),
        # Bills and Services
        "TELECOMMUNICATION SERVICES": CategoryMapping(
            category=Category.BILLS, subcategory=BillsSubcategory.TELECOM
        ),
        "MEDICAL SERVICES": CategoryMapping(
            category=Category.PERSONAL_CARE, subcategory=PersonalCareSubcategory.MEDICAL
        ),
        # Personal Care
        "DRUG STORES": CategoryMapping(
            category=Category.PERSONAL_CARE, subcategory=PersonalCareSubcategory.MEDICAL
        ),
        "COSMETIC STORES": CategoryMapping(
            category=Category.PERSONAL_CARE,
            subcategory=PersonalCareSubcategory.PERSONAL,
        ),
        # Shopping - Gifts
        "GIFT SHOPS": CategoryMapping(
            category=Category.SHOPPING, subcategory=ShoppingSubcategory.GIFTS
        ),
        # Travel
        "TRAVEL AGENCIES": CategoryMapping(category=Category.TRAVEL),
        # Hobbies
        "HOBBY STORES": CategoryMapping(
            category=Category.HOBBIES, subcategory=HobbiesSubcategory.TECH
        ),
    }
    return default_mappings


@click.group()
def main():
    """Cashewiss - Process Swiss financial transactions for Cashew budget app"""
    load_dotenv()
    pass


@main.command()
@click.argument("file_path", type=click.Path(exists=True), required=False)
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
    help="Custom name for the processor (used in transaction notes)",
)
@click.option(
    "--account",
    help="Custom account name (if different from processor name)",
)
@click.option(
    "--processor",
    type=click.Choice(["swisscard", "viseca"]),
    default="swisscard",
    help="Processor to use (default: swisscard)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview mode (shows first 5 rows for CSV, shows URL for API)",
)
def process(
    file_path: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    method: str,
    output: Optional[str],
    cashew_url: str,
    name: str,
    account: Optional[str],
    processor: str,
    dry_run: bool,
):
    """Process transactions from a Swisscard XLSX file or Viseca API"""
    try:
        # Parse dates if provided
        from_date = (
            datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
        )
        to_date = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None

        # Initialize processor with custom name, account and default category mappings
        if processor == "swisscard":
            if not file_path:
                raise click.UsageError("file_path is required for Swisscard processor")
            processor_instance = SwisscardProcessor(name=name, account=account)
        else:  # viseca
            if importlib.util.find_spec("viseca") is None:
                raise click.UsageError(
                    "Viseca processor requires the viseca package. "
                    "Install it with: pip install cashewiss[viseca]"
                )
            processor_instance = VisecaProcessor(name=name, account=account)
            if file_path:
                click.echo(
                    "Note: file_path is ignored for Viseca processor as it uses API"
                )

        # Process transactions
        batch = processor_instance.process(
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
            click.echo(f"Category: {t.category.value if t.category else None}")
            click.echo(f"Subcategory: {t.subcategory.value if t.subcategory else None}")
            click.echo(f"Account: {t.account}")
            if t.meta and t.meta.get("original_merchant_category"):
                click.echo("Original Categories:")
                click.echo(
                    f"  Merchant Category: {t.meta['original_merchant_category']}"
                )
                if "original_registered_category" in t.meta:
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
    mappings = setup_category_mapper()

    click.echo("Available category mappings:")
    for merchant_category, mapping in mappings.items():
        subcategory_str = (
            f" -> {mapping.subcategory.value}" if mapping.subcategory else ""
        )
        click.echo(f"{merchant_category}: {mapping.category.value}{subcategory_str}")


if __name__ == "__main__":
    main()
