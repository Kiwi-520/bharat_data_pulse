import sys
sys.path.insert(0, "/home/disha/Projects/bharat_data_pulse/bharat_data_pulse")

from airflow.decorators import dag, task
from datetime import datetime
# from ingestion.fetch import get_data  -> ##use once api revivies
from ingestion.file_fetch import load_data_from_file
from loaders.load_dimensions import load_dimensions
from loaders.load_facts import load_facts

DATA_FILE = "/home/disha/Projects/bharat_data_pulse/bharat_data_pulse/data1.jsonl"
@dag(
    dag_id="refresh_dag",
    start_date=datetime(2026,9,1),
    schedule="@daily",
    catchup=False,
    tags=["refresh", "fallback"]
)
def refresh_pipeline():

    @task
    def get_records_task():
        records = load_data_from_file(DATA_FILE)
        print(f"Loaded {len(records)} records")
        return records

    @task
    def load_dimensions_task(records):
        market_map, commodity_map = load_dimensions(records)
        return {
            "market_map": market_map,
            "commodity_map": commodity_map,
        }


    @task
    def load_facts_task(records, maps):
        load_facts(records, maps['market_map'], maps['commodity_map'])

    records = get_records_task()
    maps = load_dimensions_task(records)
    load_facts_task(records, maps)

refresh_pipeline()
