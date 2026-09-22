import mysql.connector
from mysql.connector import errorcode
import json
import os
from dotenv import load_dotenv
from main import get_data

load_dotenv()

try:
    cnx = mysql.connector.connect(
        user = os.getenv('MYSQL_USERNAME'),
        password = os.getenv('MYSQL_PASSWORD'),
        host = os.getenv("DB_HOST"),
        database = os.getenv("DB_NAME")
    )
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Wrong password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("wrong host or db name")
    else:
        print(err)
cursor = cnx.cursor()


def is_available(commodity = "Onion", date = "2026-02-02", state = "Maharashtra"):
    fetch_data = ("SELECT COUNT(*) "
                  "FROM fact_daily_price f "
                  "JOIN dim_commodity c ON f.commodity_id = c.commodity_id "
                  "JOIN dim_location m ON f.location_id = m.location_id "
                  "WHERE c.commodity = %s AND f.arrival_date = %s AND m.state = %s"
                  )
    cursor.execute(fetch_data, (commodity, date, state))
    result = cursor.fetchone()[0]

    if result > 0:
        return True
    else:
        return False
# print(is_available("Onion",state = "Maharashtra"))

def fect_or_serve(commodity = "Onion", date = "2026-02-02", state = "Maharashtra"):
    available = is_available(commodity, date, state)
    if available:
        fetch_data = ("SELECT * "
                          "FROM fact_daily_price f "
                          "JOIN dim_commodity c ON f.commodity_id = c.commodity_id "
                          "JOIN dim_location m ON f.location_id = m.location_id "
                          "WHERE c.commodity = %s AND f.arrival_date = %s AND m.state = %s "
                          )
        cursor.execute(fetch_data, (commodity, date, state))
        result = cursor.fetchone()
        return result
    else:
        data = get_data(state = state, commodity=commodity, date=date)
        organized_data =


