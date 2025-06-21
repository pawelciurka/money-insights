from dataclasses import dataclass

import pandas as pd
import numpy as np

from project.enums import TransactionColumn, TransactionType


@dataclass
class FrequencyConfig:
    tag: str  # e.g. 1D, see: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
    display_name: str  # e.g. : Day
    value_format: str
    label: str  # 'right' or 'left'
    tree_supported: bool


FREQUENCIES = [
    FrequencyConfig("1D", "Day", "%B %d", "left", True),
    FrequencyConfig("1ME", "Month", "%B %Y", "right", True),
    FrequencyConfig("1Y", "Year", "%Y", "right", True),
    FrequencyConfig("5Y", "5 Years", "%Y", "right", False),
    FrequencyConfig("10Y", "10 Years", "%Y", "right", False),
]


def get_time_aggregated_transactions_df(
    input_df: pd.DataFrame,
    frequency: FrequencyConfig,
) -> pd.DataFrame:

    groupers = []
    groupers.append(pd.Grouper(key="group_value"))
    groupers.append(
        pd.Grouper(
            key=TransactionColumn.TRANSACTION_DATE,
            freq=frequency.tag,
            label=frequency.label,
        )
    )

    # group by time and aggregate
    out_df = (
        input_df.groupby(groupers, group_keys=True)[TransactionColumn.AMOUNT_ABS]
        .apply(np.sum)
        .reset_index()
        .pivot(
            index=TransactionColumn.TRANSACTION_DATE,
            columns="group_value",
            values=TransactionColumn.AMOUNT_ABS,
        )
        .fillna(0.0)
    )

    out_df.index = out_df.index.map(lambda x: x.strftime(frequency.value_format))

    return out_df


def get_time_aggregated_summarized_delta_df(
    income_df: pd.DataFrame, expense_df: pd.DataFrame
) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            TransactionType.INCOME: income_df.apply(sum, axis=1),
            TransactionType.OUTCOME: expense_df.apply(sum, axis=1),
        }
    ).fillna(0.0)
    df[TransactionColumn.DELTA] = (
        df[TransactionType.INCOME] - df[TransactionType.OUTCOME]
    )
    return df


def get_significant_group_values(
    transactions_df: pd.DataFrame, group_by_col: str, n_biggest_groups: int
) -> set:
    biggest_groups_names = (
        transactions_df.groupby(group_by_col)[TransactionColumn.AMOUNT_ABS]
        .sum()
        .sort_values(ascending=False)[:n_biggest_groups]
    )
    return {g for g, _ in biggest_groups_names.items()}


def get_file_path_aggregated_df(transactions_df: pd.DataFrame) -> pd.DataFrame:
    return (
        transactions_df.groupby(TransactionColumn.SOURCE_FILE_PATH)
        .apply(
            lambda _df: pd.Series(
                {
                    TransactionColumn.SOURCE_TYPE: set(
                        _df[TransactionColumn.SOURCE_TYPE]
                    ),
                    TransactionColumn.N_TRANSACTIONS: len(_df),
                    TransactionColumn.MIN_DATE: min(
                        _df[TransactionColumn.TRANSACTION_DATE_ISOSTR]
                    ),
                    TransactionColumn.MAX_DATE: max(
                        _df[TransactionColumn.TRANSACTION_DATE_ISOSTR]
                    ),
                }
            )
        )
        .sort_values(TransactionColumn.MAX_DATE, ascending=False)
    )
