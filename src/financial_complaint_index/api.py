import os
from datetime import date
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
        "web_app": "/app",
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
def search_complaints(
    query: str,
    limit: int = 5,
    state: str | None = None,
    product: str | None = None,
    company: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    query = query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty.",
        )

    if not 1 <= limit <= 20:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 20.",
        )

    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=400,
            detail="Start date cannot be after end date.",
        )

    where_clauses = [
        "search_vector @@ websearch_to_tsquery('english', %s)",
    ]
    filter_values = [query]

    if state:
        where_clauses.append("state = %s")
        filter_values.append(state.strip().upper())

    if product:
        where_clauses.append("product ILIKE %s")
        filter_values.append(f"%{product.strip()}%")

    if company:
        where_clauses.append("company ILIKE %s")
        filter_values.append(f"%{company.strip()}%")

    if date_from:
        where_clauses.append("date_received >= %s")
        filter_values.append(date_from)

    if date_to:
        where_clauses.append("date_received <= %s")
        filter_values.append(date_to)

    where_sql = " AND ".join(where_clauses)

    sql = f"""
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
        WHERE {where_sql}
        ORDER BY rank DESC
        LIMIT %s
    """

    parameters = [query, query, *filter_values, limit]

    try:
        with psycopg.connect(**connection_settings) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, parameters)
                rows = cursor.fetchall()

        results = [
            {
                "complaint_id": complaint_id,
                "company": result_company,
                "product": result_product,
                "state": complaint_state,
                "date_received": (
                    date_received.isoformat() if date_received else None
                ),
                "excerpt": excerpt,
                "rank": float(rank),
            }
            for (
                complaint_id,
                result_company,
                result_product,
                complaint_state,
                date_received,
                excerpt,
                rank,
            ) in rows
        ]

        return {
            "query": query,
            "state": state.strip().upper() if state else None,
            "product": product.strip() if product else None,
            "company": company.strip() if company else None,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "result_count": len(results),
            "results": results,
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