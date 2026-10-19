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

def load_facts(records, market_map, commodity_map, batch_size=5000):
    cnx = get_connection()
    if cnx is None:
        raise Exception("Could not connect to database")
    cursor = cnx.cursor()

    # Step 1: pull existing fact identities into memory, once
    cursor.execute(
        "SELECT location_id, commodity_id, min_price, max_price, modal_price, "
        "grade, variety, arrival_date FROM fact_daily_price"
    )
    existing = set(cursor.fetchall())  # set of tuples, fast lookup

    # Step 2: build the list of new rows to insert, skipping duplicates
    new_rows = []
    for entry in records:
        location_id = market_map[entry["Market"]]["id"]
        commodity_id = commodity_map[entry["Commodity"]]["id"]
        min_p = numeric_conversion(entry["Min_Price"])
        max_p = numeric_conversion(entry["Max_Price"])
        modal_p = numeric_conversion(entry["Modal_Price"])
        grade = entry["Grade"]
        variety = entry["Variety"]
        arrival = date_conversion(entry["Arrival_Date"])

        row = (location_id, commodity_id, min_p, max_p, modal_p, grade, variety, arrival)
        if row not in existing:
            new_rows.append(row)
            existing.add(row)

    print(f"{len(records)} records checked, {len(new_rows)} new rows to insert")

    # Step 3: insert in batches using executemany
    add_fact_daily_price = (
        "INSERT INTO fact_daily_price "
        "(location_id, commodity_id, min_price, max_price, modal_price, grade, variety, arrival_date) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )

    for i in range(0, len(new_rows), batch_size):
        batch = new_rows[i:i + batch_size]
        cursor.executemany(add_fact_daily_price, batch)
        cnx.commit()
        print(f"Inserted batch {i // batch_size + 1} ({len(batch)} rows)")

    cursor.close()
    cnx.close()