import streamlit as st
import pandas as pd
from analytics.queries import get_commodity_summary
from datetime import datetime, date

st.set_page_config(
    page_title="Bharat Data Pulse - Commodities",
    layout="wide"
)

data = get_commodity_summary()
# # print(data)
commodities_list = [x['commodity'] for x in data]

st.title("Bharat Data Pulse- Commodities")

st.write(f"List of all {len(data)} commodities available...")
choice = st.selectbox("Pick a commodity", commodities_list)
choosen_price = [x['latest_modal_price'] for x in data if x['commodity'] == choice]
st.write(f"{choice} price: ₹{choosen_price[0]}")
# print(pd.DataFrame(list(data.items())))
st.dataframe(pd.DataFrame(data))
