import json
import os
import re
from pathlib import Path
from collections import Counter, defaultdict

import mysql.connector
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=ROOT / ".env", override=True)

INPUT = ROOT / "filtered_data" / "maharashtra_2025_2026.jsonl"


def norm(value):
    return str(value or "").strip().casefold() or None


def norm_market(value):
    value = norm(value)
    if not value:
        return None

    parts = value.split()
    if parts and parts[-1] == "apmc":
        parts = parts[:-1]

    return "".join(ch for ch in " ".join(parts) if ch.isalnum())


def location_key(state, district, market):
    return norm(state), norm(district), norm_market(market)


source_counts = Counter()
source_examples = defaultdict(Counter)

with INPUT.open(encoding="utf-8") as file:
    for line in file:
        if not line.strip():
            continue
        record = json.loads(line)
        key = location_key(
            record.get("State"),
            record.get("District"),
            record.get("Market"),
        )
        source_counts[key] += 1
        source_examples[key][(
            record.get("State"),
            record.get("District"),
            record.get("Market"),
        )] += 1

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
    cursor.execute("""
        SELECT location_id, district, state, market
        FROM dim_location
    """)

    candidates = defaultdict(list)
    for location_id, district, state, market in cursor.fetchall():
        candidates[location_key(state, district, market)].append(
            (location_id, state, district, market)
        )

    ambiguous = {
        key: count for key, count in source_counts.items()
        if len(candidates.get(key, [])) > 1
    }
    missing = {
        key: count for key, count in source_counts.items()
        if not candidates.get(key)
    }

    print("SOURCE RECORDS WITH AMBIGUOUS LOCATIONS:", 
          f"{sum(ambiguous.values()):,}")
    print("SOURCE RECORDS WITH NO LOCATION MATCH:",
          f"{sum(missing.values()):,}")

    print("\n=== TOP AMBIGUOUS LOCATION KEYS ===")
    for key, count in sorted(
        ambiguous.items(), key=lambda item: item[1], reverse=True
    )[:12]:
        print(f"\nSource key: {key} | records: {count:,}")
        print("Source spelling examples:")
        for raw, n in source_examples[key].most_common(3):
            print(f"  {raw} ({n:,})")
        print("Aiven candidates:")
        for row in candidates[key][:10]:
            print(f"  id={row[0]} | state={row[1]} | "
                  f"district={row[2]} | market={row[3]}")

    print("\n=== TOP UNMATCHED LOCATION KEYS ===")
    for key, count in sorted(
        missing.items(), key=lambda item: item[1], reverse=True
    )[:12]:
        print(f"\nSource key: {key} | records: {count:,}")
        for raw, n in source_examples[key].most_common(3):
            print(f"  Source spelling: {raw} ({n:,})")

    print("\nRead-only diagnosis complete. No data changed.")

finally:
    if cursor is not None:
        cursor.close()
    if connection is not None and connection.is_connected():
        connection.close()
