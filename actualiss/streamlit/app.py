"""
Streamlit UI for Actualiss - Actual Budget Import Tool

Provides a web interface for:
- Connection to Actual Budget server
- Transaction file upload (ZKB/Swisscard)
- Category mapping preview
- Transaction preview before import
- Progress tracking during import
"""

import streamlit as st
import pandas as pd
import tempfile
import os
import yaml
from typing import Optional

# Import actualiss components
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from actualiss import (
    ActualClient,
    ZKBProcessor,
    SwisscardProcessor,
)
from actualiss.core.category_map import ACTUAL_CATEGORY_MAP
from actualiss.core.enums import Category


def init_session_state():
    """Initialize session state variables."""
    if "connected" not in st.session_state:
        st.session_state.connected = False
    if "client_config" not in st.session_state:
        st.session_state.client_config = None
    if "transactions" not in st.session_state:
        st.session_state.transactions = None
    if "accounts" not in st.session_state:
        st.session_state.accounts = None
    if "custom_mappings" not in st.session_state:
        st.session_state.custom_mappings = {}


def render_sidebar():
    """Render the connection settings sidebar."""
    with st.sidebar:
        st.header("⚙️ Connection Settings")

        st.markdown("""
        Configure your Actual Budget connection details.
        These settings are used to connect to your Actual Budget server.
        """)

        st.markdown("---")

        # Server URL
        server_url = st.text_input(
            "Server URL",
            value="http://localhost:5006",
            help="Actual Budget server URL (e.g., http://localhost:5006)",
            placeholder="http://localhost:5006",
        )

        # Password
        password = st.text_input(
            "Password",
            type="password",
            help="Actual Budget account password",
            placeholder="Enter password",
        )

        # Budget file name
        budget_file = st.text_input(
            "Budget File Name",
            value="My Budget",
            help="Name of your budget file in Actual (case-sensitive)",
            placeholder="My Budget",
        )

        # Optional: Encryption password
        with st.expander("Advanced Settings"):
            encryption_password = st.text_input(
                "Encryption Password (Optional)",
                type="password",
                help="Required if your budget file is encrypted",
                placeholder="Leave empty if not encrypted",
            )

        st.markdown("---")

        # Test connection button
        col1, col2 = st.columns(2)
        with col1:
            test_button = st.button("🔌 Test Connection", use_container_width=True)

        with col2:
            if st.session_state.get("connected", False):
                st.success("✓ Connected")

        if test_button:
            try:
                with st.spinner("Connecting to Actual Budget..."):
                    client = ActualClient(
                        server_url=server_url,
                        password=password,
                        file=budget_file,
                        encryption_password=encryption_password or None,
                    )

                    with client:
                        accounts = client.get_accounts()
                        st.session_state.connected = True
                        st.session_state.accounts = accounts
                        st.session_state.client_config = {
                            "server_url": server_url,
                            "password": password,
                            "file": budget_file,
                            "encryption_password": encryption_password or None,
                        }

                    st.success(f"✅ Connected! Found {len(accounts)} accounts")
                    st.balloons()

            except Exception as e:
                st.error(f"❌ Connection failed: {e}")
                st.session_state.connected = False
                st.session_state.client_config = None
                st.session_state.accounts = None

        st.markdown("---")

        # Connection info
        if st.session_state.get("connected", False):
            st.info(f"""
            **Connected to:**
            - Server: {st.session_state.client_config["server_url"]}
            - Budget: {st.session_state.client_config["file"]}
            - Accounts: {len(st.session_state.accounts)}
            """)


def render_file_upload():
    """Render file upload section."""
    st.subheader("📤 1. Upload Transaction File")

    st.markdown("""
    Upload your transaction file from ZKB or Swisscard.
    The file will be processed and transactions will be extracted.
    """)

    uploaded_file = st.file_uploader(
        "Choose a transaction file",
        type=["xlsx", "csv"],
        help="""
        - **XLSX**: Swisscard or ZKB Excel export
        - **CSV**: ZKB CSV export (semicolon-separated)
        """,
        label_visibility="visible",
    )

    return uploaded_file


def process_uploaded_file(uploaded_file):
    """Process uploaded file and return transactions."""
    if not uploaded_file:
        return None

    try:
        # Save to temp file
        file_suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name

        # Determine processor based on file type
        with st.spinner("Processing transactions..."):
            if uploaded_file.name.endswith(".xlsx"):
                # Could be Swisscard or ZKB
                # Try Swisscard first
                try:
                    processor = SwisscardProcessor()
                    batch = processor.process(tmp_path)
                except Exception:
                    # Fall back to ZKB
                    processor = ZKBProcessor()
                    batch = processor.process(tmp_path)
            else:
                # CSV - assume ZKB
                processor = ZKBProcessor()
                batch = processor.process(tmp_path)

            transactions = batch.to_actual_format()
            st.session_state.transactions = transactions

            return transactions

    except Exception as e:
        st.error(f"❌ Failed to process file: {e}")
        return None
    finally:
        if "tmp_path" in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass


def render_transaction_preview(transactions):
    """Render transaction preview table."""
    st.subheader("👀 2. Preview Transactions")

    if not transactions:
        st.warning("No transactions to preview. Upload a file first.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(transactions)

    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Transactions", len(df))
    with col2:
        total_amount = df["amount"].sum()
        st.metric("Total Amount", f"CHF {total_amount:,.2f}")
    with col3:
        if "date" in df.columns and not df["date"].empty:
            date_range = f"{df['date'].min()} to {df['date'].max()}"
            st.metric("Date Range", date_range)

    # Transaction table
    st.markdown("### Transaction Details")

    # Configure columns
    column_config = {
        "date": st.column_config.DateColumn(
            "Date", format="YYYY-MM-DD", help="Transaction date"
        ),
        "title": st.column_config.TextColumn(
            "Title", help="Transaction description", width="large"
        ),
        "amount": st.column_config.NumberColumn(
            "Amount (CHF)", format="%.2f", help="Transaction amount"
        ),
        "category": st.column_config.TextColumn(
            "Category", help="Mapped Actual Budget category", width="medium"
        ),
    }

    # Display editable dataframe
    st.dataframe(
        df.head(50),  # Show first 50
        use_container_width=True,
        column_config=column_config,
        hide_index=True,
    )

    if len(df) > 50:
        st.info(f"📊 Showing first 50 of {len(df)} transactions")


def render_account_selector(accounts):
    """Render account selection dropdown."""
    st.subheader("🏦 3. Select Import Account")

    if not accounts:
        st.warning("No accounts available. Connect to Actual Budget first.")
        return None

    account_options = {acc["name"]: acc for acc in accounts}
    selected_name = st.selectbox(
        "Select Account to Import Transactions",
        options=list(account_options.keys()),
        help="Choose the Actual Budget account to import these transactions into",
    )

    return account_options[selected_name]


def render_category_mappings():
    """Render category mapping information."""
    with st.expander("📋 Category Mappings", expanded=False):
        st.markdown("""
        This shows how Cashew categories are mapped to Actual Budget categories.
        """)

        # Create mapping table
        mapping_data = []
        for cat_enum, actual_name in ACTUAL_CATEGORY_MAP.items():
            mapping_data.append(
                {
                    "Cashew Category": cat_enum.value,
                    "Actual Budget Category": actual_name,
                }
            )

        df = pd.DataFrame(mapping_data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Cashew Category": st.column_config.TextColumn(
                    "Cashew Category", width="medium"
                ),
                "Actual Budget Category": st.column_config.TextColumn(
                    "Actual Budget Category", width="medium"
                ),
            },
        )


def render_category_mapping_configuration():
    """Render category mapping configuration interface."""
    with st.expander("🔧 Category Mapping Configuration", expanded=False):
        st.markdown("""
        Customize how Cashew categories map to Actual Budget categories.
        Leave a field empty to use the default mapping.
        """)

        st.markdown("---")

        total = len(ACTUAL_CATEGORY_MAP)
        custom = len(st.session_state.custom_mappings)
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            st.metric("Total Mappings", total)
        with col2:
            st.metric("Customized", custom)
        with col3:
            st.metric("Using Defaults", total - custom)

        st.markdown("---")
        st.write("### Category Mappings")

        for cat_enum, default_name in ACTUAL_CATEGORY_MAP.items():
            current_mapping = st.session_state.custom_mappings.get(
                cat_enum, default_name
            )
            is_custom = cat_enum in st.session_state.custom_mappings

            if is_custom:
                st.markdown(f"**✏️ {cat_enum.value}** *(customized)*")
            else:
                st.markdown(f"**{cat_enum.value}**")

            col1, col2, col3 = st.columns([3, 3, 1])
            with col1:
                st.text("Default:")
                st.caption(default_name)

            with col2:
                new_name = st.text_input(
                    "Custom Mapping",
                    value=current_mapping if is_custom else "",
                    key=f"map_{cat_enum.name}",
                    help="Enter custom category name or leave empty to use default",
                    label_visibility="collapsed",
                )

                if new_name and new_name != default_name:
                    st.session_state.custom_mappings[cat_enum] = new_name
                elif not new_name and is_custom:
                    del st.session_state.custom_mappings[cat_enum]

            with col3:
                if is_custom:
                    if st.button(
                        "↺", key=f"reset_{cat_enum.name}", help="Reset to default"
                    ):
                        del st.session_state.custom_mappings[cat_enum]
                        st.rerun()

            st.markdown("---")

        col1, col2, col3 = st.columns([2, 2, 2])

        with col1:
            if st.button(
                "💾 Save Configuration", type="secondary", use_container_width=True
            ):
                config_data = {
                    "custom_category_mappings": {
                        cat.name: name
                        for cat, name in st.session_state.custom_mappings.items()
                    }
                }

                try:
                    config_path = os.path.join(
                        os.path.dirname(__file__), "..", "category_mappings.yml"
                    )

                    with open(config_path, "w") as f:
                        yaml.dump(config_data, f, default_flow_style=False)

                    st.success("✓ Configuration saved to category_mappings.yml")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Failed to save configuration: {e}")

        with col2:
            if st.button(
                "🔄 Reset to Defaults", type="secondary", use_container_width=True
            ):
                st.session_state.custom_mappings = {}
                st.rerun()

        with col3:
            if st.button(
                "📂 Load from File", type="secondary", use_container_width=True
            ):
                try:
                    config_path = os.path.join(
                        os.path.dirname(__file__), "..", "category_mappings.yml"
                    )

                    if os.path.exists(config_path):
                        with open(config_path, "r") as f:
                            config_data = yaml.safe_load(f)

                        if config_data and "custom_category_mappings" in config_data:
                            for cat_name, actual_name in config_data[
                                "custom_category_mappings"
                            ].items():
                                try:
                                    cat_enum = Category[cat_name]
                                    st.session_state.custom_mappings[cat_enum] = (
                                        actual_name
                                    )
                                except KeyError:
                                    st.warning(f"⚠️ Unknown category: {cat_name}")

                            st.success(
                                f"✓ Loaded {len(config_data['custom_category_mappings'])} custom mappings"
                            )
                            st.rerun()
                    else:
                        st.info("No existing configuration file found")
                except Exception as e:
                    st.error(f"❌ Failed to load configuration: {e}")


def render_import_section(transactions, selected_account):
    """Render import button and execute import."""
    st.subheader("🚀 4. Import to Actual Budget")

    if not transactions:
        st.warning("No transactions to import. Upload and preview a file first.")
        return

    if not selected_account:
        st.warning("No account selected. Choose an account first.")
        return

    # Import options
    col1, col2 = st.columns(2)
    with col1:
        dry_run = st.checkbox(
            "🔍 Dry Run (Validate Only)",
            value=True,
            help="Validate transactions without importing",
        )

    with col2:
        if dry_run:
            st.info("Will validate without importing")
        else:
            st.warning("Will import transactions to Actual")

    # Import button
    import_button = st.button(
        "🚀 Import Transactions",
        type="primary",
        use_container_width=True,
        disabled=not transactions or not selected_account,
    )

    if import_button and transactions and selected_account:
        try:
            client = ActualClient(**st.session_state.client_config)

            with client:
                account_id = selected_account["id"]
                account_name = selected_account["name"]

                if dry_run:
                    # Dry run - show what would be imported
                    st.info(
                        f"🔍 Dry run mode - validating {len(transactions)} transactions"
                    )

                    with st.expander("Sample transactions to import", expanded=True):
                        for i, txn in enumerate(transactions[:5]):
                            st.json(txn)
                        if len(transactions) > 5:
                            st.info(f"... and {len(transactions) - 5} more")

                    st.success(
                        f"✅ Validation passed! Ready to import {len(transactions)} transactions to '{account_name}'"
                    )

                else:
                    # Actual import
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    status_text.text(f"Importing {len(transactions)} transactions...")

                    for i, txn in enumerate(transactions):
                        client.import_transactions([txn], account_id)
                        progress = (i + 1) / len(transactions)
                        progress_bar.progress(progress)

                        if (i + 1) % 10 == 0:
                            status_text.text(
                                f"Imported {i + 1}/{len(transactions)} transactions..."
                            )

                    client.commit()

                    progress_bar.empty()
                    status_text.empty()

                    st.success(
                        f"✅ Successfully imported {len(transactions)} transactions to '{account_name}'!"
                    )
                    st.balloons()

        except Exception as e:
            st.error(f"❌ Import failed: {e}")
            st.exception(e)


def main():
    """Main application entry point."""
    # Page config
    st.set_page_config(
        page_title="Actualiss - Actual Budget Import",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    init_session_state()

    # Header
    st.title("🏦 Actualiss - Actual Budget Import")
    st.markdown("""
    Import your Swiss financial transactions (ZKB, Swisscard) directly into Actual Budget.
    Connect to your Actual Budget server, upload transaction files, and import with category mapping.
    """)

    st.markdown("---")

    # Render sidebar with connection settings
    render_sidebar()

    # Check connection
    if not st.session_state.get("connected", False):
        st.info(
            "👈 Configure your Actual Budget connection in the sidebar and click 'Test Connection' to get started"
        )
        st.stop()

    # File upload section
    uploaded_file = render_file_upload()

    if uploaded_file:
        # Process file
        transactions = process_uploaded_file(uploaded_file)

        if transactions:
            # Render preview
            render_transaction_preview(transactions)

            st.markdown("---")

            # Account selection
            selected_account = render_account_selector(st.session_state.accounts)

            # Category mappings
            render_category_mappings()

            render_category_mapping_configuration()

            # Import section
            render_import_section(transactions, selected_account)


if __name__ == "__main__":
    main()
