# 🌾 Bharat Data Pulse

A real, end-to-end data engineering pipeline that turns India's open government agricultural market (mandi) price data into clean, queryable insight — ingestion, cleaning, a normalized schema, scheduled orchestration, real analytics, and an interactive dashboard.

Built from scratch, including every bug fixed along the way: a pagination offset error, a non-unique natural key discovered in real government data, a 5-hour Airflow timeout traced to row-by-row inserts at scale, and more — documented honestly, not hidden.

---

## What it does

- Ingests commodity price data (state, district, market, commodity, variety, grade, price, date)
- Cleans and type-casts genuinely inconsistent real-world data (prices arriving as both strings and numbers depending on source year, day-first date formats)
- Loads it into a normalized star-schema MySQL database (`dim_location`, `dim_commodity`, `fact_daily_price`)
- Orchestrates refresh via Apache Airflow
- Answers real decision-support questions through an analytics layer:
  - Price volatility per market (standard deviation, computed from scratch)
  - Cross-market price comparison
  - Price trend detection (rising/falling/stable)
  - Price band (min/max/modal), month-over-month change, grade/variety breakdown, top movers across commodities
- Exposes all of this through a FastAPI backend and an interactive Streamlit dashboard

---

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full layer-by-layer breakdown.

```
data.gov.in / Kaggle historical mirror
        │
        ▼
  Ingestion (ingestion/fetch.py)
        │
        ▼
  Cleaning (ingestion/clean.py)
        │
        ▼
  Storage — normalized MySQL schema (loaders/, sql/schema.sql)
        │
        ▼
  Orchestration — Airflow DAG (airflow/dags/refresh_dag.py)
        │
        ▼
  Analytics (analytics/queries.py)
        │
        ▼
  Delivery — FastAPI (app/main.py) + Streamlit dashboard (dashboard/)
```

---

## Setup

See [`docs/setup.md`](docs/setup.md) for full step-by-step instructions, including MySQL and Airflow setup.

Quick start:

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your real DB credentials
mysql -u <user> -p <database> < sql/schema.sql
python scripts/run_full_pipeline.py
uvicorn app.main:app --reload
streamlit run dashboard/streamlit_app.py
```

---

## Tech stack

Python · MySQL · Apache Airflow · FastAPI · Streamlit · pandas · Plotly

---

## Known limitations

See [`docs/known_limitations.md`](docs/known_limitations.md) for the full list. The short version:

- **Live ingestion from data.gov.in is implemented and tested, but currently unused** due to an extended outage of the source API. Historical data (through April 2026) is sourced from a Kaggle mirror of the same government dataset, with full attribution.
- This is a **batch pipeline, by design** — the source data updates daily, so a streaming architecture would be a mismatch, not an improvement.
- Dashboard defaults are anchored to the latest available data date, not "today," given the above.
- Bulk inserts (`executemany()`) and indexes on `arrival_date`/`commodity_id` were added to handle full-scale (500K+ row) loads efficiently.

---

## Testing

```bash
pytest tests/
```

Unit tests cover core data-cleaning logic. Integration tests verify database operations (including that repeated pipeline runs don't create duplicate rows). See [`tests/`](tests/) for structure.

---

## Project status

Actively developed. Core pipeline, orchestration, analytics, and dashboard are complete and tested. Planned next: a retrieval-based natural-language query layer.

---

## Author

**Disha Holmukhe** — Data Engineering | building toward a remote Data Engineering role.
