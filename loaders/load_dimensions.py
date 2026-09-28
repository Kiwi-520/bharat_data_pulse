from app.db import get_connection

def build_dimension_maps(records):
    """Takes fetched records, returns market_id and commodity_id dicts (in-memory only, no DB yet)."""
    market_id = {}
    commodity_id = {}
    for entry in records:
        if entry['Market'] not in market_id:
            market_id[entry['Market']] = {
                "state": entry["State"],
                "district": entry["District"]
            }
        if entry["Commodity"] not in commodity_id:
            commodity_id[entry["Commodity"]] = {
                "code": entry["Commodity_Code"]
            }
    return market_id, commodity_id

def get_or_create_location(cursor, market, district, state):
    cursor.execute(
        "SELECT location_id FROM dim_location WHERE market = %s AND district = %s AND state = %s",
        (market, district, state)
    )
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(
        "INSERT INTO dim_location (district, state, market) VALUES (%s, %s, %s)",
        (district, state, market)
    )
    return cursor.lastrowid

def get_or_create_commodity(cursor, commodity, code):
    cursor.execute(
        "SELECT commodity_id FROM dim_commodity WHERE commodity = %s",
        (commodity,)
    )
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(
        "INSERT INTO dim_commodity (commodity_code, commodity) VALUES (%s, %s)",
        (code, commodity)
    )
    return cursor.lastrowid

def load_dimensions(records):
    """Main entry point: given raw records, ensures all markets/commodities exist in DB,
    returns market_id and commodity_id dicts with real DB ids attached."""
    market_map, commodity_map = build_dimension_maps(records)

    cnx = get_connection()
    if cnx is None:
        raise Exception("Could not connect to database")
    cursor = cnx.cursor()

    for market, info in market_map.items():
        info["id"] = get_or_create_location(cursor, market, info["district"], info["state"])

    for commodity, info in commodity_map.items():
        info["id"] = get_or_create_commodity(cursor, commodity, info["code"])

    cnx.commit()
    cursor.close()
    cnx.close()

    return market_map, commodity_map