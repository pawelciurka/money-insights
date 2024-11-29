from dataclasses import dataclass

import pandas as pd
import numpy as np


@dataclass
class FrequencyConfig:
    tag: str  # e.g. 1D, see: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
    display_name: str  # e.g. : Day
    value_format: str
    label: str  # 'right' or 'left'


FREQUENCIES = [
    FrequencyConfig("1D", "Day", "%B %d", "left"),
    FrequencyConfig("1ME", "Month", "%B %YE", "right"),
    FrequencyConfig("1Y", "Year", "%YE", "right"),
    FrequencyConfig("5Y", "5 Years", "%YE", "right"),
    FrequencyConfig("10Y", "10 Years", "%YE", "right"),
]


def get_time_aggregated_transactions_df(
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
        input_df.groupby(groupers, group_keys=True)["amount_abs"]
        .apply(np.sum)
        .reset_index()
        .pivot(index="transaction_date", columns="group_value", values="amount_abs")
        .fillna(0.0)
    )

    out_df.index = out_df.index.map(lambda x: x.strftime(frequency.value_format))

    return out_df


def get_time_aggregated_summarized_delta_df(
    income_df: pd.DataFrame, expense_df: pd.DataFrame
) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            'income': income_df.apply(sum, axis=1),
            'expense': expense_df.apply(sum, axis=1),
        }
    ).fillna(0.0)
    df['delta'] = df['income'] - df['expense']
    return df


def get_significant_group_values(
    transactions_df: pd.DataFrame, group_by_col: str, n_biggest_groups: int
) -> set:
    biggest_groups_names = (
        transactions_df.groupby(group_by_col)["amount_abs"]
        .sum()
        .sort_values(ascending=False)[:n_biggest_groups]
    )
    return {g for g, _ in biggest_groups_names.items()}
