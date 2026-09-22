import json
from pprint import pprint

markets_seen = []
market_id = {}
current_market_id = 1
commodity_seen = []
commodity_id = {}
current_commodity_id = 1
def market_table(entry):
    if entry['Market'] not in markets_seen:
        market_id[entry['Market']] = {"id": current_market_id, "state": entry["State"], "district":entry['District']}
        markets_seen.append(entry['Market'])

def commodity_table(entry):
    if entry["Commodity"] not in commodity_seen:
        commodity_id[entry['Commodity']] = {"id": current_commodity_id, "code": entry['Commodity_Code']}
        commodity_seen.append(entry['Commodity'])


with open("data1.jsonl", 'r') as f:
    for line in f:
        content = json.loads(line)
        market_table(content)
        count_market = len(market_id)+1
        current_market_id =count_market
        commodity_table(content)
        count_commodity = len(commodity_id)+1
        current_commodity_id =count_commodity

import mysql.connector
from mysql.connector import errorcode
import json
import os
from dotenv import load_dotenv
from data_organizing import market_id, commodity_id
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

add_dim_location = ("INSERT INTO dim_location"
                    "(district, state, market)"
                    "VALUES (%s, %s, %s)"
                    )

add_dim_commodity = ("INSERT INTO dim_commodity"
                     "(commodity_code, commodity)"
                     "VALUES (%s, %s)"
                    )

for market in market_id:
    data_dim_location = (market_id[market]['district'],
                        market_id[market]['state'],
                        market)
    cursor.execute(add_dim_location, data_dim_location)

for commodity in commodity_id:
    data_commodity = (
        commodity_id[commodity]['code'],
        commodity
    )
    cursor.execute(add_dim_commodity, data_commodity)

cnx.commit()
cnx.close()
