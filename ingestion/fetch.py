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

import requests


def check_api() -> bool:
    """Return True only if the API returns valid JSON with records."""
    try:
        response = requests.get(
            API_URL,
            params={
                "api-key": API_KEY,
                "format": "json",
                "limit": 1,
            },
            timeout=10,
        )

        if response.status_code != 200:
            return False

        data = response.json()
        return isinstance(data, dict) and "records" in data

    except Exception:
        return False

def get_data(
    format: str = "json",
    offset: int = 0,
    limit: int = 10,
    state: str | None = None,
    district: str | None = None,
    commodity: str | None = None,
    arrival_date: str | None = None,
):
    data_list = []

    myparams = {
        "api-key": API_KEY,
        "format": format,
        "offset": offset,
        "limit": limit,
    }

    if state:
        myparams["filters[State]"] = state
    if district:
        myparams["filters[District]"] = district
    if commodity:
        myparams["filters[Commodity]"] = commodity
    if arrival_date:
        myparams["filters[Arrival_Date]"] = arrival_date

    headers = {
        "User-Agent": "curl/8.21.0",
        "Accept": "*/*",
    }

    try:
        with requests.Session() as session:
            session.trust_env = False

            print("Fetching first page...")
            response = session.get(
                API_URL,
                params=myparams,
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict) or not isinstance(
                data.get("records"), list
            ):
                raise ValueError("Invalid API response: missing records list")

            total = int(data.get("total", len(data["records"])))
            if arrival_date and total > 100000:
                raise ValueError(
                    f"Date filter may have failed: API reported {total} records "
                    f"for arrival_date={arrival_date}. Aborting pagination."
                )
            data_list.extend(data["records"])

            # Fetch remaining pages without requesting the first page again.
            for page_offset in range(
                offset + limit, offset + total, limit
            ):
                myparams["offset"] = page_offset

                page_response = session.get(
                    API_URL,
                    params=myparams,
                    headers=headers,
                    timeout=30,
                )
                page_response.raise_for_status()

                page_data = page_response.json()

                if not isinstance(page_data, dict) or not isinstance(
                    page_data.get("records"), list
                ):
                    raise ValueError(
                        "Invalid API response during pagination"
                    )

                page_records = page_data["records"]

                if not page_records:
                    break

                data_list.extend(page_records)
                print(f"Fetched {len(data_list)}/{total} records")

        # Save once after all pages have been fetched successfully.
        os.makedirs("api_responses", exist_ok=True)

        filename = (
            f"api_responses/{arrival_date or date.today().isoformat()}"
            f"_{offset}_{limit}.json"
        )

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(
                {
                    "total": total,
                    "records_fetched": len(data_list),
                    "records": data_list,
                },
                file,
                indent=4,
                default=str,
            )

        print(f"Saved API response to {filename}")
        return data_list

    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(f"Failed to fetch mandi data: {exc}") from exc
