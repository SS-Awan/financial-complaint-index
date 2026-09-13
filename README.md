# Financial Complaint Index

A PostgreSQL-powered search and analysis system for CFPB consumer complaints.

The project downloads the official CFPB Consumer Complaint Database, stores complaints in a structured database, and lets users search consumer narratives through a ranked API and web interface.

## Why I built this

Public complaint data is large and difficult to explore manually. This project turns it into a searchable system where an analyst can investigate themes such as identity theft, credit reporting, debt collection, companies, products, states, and dates.

## Current capabilities

- Downloads the official CFPB complaint dataset directly from the source
- Stores complaint data in PostgreSQL
- Uses an auditable `ingestion_runs` table to track data loads
- Includes a trial loader and batch ingestion script
- Validated the pipeline with 11,000 complaint records
- Creates indexes for common filtering and analytical queries
- Uses PostgreSQL full-text search and a GIN index for ranked narrative search
- Includes summary and command-line search scripts
- Provides a FastAPI service with health and ranked-search endpoints
- Includes a browser-based search interface for exploring complaint narratives
- Includes automated tests for loader data-cleaning functions

## Tech stack

- Python
- PostgreSQL
- psycopg
- FastAPI
- Uvicorn
- python-dotenv
- pytest
- HTML, CSS, and JavaScript
- Git and GitHub

## Project structure

```text
financial-complaint-index/
├── data/
│   ├── raw/                 # Downloaded source data; excluded from Git
│   └── processed/
├── scripts/
│   ├── check_database.py
│   ├── download_cfpb_data.py
│   ├── ingest_complaints.py
│   ├── load_complaints.py
│   ├── query_summary.py
│   └── search_complaints.py
├── sql/
│   └── 001_create_schema.sql
├── src/
│   └── financial_complaint_index/
│       ├── api.py
│       └── static/
│           └── index.html
├── tests/
│   └── test_load_complaints.py
├── .env.example
├── requirements.txt
└── README.md
```

## Data source

The data comes from the official [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/).

Raw downloaded data is intentionally excluded from this repository.

## Local setup

1. Create and activate a virtual environment.

2. Install dependencies:

   ```cmd
   python -m pip install -r requirements.txt
   ```

3. Create a local `.env` file from `.env.example` and provide your own PostgreSQL credentials.

4. Create the database schema:

   ```cmd
   "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d financial_complaint_index -f sql\001_create_schema.sql
   ```

5. Download the official CFPB source data:

   ```cmd
   python scripts\download_cfpb_data.py --download
   ```

6. Load the validation sample:

   ```cmd
   python scripts\load_complaints.py
   ```

## Example commands

Check the database connection:

```cmd
python scripts\check_database.py
```

View a summary of loaded complaints:

```cmd
python scripts\query_summary.py
```

Search complaint narratives from the command line:

```cmd
python scripts\search_complaints.py "identity theft"
```

Run automated tests:

```cmd
python -m pytest
```

## Run the web application

Start the local API and web interface:

```cmd
python -m uvicorn --app-dir src financial_complaint_index.api:app --reload
```

Then open:

- Web interface: `http://127.0.0.1:8000/app`
- Interactive API documentation: `http://127.0.0.1:8000/docs`
- API health check: `http://127.0.0.1:8000/health`

## API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /` | Returns basic API information |
| `GET /health` | Confirms database connectivity and returns complaint count |
| `GET /search?query=identity%20theft&limit=5` | Returns ranked complaint narrative matches |
| `GET /app` | Opens the browser-based complaint search interface |

## Example search result

The search feature returns ranked matches with the complaint ID, company, product, state, date received, and a short narrative excerpt.

```text
Search: 'identity theft'

#24150269 | TRANSUNION INTERMEDIATE HOLDINGS, INC. |
Credit reporting or other personal consumer reports | VA | 2026-07-13
Rank: 0.567
[identity] [theft] report ...
```

## Next steps

- Add API integration tests
- Add filters for state, product, company, and date range
- Add pagination for larger result sets
- Scale ingestion from the validation sample to the full dataset
- Add additional data-quality checks
- Deploy a public demo