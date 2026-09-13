# Financial Complaint Index

A PostgreSQL-powered search and analysis system for CFPB consumer complaints.

The project downloads the official CFPB Consumer Complaint Database, stores complaints in a structured relational database, and supports ranked full-text search across consumer narratives.

## Why I built this

Public complaint data is large and difficult to explore manually. This project turns it into a searchable system where an analyst can investigate themes such as identity theft, credit reporting, debt collection, companies, products, states, and dates.

## Current capabilities

- Downloads the official CFPB complaint dataset directly from the source
- Stores complaint data in PostgreSQL
- Uses an auditable `ingestion_runs` table to track data loads
- Creates indexes for common filtering and analytical queries
- Uses PostgreSQL full-text search and a GIN index for ranked narrative search
- Includes a trial loader that imports 10,000 records to validate the pipeline
- Includes summary and search scripts for exploring loaded data

## Tech stack

- Python
- PostgreSQL
- psycopg
- python-dotenv
- pytest
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
│   ├── load_complaints.py
│   ├── query_summary.py
│   └── search_complaints.py
├── sql/
│   └── 001_create_schema.sql
├── src/
├── tests/
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

6. Load the 10,000-row validation sample:

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

Search complaint narratives:

```cmd
python scripts\search_complaints.py "identity theft"
```

## Example search result

The search script returns ranked matches with the complaint ID, company, product, state, date received, and a short narrative excerpt.

```text
Search: 'identity theft'

#24150269 | TRANSUNION INTERMEDIATE HOLDINGS, INC. |
Credit reporting or other personal consumer reports | VA | 2026-07-13
Rank: 0.567
[identity] [theft] report ...
```

## Next steps

- Scale ingestion from the validation sample to the full dataset
- Add data-quality checks and automated tests
- Build a Python API for filters and search
- Build a simple analyst-facing web interface
- Deploy a public demo