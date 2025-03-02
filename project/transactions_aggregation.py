from dataclasses import dataclass

import pandas as pd
import numpy as np

from project.transactions_read import TRANSACTION_COLUMNS


@dataclass
class FrequencyConfig:
    tag: str  # e.g. 1D, see: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
    display_name: str  # e.g. : Day
    value_format: str
    label: str  # 'right' or 'left'


FREQUENCIES = [
    FrequencyConfig("1D", "Day", "%B %d", "left"),
    FrequencyConfig("1ME", "Month", "%B %Y", "right"),
    FrequencyConfig("1Y", "Year", "%Y", "right"),
    FrequencyConfig("5Y", "5 Years", "%Y", "right"),
    FrequencyConfig("10Y", "10 Years", "%Y", "right"),
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


def get_file_path_aggregated_df(transactions_df: pd.DataFrame) -> pd.DataFrame:
    return (
        transactions_df.groupby(TRANSACTION_COLUMNS.SOURCE_FILE_PATH)
        .apply(
            lambda _df: pd.Series(
                {
                    "source_type": set(_df[TRANSACTION_COLUMNS.SOURCE_TYPE]),
                    'n_transactions': len(_df),
                    'min_date': min(_df['transaction_date_isostr']),
                    'max_date': max(_df['transaction_date_isostr']),
                }
            )
        )
        .sort_values("max_date", ascending=False)
    )
