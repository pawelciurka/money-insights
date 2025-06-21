import pandas as pd

from project.transactions_aggregation import get_significant_group_values
from project.transactions_filters import filter_transactions_date_range
from project.utils import get_emoji
from project.enums import TransactionColumn


def get_state_transactions_df(
    all_transactions_df: pd.DataFrame,
    categories: list[str],
    start_date,
    end_date,
    group_by_col: str,
    n_biggest_groups: int,
    order_by_command: str | None = None,
) -> pd.DataFrame:

    # filter by date range
    state_transactions_df = filter_transactions_date_range(
        all_transactions_df, start_date, end_date
    )
    # filter by category
    state_transactions_df = state_transactions_df[
        state_transactions_df[TransactionColumn.CATEGORY].isin(categories)
    ]

    # set group_value column for N biggest groups
    biggest_groups_values = get_significant_group_values(
        transactions_df=state_transactions_df,
        group_by_col=group_by_col,
        n_biggest_groups=n_biggest_groups,
    )
    state_transactions_df[TransactionColumn.GROUP_VALUE] = state_transactions_df[
        group_by_col
    ].map(lambda group: group if group in biggest_groups_values else "other")

    if order_by_command:
        order_by_col = order_by_command.split(':')[0]
        ascending = {'ascending': True, 'descending': False}[
            order_by_command.split(':')[1]
        ]
        state_transactions_df = state_transactions_df.sort_values(
            by=order_by_col, ascending=ascending
        )

    state_transactions_df[TransactionColumn.DISPLAY_CATEGORY] = state_transactions_df[
        TransactionColumn.CATEGORY
    ].map(lambda c: f"{get_emoji(c)}{c}")
    state_transactions_df[TransactionColumn.DISPLAY_TYPE] = state_transactions_df[
        TransactionColumn.TYPE
    ].map(lambda t: f"{t}{get_emoji(t)}")

    return state_transactions_df
