import streamlit as st
import plotly.express as px
from datetime import date, timedelta
import pandas as pd
import time
import webbrowser
import json
import urllib.parse
import traceback

from cashewiss import (
    SwisscardProcessor,
    VisecaProcessor,
    MigrosProcessor,
    ZKBProcessor,
    TransactionBatch,
    Transaction,
    CashewClient,
)
from cashewiss.core.enums import (
    Category as TransactionCategory,
    IncomeSubcategory,
    BillsSubcategory,
    EssentialsSubcategory,
    DiningSubcategory,
    ShoppingSubcategory,
    HouseholdSubcategory,
    PersonalCareSubcategory,
    LeisureSubcategory,
    HobbiesSubcategory,
    TravelSubcategory,
    FinancialSubcategory,
)


class StreamlitProcessorComponent:
    """Base component for handling processor-specific Streamlit UIs with state management."""

    def __init__(
        self,
        processor_type: str,
        file_extensions: list[str],
        default_name: str,
        info_message: str = None,
    ):
        self.processor_type = (
            processor_type.lower()
        )  # e.g. "swisscard", "migros", "zkb"
        self.file_extensions = file_extensions  # e.g. ["xlsx"] or ["csv"]
        self.default_name = default_name
        self.info_message = info_message

        # Initialize session state
        if f"{self.processor_type}_file" not in st.session_state:
            st.session_state[f"{self.processor_type}_file"] = None
        if f"{self.processor_type}_processor" not in st.session_state:
            st.session_state[f"{self.processor_type}_processor"] = None
        if f"{self.processor_type}_account" not in st.session_state:
            st.session_state[f"{self.processor_type}_account"] = ""
        if f"{self.processor_type}_provider" not in st.session_state:
            st.session_state[f"{self.processor_type}_provider"] = default_name

    def render(self, date_from: date, date_to: date):
        """Render the processor UI and handle file processing."""
        st.header(f"{self.default_name} Transaction Processing")

        if self.info_message:
            st.info(self.info_message)

        col1, col2 = st.columns(2)

        with col1:
            uploaded_file = st.file_uploader(
                f"Upload {self.default_name} {self.file_extensions[0].upper()} file",
                type=self.file_extensions,
            )
            if uploaded_file != st.session_state[f"{self.processor_type}_file"]:
                st.session_state[f"{self.processor_type}_file"] = uploaded_file
                st.session_state[f"{self.processor_type}_processor"] = None
                # Clear any existing transaction data
                if "edited_transactions" in st.session_state:
                    del st.session_state["edited_transactions"]
                if "filtered_transactions" in st.session_state:
                    del st.session_state["filtered_transactions"]
                st.rerun()

        with col2:
            account_name = st.text_input(
                "Account Name (for categorization)",
                value=st.session_state[f"{self.processor_type}_account"],
                key=f"{self.processor_type}_account_input",
            )
            provider_name = st.text_input(
                "Provider Name (will be added to all transactions)",
                value=st.session_state[f"{self.processor_type}_provider"],
                key=f"{self.processor_type}_provider_input",
            )

            # Update stored values and reprocess if needed
            values_changed = False
            if account_name != st.session_state[f"{self.processor_type}_account"]:
                st.session_state[f"{self.processor_type}_account"] = account_name
                values_changed = True
            if provider_name != st.session_state[f"{self.processor_type}_provider"]:
                st.session_state[f"{self.processor_type}_provider"] = provider_name
                values_changed = True

            if (
                values_changed
                and st.session_state[f"{self.processor_type}_processor"] is not None
            ):
                st.info("Updating processor with new values...")
                # Clear processor and any existing transaction data
                st.session_state[f"{self.processor_type}_processor"] = None
                if "edited_transactions" in st.session_state:
                    del st.session_state["edited_transactions"]
                st.rerun()

        # Process file if we have it
        if st.session_state[f"{self.processor_type}_file"]:
            try:
                with st.spinner("Processing transactions..."):
                    processor = self.get_processor(provider_name, account_name)
                    batch = processor.process(
                        st.session_state[f"{self.processor_type}_file"],
                        date_from=date_from,
                        date_to=date_to,
                    )
                    display_transactions(batch.transactions)
            except Exception as e:
                st.error(f"Error processing transactions: {str(e)}")

    def get_processor(self, provider_name: str, account_name: str):
        """Get or create processor with current settings."""
        processor = st.session_state[f"{self.processor_type}_processor"]

        # Create new processor if needed or if values changed
        if (
            processor is None
            or processor.name != provider_name
            or processor.account_name != account_name
        ):
            processor = self.create_processor(provider_name, account_name)
            st.session_state[f"{self.processor_type}_processor"] = processor

        return processor

    def create_processor(self, provider_name: str, account_name: str):
        """Create appropriate processor based on type."""
        if self.processor_type == "swisscard":
            return SwisscardProcessor(name=provider_name, account=account_name)
        elif self.processor_type == "migros":
            return MigrosProcessor(name=provider_name, account=account_name)
        elif self.processor_type == "zkb":
            return ZKBProcessor(name=provider_name, account=account_name)


def get_subcategories_for_category(category: str) -> list[str]:
    """Get valid subcategories for a given category."""
    category_to_subcategory = {
        TransactionCategory.INCOME.value: [sub.value for sub in IncomeSubcategory],
        TransactionCategory.BILLS.value: [sub.value for sub in BillsSubcategory],
        TransactionCategory.ESSENTIALS.value: [
            sub.value for sub in EssentialsSubcategory
        ],
        TransactionCategory.DINING.value: [sub.value for sub in DiningSubcategory],
        TransactionCategory.SHOPPING.value: [sub.value for sub in ShoppingSubcategory],
        TransactionCategory.HOUSEHOLD.value: [
            sub.value for sub in HouseholdSubcategory
        ],
        TransactionCategory.PERSONAL_CARE.value: [
            sub.value for sub in PersonalCareSubcategory
        ],
        TransactionCategory.LEISURE.value: [sub.value for sub in LeisureSubcategory],
        TransactionCategory.HOBBIES.value: [sub.value for sub in HobbiesSubcategory],
        TransactionCategory.TRAVEL.value: [sub.value for sub in TravelSubcategory],
        TransactionCategory.FINANCIAL.value: [
            sub.value for sub in FinancialSubcategory
        ],
    }
    return category_to_subcategory.get(category, [])


st.set_page_config(
    page_title="Cashewiss - Swiss Card Transaction Processor",
    page_icon=":currency_exchange:",
    layout="wide",
)


def main():
    st.title("Cashewiss - Swiss Card Transaction Processor")

    st.markdown("""
    Process your credit card transactions from Swiss financial institutions and integrate them with the Cashew budget app.
    
    ### Features
    - Process transactions from Viseca, Swisscard, and Migros Bank
    - Automatic category mapping
    - Export to CSV or directly to Cashew
    - Transaction analytics and visualizations
    """)

    processor_type = st.sidebar.selectbox(
        "Select Processor", ["Viseca", "Swisscard", "Migros Bank", "ZKB"]
    )

    # Date range selector in sidebar
    st.sidebar.header("Date Range")
    today = date.today()
    default_end = today.replace(day=1) - timedelta(days=1)  # Last day of previous month
    default_start = default_end.replace(day=1)  # First day of previous month
    date_from = st.sidebar.date_input("From", value=default_start)
    date_to = st.sidebar.date_input("To", value=default_end)

    if date_from > date_to:
        st.error("Error: Start date must be before end date")
        return

    if processor_type == "Viseca":
        process_viseca(date_from, date_to)
    elif processor_type == "Migros Bank":
        process_migros(date_from, date_to)
    elif processor_type == "ZKB":
        process_zkb(date_from, date_to)
    else:
        process_swisscard(date_from, date_to)


def process_zkb(date_from: date, date_to: date):
    """Handle ZKB transaction processing."""
    processor = StreamlitProcessorComponent(
        processor_type="zkb",
        file_extensions=["csv"],
        default_name="ZKB",
        info_message="""
        ℹ️ Expected CSV format:
        - Semicolon (;) separated values
        - Required columns: Date, Booking text, ZKB reference, Reference number, Debit CHF, Credit CHF, Value date, Balance CHF
        - Debit/Credit amounts in separate columns
        """,
    )
    processor.render(date_from, date_to)


def process_viseca(date_from: date, date_to: date):
    """Handle Viseca transaction processing."""
    st.header("Viseca Transaction Processing")

    # Store transaction results in session state
    if "viseca_results" not in st.session_state:
        st.session_state.viseca_results = None
        st.session_state.viseca_show_results = False

    # Store the client to avoid reinitializing
    if "viseca_client" not in st.session_state:
        st.session_state.viseca_client = None

    # Store credentials separately (not for form input)
    if "saved_viseca_username" not in st.session_state:
        st.session_state.saved_viseca_username = ""
    if "saved_viseca_password" not in st.session_state:
        st.session_state.saved_viseca_password = ""
    if "saved_viseca_card_id" not in st.session_state:
        st.session_state.saved_viseca_card_id = ""
    if "saved_viseca_account_name" not in st.session_state:
        st.session_state.saved_viseca_account_name = ""
    if "saved_viseca_provider_name" not in st.session_state:
        st.session_state.saved_viseca_provider_name = "Viseca"

    # Show the info box only if we haven't processed anything yet
    if not st.session_state.viseca_show_results:
        st.info("""
        ℹ️ To obtain your Card ID, you'll need to:
        1. Login to your account on the Viseca website
        2. Go to your card details section
        3. Find your Card ID in the card information
        """)

    # Create the form for credentials
    with st.form("viseca_credentials"):
        # Display form inputs with default values (not using session state directly)
        username = st.text_input(
            "Username", value=st.session_state.saved_viseca_username
        )
        password = st.text_input(
            "Password", type="password", value=st.session_state.saved_viseca_password
        )
        card_id = st.text_input("Card ID", value=st.session_state.saved_viseca_card_id)
        account_name = st.text_input(
            "Account Name (for categorization)",
            value=st.session_state.saved_viseca_account_name,
        )
        provider_name = st.text_input(
            "Provider Name (will be added to all transactions)",
            value=st.session_state.saved_viseca_provider_name,
        )

        # Add checkbox to force reinitialization of client (useful if 2FA token expires)
        reinit_client = st.checkbox(
            "Reinitialize client (check if 2FA token expired)", value=False
        )

        submit = st.form_submit_button("Process Transactions")

        # Display warning about Viseca One App
        if not st.session_state.viseca_show_results:
            st.warning("""
                    ⚠️ **Important: Viseca One App Required**
                    
                    This integration requires you to have the Viseca One mobile app installed and set up.
                    The app is necessary for authentication and accessing your transaction data.
                    """)

    # Handle form submission or use cached results
    if submit or st.session_state.viseca_show_results:
        if submit and not all([username, password, card_id]):
            st.error("Please fill in all credentials")
        else:
            # Set the flag to show results even after page refresh
            st.session_state.viseca_show_results = True

            # If we have submitted the form, process the transactions
            if submit:
                # Save credentials to session state (separate from form)
                st.session_state.saved_viseca_username = username
                st.session_state.saved_viseca_password = password
                st.session_state.saved_viseca_card_id = card_id
                st.session_state.saved_viseca_account_name = account_name
                st.session_state.saved_viseca_provider_name = provider_name

                try:
                    # Check if we need to reinitialize the processor
                    if (
                        st.session_state.viseca_client is None
                        or reinit_client
                        or username != st.session_state.saved_viseca_username
                        or password != st.session_state.saved_viseca_password
                        or card_id != st.session_state.saved_viseca_card_id
                    ):
                        with st.spinner(
                            "Initializing Viseca client... (check your mobile app for 2FA)"
                        ):
                            # Set credentials in environment
                            import os

                            os.environ["VISECA_USERNAME"] = username
                            os.environ["VISECA_PASSWORD"] = password
                            os.environ["VISECA_CARD_ID"] = card_id

                            # Create a new processor with the credentials
                            processor = VisecaProcessor(
                                name=provider_name, account=account_name
                            )

                            # Save the client for future use
                            st.session_state.viseca_client = processor
                            st.success(
                                "Successfully authenticated with Viseca (2FA token saved)"
                            )
                    else:
                        # Reuse existing client
                        processor = st.session_state.viseca_client
                        st.info("Reusing existing Viseca client (no 2FA required)")

                        # Update the processor name and account if they changed
                        if (
                            processor.name != provider_name
                            or processor.account_name != account_name
                        ):
                            processor.name = provider_name
                            processor.account_name = account_name

                    # Process transactions
                    with st.spinner("Processing transactions..."):
                        batch = processor.process(
                            None,  # No file needed for Viseca
                            date_from=date_from,
                            date_to=date_to,
                        )

                        # Convert to DataFrame and store in session state
                        if batch.transactions:
                            df = pd.DataFrame(
                                [
                                    {
                                        "Date": t.date,
                                        "Title": t.title,
                                        "Amount": t.amount,
                                        "Currency": t.currency,
                                        "Category": t.category.value
                                        if t.category
                                        else None,
                                        "Subcategory": t.subcategory.value
                                        if t.subcategory
                                        else None,
                                        "Account": t.account,
                                        "Notes": t.notes,
                                    }
                                    for t in batch.transactions
                                ]
                            )
                            st.session_state.viseca_results = df
                        else:
                            st.warning(
                                "No transactions found for the selected date range"
                            )
                            # Don't clear previous results if no new results found
                            if st.session_state.viseca_results is None:
                                st.session_state.viseca_show_results = False
                                return

                except Exception as e:
                    st.error(f"Error processing transactions: {str(e)}")
                    st.session_state.viseca_show_results = False
                    return

            # Display results if available
            if st.session_state.viseca_results is not None:
                df = st.session_state.viseca_results
                st.success(f"Found {len(df)} transactions")

                # Display the transactions table
                st.dataframe(
                    df,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Amount": st.column_config.NumberColumn(
                            "Amount", format="CHF %.2f"
                        ),
                        "Date": st.column_config.DateColumn(
                            "Date", format="DD/MM/YYYY"
                        ),
                    },
                )

                # Export section in its own container to survive refreshes
                export_container = st.container()
                with export_container:
                    st.subheader("Export Options")
                    col1, col2 = st.columns(2)

                    with col1:
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "Export to CSV",
                            csv,
                            "viseca_transactions.csv",
                            "text/csv",
                            key="download-viseca-csv",
                            use_container_width=True,
                        )

                    with col2:
                        if st.button(
                            "Export to Cashew",
                            key="export-viseca-cashew",
                            use_container_width=True,
                        ):
                            # Create export UI in its own container
                            st.info("Preparing Cashew export...")

                            try:
                                # Generate export URL without complex Transaction objects
                                base_url = "https://budget-track.web.app/addTransaction"

                                # Convert to simple transaction format
                                simple_transactions = []
                                for _, t in df.iterrows():
                                    date_str = (
                                        t["Date"].isoformat()
                                        if hasattr(t["Date"], "isoformat")
                                        else str(t["Date"])
                                    )
                                    simple_transactions.append(
                                        {
                                            "date": date_str,
                                            "title": str(t["Title"]),
                                            "amount": float(t["Amount"]),
                                            "currency": str(t["Currency"]),
                                            "category": str(t["Category"])
                                            if pd.notna(t["Category"])
                                            else None,
                                            "subcategory": str(t["Subcategory"])
                                            if pd.notna(t["Subcategory"])
                                            else None,
                                            "account": str(t["Account"])
                                            if pd.notna(t["Account"])
                                            else None,
                                            "notes": str(t["Notes"])
                                            if pd.notna(t["Notes"])
                                            else None,
                                        }
                                    )

                                # Split into manageable batches
                                batch_size = 25
                                batches = [
                                    simple_transactions[i : i + batch_size]
                                    for i in range(
                                        0, len(simple_transactions), batch_size
                                    )
                                ]

                                if batches:
                                    # Generate URL for first batch
                                    first_batch = batches[0]
                                    transactions_data = {"transactions": first_batch}
                                    json_str = json.dumps(
                                        transactions_data, separators=(",", ":")
                                    )
                                    encoded_json = urllib.parse.quote(json_str)
                                    export_url = f"{base_url}?JSON={encoded_json}"

                                    # Show clickable URL
                                    st.success(
                                        f"Export ready with {len(batches)} batch(es) of transactions"
                                    )
                                    st.markdown(
                                        f"**[Click here to open first batch in Cashew]({export_url})**"
                                    )

                                    # Option to open all batches
                                    if st.button("Open All Batches in Browser"):
                                        progress_bar = st.progress(0)
                                        status_text = st.empty()

                                        for i, batch in enumerate(batches):
                                            try:
                                                status_text.text(
                                                    f"Processing batch {i + 1}/{len(batches)}..."
                                                )
                                                batch_data = {"transactions": batch}
                                                batch_json = json.dumps(
                                                    batch_data, separators=(",", ":")
                                                )
                                                batch_encoded = urllib.parse.quote(
                                                    batch_json
                                                )
                                                batch_url = (
                                                    f"{base_url}?JSON={batch_encoded}"
                                                )

                                                webbrowser.open(batch_url)
                                                progress_bar.progress(
                                                    (i + 1) / len(batches)
                                                )

                                                if i < len(batches) - 1:
                                                    time.sleep(
                                                        3
                                                    )  # Give browser time to open tab

                                            except Exception as e:
                                                st.error(
                                                    f"Error opening batch {i + 1}: {str(e)}"
                                                )
                                                st.markdown(
                                                    f"**[Manual link for batch {i + 1}]({batch_url})**"
                                                )
                                                continue

                                        status_text.success(
                                            f"All {len(batches)} batches processed!"
                                        )
                                        progress_bar.empty()
                                else:
                                    st.error("No transactions to export")

                            except Exception as e:
                                st.error(f"Error during export: {str(e)}")
                                st.code(traceback.format_exc())

                # Add a reset button to start over
                if st.button("Process Different Transactions", key="reset-viseca"):
                    st.session_state.viseca_show_results = False
                    st.session_state.viseca_results = None
                    st.rerun()


def process_migros(date_from: date, date_to: date):
    """Handle Migros Bank transaction processing."""
    processor = StreamlitProcessorComponent(
        processor_type="migros",
        file_extensions=["csv"],
        default_name="Migros Bank",
        info_message="""
        ℹ️ Expected CSV format:
        - Semicolon (;) separated values
        - Header starts at row 14
        - Required columns: Datum, Buchungstext, Mitteilung, Referenznummer, Betrag, Saldo, Valuta
        - Amounts in Swiss format (e.g. -12,32)

        Note: The processor automatically filters out:
        - Viseca card entries (containing "Karte: 474124*****0910")
        - TWINT entries containing "+417"
        """,
    )
    processor.render(date_from, date_to)


def process_swisscard(date_from: date, date_to: date):
    """Handle Swisscard transaction processing."""
    processor = StreamlitProcessorComponent(
        processor_type="swisscard",
        file_extensions=["xlsx"],
        default_name="Swisscard",
        info_message=None,
    )
    processor.render(date_from, date_to)


def display_transactions(transactions):
    """Display processed transactions with visualizations."""
    if not transactions:
        st.warning("No transactions found for the selected date range")
        return

    # Convert transactions to DataFrame
    df = pd.DataFrame(
        [
            {
                "Date": t.date,
                "Title": t.title,
                "Amount": t.amount,
                "Currency": t.currency,
                "Category": t.category.value if t.category else None,
                "Subcategory": t.subcategory.value if t.subcategory else None,
                "Account": t.account,
                "Notes": t.notes,
            }
            for t in transactions
        ]
    )

    # Add sorting and filtering options
    st.sidebar.header("Filters")

    # Category filter
    categories = sorted(df["Category"].unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "Filter by Categories", categories, default=categories
    )

    # Account filter
    accounts = sorted(df["Account"].unique().tolist())
    selected_accounts = st.sidebar.multiselect(
        "Filter by Accounts", accounts, default=accounts
    )

    # Amount range filter
    min_amount = float(df["Amount"].min())
    max_amount = float(df["Amount"].max())
    amount_range = st.sidebar.slider(
        "Amount Range", min_amount, max_amount, (min_amount, max_amount), step=10.0
    )

    # Apply filters
    mask = (
        df["Category"].isin(selected_categories)
        & df["Account"].isin(selected_accounts)
        & (df["Amount"] >= amount_range[0])
        & (df["Amount"] <= amount_range[1])
    )
    filtered_df = df[mask]

    # Display transaction statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Transactions", len(filtered_df))
    with col2:
        total_spent = filtered_df["Amount"].sum()
        st.metric("Total Amount", f"CHF {total_spent:,.2f}")
    with col3:
        avg_transaction = filtered_df["Amount"].mean()
        st.metric("Average Transaction", f"CHF {avg_transaction:,.2f}")

    # Transaction timeline
    st.subheader("Transaction Timeline")
    daily_totals = filtered_df.groupby("Date")["Amount"].sum().reset_index()
    fig = px.line(
        daily_totals,
        x="Date",
        y="Amount",
        title="Daily Transaction Amounts",
    )
    st.plotly_chart(fig)

    # Enhanced transaction table
    st.subheader("Transaction Details")

    # Group by options
    group_by = st.selectbox("Group by", ["None", "Category", "Account", "Date"])

    if group_by != "None":
        filtered_df = filtered_df.sort_values(group_by)

    # Help message for editing
    st.info(
        "💡 Click on the Category or Subcategory cells to change them. Changes will be saved automatically."
    )

    # Initialize edited data in session state
    if "edited_transactions" not in st.session_state:
        st.session_state.edited_transactions = filtered_df.copy()

    # Display enhanced table with custom formatting and editing capabilities
    edited_df = st.data_editor(
        st.session_state.edited_transactions,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Amount": st.column_config.NumberColumn(
                "Amount", format="CHF %.2f", help="Transaction amount", disabled=True
            ),
            "Date": st.column_config.DateColumn(
                "Date", format="DD/MM/YYYY", help="Transaction date", disabled=True
            ),
            "Category": st.column_config.SelectboxColumn(
                "Category",
                help="Click to change transaction category",
                width="medium",
                options=sorted([cat.value for cat in TransactionCategory]),
                required=True,
            ),
            "Title": st.column_config.TextColumn(
                "Title", help="Transaction description", width="large", disabled=True
            ),
            "Currency": st.column_config.TextColumn(
                "Currency", help="Transaction currency", width="small", disabled=True
            ),
            "Subcategory": st.column_config.SelectboxColumn(
                "Subcategory",
                help="Click to change transaction subcategory (options depend on selected category)",
                width="medium",
                options=sorted(
                    set(
                        sub.value
                        for cat_enum in [
                            IncomeSubcategory,
                            BillsSubcategory,
                            EssentialsSubcategory,
                            DiningSubcategory,
                            ShoppingSubcategory,
                            HouseholdSubcategory,
                            PersonalCareSubcategory,
                            LeisureSubcategory,
                            HobbiesSubcategory,
                            TravelSubcategory,
                            FinancialSubcategory,
                        ]
                        for sub in cat_enum
                    )
                ),
            ),
            "Account": st.column_config.TextColumn(
                "Account", help="Account name", width="medium", disabled=True
            ),
            "Notes": st.column_config.TextColumn(
                "Notes", help="Additional notes", width="large", disabled=True
            ),
        },
        key="transaction_editor",
    )

    # Update session state with edited data
    if edited_df is not None:
        st.session_state.edited_transactions = edited_df
        filtered_df = edited_df  # Update filtered_df to reflect changes

    # Export options
    st.subheader("Export Options")

    # Store filtered data in session state
    st.session_state.filtered_transactions = filtered_df

    col1, col2 = st.columns(2)

    with col1:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            "Export to CSV",
            csv,
            "transactions.csv",
            "text/csv",
            key="download-csv",
            use_container_width=True,
        )

    with col2:
        if st.button("Export to Cashew", key="export-cashew", use_container_width=True):
            # Create a container that will persist through rerendering
            debug_container = st.container()
            with debug_container:
                # Add debug log file
                import logging
                import tempfile
                import os
                import traceback

                # Create a temp log file
                log_dir = tempfile.gettempdir()
                log_file = os.path.join(log_dir, "cashewiss_export.log")

                # Configure logging
                logging.basicConfig(
                    filename=log_file,
                    level=logging.DEBUG,
                    format="%(asctime)s - %(levelname)s - %(message)s",
                )

                # Log the start of processing
                logging.info(f"Starting Cashew export - Log file: {log_file}")

                try:
                    # Load CashewClient
                    logging.info("Attempting to initialize CashewClient")
                    try:
                        client = CashewClient()
                        logging.info("CashewClient initialized successfully")
                    except Exception as e:
                        error_msg = f"Failed to import CashewClient: {str(e)}"
                        logging.error(error_msg)
                        st.error(error_msg)
                        st.error("Please check if package is installed correctly")
                        logging.error(f"Exception details: {repr(e)}")
                        return

                    # Check session state
                    logging.info("Checking for filtered transactions in session state")
                    if "filtered_transactions" not in st.session_state:
                        error_msg = "No filtered_transactions in session state"
                        logging.error(error_msg)
                        st.error(error_msg)
                        return

                    # Get the filtered transactions
                    stored_df = st.session_state.filtered_transactions
                    logging.info(
                        f"Found dataframe with {len(stored_df) if stored_df is not None else 0} rows"
                    )

                    if stored_df is None or stored_df.empty:
                        error_msg = "No transactions found to export"
                        logging.error(error_msg)
                        st.error(error_msg)
                        return

                    # Confirm dataframe content
                    st.write(f"Found {len(stored_df)} transactions")
                    logging.info(f"DataFrame columns: {list(stored_df.columns)}")

                    # Try to create a simple Transaction first to test
                    logging.info("Testing Transaction creation")
                    try:
                        test_transaction = Transaction(
                            amount=1.0,
                            title="Test Transaction",
                            date=date.today(),
                            currency="CHF",
                            category=None,
                            subcategory=None,
                            account="Test",
                            notes="Test",
                        )
                        logging.info("Test transaction created successfully")
                    except Exception as e:
                        error_msg = f"Failed to create test transaction: {str(e)}"
                        logging.error(error_msg)
                        st.error(error_msg)
                        st.exception(e)
                        return

                    # Test the CashewClient
                    logging.info("Testing CashewClient initialization")
                    try:
                        client = CashewClient()
                        logging.info("CashewClient initialized successfully")
                    except Exception as e:
                        error_msg = f"Failed to initialize CashewClient: {str(e)}"
                        logging.error(error_msg)
                        st.error(error_msg)
                        st.exception(e)
                        return

                    # Process just one transaction as a test
                    logging.info("Testing export with a single transaction")
                    test_batch = TransactionBatch(
                        transactions=[test_transaction], source="Streamlit Test"
                    )

                    try:
                        # Try the export with dry_run=True to test
                        logging.info("Attempting test export with dry_run=True")
                        test_url = client.export_to_api(test_batch, dry_run=True)
                        logging.info(f"Test export successful: {test_url}")
                    except Exception as e:
                        error_msg = f"Test export failed: {str(e)}"
                        logging.error(error_msg)
                        logging.error(f"Exception details: {repr(e)}")
                        st.error(error_msg)
                        st.exception(e)
                        st.error(
                            "The export failed at the test stage. Please check the log file."
                        )
                        return

                    # Now proceed with validating the actual transactions
                    logging.info("Beginning transaction validation")

                    # Convert DataFrame rows back to Transaction objects
                    logging.info("Converting DataFrame to Transaction objects")
                    try:
                        from cashewiss.core.enums import Category, SUBCATEGORY_TYPES

                        export_transactions = []
                        for _, row in stored_df.iterrows():
                            try:
                                # Get category and subcategory objects from string values
                                category = None
                                subcategory = None

                                if row["Category"]:
                                    try:
                                        category = Category(row["Category"])

                                        if row["Subcategory"]:
                                            # Find the correct subcategory enum type for this category
                                            subcategory_type = SUBCATEGORY_TYPES.get(
                                                category
                                            )
                                            if subcategory_type:
                                                subcategory = subcategory_type(
                                                    row["Subcategory"]
                                                )
                                    except ValueError as ve:
                                        logging.warning(
                                            f"Could not parse category/subcategory: {ve}"
                                        )

                                # Create Transaction object
                                transaction = Transaction(
                                    date=row["Date"],
                                    title=row["Title"],
                                    amount=float(row["Amount"]),
                                    currency=row["Currency"],
                                    category=category,
                                    subcategory=subcategory,
                                    account=row["Account"],
                                    notes=row["Notes"],
                                )
                                export_transactions.append(transaction)
                                logging.debug(
                                    f"Successfully converted row: {row['Title']}"
                                )
                            except Exception as row_error:
                                logging.error(
                                    f"Error converting row {row['Title']}: {str(row_error)}"
                                )
                                continue

                        logging.info(
                            f"Successfully converted {len(export_transactions)} transactions"
                        )

                        # Create TransactionBatch
                        export_batch = TransactionBatch(
                            transactions=export_transactions, source="Streamlit Export"
                        )

                        # Attempt the actual export
                        st.info(
                            f"Exporting {len(export_transactions)} transactions to Cashew..."
                        )

                        # Enable debug mode for Viseca exports
                        enable_debug = any(
                            t.notes == "Viseca"
                            or (
                                hasattr(t, "meta")
                                and t.meta
                                and t.meta.get("processor") == "Viseca"
                            )
                            for t in export_transactions
                        )

                        if enable_debug:
                            logging.info(
                                "Detected Viseca transactions - enabling debug mode"
                            )
                            st.info("Debug mode enabled for Viseca transactions")

                        export_result = client.export_to_api(
                            export_batch, dry_run=True, debug=enable_debug
                        )
                        st.success("Successfully generated export URL!")
                        st.markdown(
                            f"**Export URL**: [Click to open in browser]({export_result})"
                        )
                        st.warning(
                            "Note: For large transaction sets, multiple browser windows may open (batches of 25 transactions)."
                        )

                        if st.button("Proceed with Export", key="execute_export"):
                            with st.spinner("Exporting transactions to Cashew..."):
                                try:
                                    client.export_to_api(
                                        export_batch, debug=enable_debug
                                    )
                                    st.success(
                                        f"Exported {len(export_transactions)} transactions to Cashew!"
                                    )
                                except Exception as export_error:
                                    error_msg = f"Export failed: {str(export_error)}"
                                    logging.error(error_msg)
                                    logging.error(
                                        f"Exception details: {traceback.format_exc()}"
                                    )
                                    st.error(error_msg)

                                    # Provide manual URL as fallback
                                    st.error(
                                        "Automatic export failed. Please use the URL below to manually import:"
                                    )
                                    st.markdown(
                                        f"**Manual Import URL**: [Click to open in browser]({export_result})"
                                    )

                    except Exception as conversion_error:
                        error_msg = f"Failed to convert and export transactions: {str(conversion_error)}"
                        logging.error(error_msg)
                        logging.error(f"Exception traceback: {traceback.format_exc()}")
                        st.error(error_msg)
                        st.error("See log file for details")
                        with open(log_file, "r") as f:
                            log_contents = f.read()
                            with st.expander("View debug log"):
                                st.text(log_contents)

                except Exception as e:
                    error_msg = f"An unexpected error occurred: {str(e)}"
                    logging.error(error_msg)
                    logging.error(f"Exception details: {repr(e)}")
                    st.error(error_msg)
                    st.exception(e)

                    # Display the log file contents for debugging
                    try:
                        with open(log_file, "r") as f:
                            log_contents = f.read()
                            with st.expander("View debug log"):
                                st.text(log_contents)
                    except Exception as log_e:
                        st.error(f"Could not read log file: {str(log_e)}")


if __name__ == "__main__":
    main()
