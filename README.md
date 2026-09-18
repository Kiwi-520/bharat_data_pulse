# Bharat Data Pulse 📊

**A data pipeline turning India's open government commodity price data into a clean, queryable dataset.**

---

## The Problem

India's government publishes genuinely valuable open data through [data.gov.in](https://data.gov.in) — including daily agricultural commodity prices across thousands of markets nationwide. In practice, this data is hard to actually use: it's accessed through an API with real inconsistencies (field types that vary across years, day-first date formats, incomplete documentation), and requires technical skill to pull and structure meaningfully.

This project builds a real, working pipeline that pulls this data, verifies its own correctness, and turns it into a properly structured, queryable dataset — using live government data, not a pre-cleaned sample.

---

## What's Built So Far

**Ingestion**
- Pulls live daily commodity price data from the data.gov.in API (Variety-wise Daily Market Prices / Agmarknet dataset), scoped to Maharashtra, onion prices.
- Correct pagination implemented and verified — handles the API's `total`/`offset`/`limit` behavior properly, including a real bug found and fixed where the offset was updating one request too late.
- Data saved in JSON Lines format, one record per line.
- Verified against the source: record counts confirmed to match the API's reported totals for every date pulled, with a separate check confirming no unintended duplicate entries within a given day.

**Schema Design**
- Designed a normalized relational schema: `dim_location` (market/district/state), `dim_commodity` (commodity/code), and `fact_daily_price` (the actual price records, linked to both dimension tables via foreign keys).
- Discovered and handled a real data nuance: the same market, commodity, and date can legitimately have multiple distinct price entries — so the fact table uses a surrogate primary key rather than forcing false uniqueness onto natural columns.

**Data Loading**
- Built Python logic to deduplicate and load dimension data (markets, commodities) into MySQL, using a "find or create" pattern to avoid duplicate rows.
- Built the fact table loader, including explicit type casting to handle the source API's inconsistent price formatting (values arrive as either strings or numbers depending on the year) and explicit date parsing (source dates are day-first, not the database's expected format).
- Full dataset loaded and verified: **475 records**, row-for-row matched between the source file and the live MySQL table.

---

## Tech Stack

- **Python** — ingestion, data cleaning, type/date handling
- **MySQL** — normalized relational storage
- **data.gov.in API** — live government data source

---

## Data Source

- **Portal:** [data.gov.in](https://data.gov.in)
- **Dataset:** Variety-wise Daily Market Prices Data of Commodity (Agmarknet)
- **Current scope:** Maharashtra state, onion prices

---

## Setup

```bash
# Clone the repo
git clone https://github.com/Kiwi-520/bharat_data_pulse.git
cd bharat_data_pulse

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Fill in your data.gov.in API key and MySQL credentials

# Run ingestion
python main.py

# Load into MySQL
python load_to_mysql.py
python load_fact.py
```

---

## Why This Project

Built as a hands-on Data Engineering project using real, live, public data rather than a pre-cleaned dataset. Every design decision here — schema structure, type handling, verification approach — is deliberate and documented; see [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full reasoning.

---

## Author

**Disha Holmukhe**
[LinkedIn](https://www.linkedin.com/in/dishaholmukhe)

---
