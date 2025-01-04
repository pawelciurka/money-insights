import logging
import streamlit as st
from project.utils import get_emoji
from project.app_data import read_fresh_data

st.set_page_config(
    layout="wide", page_icon=get_emoji("favicon"), page_title="MI | Transactions"
)
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s %(name)s :: %(levelname)s :: %(message)s'
)


st.title("Welcome to the Dashboard! 📊")
st.subheader("Overview of Features and Capabilities")

st.write(
    """
    This dashboard provides insightful visualizations and summaries to help you understand the data better. 
    Here's what you can explore:
    - **Transactions**: A detailed visualization showcasing data distribution and trends.
    - **Last Month Summary**: A concise summary of key metrics and highlights from the previous month.
    
    Navigate through the sections using the sidebar to explore each feature in detail.
    """
)

# Optional: Add a placeholder for future updates
st.info("More features are coming soon! Stay tuned.")

read_fresh_data()
