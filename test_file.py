import json
from collections import Counter, defaultdict

EXPECTED_TOTALS = {
    "01/02/2026": None,  # fill in per-date totals if you have them, or leave None to skip that check
    "02/02/2026": None,
    "03/02/2026": None,
    # ... add the rest of your dates here
}

records_by_date = defaultdict(list)

with open("data1.jsonl", "r") as f:
    for line in f:
        record = json.loads(line)
        records_by_date[record["Arrival_Date"]].append(record)

for target_date, records in sorted(records_by_date.items()):
    print(f"\n--- {target_date} ---")
    print(f"Records found: {len(records)}")

    expected = EXPECTED_TOTALS.get(target_date)
    if expected is not None:
        status = "✅ matches" if len(records) == expected else "⚠️ MISMATCH"
        print(f"Expected: {expected} — {status}")

    # duplicate check, now scoped to just this one date
    signatures = [(r["Market"], r["Variety"], r["Grade"]) for r in records]
    counts = Counter(signatures)
    duplicates = {sig: c for sig, c in counts.items() if c > 1}

    if duplicates:
        print(f"⚠️ {len(duplicates)} duplicate(s) WITHIN this date:")
        for sig, c in duplicates.items():
            print(f"  {sig} appears {c} times")
    else:
        print("✅ No duplicates within this date.")