from datetime import datetime
from turtle import width
import streamlit as st
import pandas as pd
from project.parsers import parse_directory_as_df
from project.settings import ROOT_INPUT_FILES_DIR
import plotly.graph_objs as go
from enum import Enum

st.set_page_config(layout="wide")


class TimeInterval(Enum):
    DAY = 1
    MONTH = 2
    YEAR = 3


# @st.cache
def read_input_df():
    return parse_directory_as_df(ROOT_INPUT_FILES_DIR)


def get_time_aggregated_expenses_df(
    input_df,
    frequency=None,
    start_date=None,
    end_date=None,
    group_by_col=None,
    n_biggest_groups=10,
    filters=None,
):

    # filter
    input_df = input_df[input_df["type"] == "outcome"].copy()
    if start_date and end_date:
        input_df = input_df[
            (input_df["transaction_date"] >= start_date)
            & (input_df["transaction_date"] <= end_date)
        ]

    group_names = (
        input_df.groupby(group_by_col)["amount_abs"]
        .sum()
        .sort_values(ascending=False)[:n_biggest_groups]
    )
    group_map = {g: g for g, _ in group_names.iteritems()}

    input_df["group_value"] = input_df[group_by_col].map(
        lambda x: group_map.get(x, "other")
    )
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
    )
    return out_df


def get_barplot(df):
    layout = go.Layout(barmode="stack")
    data = []
    for name, trace in df.iteritems():
        data.append(go.Bar(x=trace.index, y=list(trace), name=name))

    fig = go.Figure(data=data, layout=layout)

    return fig


expenses = st.container()
debug = st.container()


def date_to_datetime(date):
    return datetime(date.year, date.month, date.day)


with expenses:
    st.title("Expense visualization")

    # inputs
    frequency = st.selectbox(
        "Frequency",
        ("1D", "1M", "1Y"),
        format_func=lambda x: {"1D": "Day", "1M": "Month", "1Y": "Year"}.get(x),
        index=1,
    )
    group_by_col = st.selectbox(
        "Group by",
        ("one_group", "contractor", "account_name"),
        index=0,
        format_func=lambda x: {"one_group": "None"}.get(x, x),
    )
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Start", value=datetime(datetime.now().year, 1, 1))
    with c2:
        end_date = st.date_input("End Date")

    # plot-ready data retrieval
    input_df = read_input_df()
    _df = get_time_aggregated_expenses_df(
        input_df,
        frequency=frequency,
        group_by_col=group_by_col,
        start_date=date_to_datetime(start_date),
        end_date=date_to_datetime(end_date),
    )

    # plot
    fig = get_barplot(_df)
    st.plotly_chart(fig, use_container_width=True)

    # table
    st.write(_df.transpose())

with debug:
    st.title("debug")
    st.write(read_input_df())
