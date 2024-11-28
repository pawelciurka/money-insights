import streamlit as st
from project import app_data
from project.utils import get_emoji
from project.dates_utils import get_past_month_start_datetime
from project.metrics import get_metrics


metrics = get_metrics(app_data.not_own_transactions_df)

for metric in metrics:
    st.metric(
        label=metric.name,
        value=metric.value,
        delta=metric.delta,
        delta_color="inverse" if metric.delta_inverse else "normal",
    )
