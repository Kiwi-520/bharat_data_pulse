# Bharat Data Pulse
### A real-time, queryable pipeline for India's public agricultural & climate data

---

## Why this needs to exist

India's government publishes genuinely valuable public data through **data.gov.in** — crop production by state and year, market/mandi prices, rainfall records, and more. This data is free, official, and covers information that directly affects farmers, traders, researchers, and policymakers.

But in practice, it's nearly unusable at scale:

- **Fragmented** — spread across dozens of separate datasets and APIs, each with its own quirks.
- **Inconsistent** — column names, units, and category labels vary across states and years. A crop or district might be spelled three different ways across sources.
- **Incomplete** — some states/years have missing or delayed reporting.
- **Static and hard to query** — the raw data is not built for someone to ask a plain question and get a plain answer. A farmer, journalist, or small trader can't just ask "what were onion prices in Nashik last month" — they'd have to manually dig through portals, download CSVs, and cross-reference by hand.

The information exists. The access doesn't. That gap is the actual problem Bharat Data Pulse solves.

---

## What it is

Bharat Data Pulse is an end-to-end data pipeline that:

1. **Ingests** real data on a schedule from data.gov.in APIs (starting with one domain — likely agricultural commodity prices and/or rainfall data).
2. **Cleans and normalizes** the inconsistencies — standardizing column names, units, and categories across states and years, handling missing values honestly rather than silently dropping them.
3. **Structures** the result into a properly designed relational schema, so it's genuinely queryable, not just "less messy."
4. **Monitors** itself — validating incoming data, flagging stale or broken pulls, logging failures instead of failing silently.
5. **Answers plain-English questions** through a retrieval layer on top of the clean data — "what was rice production in Maharashtra in 2023?" gets a real, grounded, sourced answer instead of requiring a manual query.

It's not a dashboard. It's not a data dump. It's a working system that turns public but practically inaccessible government data into something a non-technical person could actually use.

---

## When it's relevant / who it's for

- **Small traders and farmers** trying to check fair market prices before selling or buying.
- **Journalists and researchers** who currently spend hours manually reconciling government datasets for a single article or study.
- **Policy analysts** who need year-over-year trend visibility across states without building their own pipeline from scratch every time.
- **Anyone** who has tried to actually use data.gov.in directly and hit the wall of inconsistent formats and scattered APIs.

---

## How it works (technical shape)

**Ingestion layer** — Scheduled pulls from data.gov.in APIs (Airflow-orchestrated), landing raw, untouched data into cloud storage (AWS S3) first, so nothing is ever lost or altered before processing.

**Cleaning & transformation layer** — Python handles parsing, error handling, and reconciliation logic; SQL handles schema design, joins across sources, and the transformation queries themselves (aggregations, trends, comparisons via window functions).

**Quality & monitoring layer** — Automated checks for missing values, type mismatches, and row-count anomalies; structured logging and alerting when a scheduled pull fails or looks suspicious.

**Query layer (the differentiator)** — Data is embedded and stored in a vector database; a retrieval-augmented generation (RAG) setup lets a plain-English question pull the right structured data and turn it into a clear, grounded answer — not a hallucinated guess, but one traceable back to the actual pipeline's output.

**Delivery layer** — Packaged in Docker; exposed through a FastAPI endpoint so it's a real usable service, not just local scripts.

---

## Case Study: A Nashik onion trader

**The situation:** Rahul runs a small onion trading stall in a Nashik mandi. Prices swing week to week based on supply from other states, and he has no easy way to check whether the rate he's being offered today is fair — he either trusts word of mouth or accepts what's quoted.

**Without Bharat Data Pulse:** He'd need to know data.gov.in exists, find the right dataset among dozens, download and interpret a CSV with unfamiliar formatting, and manually compare it against other states and past months — a task most people in his position simply don't have the time, tools, or technical background to do.

**With Bharat Data Pulse:** Rahul (or someone helping him) asks, in plain language, "what were onion prices in Nashik and nearby markets over the last month?" and gets a clear, structured, sourced answer in seconds — built entirely from real government data that already existed, just never in a usable shape.

**The value demonstrated:** the pipeline doesn't invent new data or new authority — it removes the friction between real, official information and the people who actually need it.

---

## User Story

> **As** a small-scale trader, farmer, journalist, or researcher
> **I want** to ask a plain-language question about India's public agricultural or climate data
> **So that** I can get a fast, accurate, sourced answer — without needing to know which government dataset to look in, how to parse its format, or how to reconcile it across states and years.

**Acceptance criteria (what "done" looks like):**
- Data is pulled automatically on a schedule, not manually.
- A query like "what was rainfall in [state] in [year]" returns a real, correct answer traceable to the underlying pipeline data.
- If a data source is temporarily unavailable or a scheduled pull fails, the system logs and surfaces that clearly rather than returning a wrong or stale answer silently.
- The system can explain, if asked, roughly where its answer came from (which dataset, which time period).

---

## Why this is a strong interview story, specifically

Every design decision in this project has a real, explainable reason behind it — not a tutorial's reason, yours:
- *Why this data source?* Because it's real, public, and genuinely messy in ways that expose real engineering problems.
- *Why this schema?* Because the raw data's inconsistencies forced specific normalization choices you can walk through.
- *Why this orchestration approach?* Because scheduled government data has real failure modes (late updates, broken endpoints) that needed real handling.
- *Why the LLM layer?* Because raw structured data isn't accessible to the people who'd actually benefit from it — the retrieval layer is the bridge, not a bolted-on buzzword.

That's the whole point: a project you can defend end-to-end, built on a problem that's real, public, and yours to explain.
