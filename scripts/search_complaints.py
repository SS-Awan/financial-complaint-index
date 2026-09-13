import argparse
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

connection_settings = {
    "host": os.environ["DB_HOST"],
    "port": os.environ["DB_PORT"],
    "dbname": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
}

parser = argparse.ArgumentParser(
    description="Search CFPB consumer-complaint narratives."
)
parser.add_argument(
    "query",
    nargs="?",
    default="credit report",
    help="Words or a phrase to search for.",
)
args = parser.parse_args()

with psycopg.connect(**connection_settings) as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                complaint_id,
                company,
                product,
                state,
                date_received,
                ts_headline(
                    'english',
                    consumer_complaint_narrative,
                    websearch_to_tsquery('english', %s),
                    'StartSel=[, StopSel=], MaxWords=25, MinWords=10'
                ) AS excerpt,
                ts_rank(
                    search_vector,
                    websearch_to_tsquery('english', %s)
                ) AS rank
            FROM complaints
            WHERE search_vector @@ websearch_to_tsquery('english', %s)
            ORDER BY rank DESC, date_received DESC
            LIMIT 5
            """,
            (args.query, args.query, args.query),
        )
        results = cursor.fetchall()

print(f"Search: {args.query!r}")

if not results:
    print("No matching complaint narratives found.")
else:
    for complaint_id, company, product, state, received, excerpt, rank in results:
        print(f"\n#{complaint_id} | {company} | {product} | {state} | {received}")
        print(f"Rank: {rank:.3f}")
        print(excerpt)