import mysql.connector
from mysql.connector import errorcode
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