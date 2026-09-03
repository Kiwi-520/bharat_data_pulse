import json
from collections import Counter
# from main import total

TARGET_DATE = "01/02/2026"   # change this to whichever day you're checking
EXPECTED_TOTAL = 31          # the "total" the API reported for that day

records_for_date = []

with open("data1.jsonl", "r") as f:
    for line in f:
        record = json.loads(line)
        if record["Arrival_Date"] == TARGET_DATE:
            records_for_date.append(record)

print(f"Records found for {TARGET_DATE}: {len(records_for_date)}")
print(f"Expected total: {EXPECTED_TOTAL}")

if len(records_for_date) == EXPECTED_TOTAL:
    print("✅ Count matches — nothing missing.")
elif len(records_for_date) < EXPECTED_TOTAL:
    print("⚠️ Fewer records than expected — pagination may have stopped early.")
else:
    print("⚠️ More records than expected — check for duplicates below.")

# Duplicate check — same Market + Variety + Grade appearing more than once
signatures = [
    (r["Market"], r["Variety"], r["Grade"]) for r in records_for_date
]
counts = Counter(signatures)
duplicates = {sig: c for sig, c in counts.items() if c > 1}

if duplicates:
    print(f"\n⚠️ Found {len(duplicates)} duplicate signature(s):")
    for sig, c in duplicates.items():
        print(f"  {sig} appears {c} times")
else:
    print("\n✅ No duplicates found for this date.")