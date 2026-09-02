from main import get_data
from datetime import date, timedelta

# dates = []

# for month in range(1, 12):
#     for day in range(1, 31):
#         dates.append(f"{day}/{month}/2026")

# print(dates)

def fetch_data():
    current = date(2026, 1, 1)
    end = date(2026, 11, 30)

    while current <= end:
        date_string = f"{current.day}/{current.month}/{current.year}"
        data = get_data(limit = 10, state='Maharashtra', commodity='Onion', arrival_date=date_string)
        with open("data.json", "a") as f:
            f.writelines(data)
        current += timedelta(days=1)

fetch_data()