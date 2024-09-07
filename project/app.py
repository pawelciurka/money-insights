from dataclasses import dataclass
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from project.parsers import (
    parse_directory_as_df,
    add_columns,
    read_categories_rules,
    filter_transactions_date_range,
)
from project.settings import (
    TRANSACTIONS_FILES_DIR,
    CATEGORIES_RULES_FILE_PATH,
    project_dir,
)
import plotly.graph_objs as go
from enum import Enum
import os
import tempfile
import logging

log = logging.getLogger(__name__)


st.set_page_config(layout="wide")

now = datetime.now()


@dataclass
class FrequencyConfig:
    tag: str  # e.g. 1D, see: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
    display_name: str  # e.g. : Day
    value_format: str
    label: str  # 'right' or 'left'


FREQUENCIES = [
    FrequencyConfig("1D", "Day", "%B %d", "left"),
    FrequencyConfig("1M", "Month", "%B %Y", "right"),
    FrequencyConfig("1Y", "Year", "%Y", "right"),
    FrequencyConfig("5Y", "5 Years", "%Y", "right"),
    FrequencyConfig("10Y", "10 Years", "%Y", "right"),
]


@st.cache_data
def read_raw_transactions() -> pd.DataFrame:
    df = parse_directory_as_df(TRANSACTIONS_FILES_DIR)
    return df


def get_time_aggregated_expenses_df(
    input_df: pd.DataFrame,
    frequency: FrequencyConfig,
) -> pd.DataFrame:

    groupers = []
    groupers.append(pd.Grouper(key="group_value"))
    groupers.append(
        pd.Grouper(key="transaction_date", freq=frequency.tag, label=frequency.label)
    )

    # group by time and aggregate
    out_df = (
        input_df.groupby(groupers)["amount_abs"]
        .apply(sum)
        .reset_index()
        .pivot(index="transaction_date", columns="group_value", values="amount_abs")
        .fillna(0.0)
    )

    out_df.index = out_df.index.map(lambda x: x.strftime(frequency.value_format))

    return out_df


def get_barplot(
    df_income: pd.DataFrame,
    df_outcome: pd.DataFrame,
    view_income=True,
    view_expense=True,
):
    if int(view_expense) + int(view_income) == 1:
        expense_bar_offset = -0.2
        income_bar_offset = -0.2
    else:
        expense_bar_offset = 0.0
        income_bar_offset = -0.4

    fig = go.Figure(
        layout=go.Layout(
            height=800,
            width=1000,
            barmode="relative",
            yaxis_showticklabels=True,
            yaxis_showgrid=True,
            # yaxis_range=[0, df.groupby(axis=1, level=0).sum().max().max() * 1.5],
            # Secondary y-axis overlayed on the primary one and not visible
            yaxis2=go.layout.YAxis(
                visible=True,
                matches="y",
                overlaying="y",
                anchor="x",
            ),
            font=dict(size=12),
            legend_orientation="h",
            hovermode="x",
            # margin=dict(b=0, t=10, l=0, r=10),
        )
    )

    if view_expense:
        for col in df_outcome.columns:
            if (df_outcome[col] == 0).all():
                continue
            fig.add_bar(
                x=df_outcome.index,
                y=df_outcome[col],
                # Set the right yaxis depending on the selected product (from enumerate)
                yaxis=f"y1",
                offsetgroup="1",
                offset=expense_bar_offset,
                width=0.4,
                legendgroup="outcome",
                legendgrouptitle_text="outcome",
                name=col,
            )

    # Add the traces
    if view_income:
        for col in df_income.columns:
            if (df_income[col] == 0).all():
                continue
            fig.add_bar(
                x=df_income.index,
                y=df_income[col],
                # Set the right yaxis depending on the selected product (from enumerate)
                yaxis=f"y2",
                # Offset the bar trace, offset needs to match the width
                # The values here are in milliseconds, 1billion ms is ~1/3 month
                offsetgroup="2",
                offset=income_bar_offset,
                width=0.4,
                legendgroup="income",
                legendgrouptitle_text="income",
                name=col,
                # marker_color=colors[t][col],
                # marker_line=dict(width=2, color="#333"),
                # hovertemplate="%{y}<extra></extra>"
            )

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


expenses = st.container()


@st.cache_data
def _add_columns(raw_transactions_df, categories_rules):
    return add_columns(raw_transactions_df, categories_rules)


with expenses:
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
        start_year = now.year if now.month > 1 else now.year - 1
        start_date = st.date_input("Start Date", value=datetime(start_year, 1, 1))
        start_date = datetime.combine(start_date, datetime.min.time())
    with c2:
        end_date = st.date_input("End Date")
        end_date = datetime.combine(end_date, datetime.min.time()) + timedelta(
            hours=23, minutes=59, seconds=59
        )

    categories_rules = read_categories_rules(CATEGORIES_RULES_FILE_PATH)

    all_categories = sorted(list(set([cr.category for cr in categories_rules])))
    default_categories = [c for c in all_categories if c != "own-transfer"]

    container = st.container()
    all = st.checkbox("Select all", value=True)

    if all:
        categories = container.multiselect(
            "Select one or more categories:", all_categories, default_categories
        )
    else:
        categories = container.multiselect(
            "Select one or more categories:", all_categories
        )

    n_biggest_groups = st.slider(
        "Number of groups", min_value=1, max_value=50, value=7, step=1
    )

    raw_transactions_df = read_raw_transactions()
    logging.info("adding columns")
    transactions_df = _add_columns(raw_transactions_df, categories_rules)

    logging.info("filtering transactions for date range")
    transactions_df = filter_transactions_date_range(
        transactions_df, start_date, end_date
    )
    transactions_df = transactions_df[transactions_df["category"].isin(categories)]

    biggest_groups_values = get_significant_group_values(
        transactions_df, group_by_col, n_biggest_groups=n_biggest_groups
    )
    transactions_df["group_value"] = transactions_df[group_by_col].map(
        lambda group: group if group in biggest_groups_values else "other"
    )

    _df_expense = get_time_aggregated_expenses_df(
        transactions_df[transactions_df["type"] == "outcome"],
        frequency=frequency,
    )

    _df_income = get_time_aggregated_expenses_df(
        transactions_df[transactions_df["type"] == "income"],
        frequency=frequency,
    )

    barplot_tab, transactions_table_tab = st.tabs(["Bars", "Transactions"])

    # plot income and outcome
    with barplot_tab:
        col1, col2 = st.columns([1, 1])
        with col1:
            view_income = st.toggle("Show income", value=True)
        with col2:
            view_expense = st.toggle("Show expense", value=True)

        fig = get_barplot(
            _df_income, _df_expense, view_income=view_income, view_expense=view_expense
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(_df_expense.transpose())

    # table
    with transactions_table_tab:
        st.dataframe(transactions_df)
