import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "jsonl_files"
OUTPUT_FILE = ROOT / "filtered_data" / "maharashtra_2025_2026.jsonl"

TARGET_STATE = "maharashtra"

TARGET_COMMODITIES = {
    "onion",
    "tomato",
    "potato",
    "cotton",
    "soybean",
    "soyabean",
}

START_DATE = date(2025, 1, 1)
END_DATE = date.today()


def parse_arrival_date(value):
    """Parse supported source date formats without guessing month order."""
    if not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    # ISO date or ISO timestamp, for example 2025-01-02 or
    # 2025-01-02T00:00:00.
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        pass

    # Day-first formats used by some source records.
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def main():
    source_files = sorted(SOURCE_DIR.glob("*.jsonl"))

    if not source_files:
        raise SystemExit(
            f"No JSONL files found in {SOURCE_DIR}. "
            "Check the location of your source files."
        )

    stats = Counter()
    commodity_counts = Counter()
    exact_records_seen = set()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"Source directory: {SOURCE_DIR}")
    print(f"Output file:      {OUTPUT_FILE}")
    print(f"Date range:       {START_DATE} to {END_DATE}")
    print("Processing files one line at a time...\n")

    with OUTPUT_FILE.open("w", encoding="utf-8") as output:
        for source_file in source_files:
            file_matches = 0
            stats["files_processed"] += 1

            with source_file.open("r", encoding="utf-8") as source:
                for line_number, line in enumerate(source, start=1):
                    if not line.strip():
                        continue

                    stats["lines_read"] += 1

                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        stats["invalid_json"] += 1
                        continue

                    if not isinstance(record, dict):
                        stats["invalid_records"] += 1
                        continue

                    state = str(record.get("State") or "").strip().casefold()
                    commodity = str(
                        record.get("Commodity") or ""
                    ).strip().casefold()

                    if state != TARGET_STATE:
                        continue

                    if commodity not in TARGET_COMMODITIES:
                        continue

                    stats["state_commodity_matches"] += 1

                    arrival_date = parse_arrival_date(
                        record.get("Arrival_Date")
                    )

                    if arrival_date is None:
                        stats["invalid_matching_dates"] += 1
                        continue

                    if not START_DATE <= arrival_date <= END_DATE:
                        continue

                    stats["date_matches"] += 1

                    # Remove exact duplicate JSON objects across source files.
                    fingerprint = json.dumps(
                        record,
                        sort_keys=True,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )

                    if fingerprint in exact_records_seen:
                        stats["exact_duplicates_skipped"] += 1
                        continue

                    exact_records_seen.add(fingerprint)

                    output.write(
                        json.dumps(
                            record,
                            ensure_ascii=False,
                            separators=(",", ":"),
                        )
                        + "\n"
                    )

                    stats["rows_written"] += 1
                    commodity_counts[str(record.get("Commodity"))] += 1
                    file_matches += 1

            print(f"{source_file.name}: {file_matches:,} unique matching rows")

    print("\n--- FILTER SUMMARY ---")
    print(f"Files processed:             {stats['files_processed']:,}")
    print(f"Non-empty lines read:        {stats['lines_read']:,}")
    print(f"Invalid JSON lines:          {stats['invalid_json']:,}")
    print(f"Invalid JSON records:        {stats['invalid_records']:,}")
    print(f"State + commodity matches:   {stats['state_commodity_matches']:,}")
    print(f"Invalid matching dates:      {stats['invalid_matching_dates']:,}")
    print(f"Rows within date range:      {stats['date_matches']:,}")
    print(f"Exact duplicates skipped:    {stats['exact_duplicates_skipped']:,}")
    print(f"Unique rows written:         {stats['rows_written']:,}")

    print("\nRows by commodity:")
    for commodity, count in sorted(commodity_counts.items()):
        print(f"  {commodity}: {count:,}")

    print(f"\nOutput size: {OUTPUT_FILE.stat().st_size:,} bytes")
    print("Aiven has NOT been modified.")


if __name__ == "__main__":
    main()