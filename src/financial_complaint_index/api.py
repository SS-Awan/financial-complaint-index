import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

connection_settings = {
    "host": os.environ["DB_HOST"],
    "port": os.environ["DB_PORT"],
    "dbname": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
}

app = FastAPI(
    title="Financial Complaint Index API",
    description="Search and analysis API for CFPB consumer complaints.",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "Financial Complaint Index API",
        "documentation": "/docs",
    }


@app.get("/health")
def health():
    try:
        with psycopg.connect(**connection_settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM complaints")
                complaint_count = cursor.fetchone()[0]

        return {
            "status": "ok",
            "database": "connected",
            "complaint_count": complaint_count,
        }
    except psycopg.Error as error:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed.",
        ) from error
@app.get("/search")
def search(query: str, limit: int = 5):
    if not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty.",
        )

    if not 1 <= limit <= 20:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 20.",
        )

    try:
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
                    LIMIT %s
                    """,
                    (query, query, query, limit),
                )
                rows = cursor.fetchall()

        return {
            "query": query,
            "result_count": len(rows),
            "results": [
                {
                    "complaint_id": complaint_id,
                    "company": company,
                    "product": product,
                    "state": state,
                    "date_received": date_received.isoformat(),
                    "rank": round(float(rank), 3),
                    "excerpt": excerpt,
                }
                for (
                    complaint_id,
                    company,
                    product,
                    state,
                    date_received,
                    excerpt,
                    rank,
                ) in rows
            ],
        }
    except psycopg.Error as error:
        raise HTTPException(
            status_code=503,
            detail="Database query failed.",
        ) from error

@app.get("/app", include_in_schema=False)
def web_app():
    app_file = Path(__file__).resolve().parent / "static" / "index.html"
    return FileResponse(app_file)