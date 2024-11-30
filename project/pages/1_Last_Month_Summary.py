import streamlit as st
from project import app_data
from project.utils import get_emoji
from project.dates_utils import get_past_month_start_datetime
from project.metrics import get_metrics


n_months_back = st.pills(
    "Month",
    [0, 1, 2],
    format_func=lambda i: {0: 'this month', 1: "last month", 2: '2 months ago'}[i],
    default=1,
    label_visibility='collapsed',
)
metrics = get_metrics(app_data.not_own_transactions_df, n_months_back=n_months_back)

for metric in metrics:
    st.metric(
        label=metric.name,
        value=metric.value,
        delta=metric.delta,
        delta_color="inverse" if metric.delta_inverse else "normal",
    )
