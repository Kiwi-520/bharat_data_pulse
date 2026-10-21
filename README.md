# 🌾 Bharat Data Pulse

**Live demo:** [Demo link](https://bharatdatapulse-dishaholmukhe.streamlit.app/)
**Pipeline status:** ![Pipeline](https://github.com/Kiwi-520/bharat-data-pulse/actions/workflows/daily_pipeline.yml/badge.svg)

An end-to-end data engineering pipeline that turns India's open government 
agricultural market (mandi) price data into real, queryable insight from 
paginated API ingestion through a normalized schema, scheduled cloud 
orchestration, and an interactive dashboard.

---

## What it does

- Ingests commodity price data from data.gov.in via a paginated REST API, 
  handling real-world messiness: prices arriving as both strings and numbers 
  across years, day-first date formats, and non-unique natural keys in the source
- Loads records into a normalized star schema in a cloud MySQL database 
  (dim_location, dim_commodity, fact_daily_price) using batched bulk inserts 
  with in-memory deduplication dropping load time from a 5-hour timeout 
  (row-by-row) to under 10 minutes for 500K+ records
- Runs a daily GitHub Actions workflow that checks API health, finds only the 
  missing dates using a watermark, fetches new data, and exits gracefully when 
  the API is unavailable — no false failures
- Serves eight analytics functions (price volatility, trend detection, 
  cross-market comparison, grade/variety breakdown, top movers) through a 
  FastAPI backend
- Displays everything on an interactive Streamlit dashboard with commodity 
  selectors, date pickers, Plotly charts, and an India distribution map

---

## Screenshots

[embed your 3 screenshots here]
<img width="1885" height="823" alt="image" src="https://github.com/user-attachments/assets/9c555ca7-91dd-4502-9819-84cb83ad5fc7" />

---

## Architecture

<img width="372" height="596" alt="image" src="https://github.com/user-attachments/assets/3bd71799-e25b-465a-b64e-d274e5654978" />


## Stack

Python · MySQL (Aiven) · GitHub Actions · FastAPI · Streamlit · pandas · Plotly

---

## Key engineering decisions

| Decision | Why |
|---|---|
| Batch pipeline, not streaming | Source data updates daily — streaming would solve a problem that doesn't exist |
| Star schema with surrogate key | market + commodity + date is not unique in the source; natural key assumption was wrong |
| Watermark-based incremental load | Prevents re-fetching data already in MySQL; catches up day by day when API resumes |
| Bulk inserts with in-memory dedup | Per-row inserts caused a 5-hour Airflow timeout at 500K rows |
| Graceful API health check | Source API has extended outages; pipeline must not fail loudly when nothing is wrong |

---

## Known limitations

- **Data current as of April 2026.** The source API (data.gov.in Agmarknet) has 
  been unavailable since mid-2026. Historical data is sourced from a Kaggle 
  mirror of the same government dataset, with full attribution. The pipeline 
  resumes live ingestion automatically when the API is restored.
- Batch pipeline by design — daily cadence matches the source update frequency
- Dashboard is read-only; no user authentication

---

## Local setup

```bash
git clone https://github.com/Kiwi-520/bharat-data-pulse
cd bharat-data-pulse
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your DB credentials
mysql -u user -p dbname < sql/schema.sql
python scripts/run_pipeline.py
streamlit run home.py
```

---

## Data source

Variety-wise Daily Market Prices of Commodities — Government of India,  
Ministry of Agriculture and Farmers Welfare, via data.gov.in (Agmarknet).  
Historical data via Kaggle mirror. Licensed under Government Open Data License — India.
