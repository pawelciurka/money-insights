import logging
import streamlit as st
from project.utils import get_emoji

st.set_page_config(
    layout="wide", page_icon=get_emoji("favicon"), page_title="MI | Transactions"
)
logging.basicConfig(level=logging.INFO)
import project.app_data
