import json
import os
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "filtered_data" / "maharashtra_2025_2026.jsonl"

TARGET_COMMODITIES = {
    "onion", "tomato", "potato", "cotton", "soybean", "soyabean"
}
QUANTUM = Decimal("0.001")


def norm(value):
    if value is None:
        return None
    value = str(value).strip().casefold()
    return value or None


def norm_market(value):
    """Normalize market formatting and a trailing APMC suffix."""
    value = norm(value)
    if not value:
        return None

    parts = value.split()
    if parts and parts[-1] == "apmc":
        parts = parts[:-1]

    return "".join(
        character
        for character in " ".join(parts)
        if character.isalnum()
    )


def parse_date(value):
    if not isinstance(value, str) or not value.strip():
        return None

    value = value.strip()

    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        pass

    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    return None


def parse_code(value):
    if value is None or not str(value).strip():
        return None

    try:
        number = Decimal(str(value).strip())
        if number.is_finite() and number == number.to_integral_value():
            return int(number)
    except InvalidOperation:
        pass

    return None


def parse_price(value):
    if value is None or not str(value).strip():
        return None, False

    try:
        number = Decimal(str(value).strip().replace(",", ""))
        if not number.is_finite():
            return None, True
        return number.quantize(QUANTUM), False
    except (InvalidOperation, ValueError):
        return None, True


def fact_keys(location_id, commodity_id, arrival_date,
              min_price, max_price, modal_price, grade, variety):
    logical = (
        location_id, commodity_id, arrival_date, norm(grade), norm(variety)
    )
    exact = logical[:3] + (
        min_price, max_price, modal_price, logical[3], logical[4]
    )
    return exact, logical, (min_price, max_price, modal_price)


def main():
    if not INPUT_FILE.is_file():
        raise SystemExit(f"Filtered file not found: {INPUT_FILE}")

    load_dotenv(dotenv_path=ROOT / ".env", override=True)

    required = ("DB_HOST", "DB_NAME", "MYSQL_USERNAME", "MYSQL_PASSWORD")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise SystemExit("Missing .env settings: " + ", ".join(missing))

    records = []
    bad_json = 0

    with INPUT_FILE.open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                bad_json += 1
                continue
            if isinstance(record, dict):
                records.append(record)

    dated_records = [
        (record, parse_date(record.get("Arrival_Date")))
        for record in records
    ]
    valid_dates = [day for _, day in dated_records if day is not None]

    print("FILTERED FILE")
    print(f"Records read: {len(records):,}")
    print(f"Invalid JSON lines: {bad_json:,}")

    if not valid_dates:
        raise SystemExit("No valid dates found in the filtered file.")

    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(
            host=os.environ["DB_HOST"],
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.environ["MYSQL_USERNAME"],
            password=os.environ["MYSQL_PASSWORD"],
            database=os.environ["DB_NAME"],
            connection_timeout=20,
            ssl_disabled=False,
        )
        cursor = connection.cursor()

        # Read the existing dimension tables.
        cursor.execute("""
            SELECT location_id, district, state, market
            FROM dim_location
        """)
        locations = cursor.fetchall()

        location_index = defaultdict(list)
        location_key_by_id = {}

        for location_id, district, state, market in locations:
            key = (norm(state), norm(district), norm_market(market))
            location_index[key].append(location_id)
            location_key_by_id[location_id] = key

        # Audit-only canonical ID for dimension rows that normalize
        # to the same state, district, and market.
        canonical_id_by_location_key = {
            key: min(ids) for key, ids in location_index.items()
        }
        duplicate_location_keys = {
            key: ids
            for key, ids in location_index.items()
            if len(ids) > 1
        }

        cursor.execute("""
            SELECT commodity_id, commodity, commodity_code
            FROM dim_commodity
        """)
        commodities = cursor.fetchall()

        commodity_names = defaultdict(list)
        commodity_codes = defaultdict(list)
        commodity_name_by_id = {}

        for commodity_id, name, code in commodities:
            name_key = norm(name)
            if name_key:
                commodity_names[name_key].append(commodity_id)
            code_key = parse_code(code)
            if code_key is not None:
                commodity_codes[code_key].append(commodity_id)
            commodity_name_by_id[commodity_id] = name_key

        # Resolve each source commodity using its name and, when available,
        # its source code. Conflicting or duplicate mappings are not guessed.
        def resolve_commodity(record):
            name = norm(record.get("Commodity"))
            code = parse_code(record.get("Commodity_Code"))

            name_ids = set(commodity_names.get(name, []))
            code_ids = set(commodity_codes.get(code, [])) if code is not None else set()

            if name_ids:
                if code_ids:
                    intersection = name_ids & code_ids
                    if len(intersection) == 1:
                        return next(iter(intersection)), "ok"
                    if len(intersection) == 0:
                        return None, "name_code_conflict"
                    return None, "ambiguous"

                if len(name_ids) == 1:
                    return next(iter(name_ids)), "ok"
                return None, "ambiguous"

            # Name aliases can differ in source data. Use a unique code only
            # when it resolves to one of the explicitly targeted commodities.
            if len(code_ids) == 1:
                commodity_id = next(iter(code_ids))
                if commodity_name_by_id.get(commodity_id) in TARGET_COMMODITIES:
                    return commodity_id, "ok"

            return None, "missing"

        stats = Counter()
        missing_locations = Counter()
        missing_commodities = Counter()
        mapped = []

        for record, arrival_date in dated_records:
            location_key = (
                norm(record.get("State")),
                norm(record.get("District")),
                norm_market(record.get("Market")),
            )
            location_ids = location_index.get(location_key, [])

            if len(location_ids) == 0:
                stats["missing_location"] += 1
                missing_locations[location_key] += 1
                continue

            if len(location_ids) > 1:
                stats["duplicate_location_rows_resolved"] += 1

            commodity_id, status = resolve_commodity(record)
            if status != "ok":
                stats[f"commodity_{status}"] += 1
                missing_commodities[
                    (norm(record.get("Commodity")),
                     parse_code(record.get("Commodity_Code")))
                ] += 1
                continue

            if arrival_date is None:
                stats["invalid_date"] += 1
                continue

            prices = [
                parse_price(record.get(field))
                for field in ("Min_Price", "Max_Price", "Modal_Price")
            ]

            if any(invalid for _, invalid in prices):
                stats["invalid_price"] += 1
                continue

            (min_price, max_price, modal_price) = [
                value for value, _ in prices
            ]

            exact, logical, price_tuple = fact_keys(
                canonical_id_by_location_key[location_key],
                commodity_id,
                arrival_date,
                min_price,
                max_price,
                modal_price,
                record.get("Grade"),
                record.get("Variety"),
            )

            mapped.append((exact, logical, price_tuple))

        if not mapped:
            print("\nNo records could be mapped to fact keys.")
            print("Mapping issues:", dict(stats))
            return

        # Query only existing Maharashtra facts for the target commodities
        # and the date range represented by the filtered file.
        commodity_placeholders = ", ".join(["%s"] * len(TARGET_COMMODITIES))
        query = f"""
            SELECT
                f.location_id, f.commodity_id, f.arrival_date,
                f.min_price, f.max_price, f.modal_price,
                f.grade, f.variety
            FROM fact_daily_price AS f
            JOIN dim_location AS l ON l.location_id = f.location_id
            JOIN dim_commodity AS c ON c.commodity_id = f.commodity_id
            WHERE LOWER(TRIM(l.state)) = %s
              AND LOWER(TRIM(c.commodity)) IN ({commodity_placeholders})
              AND f.arrival_date BETWEEN %s AND %s
        """

        params = [
            "maharashtra",
            *sorted(TARGET_COMMODITIES),
            min(valid_dates),
            max(valid_dates),
        ]

        cursor.execute(query, params)

        existing_exact = set()
        existing_logical = defaultdict(set)
        existing_rows = 0

        for row in cursor:
            (location_id, commodity_id, arrival_date,
             min_price, max_price, modal_price, grade, variety) = row

            # Compare existing facts using the same canonical location
            # identity as the filtered source. No DB rows are changed.
            location_identity = location_key_by_id.get(location_id)
            if location_identity is not None:
                location_id = canonical_id_by_location_key[location_identity]

            exact, logical, price_tuple = fact_keys(
                location_id,
                commodity_id,
                arrival_date,
                min_price,
                max_price,
                modal_price,
                grade,
                variety,
            )

            existing_rows += 1
            existing_exact.add(exact)
            existing_logical[logical].add(price_tuple)

        source_exact = set()
        source_prices_by_logical = defaultdict(set)

        for exact, logical, price_tuple in mapped:
            source_exact.add(exact)
            source_prices_by_logical[logical].add(price_tuple)

        existing_logical_keys = set(existing_logical)
        exact_matches = source_exact & existing_exact

        # A different price for an already-recorded logical observation
        # needs review; do not silently append it as another observation.
        price_conflicts = {
            exact
            for exact in source_exact - existing_exact
            if exact[:3] + (exact[6], exact[7]) in existing_logical_keys
        }

        safe_new = {
            exact
            for exact in source_exact
            if (
                exact[:3] + (exact[6], exact[7])
                not in existing_logical_keys
                and len(
                    source_prices_by_logical[
                        exact[:3] + (exact[6], exact[7])
                    ]
                ) == 1
            )
        }

        source_multi_price_groups = sum(
            len(prices) > 1
            for prices in source_prices_by_logical.values()
        )

        print("\n--- AIVEN READ-ONLY AUDIT ---")
        print(f"Source records: {len(records):,}")
        print(f"Records mapped for comparison: {len(mapped):,}")
        print(f"Unique candidate fact records: {len(source_exact):,}")
        print(f"Existing fact rows examined: {existing_rows:,}")
        print(f"Exact records already in Aiven: {len(exact_matches):,}")
        print(f"Price-conflict records needing review: {len(price_conflicts):,}")
        print(f"Potentially safe new fact records: {len(safe_new):,}")
        print(f"Source logical groups with different prices: "
              f"{source_multi_price_groups:,}")
        print(f"Records with missing locations: {stats['missing_location']:,}")
        print(f"Duplicate normalized location groups: {len(duplicate_location_keys):,}")
        print(
            "Source records mapped through duplicate location groups: "
            f"{stats['duplicate_location_rows_resolved']:,}"
        )
        print(f"Unresolved ambiguous locations: {stats['ambiguous_location']:,}")
        print(f"Records with invalid dates: {stats['invalid_date']:,}")
        print(f"Records with invalid prices: {stats['invalid_price']:,}")
        print(f"Commodity mappings missing: {stats['commodity_missing']:,}")
        print(f"Commodity mappings ambiguous: {stats['commodity_ambiguous']:,}")
        print(f"Name/code conflicts: {stats['commodity_name_code_conflict']:,}")

        print("\nUnmapped location examples:")
        for key, count in missing_locations.most_common(8):
            print(f"  {key}: {count:,}")

        print("\nUnmapped commodity examples:")
        for key, count in missing_commodities.most_common(8):
            print(f"  {key}: {count:,}")

        print("\nAudit complete. No records were inserted, updated, or deleted.")

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()
