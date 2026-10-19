
import streamlit as st
import pandas as pd
from datetime import date

from analytics.queries import (
    get_grade_variety_breakdown,
    get_top_movers,
    get_latest_data_date,
    get_market_summary,
    get_commodity_summary,
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================
st.set_page_config(
    page_title="Bharat Data Pulse",
    page_icon="🌾",
    layout="wide",
)


# ==================================================
# HOME DASHBOARD
# ==================================================
def render_home():
    st.title("🌾 Bharat Data Pulse")
    st.caption("Agri-Market Mandi Analytics Suite")

    # ----------------------------------------------
    # Fetch filter options
    # ----------------------------------------------
    markets_data = get_market_summary() or []
    commodities_data = get_commodity_summary() or []

    markets_list = [
        item["market"] for item in markets_data
    ]
    commodities_list = [
        item["commodity"] for item in commodities_data
    ]

    # ----------------------------------------------
    # Last Updated
    # ----------------------------------------------
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

    last_date = get_latest_data_date()

    with col7:
        with st.container(border=True):
            st.write("Last Updated")
            st.write(last_date if last_date else "N/A")

    # ----------------------------------------------
    # Filters
    # ----------------------------------------------
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        selected_market = st.selectbox(
            "Select Market",
            markets_list,
            index=0 if markets_list else None,
            placeholder="Select a market",
            key="home_market",
        )

    with c2:
        selected_commodity = st.selectbox(
            "Select Commodity",
            commodities_list,
            index=0 if commodities_list else None,
            placeholder="Select a commodity",
            key="home_commodity",
        )

    with c3:
        start_date = st.date_input(
            "Start Date",
            value=date(2024, 1, 1),
            key="home_start_date",
        )

    with c4:
        end_date = st.date_input(
            "End Date",
            value=date(2026, 4, 4),
            key="home_end_date",
        )

    # ----------------------------------------------
    # Top Market Movers
    # ----------------------------------------------
    with st.container(border=True):
        st.markdown("### 📊 Top Market Movers")

        if start_date > end_date:
            st.warning(
                "Start Date must be before or equal to End Date."
            )
        else:
            movers = get_top_movers(
                start_date,
                end_date,
                limit=5,
            ) or {}

            gain_col, loss_col = st.columns(2, gap="medium")

            # Top Gainers
            with gain_col:
                with st.container(border=True):
                    st.markdown("#### 🟢 Top Gainers")

                    gainers = movers.get("gainers", [])

                    if gainers:
                        for item in gainers:
                            st.markdown(
                                f"**{item['commodity']}** "
                                f"<span style='color: #16a34a; "
                                f"float: right;'>"
                                f"+{item['change_pct']:.2f}%"
                                f"</span>",
                                unsafe_allow_html=True,
                            )
                            st.divider()
                    else:
                        st.info(
                            "No gainers found for this period."
                        )

            # Top Losers
            with loss_col:
                with st.container(border=True):
                    st.markdown("#### 🔴 Top Losers")

                    losers = movers.get("losers", [])

                    if losers:
                        for item in losers:
                            st.markdown(
                                f"**{item['commodity']}** "
                                f"<span style='color: #dc2626; "
                                f"float: right;'>"
                                f"{item['change_pct']:.2f}%"
                                f"</span>",
                                unsafe_allow_html=True,
                            )
                            st.divider()
                    else:
                        st.info(
                            "No losers found for this period."
                        )

    # ----------------------------------------------
    # Grade Variety
    # ----------------------------------------------
    with st.container(border=True):
        st.markdown("### Grade Variety")

        if selected_commodity and selected_market:
            data = get_grade_variety_breakdown(
                selected_commodity,
                selected_market,
            )

            if data:
                st.dataframe(
                    pd.DataFrame(data),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info(
                    "No grade or variety data found for these filters."
                )
        else:
            st.info(
                "Select a market and commodity to view grade variety."
            )


# ==================================================
# SIDEBAR BRANDING
# ==================================================
with st.sidebar:
    st.title("🌾 Bharat Data Pulse")
    st.caption("Agri-Market Intelligence")
    st.divider()


# ==================================================
# NAVIGATION
# ==================================================
home_page = st.Page(
    render_home,
    title="Home",
    icon="🏠",
    default=True,
)

commodities_page = st.Page(
    "comodities.py",
    title="Commodities",
    icon="🌾",
)

markets_page = st.Page(
    "markets.py",
    title="Markets",
    icon="📍",
)

price_analytics_page = st.Page(
    "price_analytics.py",
    title="Price Analytics",
    icon="📈",
)

decision_cards_page = st.Page(
    "decisions_cards.py",
    title="Decision Cards",
    icon="🎯",
)

navigation = st.navigation(
    [
        home_page,
        commodities_page,
        markets_page,
        price_analytics_page,
        decision_cards_page,
    ],
    position="sidebar",
)

navigation.run()