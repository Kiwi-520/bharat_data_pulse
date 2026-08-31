from fastapi import FastAPI
import requests
import os
import json
from datetime import date
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

API_KEY = os.getenv("API_KEY")
API_URL = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"
@app.get("/")
def get_data(
    format: str = 'json',
    offset: int = 0,
    limit: int = 10,
    state: str | None = None,
    district: str | None = None,
    commodity: str | None = None,
    arrival_date: str | None = None,
):
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
        print(response.status_code)
        print(response.headers)
        print(response.text)
        print(response.url)

        response.raise_for_status()
        filename = str(date.today())+"data.json"

        with open(filename, "w") as f:
            json.dump(response.json(), f, indent=4)
        return {"message":"successfully call made!"}

    except requests.exceptions.RequestException as e:
        return {
            "message": "No data found",
            "error": str(e)
        }
