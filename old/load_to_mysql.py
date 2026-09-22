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
