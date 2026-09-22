import mysql.connector
from mysql.connector import errorcode
import json
import os
from dotenv import load_dotenv
from data_organizing import market_id, commodity_id
import re
from decimal import *
from datetime import datetime

def numeric_conversion(num):
    if isinstance(num, (int, float)):
        return round(Decimal(num), 3)
    else:
        temp = num
        price = re.findall('\d+[.]?\d+', temp)[0]
        return round(Decimal(price), 3)

def date_conversion(arrival_date):
    temp = arrival_date
    converted_date = datetime.strptime(temp, "%d/%m/%Y").date()
    return converted_date

load_dotenv()

try:
    cnx = mysql.connector.connect(
        user = os.getenv("MYSQL_USERNAME"),
        password = os.getenv("MYSQL_PASSWORD"),
        host = os.getenv("DB_HOST"),
        database = os.getenv("DB_NAME")
    )
    print("Connected sucessfully...")
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Wrong password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("wrong host or db name")
    else:
        print(err)
cursor = cnx.cursor()

with open('data1.jsonl', 'r') as f:
    record = []
    for line in f:
        record.append(json.loads(line))

add_fact_daily_price = ("INSERT INTO fact_daily_price"
                     "(location_id, commodity_id, min_price, max_price, modal_price, grade, variety, arrival_date)"
                     "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")

for entry in record:
    data_fact_daily_price = (
        market_id[entry["Market"]]["id"],
        commodity_id[entry["Commodity"]]["id"],
        numeric_conversion(entry["Min_Price"]),
        numeric_conversion(entry["Max_Price"]),
        numeric_conversion(entry["Modal_Price"]),
        entry["Grade"],
        entry["Variety"],
        date_conversion(entry["Arrival_Date"])
    )
    cursor.execute(add_fact_daily_price, data_fact_daily_price)

cnx.commit()
cnx.close()

