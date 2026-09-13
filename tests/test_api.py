import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from financial_complaint_index.api import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["complaint_count"] >= 11000


def test_search_endpoint_returns_ranked_results():
    response = client.get(
        "/search",
        params={"query": "identity theft", "limit": 5},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["query"] == "identity theft"
    assert 1 <= len(data["results"]) <= 5
    assert "complaint_id" in data["results"][0]
    assert "rank" in data["results"][0]


def test_search_endpoint_filters_by_state():
    response = client.get(
        "/search",
        params={
            "query": "identity theft",
            "state": "FL",
            "limit": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["state"] == "FL"
    assert len(data["results"]) > 0
    assert all(result["state"] == "FL" for result in data["results"])


def test_search_endpoint_filters_by_product():
    response = client.get(
        "/search",
        params={
            "query": "identity theft",
            "product": "Credit reporting",
            "limit": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["product"] == "Credit reporting"
    assert len(data["results"]) > 0
    assert all(
        "credit reporting" in result["product"].lower()
        for result in data["results"]
    )