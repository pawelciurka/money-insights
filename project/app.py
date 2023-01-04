from datetime import datetime
from turtle import width
import streamlit as st
import pandas as pd
from project.parsers import parse_directory_as_df
from project.settings import (
    TRANSACTIONS_FILES_DIR,
    CATEGORIES_RULES_FILE_PATH,
    project_dir,
)
import plotly.graph_objs as go
from enum import Enum
import os
import tempfile

st.set_page_config(layout="wide")

now = datetime.now()


class TimeInterval(Enum):
    DAY = 1
    MONTH = 2
    YEAR = 3


@st.cache
def read_all_transactions() -> pd.DataFrame:
    df = parse_directory_as_df(TRANSACTIONS_FILES_DIR, CATEGORIES_RULES_FILE_PATH)
    return df


def get_time_aggregated_expenses_df(
    input_df: pd.DataFrame,
    frequency=None,
) -> pd.DataFrame:

    # group by time and aggregate
    out_df = (
        input_df.groupby(
            [
                pd.Grouper(key="transaction_date", freq=frequency, label="left"),
                pd.Grouper(key="group_value"),
            ]
        )["amount_abs"]
        .apply(sum)
        .reset_index()
        .pivot(index="transaction_date", columns="group_value", values="amount_abs")
        .fillna(0.0)
    )
    return out_df


def get_barplot(df):
    layout = go.Layout(barmode="stack")
    data = []
    for name, trace in df.iteritems():
        data.append(go.Bar(x=trace.index, y=list(trace), name=name))

    fig = go.Figure(data=data, layout=layout)

    return fig


def get_significant_group_values(
    transactions_df: pd.DataFrame, group_by_col: str, n_biggest_groups: int
) -> set:
    biggest_groups_names = (
        transactions_df.groupby(group_by_col)["amount_abs"]
        .sum()
        .sort_values(ascending=False)[:n_biggest_groups]
    )
    return {g for g, _ in biggest_groups_names.iteritems()}


def date_to_datetime(date):
    return datetime(date.year, date.month, date.day)


expenses = st.container()


with expenses:
    st.title("Expense visualization")

    frequency = st.selectbox(
        "Frequency",
        ("1D", "1M", "1Y"),
        format_func=lambda x: {"1D": "Day", "1M": "Month", "1Y": "Year"}.get(x),
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
        start_year = now.year if now.month > 1 else now.year - 1
        start_date = st.date_input("Start Date", value=datetime(start_year, 1, 1))
    with c2:
        end_date = st.date_input("End Date")

    all_transactions_df = read_all_transactions()
    transactions_mask = (
        (all_transactions_df["type"] == "outcome")
        & (all_transactions_df["transaction_date"] >= date_to_datetime(start_date))
        & (all_transactions_df["transaction_date"] <= date_to_datetime(end_date))
    )
    selected_transactions_df = all_transactions_df[transactions_mask]

    unique_categories = list(set(selected_transactions_df["category"]))
    default_categories = [c for c in unique_categories if c != "own-transfer"]
    categories = st.multiselect(
        "Categories", unique_categories, default=default_categories
    )

    selected_transactions_df = selected_transactions_df[
        selected_transactions_df["category"].isin(categories)
    ]

    n_biggest_groups = st.slider(
        "Number of groups", min_value=1, max_value=50, value=7, step=1
    )
    biggest_groups_values = get_significant_group_values(
        selected_transactions_df, group_by_col, n_biggest_groups=n_biggest_groups
    )
    selected_transactions_df["group_value"] = selected_transactions_df[
        group_by_col
    ].map(lambda group: group if group in biggest_groups_values else "other")

    _df = get_time_aggregated_expenses_df(
        selected_transactions_df,
        frequency=frequency,
    )

    # plot
    fig = get_barplot(_df)
    st.plotly_chart(fig, use_container_width=True)

    # table
    st.dataframe(_df.transpose())

    # transactions_table
    st.title("Transactions")
    with st.expander("Open to see transactions table"):
        st.dataframe(selected_transactions_df)
        if st.button("Save transactions to CSV"):
            transaction_dumps_dir = os.path.join(
                project_dir, "data", "dumps", "transactions"
            )
            os.makedirs(transaction_dumps_dir, exist_ok=True)
            file_prefix = f"{now.year:04d}_{now.month:02d}_{now.day:02d}_{now.hour:02d}_{now.minute:02d}_"
            with tempfile.NamedTemporaryFile(
                "w",
                dir=transaction_dumps_dir,
                delete=False,
                prefix=file_prefix,
                suffix=".csv",
            ) as f:
                selected_transactions_df.to_csv(f, index=False, line_terminator="\n")
                st.write(f"Saved in {f.name}")
