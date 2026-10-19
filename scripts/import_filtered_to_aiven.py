import argparse
import os
import json
from collections import Counter, defaultdict
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

from audit_filtered_import import (
    ROOT, INPUT_FILE, TARGET_COMMODITIES,
    norm, norm_market, parse_date, parse_code, parse_price, fact_keys,
)


def main():
    parser = argparse.ArgumentParser(
        description="Idempotent, guarded import into Aiven MySQL."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Insert approved new records after interactive confirmation.",
    )
    args = parser.parse_args()

    load_dotenv(dotenv_path=ROOT / ".env", override=True)

    if not INPUT_FILE.exists():
        raise SystemExit(f"Filtered input not found: {INPUT_FILE}")

    records = []
    with INPUT_FILE.open(encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            record = json.loads(line)
            if isinstance(record, dict):
                records.append(record)

    if not records:
        raise SystemExit("Input file contains no records.")

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

        # Load locations and establish a consistent audit-only ID for
        # dimension entries that normalize to the same location.
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

        canonical_id = {
            key: min(ids) for key, ids in location_index.items()
        }

        # Load commodity mappings.
        cursor.execute("""
            SELECT commodity_id, commodity, commodity_code
            FROM dim_commodity
        """)
        commodities = cursor.fetchall()

        names = defaultdict(set)
        codes = defaultdict(set)
        names_by_id = {}

        for cid, name, code in commodities:
            if norm(name):
                names[norm(name)].add(cid)
            parsed_code = parse_code(code)
            if parsed_code is not None:
                codes[parsed_code].add(cid)
            names_by_id[cid] = norm(name)

        def resolve_commodity(record):
            name = norm(record.get("Commodity"))
            code = parse_code(record.get("Commodity_Code"))

            name_ids = names.get(name, set())
            code_ids = codes.get(code, set()) if code is not None else set()

            if name_ids:
                if code_ids:
                    matches = name_ids & code_ids
                    if len(matches) == 1:
                        return next(iter(matches))
                    return None
                if len(name_ids) == 1:
                    return next(iter(name_ids))
                return None

            if len(code_ids) == 1:
                cid = next(iter(code_ids))
                if names_by_id.get(cid) in TARGET_COMMODITIES:
                    return cid

            return None

        source_exact = set()
        source_prices = defaultdict(set)
        payloads = {}
        missing_locations = 0
        rejected = Counter()
        valid_dates = []

        for record in records:
            if norm(record.get("State")) != "maharashtra":
                continue
            if norm(record.get("Commodity")) not in TARGET_COMMODITIES:
                continue

            arrival_date = parse_date(record.get("Arrival_Date"))
            if arrival_date is None:
                rejected["invalid_date"] += 1
                continue

            valid_dates.append(arrival_date)

            source_key = (
                norm(record.get("State")),
                norm(record.get("District")),
                norm_market(record.get("Market")),
            )

            if source_key not in canonical_id:
                missing_locations += 1
                continue

            cid = resolve_commodity(record)
            if cid is None:
                rejected["unmapped_commodity"] += 1
                continue

            price_results = [
                parse_price(record.get(field))
                for field in ("Min_Price", "Max_Price", "Modal_Price")
            ]

            if any(invalid for _, invalid in price_results):
                rejected["invalid_price"] += 1
                continue

            min_price, max_price, modal_price = [
                value for value, _ in price_results
            ]
            loc_id = canonical_id[source_key]

            exact, logical, prices = fact_keys(
                loc_id,
                cid,
                arrival_date,
                min_price,
                max_price,
                modal_price,
                record.get("Grade"),
                record.get("Variety"),
            )

            source_exact.add(exact)
            source_prices[logical].add(prices)

            # Save the real database values for later insertion.
            payloads[exact] = (
                loc_id, cid, min_price, max_price, modal_price,
                record.get("Grade"), record.get("Variety"), arrival_date,
            )

        if not valid_dates or not source_exact:
            raise SystemExit("No valid mapped records available to import.")

        # Fetch existing fact rows in the relevant period.
        placeholders = ", ".join(["%s"] * len(TARGET_COMMODITIES))
        cursor.execute(
            f"""
            SELECT
                f.location_id, f.commodity_id, f.arrival_date,
                f.min_price, f.max_price, f.modal_price,
                f.grade, f.variety
            FROM fact_daily_price f
            JOIN dim_location l ON l.location_id = f.location_id
            JOIN dim_commodity c ON c.commodity_id = f.commodity_id
            WHERE LOWER(TRIM(l.state)) = %s
              AND LOWER(TRIM(c.commodity)) IN ({placeholders})
              AND f.arrival_date BETWEEN %s AND %s
            """,
            (
                "maharashtra",
                *sorted(TARGET_COMMODITIES),
                min(valid_dates),
                max(valid_dates),
            ),
        )

        existing_exact = set()
        existing_logical = set()

        for row in cursor:
            (
                loc_id, cid, day, min_price, max_price, modal_price,
                grade, variety,
            ) = row

            # Apply the same location canonicalization to existing rows.
            location_key = location_key_by_id.get(loc_id)
            if location_key in canonical_id:
                loc_id = canonical_id[location_key]

            exact, logical, _ = fact_keys(
                loc_id, cid, day, min_price, max_price, modal_price,
                grade, variety,
            )
            existing_exact.add(exact)
            existing_logical.add(logical)

        already_present = source_exact & existing_exact

        conflicts = {
            exact for exact in source_exact - existing_exact
            if (
                exact[0], exact[1], exact[2], exact[6], exact[7]
            ) in existing_logical
        }

        multi_price_groups = {
            key for key, values in source_prices.items()
            if len(values) > 1
        }

        safe_new = {
            exact for exact in source_exact
            if (
                (exact[0], exact[1], exact[2], exact[6], exact[7])
                not in existing_logical
                and len(source_prices[
                    (exact[0], exact[1], exact[2], exact[6], exact[7])
                ]) == 1
            )
        }

        print("\n--- IMPORT PREFLIGHT ---")
        print(f"Filtered file records: {len(records):,}")
        print(f"Unique mapped facts: {len(source_exact):,}")
        print(f"Exact matches already in Aiven: {len(already_present):,}")
        print(f"Price conflicts requiring review: {len(conflicts):,}")
        print(f"Source groups with multiple prices: {len(multi_price_groups):,}")
        print(f"Unmatched locations skipped: {missing_locations:,}")
        print(f"Other rejected records: {dict(rejected)}")
        print(f"Potential inserts: {len(safe_new):,}")

        cursor.execute("""
            SELECT DATA_LENGTH, INDEX_LENGTH
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'fact_daily_price'
        """, (os.environ["DB_NAME"],))
        size_row = cursor.fetchone()
        if size_row:
            size_mb = sum(value or 0 for value in size_row) / (1024 ** 2)
            print(f"Current fact table + indexes: approximately {size_mb:.2f} MiB")

        # Never write records with unresolved conflicts.
        if conflicts or multi_price_groups:
            print("Blocked: resolve price conflicts before importing.")
            return

        if not args.apply:
            print("\nDRY RUN ONLY: Aiven was not changed.")
            print("Inspect this result, then rerun with --apply to write.")
            return

        if not safe_new:
            print("Nothing new to import.")
            return

        confirmation = f"IMPORT {len(safe_new)}"
        print(f"\nThis will INSERT fact rows into {os.environ['DB_NAME']}.")
        print("It will not delete or update existing records.")
        if input(f"Type {confirmation} to confirm: ").strip() != confirmation:
            print("Cancelled. No records inserted.")
            return

        insert_sql = """
            INSERT INTO fact_daily_price
                (location_id, commodity_id, min_price, max_price,
                 modal_price, grade, variety, arrival_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        ordered_keys = sorted(safe_new, key=repr)
        inserted = 0

        for start in range(0, len(ordered_keys), 500):
            batch_keys = ordered_keys[start:start + 500]
            batch = [payloads[key] for key in batch_keys]

            try:
                cursor.executemany(insert_sql, batch)
                connection.commit()
                inserted += len(batch)
                print(f"Committed {inserted:,} / {len(ordered_keys):,}")
            except Exception:
                connection.rollback()
                print(
                    "Batch failed. Earlier committed batches, if any, "
                    "remain in Aiven. Rerun the preflight before retrying."
                )
                raise

        print(f"\nImport complete. Rows inserted: {inserted:,}")
        print("Unmatched locations were left out for later review.")

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()
