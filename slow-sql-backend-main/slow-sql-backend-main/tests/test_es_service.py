from app.services.es_service import ESService


def test_build_query_does_not_require_query_keyword_prefix_filter() -> None:
    service = ESService()

    query = service.build_query(type="postgresql")
    must_clauses = query["bool"]["must"]

    assert {"term": {"cmd.keyword": "query"}} in must_clauses
    assert not any(
        "prefix" in clause.get("bool", {}).get("should", [{}])[0]
        or any("prefix" in item for item in clause.get("bool", {}).get("should", []))
        for clause in must_clauses
    )


def test_cluster_records_groups_same_template_and_calculates_stats() -> None:
    records = [
        {
            "query": "/* trace */ select  *  from orders where id = 1 and status in (1, 2, 3) limit 10;",
            "dbname": "demo",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.1",
            "query_time": "0.5",
            "timestamp": 1000,
        },
        {
            "query": "SELECT * FROM orders WHERE id=99 AND status IN (9,8,7) LIMIT 5",
            "dbname": "demo",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.1",
            "query_time": "1.5",
            "timestamp": 3000,
        },
        {
            "query": "select *\nfrom orders where id = 42 and status in (4) limit 1",
            "dbname": "demo",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.1",
            "query_time": "1.0",
            "timestamp": 2000,
        },
    ]

    result = ESService._cluster_records(records=records, page=1, page_size=10)

    assert result["total_record_count"] == 3
    assert result["scanned_record_count"] == 3
    assert result["truncated"] is False
    assert result["total"] == 1
    cluster = result["items"][0]
    assert cluster["cluster_count"] == 3
    assert cluster["dbuser"] == "reader"
    assert cluster["first_timestamp"] == 1000
    assert cluster["template_sql"] == "SELECT * FROM ORDERS WHERE ID = ? AND STATUS IN (?) LIMIT ?"
    assert cluster["sample_sql"] == records[1]["query"]
    assert cluster["min_query_time_ms"] == 500.0
    assert cluster["avg_query_time_ms"] == 1000.0
    assert cluster["max_query_time_ms"] == 1500.0
    assert cluster["latest_timestamp"] == 3000


def test_cluster_records_keep_dbname_and_upstream_isolated_and_null_stats_when_unparseable() -> None:
    records = [
        {
            "query": "select * from orders where id = 1",
            "dbname": "demo",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.1",
            "query_time": "oops",
            "timestamp": 1000,
        },
        {
            "query": "select * from orders where id = 2",
            "dbname": "demo_reporting",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.1",
            "query_time": None,
            "timestamp": 2000,
        },
        {
            "query": "select * from orders where id = 3",
            "dbname": "demo",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.2",
            "query_time": "",
            "timestamp": 3000,
        },
    ]

    result = ESService._cluster_records(records=records, page=1, page_size=10)

    assert result["total_record_count"] == 3
    assert result["scanned_record_count"] == 3
    assert result["truncated"] is False
    assert result["total"] == 3
    assert [item["latest_timestamp"] for item in result["items"]] == [3000, 2000, 1000]
    for cluster in result["items"]:
        assert cluster["cluster_count"] == 1
        assert cluster["min_query_time_ms"] is None
        assert cluster["avg_query_time_ms"] is None
        assert cluster["max_query_time_ms"] is None


def test_cluster_records_sorts_globally_before_pagination() -> None:
    records = [
        {
            "query": "select * from orders where id = 1",
            "dbname": "demo",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.1",
            "query_time": "1.2",
            "timestamp": 1000,
        },
        {
            "query": "select * from orders where id = 2",
            "dbname": "demo",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.1",
            "query_time": "0.1",
            "timestamp": 2000,
        },
        {
            "query": "select * from users where id = 1",
            "dbname": "demo",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.1",
            "query_time": "0.6",
            "timestamp": 3000,
        },
        {
            "query": "select * from users where id = 2",
            "dbname": "demo",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.1",
            "query_time": "0.4",
            "timestamp": 4000,
        },
        {
            "query": "select * from payments where id = 1",
            "dbname": "demo",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.1",
            "query_time": "0.9",
            "timestamp": 5000,
        },
    ]

    result = ESService._cluster_records(
        records=records,
        sort_by="avg_query_time_ms",
        sort_order="asc",
        page=1,
        page_size=2,
    )

    assert result["total"] == 3
    assert [item["template_sql"] for item in result["items"]] == [
        "SELECT * FROM USERS WHERE ID = ?",
        "SELECT * FROM ORDERS WHERE ID = ?",
    ]


def test_cluster_records_default_to_cluster_count_desc() -> None:
    records = [
        {
            "query": "select * from orders where id = 1",
            "dbname": "demo",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.1",
            "query_time": "1.0",
            "timestamp": 1000,
        },
        {
            "query": "select * from orders where id = 2",
            "dbname": "demo",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.1",
            "query_time": "1.1",
            "timestamp": 2000,
        },
        {
            "query": "select * from users where id = 1",
            "dbname": "demo",
            "dbuser": "reader",
            "type": "mysql",
            "upstream_addr": "10.0.0.1",
            "query_time": "0.9",
            "timestamp": 3000,
        },
    ]

    result = ESService._cluster_records(records=records, page=1, page_size=10)

    assert result["sort_by"] == "cluster_count"
    assert result["sort_order"] == "desc"
    assert [item["cluster_count"] for item in result["items"]] == [2, 1]


def test_search_clusters_uses_bounded_recent_fetch(monkeypatch) -> None:
    service = ESService()
    captured: dict = {}

    def fake_fetch(self, **kwargs):
        captured.update(kwargs)
        return (
            [
                {
                    "query": "select * from orders where id = 1",
                    "dbname": "demo",
                    "dbuser": "reader",
                    "type": "mysql",
                    "upstream_addr": "10.0.0.1",
                    "query_time": "1.2",
                    "timestamp": 1000,
                }
            ],
            42,
            True,
        )

    monkeypatch.setattr(
        ESService,
        "_fetch_recent_filtered_records_for_clustering",
        fake_fetch,
    )

    result = service.search_clusters(
        keyword="orders",
        dbname="demo",
        dbuser="reader",
        type="mysql",
        upstream_addr="10.0.0.1",
        sort_by="latest_timestamp",
        sort_order="desc",
        page=1,
        page_size=10,
    )

    assert result["total_record_count"] == 42
    assert result["scanned_record_count"] == 1
    assert result["truncated"] is True
    assert captured["keyword"] == "orders"
    assert captured["max_records"] == ESService.CLUSTER_SCAN_LIMIT
    assert captured["batch_size"] == ESService.CLUSTER_BATCH_SIZE
