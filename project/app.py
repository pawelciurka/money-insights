from datetime import datetime
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


class TimeInterval(Enum):
    DAY = 1
    MONTH = 2
    YEAR = 3


@st.cache
def read_raw_transactions() -> pd.DataFrame:
    df = parse_directory_as_df(TRANSACTIONS_FILES_DIR)
    return df


def get_time_aggregated_expenses_df(
    input_df: pd.DataFrame,
    frequency=None,
) -> pd.DataFrame:

    groupers = []
    groupers.append(pd.Grouper(key="group_value"))
    groupers.append(pd.Grouper(key="transaction_date", freq=frequency, label="left"))

    # group by time and aggregate
    out_df = (
        input_df.groupby(groupers)["amount_abs"]
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


def get_barplot_2(
    df_income: pd.DataFrame,
    df_outcome: pd.DataFrame,
    view_income=True,
    view_outcome=True,
):
    fig = go.Figure(
        layout=go.Layout(
            height=1600,
            width=1000,
            barmode="relative",
            yaxis_showticklabels=False,
            yaxis_showgrid=False,
            # yaxis_range=[0, df.groupby(axis=1, level=0).sum().max().max() * 1.5],
            # Secondary y-axis overlayed on the primary one and not visible
            yaxis2=go.layout.YAxis(
                visible=False,
                matches="y",
                overlaying="y",
                anchor="x",
            ),
            font=dict(size=12),
            legend_x=0,
            legend_y=1,
            legend_orientation="h",
            hovermode="x",
            margin=dict(b=0, t=10, l=0, r=10),
        )
    )

    # Add the traces
    for col in df_income.columns:
        if (df_income[col] == 0).all():
            continue
        fig.add_bar(
            x=df_income.index,
            y=df_income[col],
            # Set the right yaxis depending on the selected product (from enumerate)
            yaxis=f"y1",
            # Offset the bar trace, offset needs to match the width
            # The values here are in milliseconds, 1billion ms is ~1/3 month
            offsetgroup="1",
            offset=0,
            width=1000000000,
            legendgroup="income",
            legendgrouptitle_text="income",
            name=col,
            # marker_color=colors[t][col],
            marker_line=dict(width=2, color="#333"),
            # hovertemplate="%{y}<extra></extra>"
        )

        # Add the traces
    for col in df_outcome.columns:
        if (df_outcome[col] == 0).all():
            continue
        fig.add_bar(
            x=df_outcome.index,
            y=df_outcome[col],
            # Set the right yaxis depending on the selected product (from enumerate)
            yaxis=f"y2",
            # Offset the bar trace, offset needs to match the width
            # The values here are in milliseconds, 1billion ms is ~1/3 month
            offsetgroup="2",
            offset=1000000000,
            width=1000000000,
            legendgroup="outcome",
            legendgrouptitle_text="outcome",
            name=col,
            # marker_color=colors[t][col],
            marker_line=dict(width=2, color="#333"),
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


@st.cache
def _add_columns(raw_transactions_df, categories_rules):
    return add_columns(raw_transactions_df, categories_rules)


with expenses:
    st.title("Expense visualization")

    frequency = st.selectbox(
        "Frequency",
        ("1D", "1M", "1Y", "5Y", "10Y", "20Y"),
        format_func=lambda x: {
            "1D": "Day",
            "1M": "Month",
            "1Y": "Year",
            "5Y": "5 Years",
            "10Y": "10 Years",
            "20Y": "20 Years",
        }.get(x),
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

    categories_rules = read_categories_rules(CATEGORIES_RULES_FILE_PATH)

    all_categories = sorted(list(set([cr.category for cr in categories_rules])))
    default_categories = [c for c in all_categories if c != "own-transfer"]

    categories = st.multiselect(
        "Categories", all_categories, default=default_categories
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

    _df_outcome = get_time_aggregated_expenses_df(
        transactions_df[transactions_df["type"] == "outcome"],
        frequency=frequency,
    )

    _df_income = get_time_aggregated_expenses_df(
        transactions_df[transactions_df["type"] == "income"],
        frequency=frequency,
    )

    # # plot outcome
    # fig = get_barplot(_df_outcome)
    # st.plotly_chart(fig, use_container_width=True)

    # # plot income
    # fig = get_barplot(_df_income)
    # st.plotly_chart(fig, use_container_width=True)

    # plot income and outcome
    fig = get_barplot_2(_df_income, _df_outcome, view_income=True, view_outcome=True)
    st.plotly_chart(fig, use_container_width=True)

    # table
    st.dataframe(_df_outcome.transpose())

    # transactions_table
    st.title("Transactions")
    with st.expander("Open to see transactions table"):
        st.dataframe(transactions_df)
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
                transactions_df.to_csv(f, index=False, line_terminator="\n")
                st.write(f"Saved in {f.name}")
