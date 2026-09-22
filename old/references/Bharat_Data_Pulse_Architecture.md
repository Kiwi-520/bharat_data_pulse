# Bharat Data Pulse — Technical Architecture

### Dataset: Variety-wise Daily Market Prices of Commodities (data.gov.in / Mandi Prices)

---

## 1. Layers Overview

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 5 — Delivery (FastAPI + Docker)                   │
├─────────────────────────────────────────────────────────┤
│  LAYER 4 — Query / Intelligence (Embeddings + Vector DB) │
├─────────────────────────────────────────────────────────┤
│  LAYER 3 — Quality & Monitoring (Checks + Logging)       │
├─────────────────────────────────────────────────────────┤
│  LAYER 2 — Transform (Clean, Normalize, Model in SQL)    │
├─────────────────────────────────────────────────────────┤
│  LAYER 1 — Ingestion (Airflow + Python, scheduled pulls) │
├─────────────────────────────────────────────────────────┤
│  LAYER 0 — Raw Storage (AWS S3)                          │
└─────────────────────────────────────────────────────────┘
        ↑ Source: data.gov.in Mandi Price API
```

---

## 2. Function of Each Layer

### Layer 0 — Raw Storage (AWS S3)
**Function:** The permanent, untouched landing zone for every API pull, exactly as received.
**Why it exists:** If a later cleaning step has a bug, you never lose the original — you can always reprocess from raw. This is standard real-world DE practice, not optional polish.
**What lives here:** Timestamped raw JSON/CSV responses from the Mandi Price API, one file per pull.

### Layer 1 — Ingestion (Airflow + Python)
**Function:** Pulls fresh data from the data.gov.in API on a schedule (e.g., daily, matching the dataset's own update cadence), and writes it to Layer 0.
**Why it exists:** Prices change daily — a one-time download goes stale immediately. This layer is what makes the project a living pipeline instead of a snapshot.
**What lives here:** An Airflow DAG with a scheduled task; Python code handling the API call, authentication (your API key), pagination if needed, and failure/retry logic when the API times out or returns malformed data.

### Layer 2 — Transform (Python + SQL)
**Function:** Takes raw data from Layer 0 and turns it into clean, structured, queryable tables.
**Why it exists:** Raw mandi data will have inconsistent commodity/variety naming, missing fields, and possible duplicate entries across states/markets — this layer is where that mess actually gets resolved.
**What lives here:** Python transformation scripts (parsing, normalizing names/units) and a SQL schema — likely a `markets` table, a `commodities` table, and a `daily_prices` fact table linking them, designed by you rather than auto-generated.

### Layer 3 — Quality & Monitoring
**Function:** Validates that each day's ingested and transformed data is actually trustworthy before it's used downstream.
**Why it exists:** A pipeline that silently accepts bad data (a broken API response, a sudden all-null day) is worse than one that has no data — this layer is what makes it production-minded rather than a script.
**What lives here:** Checks for null rates, unexpected row-count drops, duplicate entries; structured logs recording each run's outcome; basic alerting if a pull fails or looks anomalous.

### Layer 4 — Query / Intelligence (Embeddings + Vector DB + RAG)
**Function:** Lets someone ask a plain-English question ("what's the onion price in Nashik today?") and get an answer grounded in Layer 2's real structured data.
**Why it exists:** This is the differentiator — it's what turns a clean dataset into something a non-technical person could actually use, and it's your LLM/GenAI skill layer.
**What lives here:** An embedding step over relevant structured summaries, a vector store (Chroma or FAISS) for retrieval, and a retrieval-augmented generation step that converts the retrieved data into a clear natural-language answer.

### Layer 5 — Delivery (FastAPI + Docker)
**Function:** Exposes the whole system as a real, runnable service — an endpoint someone could actually query.
**Why it exists:** A project that only runs as disconnected local scripts isn't a system. This layer is what makes it demoable and deployable.
**What lives here:** A FastAPI app with an endpoint (e.g., `/ask`) that takes a question and returns an answer; a Dockerfile so the whole thing runs identically anywhere.

---

## 3. Usage (what a user actually does)

1. A user (or you, in a demo) sends a question to the FastAPI endpoint — e.g., `POST /ask {"question": "what was the onion price in Nashik last week?"}`.
2. The system retrieves the relevant structured data via the query layer and returns a clear, sourced answer.
3. Behind the scenes, none of this depends on the user knowing the pipeline exists — they just get a fast, correct answer to a real question about real government data.

---

## 4. Connection Between Layers

- **Layer 1 → Layer 0:** Airflow triggers Python ingestion code, which writes raw output directly into S3.
- **Layer 0 → Layer 2:** Transform scripts read raw files from S3, not from the live API — this decouples cleaning logic from ingestion timing.
- **Layer 2 → Layer 3:** Every transform run is checked before being considered "final" — quality checks sit right after transformation, gating what counts as trustworthy.
- **Layer 2/3 → Layer 4:** Only validated, clean structured data gets embedded and indexed — the intelligence layer never touches raw or unvalidated data.
- **Layer 4 → Layer 5:** FastAPI calls into the retrieval/RAG logic directly when a request comes in; Docker packages all layers together so the connections work identically in any environment.

---

## 5. Flow (end-to-end, one pull cycle)

```
data.gov.in API
      │
      ▼
[Airflow DAG triggers on schedule]
      │
      ▼
[Python ingestion script calls API] ──(failure?)──▶ [Log + alert, retry]
      │
      ▼
[Raw response saved to S3, timestamped]
      │
      ▼
[Transform script reads raw file]
      │
      ▼
[Clean, normalize, structure into SQL tables]
      │
      ▼
[Quality checks run] ──(fails?)──▶ [Flag run as bad, don't promote to "clean"]
      │
      ▼
[Validated data embedded + indexed in vector store]
      │
      ▼
[Ready for queries via FastAPI /ask endpoint]
```

---

## 6. Sequence (a single user query, step by step)

1. User sends a question to `POST /ask` via FastAPI.
2. FastAPI passes the question to the query layer.
3. The question is embedded (turned into a vector).
4. The vector store retrieves the most relevant structured data chunks (e.g., recent price records matching the commodity/location mentioned).
5. Retrieved data + the original question are passed to the LLM to generate a grounded natural-language answer.
6. FastAPI returns the answer as the API response.
7. (Optional, good practice) The interaction is logged, so you can later see what kinds of questions are actually being asked.

---

## Why this structure matters for interviews

Each layer maps to a specific, real decision you can defend: why raw storage exists separately from transformed data, why quality checks gate promotion instead of just logging silently, why the intelligence layer only touches validated data. That's the actual signal of "systems thinking" interviewers are listening for — not that every layer exists, but that you can explain *why* each one exists and what breaks if you removed it.
