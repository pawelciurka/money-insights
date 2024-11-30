import logging
import streamlit as st
from project.utils import get_emoji

st.set_page_config(
    layout="wide", page_icon=get_emoji("favicon"), page_title="MI | Transactions"
)
logging.basicConfig(level=logging.INFO)


# Add a title and subtitle
st.title("Welcome to the Dashboard! 📊")
st.subheader("Overview of Features and Capabilities")

# Add a description
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
import project.app_data
