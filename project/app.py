import streamlit as st


st.set_page_config(layout="wide")


from datetime import datetime, timedelta
import logging

from project.settings import (
    NOW,
)
from project.transactions_state import get_state_transactions_df
from project.transactions_aggregation import (
    FREQUENCIES,
    get_time_aggregated_transactions_df,
)
from project.barplot import get_barplot
from project import app_data

log = logging.getLogger(__name__)
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


expenses_container = st.container()

with expenses_container:
    st.title("Expense visualization")

    frequency = st.selectbox(
        "Frequency",
        [f for f in FREQUENCIES],
        format_func=lambda x: x.display_name,
        index=1,
    )
    group_by_col = st.selectbox(
        "Group by",
        ("one_group", "contractor", "account_name", "category"),
        index=0,
        format_func=lambda x: {"one_group": "None"}.get(x, x),
    )

    c1, c2 = st.columns(2)
    with c1:
        start_year = NOW.year if NOW.month > 1 else NOW.year - 1
        start_date = st.date_input("Start Date", value=datetime(start_year, 1, 1))
        start_date = datetime.combine(start_date, datetime.min.time())
    with c2:
        end_date = st.date_input("End Date")
        end_date = datetime.combine(end_date, datetime.min.time()) + timedelta(
            hours=23, minutes=59, seconds=59
        )

    container = st.container()
    all = st.checkbox("Select all transactions", value=True)

    if all:
        categories = container.multiselect(
            "Select one or more categories:",
            app_data.all_categories,
            [c for c in app_data.all_categories if c != "own-transfer"],
        )
    else:
        categories = container.multiselect(
            "Select one or more categories:", app_data.all_categories
        )

    n_biggest_groups = st.slider(
        "Number of groups", min_value=1, max_value=50, value=7, step=1
    )

    state_transactions_df = get_state_transactions_df(
        all_transactions_df=app_data.all_transactions_df,
        categories=categories,
        start_date=start_date,
        end_date=end_date,
        group_by_col=group_by_col,
        n_biggest_groups=n_biggest_groups,
    )

    _df_expense = get_time_aggregated_transactions_df(
        state_transactions_df[state_transactions_df["type"] == "outcome"],
        frequency=frequency,
    )

    _df_income = get_time_aggregated_transactions_df(
        state_transactions_df[state_transactions_df["type"] == "income"],
        frequency=frequency,
    )

    barplot_tab, transactions_table_tab = st.tabs(["Bars", "Transactions"])

    # plot income and outcome
    with barplot_tab:
        col1, col2 = st.columns([1, 1])
        with col1:
            view_income = st.toggle("Show income", value=False)
        with col2:
            view_expense = st.toggle("Show expense", value=True)

        st.plotly_chart(
            get_barplot(
                _df_income,
                _df_expense,
                view_income=view_income,
                view_expense=view_expense,
            ),
            use_container_width=True,
        )

        st.dataframe(_df_expense.transpose())

    # table
    with transactions_table_tab:
        st.dataframe(state_transactions_df)
