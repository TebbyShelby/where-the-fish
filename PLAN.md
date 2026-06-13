# Where The Fish — Project Plan

> Fishing intelligence pipeline. End-to-end data engineering with CI/CD.
>
> _"WTF should I fish today?"_ 🎣

---

## 1. Project Overview

**What it does:** Ingest weather, marine, and tide data for Malaysian coastal locations → transform into a "fishing score" → surface on a dashboard so you know when and where to fish.

**Title:** Where The Fish (WTF)

**Output:** A functional data pipeline you can actually use for your hobby.

---

## 2. Proposed Stack

| Layer | Tool | Why |
|-------|------|-----|
| **Language** | Python 3.12+ | Your strength, industry standard for DE |
| **Orchestration** | **Prefect** or **Dagster** | Move from option-based Airflow to modern Python-native |
| **Storage** | **DuckDB** + Parquet | Local-first, no infra overhead. DuckDB is trendy in DE right now |
| **Transform** | **dbt-core** + **duckdb adapter** | SQL transformations, testing, docs — industry gold standard |
| **Ingestion** | **httpx** (async) + **Pydantic** | Clean API calls with schema validation |
| **Quality** | **Great Expectations** or **dbt tests** | Data contracts, validation thresholds |
| **CI/CD** | **GitHub Actions** | Already using it, free tier sufficient |
| **Containers** | **Docker Compose** | Reproducible environments for dev/staging/prod |
| **Dashboard** | **Streamlit** or **Evidence** | Lightweight, Python (Streamlit) or SQL/MDX (Evidence) |

### Key Decisions to Make

| Decision | Option A | Option B | My Pick |
|----------|----------|----------|---------|
| **Orchestrator** | Prefect | Dagster | Prefect (simpler to start) |
| **Dashboard** | Streamlit | Evidence.dev | Streamlit (you know Python) |
| **Data Quality** | Great Expectations | dbt tests only | dbt tests first, GE optional later |
| **Container** | Docker only | Docker Compose | Docker Compose (multi-service) |

### Why Not Airflow?

Airflow is the classic choice but heavier. For a single-person project, Prefect gives you the same DAG concepts with way less boilerplate. Dagster is also great but has a steeper initial learning curve.

---

## 3. Data Sources Detail

### Source 1: data.gov.my — Weather Forecast
- **URL:** `https://api.data.gov.my/weather/forecast`
- **Auth:** None
- **Frequency:** Updated daily
- **Data:** 7-day forecast for Malaysian locations (temp, rain in BM)
- **Key fields:** `morning_forecast`, `afternoon_forecast`, `night_forecast`, `min/max_temp`

### Source 2: Open-Meteo Marine API — Waves & Swell
- **URL:** `https://marine-api.open-meteo.com/v1/marine`
- **Auth:** None (free, no key needed)
- **Data:** Wave height/direction/period, swell, sea surface temp, ocean currents
- **Covers:** Global (use lat/lon of your fishing spots)

### Source 3: TideCheck API — Tides & Solunar
- **URL:** `https://tidecheck.com/api/station/{id}/tides`
- **Auth:** Free API key (50 req/day)
- **Data:** High/low tide times, heights, solunar fishing rating (1-5⭐), moon phase, sunrise/sunset
- **Covers:** 20,000+ stations worldwide, including Malaysia

### Source 4: Manual Fishing Log (optional)
- Track your own catches: date, location, species, success (yes/no)
- Turns the pipeline from "external data only" to **ML-lite** — correlate conditions with actual catch rates

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DATA SOURCES                          │
│  data.gov.my    Open-Meteo    TideCheck    Fishing Log   │
│  (weather)      (waves)       (tides)      (manual/csv)  │
└────────┬──────────┬─────────────┬──────────────┬─────────┘
         │          │             │              │
         ▼          ▼             ▼              ▼
┌─────────────────────────────────────────────────────────┐
│                    INGESTION (Prefect)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ weather  │ │  marine  │ │  tide    │ │  log     │    │
│  │ _fetch   │ │  _fetch  │ │  _fetch  │ │  _load   │    │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘    │
│       │            │            │            │           │
└───────┴────────────┴────────────┴────────────┴───────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────┐
│              STORAGE — DuckDB (Medallion)                 │
│                                                          │
│   bronze.weather_raw      silver.weather_clean            │
│   bronze.marine_raw       silver.marine_enriched          │
│   bronze.tide_raw         silver.tide_enriched            │
│   bronze.fishing_log      silver.fishing_log_clean        │
│                                                          │
│                   gold.fishing_score                      │
│                   gold.location_summary                   │
│                   gold.best_fishing_times                 │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              TRANSFORM — dbt                              │
│  models/staging/   → clean raw data                      │
│  models/marts/     → join + aggregate + score             │
│  tests/            → schema & data tests                  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              DASHBOARD — Streamlit                        │
│                                                          │
│   "Should I fish today?"                                 │
│   ┌─────────────────────────────────┐                   │
│   │  🌊 Kertih ★★★★☆               │                   │
│   │  Temp: 29°C | Waves: 0.8m      │                   │
│   │  Tide: High 06:30 | Low 12:45   │                   │
│   │  [🐟 Best time: 06:00-08:00]    │                   │
│   └─────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

---

## 5. CI/CD & Environments

### Three Environments

| Env | Data | Trigger | Purpose |
|-----|------|---------|---------|
| **dev** | Subset (1-2 locations) | Local `docker compose up` | Development, experiments |
| **staging** | Full data (all locations) | GitHub: push to `staging` branch | Pre-merge validation |
| **prod** | Full data + scheduled runs | GitHub: merge to `main` | Deployed pipeline |

### CI/CD Flow

```
developer (local)
    │ git push feature-branch
    ▼
GitHub Actions
    ├── lint (ruff)
    ├── test (pytest)
    ├── dbt build (staging DuckDB)
    │   └── dbt test
    ├── great_expectations check (optional)
    └── if all pass → merge to main
         │
         ▼
GitHub Actions (main branch)
    ├── deploy to prod (docker compose)
    └── schedule: daily 06:00 run
```

### GitHub Actions Structure

```
.github/workflows/
├── ci.yml           # Lint + test + dbt build on PR
├── deploy.yml       # Deploy on merge to main
└── schedule.yml     # Daily pipeline run (scheduled)
```

---

## 6. Project Folder Structure

```
fishsense/
├── README.md
├── docker-compose.yml          # Dev/staging/local
├── Dockerfile                  # If needed
├── .env.example
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── deploy.yml
│       └── schedule.yml
├── src/
│   ├── ingest/
│   │   ├── base.py             # Base fetch class
│   │   ├── weather.py          # data.gov.my
│   │   ├── marine.py           # Open-Meteo
│   │   ├── tide.py             # TideCheck
│   │   └── fishing_log.py      # CSV ingest
│   ├── models/
│   │   ├── weather.py          # Pydantic models
│   │   ├── marine.py
│   │   └── tide.py
│   └── dashboard/
│       ├── app.py              # Streamlit app
│       └── components/         # UI components
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/
│   │   ├── staging/
│   │   │   ├── stg_weather.sql
│   │   │   ├── stg_marine.sql
│   │   │   └── stg_tide.sql
│   │   └── marts/
│   │       ├── fishing_score.sql
│   │       └── location_summary.sql
│   └── tests/
│       ├── weather_not_null.sql
│       └── tide_height_positive.sql
├── tests/
│   ├── test_ingest.py
│   └── test_transform.py
└── data/                       # Local DuckDB files (gitignored)
    ├── dev/
    ├── staging/
    └── prod/
```

---

## 7. Data Model (Gold Layer)

### `gold.fishing_score`

| Column | Type | Source |
|--------|------|--------|
| location | TEXT | All |
| date | DATE | All |
| solunar_rating | INT (1-5) | TideCheck ⭐ |
| wave_height_max | FLOAT | Open-Meteo |
| sea_temp | FLOAT | Open-Meteo |
| tide_phase | TEXT (high/low) | TideCheck |
| best_fishing_time | TEXT (time window) | Derived from tide + solunar |
| wind_condition | TEXT | data.gov.my |
| overall_score | INT (0-100) | Composite of above factors |

### Scoring Logic (v1 — simple)

```
overall_score = 
   solunar_rating * 25            (max 100)  
   + wave_penalty (-10 if >1.5m)
   + tide_bonus (+10 if high tide during dawn/dusk)
   + temp_bonus (+10 if 25-30°C)
```

v2 can use your actual catch data to train a simple model.

---

## 8. Next Steps

If the stack looks good, the build order would be:

1. **Setup** — Python project, DuckDB, Prefect skeleton
2. **Ingestion** — Fetch from all 3 APIs, validate with Pydantic
3. **Bronze** — Load raw JSON to DuckDB
4. **dbt transforms** — Clean, join, score
5. **Dashboard** — Streamlit quick view
6. **CI/CD** — GitHub Actions pipeline
7. **Refine** — Add data quality, tests, actual catch logging

---

> **Open question:** Want to skip Prefect for v1 and just use a Makefile/Python script (simpler, less overhead)? Prefect adds real value for DAGs/scheduling/retries but for a personal project you can always add it later.

> **Also:** Name suggestions? FishSense? TidePredict? ReelData? 🎣
