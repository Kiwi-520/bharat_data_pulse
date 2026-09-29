from math import sqrt
from datetime import date, timedelta, datetime
from math import isclose
from app.db import get_connection

def get_volatility(commodity, market, start_date, end_date):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    cnx = get_connection()
    if cnx is None:
        raise Exception("Couldnot connect to database")
    cursor = cnx.cursor()
    cursor.execute( #this only causes database to return the records we need to fecth them speararlty to use.
        "SELECT Modal_Price FROM fact_daily_price f"
        " JOIN dim_commodity c ON f.commodity_id=c.commodity_id"
        " JOIN dim_location l ON f.location_id=l.location_id"
        " WHERE c.commodity=%s AND l.market=%s AND f.arrival_date BETWEEN %s AND %s",
        (commodity, market, start_date, end_date)
    )
    modal_price_list = cursor.fetchall()
    cursor.close()
    cnx.close()

    total_price = 0
    for price in modal_price_list:
        total_price += price[0]

    if len(modal_price_list) != 0:
        avg = total_price/len(modal_price_list)
    else:
        return "No Data Found"

    price_diff_square_list = []
    total_diff_square = 0

    for price in modal_price_list:
        price_diff_square_list.append((price[0]-avg)*(price[0]-avg))
        total_diff_square += (price[0]-avg)*(price[0]-avg)

    std_volatility = sqrt(total_diff_square/len(modal_price_list))

    return std_volatility

def compare_markets(commodity, start_date, end_date):
    if start_date is None:
        start_date = date.today() - timedelta(days=30)
    if end_date is None:
        end_date = date.today()
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    cnx = get_connection()
    if cnx is None:
        raise Exception("Couldnot connect to database")
    cursor = cnx.cursor()
    cursor.execute( #this only causes database to return the records we need to fecth them speararlty to use.
        "SELECT l.market, AVG(f.modal_price) "
        "FROM fact_daily_price f "
        "JOIN dim_commodity c ON f.commodity_id=c.commodity_id "
        "JOIN dim_location l ON f.location_id=l.location_id "
        "WHERE c.commodity=%s AND arrival_date BETWEEN %s AND %s "
        "GROUP BY l.market ",
        (commodity,start_date, end_date)
    )
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    return rows

def get_price_trend(commodity, market, start_date=None, end_date=None):

    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Default: last 30 days
    if start_date is None:
        start_date = date.today() - timedelta(days=30)

    if end_date is None:
        end_date = date.today()

    # Connect to database
    cnx = get_connection()

    if cnx is None:
        raise Exception("Could not connect to database")

    cursor = cnx.cursor()

    # Fetch date + modal price
    cursor.execute(
        """
        SELECT f.arrival_date, f.modal_price
        FROM fact_daily_price f
        JOIN dim_commodity c
            ON f.commodity_id = c.commodity_id
        JOIN dim_location l
            ON f.location_id = l.location_id
        WHERE c.commodity = %s
          AND l.market = %s
          AND f.arrival_date BETWEEN %s AND %s
        ORDER BY f.arrival_date
        """,
        (commodity, market, start_date, end_date)
    )

    rows = cursor.fetchall()

    cursor.close()
    cnx.close()

    if not rows:
        return {
            "commodity": commodity,
            "market": market,
            "trend": "no data",
            "change_pct": None
        }

    # Find middle of the date range
    mid_date = start_date + (end_date - start_date) / 2

    # Split prices into two halves
    first_half_prices = []
    second_half_prices = []

    for arrival_date, price in rows:

        if arrival_date <= mid_date:
            first_half_prices.append(float(price))
        else:
            second_half_prices.append(float(price))

    # Make sure both halves contain data
    if not first_half_prices or not second_half_prices:
        return {
            "commodity": commodity,
            "market": market,
            "trend": "insufficient data",
            "change_pct": None
        }

    # Calculate averages
    first_half_avg = sum(first_half_prices) / len(first_half_prices)
    second_half_avg = sum(second_half_prices) / len(second_half_prices)

    # Calculate percentage change
    change_pct = (
        (second_half_avg - first_half_avg)
        / first_half_avg
    ) * 100

    # Apply 5% threshold
    if change_pct > 5:
        trend = "rising"

    elif change_pct < -5:
        trend = "falling"

    else:
        trend = "stable"

    return {
        "commodity": commodity,
        "market": market,
        "trend": trend,
        "change_pct": round(change_pct, 2)
    }
