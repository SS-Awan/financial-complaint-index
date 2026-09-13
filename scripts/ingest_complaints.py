import argparse
import csv
import io
import zipfile

import psycopg

from load_complaints import (
    ARCHIVE_PATH,
    INSERT_COMPLAINT_SQL,
    SOURCE_URL,
    complaint_values,
    connection_settings,
)

BATCH_SIZE = 1_000


def write_batch(connection, cursor, batch: list[tuple]) -> None:
    cursor.executemany(INSERT_COMPLAINT_SQL, batch)
    connection.commit()


def main(limit: int | None) -> None:
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

            cursor.execute("SELECT COUNT(*) FROM complaints")
            complaints_before = cursor.fetchone()[0]
            connection.commit()

            processed_count = 0
            batch = []

            with zipfile.ZipFile(ARCHIVE_PATH) as archive:
                csv_name = archive.namelist()[0]

                with archive.open(csv_name) as compressed_file:
                    reader = csv.DictReader(
                        io.TextIOWrapper(compressed_file, encoding="utf-8-sig")
                    )

                    for row in reader:
                        if limit is not None and processed_count >= limit:
                            break

                        batch.append(complaint_values(row, ingestion_run_id))
                        processed_count += 1

                        if len(batch) == BATCH_SIZE:
                            write_batch(connection, cursor, batch)
                            batch = []
                            print(
                                f"\rProcessed: {processed_count:,}",
                                end="",
                                flush=True,
                            )

            if batch:
                write_batch(connection, cursor, batch)

            cursor.execute("SELECT COUNT(*) FROM complaints")
            complaints_after = cursor.fetchone()[0]
            inserted_count = complaints_after - complaints_before

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
                (processed_count, inserted_count, ingestion_run_id),
            )
            connection.commit()

    print(
        f"\nFinished. Processed {processed_count:,}; "
        f"inserted {inserted_count:,} new complaints."
    )


parser = argparse.ArgumentParser(
    description="Batch-ingest CFPB complaints into PostgreSQL."
)
parser.add_argument(
    "--limit",
    type=int,
    help="Optional number of rows to process. Omit for the full dataset.",
)
args = parser.parse_args()

if __name__ == "__main__":
    main(args.limit)