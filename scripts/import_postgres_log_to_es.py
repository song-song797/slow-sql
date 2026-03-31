import argparse
import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Iterator, List

from elasticsearch import Elasticsearch, helpers


TIMESTAMP_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) "
    r"(?P<tz>[A-Z]+) "
    r"\[(?P<pid>\d+)\] "
    r"user:(?P<user>.*?), "
    r"client:(?P<client_host>[^,(]+)(?:\((?P<client_port>\d+)\))?, "
    r"database:(?P<database>.*?) "
    r"(?P<level>LOG|FATAL|ERROR|DETAIL|日志|致命错误|错误|详细信息):\s+(?P<message>.*)$"
)

DURATION_SQL_PREFIX_RE = re.compile(
    r"^(?:(?:duration|执行时间):\s*(?P<duration_ms>\d+(?:\.\d+)?)\s*ms\s+)?"
    r"(?:(?:execute\s+[^:]+)|statement|语句):\s*(?P<sql>.*)$",
    re.IGNORECASE | re.DOTALL,
)
DURATION_ONLY_RE = re.compile(
    r"^(?:duration|执行时间):\s*(?P<duration_ms>\d+(?:\.\d+)?)\s*ms(?:\s.*)?$",
    re.IGNORECASE | re.DOTALL,
)
SQL_KEYWORDS = ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "GRANT", "REVOKE")
SQL_EVENT_LEVELS = {"LOG", "DETAIL", "日志", "详细信息"}
SOURCE_TAG = "postgresql-log-import"


@dataclass
class Event:
    timestamp: datetime
    pid: str
    user: str
    client_host: str
    client_port: str
    database: str
    level: str
    message: str


@dataclass
class PendingSql:
    event: Event
    sql: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import PostgreSQL log SQL statements into Elasticsearch")
    parser.add_argument("logfile", type=Path, help="Path to PostgreSQL log file")
    parser.add_argument("--es-url", default="http://127.0.0.1:9200")
    parser.add_argument("--index", default="triangle-mysql-local")
    parser.add_argument("--default-db-host", default="127.0.0.1")
    parser.add_argument("--default-query-time", default="0.10")
    parser.add_argument("--tz", default="Asia/Shanghai")
    return parser.parse_args()


def iter_events(log_path: Path, tz_name: str) -> Iterable[Event]:
    zone = timezone(timedelta(hours=8 if tz_name in {"Asia/Shanghai", "CST"} else 0))
    current = None
    buffer: List[str] = []

    with log_path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")
            match = TIMESTAMP_RE.match(line)
            if match:
                if current is not None:
                    yield Event(
                        timestamp=current["timestamp"],
                        pid=current["pid"],
                        user=current["user"],
                        client_host=current["client_host"],
                        client_port=current["client_port"],
                        database=current["database"],
                        level=current["level"],
                        message="\n".join(buffer),
                    )

                timestamp = datetime.strptime(match.group("ts"), "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=zone)
                current = {
                    "timestamp": timestamp,
                    "pid": match.group("pid"),
                    "user": match.group("user"),
                    "client_host": match.group("client_host"),
                    "client_port": match.group("client_port") or "",
                    "database": match.group("database"),
                    "level": match.group("level"),
                }
                buffer = [match.group("message")]
            elif current is not None:
                buffer.append(line)

    if current is not None:
        yield Event(
            timestamp=current["timestamp"],
            pid=current["pid"],
            user=current["user"],
            client_host=current["client_host"],
            client_port=current["client_port"],
            database=current["database"],
            level=current["level"],
            message="\n".join(buffer),
        )


def normalize_sql(sql_text: str) -> str | None:
    sql = re.sub(r"\s+", " ", sql_text).strip().rstrip(";")
    if not sql:
        return None

    upper_sql = sql.upper()
    if not upper_sql.startswith(SQL_KEYWORDS):
        return None
    return sql


def duration_ms_to_seconds_text(duration_ms: str) -> str | None:
    try:
        seconds = Decimal(duration_ms) / Decimal("1000")
    except (InvalidOperation, ValueError):
        return None

    text = format(seconds, "f").rstrip("0").rstrip(".")
    return text or "0"


def extract_sql(message: str) -> str | None:
    match = DURATION_SQL_PREFIX_RE.match(message.strip())
    if not match:
        return None
    return normalize_sql(match.group("sql"))


def extract_duration_ms(message: str) -> str | None:
    stripped = message.strip()
    match = DURATION_SQL_PREFIX_RE.match(stripped)
    if match and match.group("duration_ms"):
        return match.group("duration_ms")

    match = DURATION_ONLY_RE.match(stripped)
    if match:
        return match.group("duration_ms")
    return None


def extract_sql_and_query_time(message: str, default_query_time: str) -> tuple[str | None, str]:
    sql = extract_sql(message)
    if not sql:
        return None, default_query_time

    duration_ms = extract_duration_ms(message)
    if not duration_ms:
        return sql, default_query_time

    query_time = duration_ms_to_seconds_text(duration_ms)
    return sql, query_time or default_query_time


def build_doc(event: Event, sql: str, default_db_host: str, query_time: str) -> dict:
    doc_id_source = f"{event.timestamp.isoformat()}|{event.user}|{event.database}|{event.client_host}|{sql}"
    return {
        "_id": hashlib.sha1(doc_id_source.encode("utf-8")).hexdigest(),
        "_source": {
            "timestamp": int(event.timestamp.timestamp() * 1000),
            "upstream_addr": default_db_host,
            "client_ip": event.client_host,
            "cmd": "query",
            "query": sql,
            "dbname": event.database if event.database != "[unknown]" else "postgres",
            "dbuser": event.user if event.user != "[unknown]" else "unknown",
            "type": "postgresql",
            "workgroup_name": SOURCE_TAG,
            "client_port": event.client_port,
            "query_time": query_time,
            "status": "success",
        },
    }


def session_key(event: Event) -> str:
    return event.pid or f"{event.user}|{event.database}|{event.client_host}|{event.client_port}"


def iter_docs_from_events(
    events: Iterable[Event],
    default_db_host: str,
    default_query_time: str,
) -> Iterator[dict]:
    pending_sql_by_key: dict[str, PendingSql] = {}
    pending_duration_by_key: dict[str, str] = {}

    def pop_query_time(key: str) -> str:
        duration_ms = pending_duration_by_key.pop(key, None)
        if not duration_ms:
            return default_query_time
        return duration_ms_to_seconds_text(duration_ms) or default_query_time

    for event in events:
        if event.level not in SQL_EVENT_LEVELS:
            continue

        key = session_key(event)
        sql = extract_sql(event.message)
        duration_ms = extract_duration_ms(event.message)

        if sql and duration_ms:
            previous_sql = pending_sql_by_key.pop(key, None)
            if previous_sql is not None:
                yield build_doc(previous_sql.event, previous_sql.sql, default_db_host, pop_query_time(key))
            pending_duration_by_key.pop(key, None)
            yield build_doc(
                event,
                sql,
                default_db_host,
                duration_ms_to_seconds_text(duration_ms) or default_query_time,
            )
            continue

        if sql:
            previous_sql = pending_sql_by_key.pop(key, None)
            if previous_sql is not None:
                yield build_doc(previous_sql.event, previous_sql.sql, default_db_host, pop_query_time(key))

            if key in pending_duration_by_key:
                yield build_doc(event, sql, default_db_host, pop_query_time(key))
            else:
                pending_sql_by_key[key] = PendingSql(event=event, sql=sql)
            continue

        if duration_ms:
            previous_sql = pending_sql_by_key.pop(key, None)
            if previous_sql is not None:
                yield build_doc(
                    previous_sql.event,
                    previous_sql.sql,
                    default_db_host,
                    duration_ms_to_seconds_text(duration_ms) or default_query_time,
                )
            else:
                pending_duration_by_key[key] = duration_ms

    for key, pending_sql in pending_sql_by_key.items():
        yield build_doc(pending_sql.event, pending_sql.sql, default_db_host, pop_query_time(key))


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


def main() -> int:
    args = parse_args()
    if not args.logfile.exists():
        raise FileNotFoundError(f"log file not found: {args.logfile}")

    client = Elasticsearch(args.es_url, verify_certs=False)
    ensure_index(client, args.index)

    actions = []
    parsed = 0
    for doc in iter_docs_from_events(
        iter_events(args.logfile, args.tz),
        default_db_host=args.default_db_host,
        default_query_time=args.default_query_time,
    ):
        parsed += 1
        actions.append(
            {
                "_op_type": "index",
                "_index": args.index,
                "_id": doc["_id"],
                "_source": doc["_source"],
            }
        )

    if not actions:
        print("No SQL statements matched import rules.")
        return 0

    helpers.bulk(client, actions, refresh="wait_for")
    print(f"Imported {len(actions)} SQL records into {args.index}. Parsed candidates: {parsed}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
