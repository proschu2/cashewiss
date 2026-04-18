"""
Actualiss CLI - Swiss Financial Institution Transaction Processor
"""

from typing import Any

import click
import sys
import os
from pathlib import Path

# Add the actualiss package to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from actualiss import SwisscardProcessor, ZKBProcessor, TransactionBatch
from actualiss.core.actual_client import ActualClient
from actualiss.config import get_config
from actualiss.logging_config import setup_logging


@click.group()
@click.version_option()
def main():
    """Actualiss - Process transactions from Swiss financial institutions for Actual Budget."""
    pass


def dry_run_process(file_path: str, processor: str, batch: Any) -> None:
    """
    Perform dry-run validation with comprehensive analysis.

    Args:
        file_path: Path to the transaction file
        processor: Name of the processor used
        batch: TransactionBatch containing processed transactions
    """
    click.echo("\n" + "=" * 60)
    click.echo("🔍 DRY-RUN VALIDATION RESULTS")
    click.echo("=" * 60)

    # 1. Show transaction preview (first 10 transactions)
    transactions = batch.to_actual_format()
    preview_count = min(10, len(transactions))

    click.echo(
        f"\n📊 TRANSACTION PREVIEW (first {preview_count} of {len(transactions)} transactions):"
    )
    click.echo("-" * 80)
    for i, tx in enumerate(transactions[:preview_count], 1):
        click.echo(
            f"{i:2d}. {tx['date']} | {tx['amount']:8d} | {tx['account']:15} | {tx['category']:15} | {tx['imported_payee']}"
        )

    # 2. Check for missing accounts
    accounts_found = set()
    categories_found = set()
    uncategorized_count = 0

    for tx in transactions:
        accounts_found.add(tx["account"])
        categories_found.add(tx["category"])
        if tx["category"] == "Uncategorized":
            uncategorized_count += 1

    missing_accounts = []
    # Common account names that might exist in Actual Budget
    common_accounts = [
        "Default Account",
        "Checking Account",
        "Savings Account",
        "Credit Card",
    ]
    for account in sorted(accounts_found):
        if account not in common_accounts:
            missing_accounts.append(account)

    click.echo(f"\n🏦 ACCOUNT ANALYSIS:")
    click.echo(f"   Total unique accounts found: {len(accounts_found)}")
    if missing_accounts:
        click.echo(f"   ⚠️  Accounts not in common list (may need manual setup):")
        for account in missing_accounts:
            click.echo(f"      - {account}")
    else:
        click.echo("   ✅ All accounts found in common reference list")

    # 3. Check for missing categories
    click.echo(f"\n📋 CATEGORY ANALYSIS:")
    click.echo(f"   Total unique categories found: {len(categories_found)}")
    if uncategorized_count > 0:
        click.echo(f"   ⚠️  Uncategorized transactions: {uncategorized_count}")
        click.echo("      These may need manual category assignment in Actual Budget")
    else:
        click.echo("   ✅ All transactions have categories assigned")

    # 4. Validation summary
    click.echo(f"\n📋 VALIDATION SUMMARY:")
    click.echo("-" * 40)
    click.echo(f"   Total transactions: {len(transactions)}")
    click.echo(
        f"   Date range: {transactions[0]['date']} to {transactions[-1]['date']}"
    )
    click.echo(f"   Processor used: {processor}")
    click.echo(f"   Source file: {file_path}")

    # 5. Issues and recommendations
    issues = []
    if missing_accounts:
        issues.append(f"Missing accounts: {len(missing_accounts)}")
    if uncategorized_count > 0:
        issues.append(f"Uncategorized transactions: {uncategorized_count}")

    if issues:
        click.echo(f"\n⚠️  POTENTIAL ISSUES:")
        for issue in issues:
            click.echo(f"   • {issue}")
        click.echo("\n💡 RECOMMENDATIONS:")
        click.echo(
            "   • Review and update category mappings in processor configuration"
        )
        click.echo("   • Ensure accounts exist in Actual Budget before importing")
        click.echo(
            "   • Consider adding custom merchant mappings for better categorization"
        )
    else:
        click.echo(f"\n✅ ALL VALIDATIONS PASSED")
        click.echo("   Ready for import to Actual Budget")


@main.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output CSV file path")
@click.option(
    "--processor",
    "-p",
    type=click.Choice(["swisscard", "zkb"]),
    default="swisscard",
    help="Transaction processor to use",
)
@click.option(
    "--date-from", type=click.DateTime(), help="Start date for filtering (YYYY-MM-DD)"
)
@click.option(
    "--date-to", type=click.DateTime(), help="End date for filtering (YYYY-MM-DD)"
)
@click.option(
    "--account",
    type=str,
    help="Actual Budget account name (defaults to 'Default Account')",
)
@click.option(
    "--dry-run", is_flag=True, help="Validate without importing to Actual Budget"
)
@click.option(
    "--method",
    type=click.Choice(["csv", "api"]),
    default="api",
    help="Export method (default: api)",
)
@click.option(
    "--actual-url",
    help="Actual Budget URL (defaults to ACTUAL_SERVER_URL env var)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
@click.option("--log-file", type=click.Path(), help="Log to file")
def process(
    file_path,
    output,
    processor,
    date_from,
    date_to,
    account,
    dry_run,
    method,
    actual_url,
    verbose,
    log_file,
):
    """Process transaction file and import to Actual Budget."""

    setup_logging(verbose=verbose, log_file=log_file)

    click.echo(f"Processing {file_path} with {processor} processor...")

    if processor == "swisscard":
        processor_instance = SwisscardProcessor()
    elif processor == "zkb":
        processor_instance = ZKBProcessor()
    else:
        raise click.ClickException(f"Unknown processor: {processor}")

    try:
        batch = processor_instance.process(file_path, date_from, date_to)
        click.echo(f"✓ Processed {len(batch.transactions)} transactions")
    except Exception as e:
        raise click.ClickException(f"Error processing file: {e}")

    if dry_run:
        dry_run_process(file_path, processor, batch)
        return

    if method == "csv":
        output_path = output or f"actual_transactions_{processor}.csv"
        _write_actual_csv(batch, output_path)
        click.echo(f"✓ CSV exported to: {output_path}")
    elif method == "api":
        try:
            config = get_config()
            if actual_url:
                config["server_url"] = actual_url
        except ValueError as e:
            click.echo(f"Configuration error: {e}", err=True)
            click.echo(
                "\nRequired environment variables:\n"
                "  ACTUAL_SERVER_URL - Actual Budget server URL\n"
                "  ACTUAL_PASSWORD - Actual Budget password\n"
                "  ACTUAL_FILE - Budget file name\n"
                "\nOptional:\n"
                "  ACTUAL_ENCRYPTION_PASSWORD - For encrypted budgets",
                err=True,
            )
            raise click.Abort()

        from actualiss import ActualClient

        client = ActualClient(**config)

        with client:
            account_name = account or "Default Account"
            try:
                account_id = client.get_or_create_account(account_name)
            except ValueError as e:
                click.echo(f"Account error: {e}", err=True)
                raise click.Abort()

            transactions = batch.to_actual_format()
            imported = client.import_transactions(transactions, account_id)
            client.commit()

            click.echo(f"✓ Imported {imported} transactions to '{account_name}'")


def _write_actual_csv(batch: Any, output_path: str):
    """Write batch to CSV in Actual Budget format."""
    import csv

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(["Date", "Amount", "Category", "Title", "Note", "Account"])

        # Write transactions
        for tx in batch.to_actual_format():
            writer.writerow(
                [
                    tx["date"],
                    tx["amount"],
                    tx["category"],
                    tx["title"],
                    tx["notes"] or "",
                    tx["account"] or "",
                ]
            )


@main.group()
def accounts():
    """Account management commands."""
    pass


@accounts.command("list")
def list_accounts():
    """List all accounts in Actual Budget."""

    try:
        config = get_config()
    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        click.echo(
            "\nRequired environment variables:\n"
            "  ACTUAL_SERVER_URL - Actual Budget server URL\n"
            "  ACTUAL_PASSWORD - Actual Budget password\n"
            "  ACTUAL_FILE - Budget file name",
            err=True,
        )
        raise click.Abort()

    from actualiss import ActualClient

    client = ActualClient(**config)

    with client:
        accs = client.get_accounts()
        click.echo(f"Found {len(accs)} accounts:")
        for acc in accs:
            balance_str = f"{acc['balance'] / 100:.2f}" if acc["balance"] else "N/A"
            click.echo(f"  - {acc['name']}: {balance_str} ({acc['type']})")


@accounts.command("create")
@click.argument("name")
@click.option(
    "--type",
    "account_type",
    type=click.Choice(["checking", "savings", "credit"]),
    default="checking",
    help="Account type (default: checking)",
)
def create_account(name, account_type):
    """Create a new account in Actual Budget."""

    try:
        config = get_config()
    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        click.echo(
            "\nRequired environment variables:\n"
            "  ACTUAL_SERVER_URL - Actual Budget server URL\n"
            "  ACTUAL_PASSWORD - Actual Budget password\n"
            "  ACTUAL_FILE - Budget file name",
            err=True,
        )
        raise click.Abort()

    from actualiss import ActualClient

    client = ActualClient(**config)

    with client:
        try:
            account_id = client.get_or_create_account(name, account_type)
            click.echo(f"✓ Account '{name}' created with ID: {account_id}")
        except ValueError as e:
            if "cancelled" in str(e).lower():
                click.echo(f"Account creation cancelled: {e}")
            else:
                click.echo(f"Error: {e}", err=True)
            raise click.Abort()


@main.command()
def categories():
    """Show Cashew to Actual category mappings."""
    from actualiss.core.category_map import ACTUAL_CATEGORY_MAP
    from actualiss.core.enums import Category

    click.echo("Category Mappings:")
    for cat, actual_name in ACTUAL_CATEGORY_MAP.items():
        click.echo(f"  {cat.name:20} -> {actual_name}")


@main.command()
def ui():
    """Launch the Streamlit web UI."""
    import subprocess

    # Path to the streamlit app
    app_path = Path(__file__).parent.parent / "streamlit" / "app.py"

    if not app_path.exists():
        click.echo(f"Error: Streamlit app not found at {app_path}", err=True)
        click.echo("\nMake sure you have installed the GUI dependencies:")
        click.echo("  pip install -e '.[gui]'")
        raise click.Abort()

    click.echo("Starting Actualiss Streamlit UI...")
    click.echo(f"App path: {app_path}")
    click.echo("\nPress Ctrl+C to stop the server")

    try:
        # Run streamlit with the app
        subprocess.run(
            ["streamlit", "run", str(app_path)],
            check=True,
        )
    except FileNotFoundError:
        click.echo(
            "\nError: streamlit not found. Install it with:",
            err=True,
        )
        click.echo("  pip install -e '.[gui]'")
        raise click.Abort()
    except KeyboardInterrupt:
        click.echo("\n\nStopped.")
    except subprocess.CalledProcessError as e:
        click.echo(f"\nError running streamlit: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
