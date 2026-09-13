import csv
from datetime import date
import io
import os
import zipfile
from pathlib import Path

import psycopg
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

SOURCE_URL = "https://files.consumerfinance.gov/ccdb/complaints.csv.zip"
ARCHIVE_PATH = PROJECT_ROOT / "data" / "raw" / "complaints.csv.zip"
TRIAL_ROW_LIMIT = 10_000

connection_settings = {
    "host": os.environ["DB_HOST"],
    "port": os.environ["DB_PORT"],
    "dbname": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
}
def blank_to_none(value: str) -> str | None:
    value = value.strip()
    return value or None


def yes_no_to_bool(value: str) -> bool | None:
    value = blank_to_none(value)

    if value == "Yes":
        return True
    if value == "No":
        return False
    return None
def parse_date(value: str) -> date | None:
    value = blank_to_none(value)
    return date.fromisoformat(value) if value else None
def complaint_values(row: dict[str, str], ingestion_run_id: int) -> tuple:
    return (
        int(row["Complaint ID"]),
        parse_date(row["Date received"]),
        blank_to_none(row["Product"]),
        blank_to_none(row["Sub-product"]),
        blank_to_none(row["Issue"]),
        blank_to_none(row["Sub-issue"]),
        blank_to_none(row["Company"]),
        blank_to_none(row["State"]),
        blank_to_none(row["ZIP code"]),
        blank_to_none(row["Tags"]),
        blank_to_none(row["Submitted via"]),
        parse_date(row["Date sent to company"]),
        blank_to_none(row["Company response to consumer"]),
        blank_to_none(row["Company public response"]),
        yes_no_to_bool(row["Timely response?"]),
        None,
        blank_to_none(row["Consumer complaint narrative"]),
        ingestion_run_id,
    )
INSERT_COMPLAINT_SQL = """
    INSERT INTO complaints (
        complaint_id, date_received, product, sub_product, issue, sub_issue,
        company, state, zip_code, tags, submitted_via, date_sent_to_company,
        company_response_to_consumer, company_public_response, timely_response,
        consumer_consent_provided, consumer_complaint_narrative, ingestion_run_id
    )
    VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (complaint_id) DO NOTHING
"""
def main() -> None:
    if not ARCHIVE_PATH.exists():
        raise FileNotFoundError(f"Missing downloaded file: {ARCHIVE_PATH}")

    with psycopg.connect(**connection_settings) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ingestion_runs (
                    source_url,
                    source_file_name,
                    status
                )
                VALUES (%s, %s, 'running')
                RETURNING ingestion_run_id
                """,
                (SOURCE_URL, ARCHIVE_PATH.name),
            )
            ingestion_run_id = cursor.fetchone()[0]

            with zipfile.ZipFile(ARCHIVE_PATH) as archive:
                csv_name = archive.namelist()[0]

                with archive.open(csv_name) as compressed_file:
                    reader = csv.DictReader(
                        io.TextIOWrapper(compressed_file, encoding="utf-8-sig")
                    )
                    rows = []

                    for row in reader:
                        if len(rows) >= TRIAL_ROW_LIMIT:
                            break

                        rows.append(complaint_values(row, ingestion_run_id))

            cursor.executemany(INSERT_COMPLAINT_SQL, rows)

            cursor.execute(
                """
                UPDATE ingestion_runs
                SET
                    status = 'succeeded',
                    finished_at = NOW(),
                    source_row_count = %s,
                    inserted_count = %s
                WHERE ingestion_run_id = %s
                """,
                (len(rows), len(rows), ingestion_run_id),
            )

    print(f"Loaded {len(rows):,} CFPB complaints into PostgreSQL.")


if __name__ == "__main__":
    main()