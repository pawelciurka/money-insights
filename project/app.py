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


# @st.cache
def get_expenses_df():
    input_df = read_input_df()
    return input_df[input_df["type"] == "outcome"].copy()


input_df = read_input_df()


def get_time_aggregated_df(
    input_df, time_interval=None, date_range=None, group_by=None, filters=None
) -> pd.DataFrame:
    agg_expenses_in_time = input_df.groupby(
        pd.Grouper(key="transaction_date", freq="1D")
    ).apply(lambda sub_df: pd.Series({"all": sum(sub_df["amount_abs"])}))

    return agg_expenses_in_time


def get_expenses_barplot(
    input_df, time_interval=None, date_range=None, group_by=None, filters=None
):
    expenses_df = get_expenses_df()

    agg_expenses_in_time = get_time_aggregated_df(expenses_df)

    layout = go.Layout(barmode="stack")
    data = []
    for name, trace in agg_expenses_in_time.iteritems():
        data.append(go.Bar(x=trace.index, y=list(trace), name=name))

    fig = go.Figure(data=data, layout=layout)

    return fig


expenses = st.container()


with expenses:
    st.title("Expense visualization")
    fig = get_expenses_barplot(input_df, "day")
    st.plotly_chart(fig, use_container_width=True)

    st.title("debug")
