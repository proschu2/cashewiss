import streamlit as st
import plotly.express as px
from datetime import date, timedelta
import pandas as pd

from cashewiss import SwisscardProcessor, VisecaProcessor, Category

st.set_page_config(
    page_title="Cashewiss - Swiss Card Transaction Processor",
    page_icon="💳",
    layout="wide",
)


def main():
    st.title("Cashewiss - Swiss Card Transaction Processor 💳")
    st.markdown("""
    Process your credit card transactions from Swiss financial institutions and integrate them with the Cashew budget app.
    
    ### Features
    - Process transactions from Viseca and Swisscard
    - Automatic category mapping
    - Export to CSV or directly to Cashew
    - Transaction analytics and visualizations
    """)

    processor_type = st.sidebar.selectbox("Select Processor", ["Viseca", "Swisscard"])

    # Date range selector in sidebar
    st.sidebar.header("Date Range")
    today = date.today()
    default_start = today - timedelta(days=90)
    date_from = st.sidebar.date_input("From", value=default_start)
    date_to = st.sidebar.date_input("To", value=today)

    if date_from > date_to:
        st.error("Error: Start date must be before end date")
        return

    if processor_type == "Viseca":
        process_viseca(date_from, date_to)
    else:
        process_swisscard(date_from, date_to)


def process_viseca(date_from: date, date_to: date):
    """Handle Viseca transaction processing."""
    st.header("Viseca Transaction Processing")

    st.info("""
    ℹ️ To obtain your Card ID, you'll need to:
    1. Login to your account on the Viseca website
    2. Go to your card details section
    3. Find your Card ID in the card information
    """)

    with st.form("viseca_credentials"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        card_id = st.text_input("Card ID")
        account_name = st.text_input("Account Name (for categorization)")
        provider_name = st.text_input(
            "Provider Name (will be added to all transactions)"
        )

        submit = st.form_submit_button("Process Transactions")

    if submit:
        if not all([username, password, card_id]):
            st.error("Please fill in all credentials")
            return

        # Check if we need to reinitialize the processor
        current_creds = {
            "username": username,
            "password": password,
            "card_id": card_id,
            "provider_name": provider_name,
            "account_name": account_name,
        }

        if (
            "viseca_processor" not in st.session_state
            or "viseca_creds" not in st.session_state
            or st.session_state.viseca_creds != current_creds
        ):
            try:
                with st.spinner("Initializing Viseca client..."):
                    # Set credentials in environment
                    import os

                    os.environ["VISECA_USERNAME"] = username
                    os.environ["VISECA_PASSWORD"] = password
                    os.environ["VISECA_CARD_ID"] = card_id

                    processor = VisecaProcessor(
                        name=provider_name, account=account_name
                    )
                    # Store in session state
                    st.session_state.viseca_processor = processor
                    st.session_state.viseca_creds = current_creds
            except Exception as e:
                st.error(f"Error initializing Viseca client: {str(e)}")
                return

        try:
            processor = st.session_state.viseca_processor
            with st.spinner("Processing transactions..."):
                st.warning("""
                ⚠️ **Important: Viseca One App Required**
                
                This integration requires you to have the Viseca One mobile app installed and set up.
                The app is necessary for authentication and accessing your transaction data.
                """)

                # Process transactions
                batch = processor.process(
                    None,  # No file needed for Viseca
                    date_from=date_from,
                    date_to=date_to,
                )

                display_transactions(batch.transactions)

        except Exception as e:
            st.error(f"Error processing transactions: {str(e)}")


def process_swisscard(date_from: date, date_to: date):
    """Handle Swisscard transaction processing."""
    st.header("Swisscard Transaction Processing")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader("Upload Swisscard XLSX file", type=["xlsx"])

    with col2:
        account_name = st.text_input(
            "Account Name (for categorization)", key="swisscard_account"
        )
        provider_name = st.text_input(
            "Provider Name (will be added to all transactions)", key="swisscard_notes"
        )

    if uploaded_file:
        try:
            with st.spinner("Processing transactions..."):
                processor = SwisscardProcessor(name=provider_name, account=account_name)

                # Process transactions
                batch = processor.process(
                    uploaded_file,
                    date_from=date_from,
                    date_to=date_to,
                )

                display_transactions(batch.transactions)

        except Exception as e:
            st.error(f"Error processing transactions: {str(e)}")


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

    # # Category breakdown
    # st.subheader("Spending by Category")
    # category_totals = filtered_df.groupby("Category")["Amount"].sum().reset_index()
    # fig = px.pie(
    #     category_totals,
    #     values="Amount",
    #     names="Category",
    #     title="Transaction Distribution by Category"
    # )
    # st.plotly_chart(fig)

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

    # Display enhanced table with custom formatting
    st.dataframe(
        filtered_df,
        hide_index=True,
        column_config={
            "Amount": st.column_config.NumberColumn(
                "Amount", format="CHF %.2f", help="Transaction amount"
            ),
            "Date": st.column_config.DateColumn(
                "Date", format="DD/MM/YYYY", help="Transaction date"
            ),
            "Category": st.column_config.Column(
                "Category", help="Transaction category", width="medium"
            ),
            "Title": st.column_config.TextColumn(
                "Title", help="Transaction description", width="large"
            ),
            "Currency": st.column_config.TextColumn(
                "Currency", help="Transaction currency", width="small"
            ),
            "Subcategory": st.column_config.TextColumn(
                "Subcategory", help="Transaction subcategory", width="medium"
            ),
            "Account": st.column_config.TextColumn(
                "Account", help="Account name", width="medium"
            ),
            "Notes": st.column_config.TextColumn(
                "Notes", help="Additional notes", width="large"
            ),
        },
    )

    # Export options
    st.subheader("Export Options")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Export to CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                "Download CSV", csv, "transactions.csv", "text/csv", key="download-csv"
            )

    with col2:
        if st.button("Export to Cashew"):
            from cashewiss import CashewClient

            client = CashewClient()
            # Convert back to TransactionBatch
            from cashewiss import TransactionBatch, Transaction

            batch = TransactionBatch(
                transactions=[
                    Transaction(
                        amount=row["Amount"],
                        title=row["Title"],
                        date=row["Date"],
                        currency=row["Currency"],
                        category=Category(row["Category"]) if row["Category"] else None,
                        subcategory=row["Subcategory"],
                        account=row["Account"],
                        notes=row["Notes"],
                    )
                    for _, row in filtered_df.iterrows()
                ],
                source="Streamlit App",
            )
            url = client.upload_transactions(batch)
            st.markdown(f"[Open in Cashew]({url})")


if __name__ == "__main__":
    main()
