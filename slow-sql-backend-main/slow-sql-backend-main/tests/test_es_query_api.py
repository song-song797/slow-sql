import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dependencies import verify_api_key
from app.routers import es_query
from app.services.es_service import ESService


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(es_query.router)
    app.dependency_overrides[verify_api_key] = lambda: "test-api-key"

    with TestClient(app) as test_client:
        yield test_client


def test_query_es_clusters_forwards_filters_and_pagination(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_search_clusters(self, **kwargs):
        captured.update(kwargs)
        return {
            "total": 1,
            "page": kwargs["page"],
            "page_size": kwargs["page_size"],
            "total_record_count": 4,
            "scanned_record_count": 4,
            "truncated": False,
            "items": [
                {
                    "cluster_id": "cluster-1",
                    "template_sql": "SELECT * FROM ORDERS WHERE ID = ?",
                    "sample_sql": "select * from orders where id = 1",
                    "dbname": "demo",
                    "dbuser": "reader",
                    "type": "mysql",
                    "upstream_addr": "10.0.0.1",
                    "cluster_count": 4,
                    "first_timestamp": 1741850000000,
                    "min_query_time_ms": 120.0,
                    "avg_query_time_ms": 250.0,
                    "max_query_time_ms": 480.0,
                    "latest_timestamp": 1741852800000,
                    "is_slow_sql": False,
                }
            ],
        }

    monkeypatch.setattr(ESService, "search_clusters", fake_search_clusters)

    response = client.get(
        "/api/v1/es-query/clusters",
        headers={"X-API-Key": "test-api-key"},
        params={
            "keyword": "orders",
            "dbname": "demo",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.1",
            "timestamp_start": "2026-03-13 00:00:00",
            "timestamp_end": "2026-03-13 23:59:59",
            "sort_by": "avg_query_time_ms",
            "sort_order": "asc",
            "page": 2,
            "page_size": 5,
            "is_slow_sql": "true",
        },
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["cluster_id"] == "cluster-1"
    assert response.json()["total_record_count"] == 4
    assert response.json()["scanned_record_count"] == 4
    assert response.json()["truncated"] is False
    assert captured == {
        "query_time_min": 1.0,
        "query_time_max": None,
        "timestamp_start": "2026-03-13 00:00:00",
        "timestamp_end": "2026-03-13 23:59:59",
        "keyword": "orders",
        "dbname": "demo",
        "dbuser": "reader",
        "type": "mysql",
        "upstream_addr": "10.0.0.1",
        "sort_by": "avg_query_time_ms",
        "sort_order": "asc",
        "page": 2,
        "page_size": 5,
    }
