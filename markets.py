import streamlit as st
import pandas as pd
from analytics.queries import get_market_summary
from datetime import datetime, date

st.set_page_config(
    page_title="Bharat Data Pulse - Markets",
    layout="wide"
)

data = get_market_summary()
# # print(data)
markets_list = [x['market'] for x in data]

st.title("Bharat Data Pulse - Markets")

# # Subtitle
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    with st.container(border=True):
        st.markdown("Total Markets")
        st.markdown(f"**{len(data)}**")
st.write("List of all markets available...")


cols = st.columns(5)

for i, item in enumerate(data):

    with cols[i % 5]:
        with st.container(border=True):

            st.markdown(f"**{item['market']}**")

            st.caption(
                    f"""
                    Location: {item['state']} - {item['district']} |
                    Commodities: {item['commodity_count']} |
                    Price records: ₹ {item['record_count']}
                    """
            )