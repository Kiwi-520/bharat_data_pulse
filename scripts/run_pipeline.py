import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.fetch import check_api, get_data
from analytics.queries import get_latest_data_date
from loaders.load_dimensions import load_dimensions
from loaders.load_facts import load_facts


MAX_DATES_PER_RUN = 7


def main():
    # 1. Check the source before doing anything else.
    print("Checking mandi API availability...")

    if not check_api():
        print("API unavailable or timed out.")
        print("Keeping existing Aiven data unchanged.")
        return

    # 2. Read the latest date already stored in Aiven.
    try:
        watermark = get_latest_data_date()
    except Exception as exc:
        print(f"Could not read database watermark: {exc}")
        print("Stopping without fetching data.")
        return

    if watermark is None:
        print("No existing data watermark found.")
        print("Stopping to avoid an unintended historical import.")
        return

    if hasattr(watermark, "date"):
        watermark = watermark.date()

    print(f"Latest stored arrival date: {watermark}")

    # 3. Select at most seven dates after the watermark.
    start_date = watermark + timedelta(days=1)
    end_date = min(
        date.today(),
        start_date + timedelta(days=MAX_DATES_PER_RUN - 1),
    )

    if start_date > date.today():
        print("Database is already current through today.")
        return

    print(f"Fetching dates from {start_date} through {end_date}")

    # 4. Fetch each date separately.
    all_records = []

    current_date = start_date
    while current_date <= end_date:
        api_date = current_date.strftime("%d/%m/%Y")
        print(f"Fetching arrival date: {api_date}")

        try:
            records = get_data(
                arrival_date=api_date,
                offset=0,
                limit=1000,
            )
        except Exception as exc:
            print(f"Fetch failed for {api_date}: {exc}")
            print("Stopping. Existing Aiven data remains unchanged by this pipeline.")
            return

        # Do not accept records that don't match the requested date.
        matching_records = [
            record
            for record in records
            if record.get("Arrival_Date") == api_date
        ]

        if len(matching_records) != len(records):
            print(
                f"Unexpected date returned for {api_date}. "
                "Stopping to avoid loading incorrect data."
            )
            return

        all_records.extend(matching_records)
        print(f"Records for {api_date}: {len(matching_records)}")

        current_date += timedelta(days=1)

    # 5. If nothing new was returned, leave Aiven unchanged.
    if not all_records:
        print("No new records returned.")
        print("Keeping existing Aiven data unchanged.")
        return

    print(f"Total new API records fetched: {len(all_records)}")

    # 6. Load only the fetched records.
    try:
        print("Loading dimensions...")
        market_map, commodity_map = load_dimensions(all_records)

        print("Loading facts...")
        load_facts(all_records, market_map, commodity_map)

    except Exception as exc:
        print(f"Database loading failed: {exc}")
        raise

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
