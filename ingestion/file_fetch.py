import json
import csv
import os


def load_data_from_file(path="data1.jsonl"):
    records = []
    with open(path,"r") as f:
        for line in f:
            records.append(json.loads(line))
    return records


# -----------------------------------------------------------------

# ============================================================
# HISTORICAL CSV INGESTION
# ============================================================

def load_csv_in_batches(file_path, batch_size=50000):
    """
    Reads a huge CSV file without loading the entire file into RAM.

    Yields one batch of records at a time.

    Example:

        for batch in load_csv_in_batches("2001.csv", 50000):
            # process batch
    """

    batch = []

    with open(
        file_path,
        "r",
        encoding="utf-8",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            batch.append(dict(row))

            if len(batch) == batch_size:

                yield batch

                batch = []

        # Final batch
        if batch:

            yield batch


# ============================================================
# MULTIPLE CSV FILES
# ============================================================

def load_csv_files_in_batches(
    folder_path,
    batch_size=50000
):
    """
    Reads all CSV files in a folder.

    Each CSV is processed as a stream of 50,000-record batches.

    Example:

        for batch in load_csv_files_in_batches(
            "/path/to/data",
            50000
        ):
            # process batch
    """

    csv_files = sorted(
        file
        for file in os.listdir(folder_path)
        if file.lower().endswith(".csv")
    )

    for file_name in csv_files:

        file_path = os.path.join(
            folder_path,
            file_name
        )

        print(f"Starting file: {file_name}")

        for batch in load_csv_in_batches(
            file_path,
            batch_size
        ):

            print(
                f"Loaded batch of {len(batch)} "
                f"records from {file_name}"
            )

            yield batch