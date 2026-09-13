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

with psycopg.connect(**connection_settings) as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS complaint_count,
                COUNT(consumer_complaint_narrative) AS narrative_count
            FROM complaints
            """
        )
        complaint_count, narrative_count = cursor.fetchone()

        cursor.execute(
            """
            SELECT product, COUNT(*) AS complaint_count
            FROM complaints
            GROUP BY product
            ORDER BY complaint_count DESC
            LIMIT 5
            """
        )
        top_products = cursor.fetchall()

print(f"Total complaints: {complaint_count:,}")
print(f"Complaints with narratives: {narrative_count:,}")
print("\nTop five products:")

for product, count in top_products:
    print(f"- {product}: {count:,}")