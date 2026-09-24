import requests
import os
import json
from datetime import date
from dotenv import load_dotenv
from math import ceil
from pprint import pprint

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"
def get_data(
    format: str = 'json',
    offset: int = 0,
    limit: int = 10,
    state: str | None = None,
    district: str | None = None,
    commodity: str | None = None,
    arrival_date: str | None = None,
):
    data_list = []
    myparams = {
        "api-key":API_KEY,
        "format":format,
        "offset":offset,
        "limit":limit
    }

    if state:
        myparams["filters[State]"] = state
    if district:
        myparams["filters[District]"] = district
    if commodity:
        myparams["filters[Commodity]"] = commodity
    if arrival_date:
        myparams["filters[Arrival_Date]"] = arrival_date

    try:
        session = requests.Session()
        session.trust_env = False
        response = session.get(
            API_URL,
            params = myparams,
            headers={
                "User-Agent": "curl/8.21.0",
                "Accept": "*/*"
                },
            timeout=30
            )
        # print(response.status_code)
        # print(response.headers)
        # print(response.text)
        # print(response.url)

        response.raise_for_status()
        filename = str(date.today())+"data.json"
        with open(filename, 'w') as f:
            json.dump(response.json(), f, indent=4)

        # pagination
        total = response.json()['total']
        number_of_pages = ceil(total/limit)
        for page in range(0, number_of_pages):
            myparams['offset'] = page * limit
            response_per_page = session.get(
                API_URL,
                params = myparams,
                headers={
                    "User-Agent": "curl/8.21.0",
                    "Accept": "*/*"
                    },
                timeout=30
                )
            print(response_per_page.status_code)
            print(response_per_page.headers)
            print(response_per_page.text)
            print(response_per_page.url)

            response_per_page.raise_for_status()
            records = response_per_page.json()['records']
            for record in records:
                with open('data1.jsonl', 'a') as f:
                    json.dump(record, f)
                    f.write("\n")
                    data_list.append(record)

        return data_list

    except requests.exceptions.RequestException as e:
        raise Exception("Failed Fetch")

results = get_data(commodity="Tomato", state="Maharashtra", arrival_date="2026-04-04")
pprint(results)