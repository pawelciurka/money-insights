from dataclasses import dataclass
import pandas as pd

from project.transactions_filters import filter_transactions
from project.enums import TransactionColumn
from project.dates_utils import get_past_month_start_datetime
import streamlit as st


@dataclass(frozen=False)
class Metric:
    name: str
    value: int | str | float | None
    delta: int | str | float | None
    delta_inverse: bool | None

    def __post_init__(self):
        if isinstance(self.value, float):
            self.value = round(self.value, 2)
        if isinstance(self.delta, float):
            self.delta = round(self.delta, 2)


@st.cache_data
def _get_month_transactions_df(
    transactions_df: pd.DataFrame,
    year_and_month: tuple[int, int],
    type: str,
    category: str | None = None,
) -> pd.DataFrame:
    return filter_transactions(
        transactions_df=transactions_df,
        exact_year_and_month=year_and_month,
        categories=[category] if category else None,
        types=[type],
    )


def _compute_total_monthly_amount_abs(
    transactions_df: pd.DataFrame,
    year_and_month: tuple[int, int],
    type: str,
    category: str | None = None,
):
    month_transactions_df = _get_month_transactions_df(
        transactions_df=transactions_df,
        year_and_month=year_and_month,
        type=type,
        category=category,
    )
    return month_transactions_df["amount_abs"].sum()


def _compute_total_monthly_n_transactions(
    transactions_df: pd.DataFrame,
    year_and_month: tuple[int, int],
    type: str,
    category: str | None = None,
):
    month_transactions_df = _get_month_transactions_df(
        transactions_df=transactions_df,
        year_and_month=year_and_month,
        type=type,
        category=category,
    )
    return len(month_transactions_df)


def compute_total_monthly_income(
    transactions_df: pd.DataFrame, year_and_month: tuple[int, int]
):
    return _compute_total_monthly_amount_abs(
        transactions_df=transactions_df, year_and_month=year_and_month, type='income'
    )


def compute_total_monthly_expense(
    transactions_df: pd.DataFrame, year_and_month: tuple[int, int]
):
    return _compute_total_monthly_amount_abs(
        transactions_df=transactions_df, year_and_month=year_and_month, type='outcome'
    )


def compute_total_monthly_savings(
    transactions_df: pd.DataFrame, year_and_month: tuple[int, int]
):
    return compute_total_monthly_income(
        transactions_df, year_and_month
    ) - compute_total_monthly_expense(transactions_df, year_and_month)


def compute_total_monthly_n_income_transactions(
    transactions_df: pd.DataFrame, year_and_month: tuple[int, int]
):
    return _compute_total_monthly_n_transactions(
        transactions_df=transactions_df, year_and_month=year_and_month, type='income'
    )


def compute_total_monthly_n_expense_transactions(
    transactions_df: pd.DataFrame, year_and_month: tuple[int, int], category=None
):
    return _compute_total_monthly_n_transactions(
        transactions_df=transactions_df,
        year_and_month=year_and_month,
        type='outcome',
        category=category,
    )


def get_day_of_last_transaction(
    transactions_df: pd.DataFrame, year_and_month: tuple[int, int]
):
    month_transaction_df = _get_month_transactions_df(
        transactions_df=transactions_df,
        year_and_month=year_and_month,
        type='outcome',
    )
    return (
        month_transaction_df[TransactionColumn.TRANSACTION_DATE].sort_values().iloc[-1]
    ).day


def get_metric(
    transactions_df: pd.DataFrame,
    year_and_month: tuple[int, int],
    reference_year_and_month: tuple[int, int],
    func: callable,
    delta_inverse: bool,
    name: str,
    **func_args,
) -> Metric:
    pass

    value = func(transactions_df, year_and_month, **func_args)
    reference_value = func(transactions_df, reference_year_and_month, **func_args)

    return Metric(
        name=name,
        value=value,
        delta=value - reference_value,
        delta_inverse=delta_inverse,
    )


def get_metrics(transactions_df: pd.DataFrame, n_months_back: int) -> list[Metric]:
    last_month_datetime = get_past_month_start_datetime(n_months_back=n_months_back)
    second_to_last_month_datetime = get_past_month_start_datetime(
        n_months_back=n_months_back + 1
    )
    last_month_year_and_month = (last_month_datetime.year, last_month_datetime.month)
    second_to_last_month_year_and_month = (
        second_to_last_month_datetime.year,
        second_to_last_month_datetime.month,
    )

    last_month_n_unrecognized_expense_transactions = (
        compute_total_monthly_n_expense_transactions(
            transactions_df=transactions_df,
            year_and_month=last_month_year_and_month,
            category='unrecognized',
        )
    )

    metrics = [
        get_metric(
            transactions_df=transactions_df,
            year_and_month=last_month_year_and_month,
            reference_year_and_month=second_to_last_month_year_and_month,
            func=compute_total_monthly_income,
            delta_inverse=False,
            name=f"{last_month_datetime.strftime('%B %Y')} total income",
        ),
        get_metric(
            transactions_df=transactions_df,
            year_and_month=last_month_year_and_month,
            reference_year_and_month=second_to_last_month_year_and_month,
            func=compute_total_monthly_expense,
            delta_inverse=True,
            name=f"{last_month_datetime.strftime('%B %Y')} total expenses",
        ),
        get_metric(
            transactions_df=transactions_df,
            year_and_month=last_month_year_and_month,
            reference_year_and_month=second_to_last_month_year_and_month,
            func=compute_total_monthly_savings,
            delta_inverse=False,
            name=f"{last_month_datetime.strftime('%B %Y')} total savings",
        ),
        get_metric(
            transactions_df=transactions_df,
            year_and_month=last_month_year_and_month,
            reference_year_and_month=second_to_last_month_year_and_month,
            func=compute_total_monthly_n_expense_transactions,
            delta_inverse=True,
            name=f"{last_month_datetime.strftime('%B %Y')} number of transactions",
        ),
        Metric(
            name=f"{last_month_datetime.strftime('%B %Y')} not recognized expense transactions",
            value=last_month_n_unrecognized_expense_transactions,
            delta=None,
            delta_inverse=None,
        ),
        Metric(
            name=f"{last_month_datetime.strftime('%B %Y')} day of last recorded transaction",
            value=get_day_of_last_transaction(
                transactions_df=transactions_df,
                year_and_month=last_month_year_and_month,
            ),
            delta=None,
            delta_inverse=None,
        ),
    ]

    return metrics
