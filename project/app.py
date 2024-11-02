import streamlit as st
from project.app_data import all_transactions_df
from project.utils import get_emoji

st.set_page_config(
    layout="wide", page_icon=get_emoji("favicon"), page_title="MI | Main"
)
