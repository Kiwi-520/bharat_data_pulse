from ingestion.clean import numeric_conversion, date_conversion
from app.db import get_connection

def fact_exists(cursor, location_id, commodity_id, min_price, max_price, modal_price, grade, variety, arrival_date):
    cursor.execute(
        """SELECT COUNT(*) FROM fact_daily_price
           WHERE location_id = %s AND commodity_id = %s
           AND min_price = %s AND max_price = %s AND modal_price = %s
           AND grade = %s AND variety = %s AND arrival_date = %s""",
        (location_id, commodity_id, min_price, max_price, modal_price, grade, variety, arrival_date)
    )
    return cursor.fetchone()[0] > 0

def load_facts(records, market_map, commodity_map):
    cnx = get_connection()
    if cnx is None:
        raise Exception("Could not connect to database")
    cursor = cnx.cursor()

    add_fact_daily_price = (
        "INSERT INTO fact_daily_price "
        "(location_id, commodity_id, min_price, max_price, modal_price, grade, variety, arrival_date) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )

    for entry in records:
        location_id = market_map[entry["Market"]]["id"]
        commodity_id = commodity_map[entry["Commodity"]]["id"]
        min_p = numeric_conversion(entry["Min_Price"])
        max_p = numeric_conversion(entry["Max_Price"])
        modal_p = numeric_conversion(entry["Modal_Price"])
        grade = entry["Grade"]
        variety = entry["Variety"]
        arrival = date_conversion(entry["Arrival_Date"])

        if fact_exists(cursor, location_id, commodity_id, min_p, max_p, modal_p, grade, variety, arrival):
            continue  # skip, already inserted

        cursor.execute(add_fact_daily_price, (location_id, commodity_id, min_p, max_p, modal_p, grade, variety, arrival))

    cnx.commit()
    cursor.close()
    cnx.close()