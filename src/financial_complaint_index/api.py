import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

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
    