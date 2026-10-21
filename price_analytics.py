
import streamlit as st
import plotly.express as px
import pandas as pd

from analytics.queries import (
    compare_markets,
    get_market_summary,
    get_commodity_summary,
    get_price_history,
    get_latest_data_date,
    get_min_data_date,
)
from datetime import date


st.set_page_config(
    page_title="Bharat Data Pulse - Price Analytics",
    layout="wide"
)

st.title("Bharat Data Pulse - Price History Analytics")

# Fetch dropdown options
data_commodity = get_commodity_summary()
commodities_list = [x["commodity"] for x in data_commodity]
latest = get_latest_data_date()

data_markets = get_market_summary()
markets_list = [x["market"] for x in data_markets]


# OUTER LAYOUT: left graph = 4 parts, right graph = 3 parts
left_panel, right_panel = st.columns([4, 3])

with left_panel:

    st.subheader("Price History")

    # Four filter columns
    commodity_col, market_col, start_col, end_col = st.columns(4)

    with commodity_col:
        choice_commodity = st.selectbox(
            "Pick a commodity",
            commodities_list,
            key="history_commodity"
        )

    with market_col:
        choice_market = st.selectbox(
            "Pick a market",
            markets_list,
            key="history_market"
        )

    with start_col:
        start_date = st.date_input(
            "Start date",
            value=min_date,
            key="history_start_date"
        )

    with end_col:
        end_date = st.date_input(
            "End date",
            value=latest,
            key="history_end_date"
        )

    if start_date > end_date:
        st.warning("Start date must be before or equal to end date.")

    else:
        data_history = get_price_history(
            choice_commodity,
            choice_market,
            start_date,
            end_date
        )

        df_history = (
            pd.DataFrame(data_history)
            if data_history
            else pd.DataFrame()
        )

        if not df_history.empty:
            df_history["date"] = pd.to_datetime(df_history["date"])

            fig_line = px.line(
                df_history,
                x="date",
                y="price",
                title=f"{choice_commodity} Price Trend — {choice_market}",
                markers=True,
                labels={
                    "date": "Date",
                    "price": "Modal Price (₹)"
                }
            )

            st.plotly_chart(
                fig_line,
                use_container_width=True
            )

        else:
            st.info("No sufficient price data found for the selected filters.")

with right_panel:

    st.subheader("Market Price Comparison")

    bar_commodity_col, bar_start_col, bar_end_col = st.columns(3)

    with bar_commodity_col:
        choice_commodity_bar = st.selectbox(
            "Pick a commodity",
            commodities_list,
            key="comparison_commodity"
        )

    with bar_start_col:
        start_date_bar = st.date_input(
            "Start date",
            value=date(2024, 1, 1),
            key="comparison_start_date"
        )

    with bar_end_col:
        end_date_bar = st.date_input(
            "End date",
            value=date.today(),
            key="comparison_end_date"
        )

    # Select specific markets
    selected_markets = st.multiselect(
        "Select markets to compare",
        options=markets_list,
        default=markets_list[:3],
        key="comparison_markets"
    )

    if start_date_bar > end_date_bar:
        st.warning("Start date must be before or equal to end date.")

    elif not selected_markets:
        st.info("Select at least one market to compare.")

    else:
        data_comparison = compare_markets(
            choice_commodity_bar,
            start_date_bar,
            end_date_bar
        )

        df_comparison = pd.DataFrame(
            data_comparison,
            columns=["market", "modal_price"]
        )

        # Keep only the markets selected by the user
        df_comparison = df_comparison[
            df_comparison["market"].isin(selected_markets)
        ]

        if not df_comparison.empty:
            fig_bar = px.bar(
                df_comparison,
                x="modal_price",
                y="market",
                orientation="h",
                title=f"Average {choice_commodity_bar} Price by Market",
                labels={
                    "market": "Market",
                    "modal_price": "Average Modal Price (₹)"
                },
                text="modal_price"
            )

            fig_bar.update_layout(
                yaxis={"categoryorder": "total ascending"},
                showlegend=False
            )

            st.plotly_chart(
                fig_bar,
                use_container_width=True
            )

        else:
            st.info("No price data found for the selected markets and dates.")
