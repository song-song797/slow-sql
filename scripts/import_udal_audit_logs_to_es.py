import argparse
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from elasticsearch import Elasticsearch, helpers


LINE_RE = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?P<payload>\{.*\})$")
LEADING_COMMENT_RE = re.compile(r"^/\*.*?\*/\s*", re.DOTALL)
SQL_START_RE = re.compile(r"^(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|GRANT|REVOKE)\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import UDAL audit logs into Elasticsearch")
    parser.add_argument("logfiles", nargs="+", type=Path, help="Audit log paths")
    parser.add_argument("--es-url", default="http://127.0.0.1:9200")
    parser.add_argument("--index", default="triangle-mysql-local")
    parser.add_argument("--default-db-host", default="127.0.0.1")
    parser.add_argument("--default-schema", default="unknown")
    parser.add_argument("--tz-offset-hours", type=int, default=8)
    parser.add_argument("--default-cost-ms", type=int, default=100)
    return parser.parse_args()


def clean_sql(sql: str) -> str | None:
    sql = LEADING_COMMENT_RE.sub("", sql).strip()
    sql = re.sub(r"\s+", " ", sql)
    if not sql:
        return None
    if sql.lower() in {"commit", "begin", "rollback"}:
        return None
    if sql.lower().startswith("set "):
        return None
    if sql.lower().startswith("udal "):
        return None
    if not SQL_START_RE.match(sql):
        return None
    return sql


def parse_user_field(user_field: str) -> tuple[str, str, str]:
    if not user_field or "@" not in user_field:
        return user_field or "unknown", "127.0.0.1", ""
    user, _, host_port = user_field.partition("@")
    host, _, port = host_port.partition(":")
    return user or "unknown", host or "127.0.0.1", port


def build_doc_id(source: str) -> str:
    return hashlib.sha1(source.encode("utf-8")).hexdigest()


def ensure_index(client: Elasticsearch, index: str) -> None:
    if client.indices.exists(index=index):
        return
    client.indices.create(
        index=index,
        mappings={
            "properties": {
                "timestamp": {"type": "long"},
                "query_time": {"type": "keyword"},
            }
        },
    )


def flush_actions(client: Elasticsearch, actions: list[dict]) -> int:
    if not actions:
        return 0
    helpers.bulk(client, actions, refresh=False)
    count = len(actions)
    actions.clear()
    return count


def main() -> int:
    args = parse_args()
    zone = timezone(timedelta(hours=args.tz_offset_hours))
    client = Elasticsearch(args.es_url, verify_certs=False)
    ensure_index(client, args.index)

    pending: dict[int, dict] = {}
    actions: list[dict] = []
    total_receive = 0
    total_end = 0
    total_sql = 0
    imported = 0
    batch_size = 5000

    def enqueue_action(request_id: int, item: dict) -> None:
        nonlocal imported
        query_time = item.get("query_time", f"{args.default_cost_ms / 1000:.3f}")
        source = {
            "timestamp": int(item["timestamp"].timestamp() * 1000),
            "upstream_addr": args.default_db_host,
            "client_ip": item["client_ip"],
            "cmd": "query",
            "query": item["sql"],
            "dbname": item["dbname"],
            "dbuser": item["dbuser"],
            "type": "mysql",
            "workgroup_name": "udal-audit-log-import",
            "client_port": item["client_port"],
            "query_time": query_time,
            "status": "success",
        }
        doc_id = build_doc_id(
            f"{item['source_file']}|{request_id}|{source['timestamp']}|{source['dbname']}|{source['dbuser']}|{source['query']}"
        )
        actions.append(
            {
                "_op_type": "index",
                "_index": args.index,
                "_id": doc_id,
                "_source": source,
            }
        )
        if len(actions) >= batch_size:
            imported += flush_actions(client, actions)

    for log_path in args.logfiles:
        if not log_path.exists():
            raise FileNotFoundError(f"log file not found: {log_path}")

        with log_path.open("r", encoding="utf-8", errors="replace") as fh:
            for raw_line in fh:
                line = raw_line.rstrip("\n")
                match = LINE_RE.match(line)
                if not match:
                    continue
                payload = json.loads(match.group("payload"))
                event_type = payload.get("eventType")
                request_id = payload.get("requestId")
                if request_id is None:
                    continue

                ts = datetime.strptime(match.group("ts"), "%Y-%m-%d %H:%M:%S").replace(tzinfo=zone)

                if event_type == "RECEIVE_REQUEST":
                    total_receive += 1
                    sql = clean_sql(payload.get("sql", ""))
                    if not sql:
                        continue
                    dbuser, client_ip, client_port = parse_user_field(payload.get("user", ""))
                    pending[request_id] = {
                        "timestamp": ts,
                        "sql": sql,
                        "dbname": payload.get("schema") or args.default_schema,
                        "dbuser": dbuser,
                        "client_ip": client_ip,
                        "client_port": client_port,
                        "source_file": str(log_path),
                    }
                    total_sql += 1
                elif event_type == "END_REQUEST":
                    total_end += 1
                    cost_ms = payload.get("cost")
                    if request_id in pending and cost_ms is not None:
                        item = pending.pop(request_id)
                        item["query_time"] = f"{max(float(cost_ms), 0.0) / 1000:.3f}"
                        enqueue_action(request_id, item)

    for request_id, item in pending.items():
        enqueue_action(request_id, item)

    imported += flush_actions(client, actions)

    client.indices.refresh(index=args.index)

    if imported == 0:
        print("No eligible SQL statements found.")
        return 0

    print(
        f"Imported {imported} SQL records into {args.index}. "
        f"RECEIVE_REQUEST={total_receive}, END_REQUEST={total_end}, eligible_sql={total_sql}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
