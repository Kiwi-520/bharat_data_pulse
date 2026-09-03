from main import get_data
from datetime import date, timedelta

# dates = []

# for month in range(1, 12):
#     for day in range(1, 31):
#         dates.append(f"{day}/{month}/2026")

# print(dates)

def fetch_data():
    start = date(2026, 2, 1)
    end = date(2026, 2, 1)

    current = start

    while current <= end:
        date_string = f"{current.day}/{current.month}/{current.year}"
        data = get_data(offset = 0, limit = 50, state='Maharashtra', commodity='Onion', arrival_date=date_string)
        current += timedelta(days=1)

fetch_data()