
import mysql.connector
from mysql.connector import errorcode
import os
from dotenv import load_dotenv
load_dotenv()

def get_connection():
    try:
        cnx = mysql.connector.connect(
            user=os.getenv("MYSQL_USERNAME"),
            password=os.getenv("MYSQL_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "3306")),
            database=os.getenv("DB_NAME")
        )
        print("Connected sucessfully...")
        return cnx
    except mysql.connector.Error as err:
        cnx = None
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Wrong password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("wrong host or db name")
        else:
            print(err)
        return cnx
