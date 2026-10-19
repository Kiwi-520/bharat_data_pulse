from math import sqrt
from datetime import date, timedelta, datetime
from math import isclose
from app.db import get_connection
from pprint import pprint

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

def compare_markets(commodity, start_date=None, end_date=None):
    if start_date is None:
        start_date = date.today() - timedelta(days=172)
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
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    # Default: last 30 days
    if start_date is None:
        start_date = date.today() - timedelta(days=201)
        start_date = datetime.strptime(str(start_date), "%Y-%m-%d").date()

    if end_date is None:
        end_date = date.today()
        end_date = datetime.strptime(str(end_date), "%Y-%m-%d").date()

    cnx = get_connection()

    if cnx is None:
        raise Exception("Could not connect to database")

    cursor = cnx.cursor()

    print("start_date:", start_date)
    print("end_date:", end_date)

    cursor.execute(
        """
        SELECT f.arrival_date, f.modal_price
        FROM fact_daily_price f
        JOIN dim_commodity c
            ON f.commodity_id = c.commodity_id
        JOIN dim_location l
            ON f.location_id = l.location_id
        WHERE c.commodity = %s
          AND l.market = %s AND f.arrival_date BETWEEN %s AND %s
        ORDER BY f.arrival_date
        """,
        (commodity, market, start_date, end_date)
    )

    rows = cursor.fetchall()

    print("rows:", rows)

    cursor.close()
    cnx.close()

    if not rows:
        return {
            "commodity": commodity,
            "market": market,
            "trend": "no data",
            "change_pct": None,
            "start_date": start_date,
            "end_date": end_date
        }

    # Find middle of date range
    mid_date = start_date + (end_date - start_date) / 2

    first_half_prices = []
    second_half_prices = []

    for arrival_date, price in rows:
        if arrival_date <= mid_date:
            first_half_prices.append(float(price))
        else:
            second_half_prices.append(float(price))

    if not first_half_prices or not second_half_prices:
        return {
            "commodity": commodity,
            "market": market,
            "trend": "insufficient data",
            "change_pct": None,
            "start_date": start_date,
            "end_date": end_date
        }

    first_half_avg = sum(first_half_prices) / len(first_half_prices)
    second_half_avg = sum(second_half_prices) / len(second_half_prices)

    change_pct = (
        (second_half_avg - first_half_avg)
        / first_half_avg
    ) * 100

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
        "change_pct": round(change_pct, 2),
        "start_date": start_date,
        "end_date": end_date
    }

def get_price_band(commodity, market):
    cnx = get_connection()
    if cnx is None:
        raise Exception("Couldnot connect to database")
    cursor = cnx.cursor()
    cursor.execute( #this only causes database to return the records we need to fecth them speararlty to use.
        "SELECT f.arrival_date, f.max_price, f.min_price, f.modal_price "
        "FROM fact_daily_price f "
        "JOIN dim_commodity c ON f.commodity_id=c.commodity_id "
        "JOIN dim_location l ON f.location_id=l.location_id "
        "WHERE c.commodity=%s AND l.market=%s "
        "ORDER BY f.arrival_date DESC LIMIT 1 ",
        (commodity, market)
    )
    rows = cursor.fetchone()
    cursor.close()
    cnx.close()
    if rows is None:
        return None
    return {
        "date": rows[0],
        "max_price": float(rows[1]),
        "min_price": float(rows[2]),
        "modal_price": float(rows[3]),
    }

def get_month_over_month(commodity, market):
    cnx = get_connection()
    if cnx is None:
        raise Exception("Couldnot connect to database")
    cursor = cnx.cursor()
    cursor.execute(
        """
            SELECT
                YEAR(f.arrival_date) AS year,
                MONTH(f.arrival_date) AS month,
                AVG(f.modal_price) AS avg_price
            FROM fact_daily_price f
            JOIN dim_commodity c
                ON f.commodity_id = c.commodity_id
            JOIN dim_location l
                ON f.location_id = l.location_id
            WHERE c.commodity = %s
            AND l.market = %s
            GROUP BY YEAR(f.arrival_date), MONTH(f.arrival_date)
            ORDER BY year DESC, month DESC
            LIMIT 2
        """,
    (commodity, market)
    )
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    if len(rows) < 2:
        error= {
            "change_pct": None
        }
        return error

    current_avg = float(rows[0][2])
    previous_avg = float(rows[1][2])

    if previous_avg == 0:
        error= {
            "current_month_avg": current_avg,
            "previous_month_avg": previous_avg,
            "change_pct": None
        }
        return error

    change_pct = ((current_avg - previous_avg) / previous_avg) * 100

    result_dict = {
        "current_month_avg": current_avg,
        "previous_month_avg": previous_avg,
        "change_pct": round(change_pct, 2)
    }

    return result_dict
# mom = get_month_over_month("Onion", "Pimpalgaon Baswant(Saykheda) APMC")
# print(mom)

def get_top_movers(start_date, end_date, limit=5):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    cnx = get_connection()
    if cnx is None:
        raise Exception("Couldnot connect to database")
    cursor = cnx.cursor()

    cursor.execute(
        """
        SELECT
            c.commodity,
            f.arrival_date,
            AVG(f.modal_price) AS avg_modal_price
        FROM fact_daily_price f
        JOIN dim_commodity c
            ON f.commodity_id = c.commodity_id
        WHERE f.arrival_date BETWEEN %s AND %s
        GROUP BY c.commodity, f.arrival_date
        ORDER BY c.commodity, f.arrival_date
        """,
        (start_date, end_date)
    )

    rows = cursor.fetchall()

    cursor.close()
    cnx.close()

    # Store prices commodity-wise
    commodity_price_dict = {}

    for row in rows:

        commodity = row[0]
        date = row[1]
        price = row[2]

        if commodity not in commodity_price_dict:
            commodity_price_dict[commodity] = []

        commodity_price_dict[commodity].append({
            "date": date,
            "price": price
        })


    # Find midpoint of the date range
    mid_date = start_date + (end_date - start_date) / 2

    results = []

    # Calculate price change for every commodity
    for commodity in commodity_price_dict:

        records = commodity_price_dict[commodity]

        first_half_prices = []
        second_half_prices = []

        for record in records:

            if record["date"] <= mid_date:
                first_half_prices.append(float(record["price"]))
            else:
                second_half_prices.append(float(record["price"]))

        # Skip commodities where one half has no data
        if not first_half_prices or not second_half_prices:
            continue

        first_half_avg = (
            sum(first_half_prices) / len(first_half_prices)
        )

        second_half_avg = (
            sum(second_half_prices) / len(second_half_prices)
        )

        # Avoid division by zero
        if first_half_avg == 0:
            continue

        change_pct = (
            (second_half_avg - first_half_avg)
            / first_half_avg
        ) * 100

        results.append({
            "commodity": commodity,
            "change_pct": round(change_pct, 3)
        })

    # Top gainers
    gainers = sorted(
        results,
        key=lambda x: x["change_pct"],
        reverse=True
    )[:limit]

    # Top losers
    losers = sorted(
        results,
        key=lambda x: x["change_pct"]
    )[:limit]

    return {
        "gainers": gainers,
        "losers": losers
    }

def get_grade_variety_breakdown(commodity, market):
    cnx = get_connection()
    if cnx is None:
        raise Exception("Couldnot connect to database")
    cursor = cnx.cursor()
    cursor.execute( #this only causes database to return the records we need to fecth them speararlty to use.
        """
        SELECT f.grade, f.variety,AVG(modal_price), COUNT(*)
        FROM fact_daily_price f
        JOIN dim_commodity c ON f.commodity_id=c.commodity_id
        JOIN dim_location l ON f.location_id=l.location_id
        WHERE c.commodity = %s AND l.market=%s
        GROUP BY f.grade, f.variety
        ORDER BY AVG(modal_price) DESC
        """,
        (commodity, market)
    )
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    if rows is None:
        return None
    result_dict = []
    for r in rows:
        result_dict.append({"grade": r[0], "variety": r[1], "avg_price": float(r[2]), "count": r[3]})
    return result_dict

def get_market_coverage_count(commodity):
    cnx = get_connection()
    if cnx is None:
        raise Exception("Couldnot connect to database")
    cursor = cnx.cursor()
    cursor.execute(
        """
        SELECT COUNT(DISTINCT l.location_id)
        FROM fact_daily_price f
        JOIN dim_commodity c ON f.commodity_id=c.commodity_id
        JOIN dim_location l ON f.location_id=l.location_id
        WHERE c.commodity = %s
        """,
        (commodity,)
    )
    rows = cursor.fetchone()[0]
    cursor.close()
    cnx.close()
    return rows

# market_coverage = get_market_coverage_count("Onion")
# print(market_coverage)

def get_latest_data_date():
    cnx = get_connection()
    if cnx is None:
        raise Exception("Couldnot connect to database")
    cursor = cnx.cursor()
    cursor.execute(
        """
        SELECT MAX(arrival_date)
        FROM fact_daily_price
        """
    )
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    return rows[0][0]

# result = get_latest_data_date()
# print(result)

def get_price_history(commodity, market, start_date, end_date):

    cnx = get_connection()

    if cnx is None:
        raise Exception("Could not connect to database")

    cursor = cnx.cursor()

    print("commodity:", commodity)
    print("market:", market)
    print("start_date:", start_date)
    print("end_date:", end_date)

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
        return []

    result_list = []

    for r in rows:
        result_list.append({
            "date": r[0],
            "price": float(r[1])
        })

    return result_list

# price_history = get_price_history("Onion", "Pune APMC", "2026-01-01", "2026-04-04")
# print(price_history)

def  get_commodity_list():
    cnx = get_connection()
    if cnx is None:
        raise Exception("Couldnot connect to database")
    cursor = cnx.cursor()
    cursor.execute(
        """
        SELECT DISTINCT(commodity)
        FROM dim_commodity
        """
    )
    rows = cursor.fetchall()
    result = []

    for i in rows:
        result.append(i[0])
    cursor.close()
    cnx.close()
    return result

def  get_market_list(commodity):
    cnx = get_connection()
    if cnx is None:
        raise Exception("Couldnot connect to database")
    cursor = cnx.cursor()
    cursor.execute(
        """
        SELECT DISTINCT(market)
        FROM fact_daily_price f
        JOIN dim_commodity c
            ON f.commodity_id = c.commodity_id
        JOIN dim_location l
            ON f.location_id = l.location_id
        WHERE c.commodity = %s
        """,
        (commodity,)
    )
    rows = cursor.fetchall()
    result = []

    for i in rows:
        result.append(i[0])
    cursor.close()
    cnx.close()
    return result

# market_list = get_market_list("Onion")
# print(market_list)

"""Add these to analytics/queries.py"""
from app.db import get_connection


def get_market_summary():
    """Per market: distinct commodity count + total record count."""
    cnx = get_connection()
    if cnx is None:
        raise Exception("Could not connect to database")
    cursor = cnx.cursor()
    cursor.execute(
        "SELECT l.market, l.district, l.state, "
        "COUNT(DISTINCT f.commodity_id) AS commodity_count, "
        "COUNT(*) AS record_count "
        "FROM fact_daily_price f "
        "JOIN dim_location l ON f.location_id = l.location_id "
        "GROUP BY l.market, l.district, l.state "
        "ORDER BY record_count DESC"
    )
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    return [{"market": r[0], "district": r[1], "state": r[2],
             "commodity_count": r[3], "record_count": r[4]} for r in rows]


def get_commodity_summary():
    """Return one summary row per commodity using an efficient aggregate query."""
    cnx = get_connection()

    if cnx is None:
        raise RuntimeError("Could not connect to database")

    cursor = cnx.cursor()

    try:
        cursor.execute("""
            WITH daily_summary AS (
                SELECT
                    commodity_id,
                    MAX(arrival_date) AS latest_date,
                    COUNT(DISTINCT location_id) AS market_count
                FROM fact_daily_price
                GROUP BY commodity_id
            ),
            latest_ids AS (
                SELECT
                    f.commodity_id,
                    MAX(f.price_id) AS price_id
                FROM fact_daily_price AS f
                JOIN daily_summary AS s
                    ON s.commodity_id = f.commodity_id
                   AND s.latest_date = f.arrival_date
                GROUP BY f.commodity_id
            )
            SELECT
                c.commodity,
                f.modal_price AS latest_price,
                s.latest_date,
                s.market_count
            FROM daily_summary AS s
            JOIN dim_commodity AS c
                ON c.commodity_id = s.commodity_id
            LEFT JOIN latest_ids AS li
                ON li.commodity_id = s.commodity_id
            LEFT JOIN fact_daily_price AS f
                ON f.price_id = li.price_id
            ORDER BY c.commodity
        """)

        rows = cursor.fetchall()

    finally:
        cursor.close()
        cnx.close()

    return [
        {
            "commodity": row[0],
            "latest_modal_price": (
                float(row[1]) if row[1] is not None else None
            ),
            "latest_date": row[2],
            "market_count": row[3],
        }
        for row in rows
    ]



def get_state_commodity_distribution(commodities):
    """Record count per state, for one or more commodities (map sizing)."""
    if not commodities:
        return []
    cnx = get_connection()
    if cnx is None:
        raise Exception("Could not connect to database")
    cursor = cnx.cursor()
    placeholders = ",".join(["%s"] * len(commodities))
    cursor.execute(
        f"SELECT l.state, COUNT(*) AS record_count, "
        f"COUNT(DISTINCT l.market) AS market_count "
        f"FROM fact_daily_price f "
        f"JOIN dim_commodity c ON f.commodity_id = c.commodity_id "
        f"JOIN dim_location l ON f.location_id = l.location_id "
        f"WHERE c.commodity IN ({placeholders}) "
        f"GROUP BY l.state",
        tuple(commodities)
    )
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    return [{"state": r[0], "record_count": r[1], "market_count": r[2]} for r in rows]
