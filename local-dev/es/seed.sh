#!/bin/sh
set -eu

ES_URL="${ES_URL:-http://elasticsearch:9200}"
INDEX_NAME="${INDEX_NAME:-triangle-mysql-local}"

echo "Seeding Elasticsearch index: ${INDEX_NAME}"

curl -sS -X PUT "${ES_URL}/${INDEX_NAME}" \
  -H "Content-Type: application/json" \
  -d '{
    "mappings": {
      "properties": {
        "timestamp": { "type": "long" },
        "query_time": { "type": "keyword" }
      }
    }
  }' >/dev/null || true

curl -sS -X POST "${ES_URL}/${INDEX_NAME}/_doc/1" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": 1736438400000,
    "upstream_addr": "127.0.0.1",
    "client_ip": "10.0.0.8",
    "cmd": "query",
    "query": "SELECT * FROM orders WHERE user_id = 123 ORDER BY created_at DESC",
    "dbname": "slow_sql_db",
    "dbuser": "slow_sql",
    "type": "mysql",
    "workgroup_name": "local",
    "client_port": "3306",
    "query_time": "2.35",
    "status": "success"
  }' >/dev/null

curl -sS -X POST "${ES_URL}/${INDEX_NAME}/_refresh" >/dev/null

echo "Elasticsearch seed completed"
