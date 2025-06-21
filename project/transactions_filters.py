import pandas as pd
import logging
import streamlit as st
from datetime import datetime
from project.enums import TransactionColumn

log = logging.getLogger(__name__)


@st.cache_data
def filter_transactions(
    transactions_df: pd.DataFrame,
    start_datetime: datetime | None = None,
    end_datetime: datetime | None = None,
    exact_year_and_month: tuple[int, int] | None = None,
    categories: list[str] | None = None,
    types: list[str] | None = None,
) -> pd.DataFrame:
    transactions_mask = pd.Series(True, index=transactions_df.index)
    if start_datetime:
        transactions_mask = transactions_mask & (
            transactions_df[TransactionColumn.TRANSACTION_DATE] >= start_datetime
        )
    if end_datetime:
        transactions_mask = transactions_mask & (
            transactions_df[TransactionColumn.TRANSACTION_DATE] <= end_datetime
        )
    if exact_year_and_month:
        year, month = exact_year_and_month
        transactions_mask = transactions_mask & (
            transactions_df[TransactionColumn.TRANSACTION_DATE].map(
                lambda d: d.year == year and d.month == month
            )
        )
    if categories:
        transactions_mask = transactions_mask & (
            transactions_df[TransactionColumn.CATEGORY].isin(categories)
        )
    if types:
        transactions_mask = transactions_mask & (transactions_df["type"].isin(types))

    log.info(
        f"{sum(transactions_mask)} transactions after filtering, before: {(len(transactions_df))} "
        f"(start_datetime: {start_datetime}, "
        f"end_datetime: {end_datetime}, "
        f"exact_year_and_month: {exact_year_and_month}, "
        f"categories: {categories}, "
        f"types: {types})"
    )

    return transactions_df[transactions_mask].copy()


def filter_transactions_date_range(
    transactions_df: pd.DataFrame,
    start_datetime: datetime,
    end_datetime: datetime,
):
    return filter_transactions(
        transactions_df=transactions_df,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )
