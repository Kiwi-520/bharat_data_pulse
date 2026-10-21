
import streamlit as st
from datetime import date

from analytics.queries import (
    get_price_trend,
    get_price_band,
    get_volatility,
    get_month_over_month,
    get_market_summary,
    get_commodity_summary,
    get_latest_data_date,
    get_min_data_date,
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================
st.set_page_config(
    page_title="Bharat Data Pulse — Market Overview",
    page_icon="🌾",
    layout="wide",
)


# ==================================================
# PAGE HEADER
# ==================================================
st.title("🌾 Bharat Data Pulse — Market Overview")
st.caption("Market trends, price ranges, volatility and monthly changes")


# ==================================================
# FETCH FILTER OPTIONS
# ==================================================
markets_data = get_market_summary() or []
commodities_data = get_commodity_summary() or []

markets_list = sorted({
    item["market"]
    for item in markets_data
    if item.get("market")
})

commodities_list = sorted({
    item["commodity"]
    for item in commodities_data
    if item.get("commodity")
})
latest = get_latest_data_date()
min_date = get_min_data_date()

if not markets_list or not commodities_list:
    st.warning(
        "Market or commodity options could not be loaded. "
        "Please check the database connection and summary queries."
    )
    st.stop()


# ==================================================
# FILTERS
# ==================================================
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    selected_commodity = st.selectbox(
        "Select Commodity",
        options=commodities_list,
        index=0,
        key="decision_commodity",
    )

with filter_col2:
    markets_list = get_market_list(selected_commodity)
    choice_market = st.selectbox(
        "Pick a market",
        markets_list,
        key="history_market"
    )

with filter_col3:
    start_date = st.date_input(
        "Start Date",
        value=min_date,
        key="decision_start_date",
    )

with filter_col4:
    end_date = st.date_input(
        "End Date",
        value=latest,
        key="decision_end_date",
    )


st.divider()


# ==================================================
# DISPLAY HELPERS
# ==================================================
def display_result(value):
    """Display a query result without failing on missing values."""

    if value is None:
        st.info("No data available for the selected filters.")
    elif isinstance(value, (dict, list, tuple)) and not value:
        st.info("No data available for the selected filters.")
    else:
        st.write(value)


def display_month_value(value):
    """Display a month average without assuming it is a valid number."""

    if value is None or value == "":
        st.write("N/A")
    else:
        st.write(value)


# ==================================================
# VALIDATE DATES AND LOAD DECISIONS
# ==================================================
if start_date > end_date:
    st.warning("Start Date must be before or equal to End Date.")

else:
    try:
        trend = get_price_trend(
            selected_commodity,
            selected_market,
            start_date,
            end_date,
        )

        band = get_price_band(
            selected_commodity,
            selected_market,
        )

        volatility = get_volatility(
            selected_commodity,
            selected_market,
            start_date,
            end_date,
        )

        mom = get_month_over_month(
            selected_commodity,
            selected_market,
        ) or {}

        if not isinstance(mom, dict):
            mom = {}

    except Exception as exc:
        st.error("Unable to load the decision cards.")
        st.exception(exc)
        st.stop()

    # --------------------------------------------------
    # METRIC CARDS
    # --------------------------------------------------
    st.subheader("Market Decision Cards")

    col1, col2, col3, col4 = st.columns(4, gap="medium")

    with col1:
        with st.container(border=True):
            st.subheader("Price Trend")
            display_result(trend)

    with col2:
        with st.container(border=True):
            st.subheader("Price Band")
            display_result(band)

    with col3:
        with st.container(border=True):
            st.subheader("Price Volatility")
            display_result(volatility)

    with col4:
        with st.container(border=True):
            st.subheader("Month-over-Month Change")

            st.caption("Current month average")
            display_month_value(
                mom.get("current_month_avg")
            )

            st.divider()

            st.caption("Previous month average")
            display_month_value(
                mom.get("previous_month_avg")
            )


# ==================================================
# FOOTER
# ==================================================
st.divider()
st.caption("Bharat Data Pulse | Mandi Market Intelligence")
