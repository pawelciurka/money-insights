import pandas as pd
import logging

log = logging.getLogger(__name__)


def filter_transactions_date_range(
    df: pd.DataFrame,
    start_datetime,
    end_datetime,
):
    log.info("filtering transactions for date range")
    transactions_mask = (df["transaction_date"] >= start_datetime) & (
        df["transaction_date"] <= end_datetime
    )
    filtered_df = df[transactions_mask].copy()
    log.info(f"{len(filtered_df)} transactions after filtering by date range")

    return filtered_df


def filter_transactions_categories(df: pd.DataFrame, categories: list[str]):
    return df[df["category"].isin(categories)]
