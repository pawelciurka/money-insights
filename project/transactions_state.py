import pandas as pd

from project.transactions_aggregation import get_significant_group_values
from project.transactions_filters import filter_transactions_date_range
from project.utils import get_emoji


def get_state_transactions_df(
    all_transactions_df: pd.DataFrame,
    categories: list[str],
    start_date,
    end_date,
    group_by_col: str,
    n_biggest_groups: int,
) -> pd.DataFrame:

    # filter by date range
    state_transactions_df = filter_transactions_date_range(
        all_transactions_df, start_date, end_date
    )
    # filter by category
    state_transactions_df = state_transactions_df[
        all_transactions_df["category"].isin(categories)
    ]

    # set group_value column for N biggest groups
    biggest_groups_values = get_significant_group_values(
        transactions_df=state_transactions_df,
        group_by_col=group_by_col,
        n_biggest_groups=n_biggest_groups,
    )
    state_transactions_df["group_value"] = state_transactions_df[group_by_col].map(
        lambda group: group if group in biggest_groups_values else "other"
    )

    state_transactions_df["display_category"] = state_transactions_df["category"].map(
        lambda c: f"{c}{get_emoji(c)}"
    )
    state_transactions_df["display_type"] = state_transactions_df["type"].map(
        lambda t: f"{t}{get_emoji(t)}"
    )

    return state_transactions_df
