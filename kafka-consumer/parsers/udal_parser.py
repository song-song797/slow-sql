"""UDAL 审计日志解析器，复用 scripts/import_udal_audit_logs_to_es.py 的核心逻辑"""

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple


# 日志行匹配：时间戳 + JSON
LINE_RE = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?P<payload>\{.*\})$")

# SQL 清洗
LEADING_COMMENT_RE = re.compile(r"^/\*.*?\*/\s*", re.DOTALL)
SQL_START_RE = re.compile(
    r"^(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|GRANT|REVOKE)\b", re.IGNORECASE
)


def clean_sql(sql: str) -> Optional[str]:
    """清洗 SQL，过滤非查询语句"""
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


def parse_user_field(user_field: str) -> Tuple[str, str, str]:
    """解析 UDAL user 字段，返回 (用户名, IP, 端口)"""
    if not user_field or "@" not in user_field:
        return user_field or "unknown", "127.0.0.1", ""
    user, _, host_port = user_field.partition("@")
    host, _, port = host_port.partition(":")
    return user or "unknown", host or "127.0.0.1", port


def parse_udal_line(line: str, tz_offset_hours: int = 8) -> Optional[dict]:
    """解析单行 UDAL 审计日志，返回结构化数据或 None"""
    match = LINE_RE.match(line.strip())
    if not match:
        return None

    try:
        payload = json.loads(match.group("payload"))
    except json.JSONDecodeError:
        return None

    ts = datetime.strptime(match.group("ts"), "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone(timedelta(hours=tz_offset_hours))
    )

    return {
        "timestamp": ts,
        "payload": payload,
        "event_type": payload.get("eventType"),
        "request_id": payload.get("requestId"),
    }


def build_udal_es_doc(
    item: dict,
    default_db_host: str = "127.0.0.1",
    source_tag: str = "kafka-udal",
) -> dict:
    """构建 UDAL ES 文档"""
    query_time = item.get("query_time", "0.100")
    doc_id = hashlib.sha1(
        f"{item.get('source_tag', '')}|{item.get('request_id', '')}|"
        f"{int(item['timestamp'].timestamp() * 1000)}|{item.get('dbname', '')}|"
        f"{item.get('dbuser', '')}|{item.get('sql', '')}".encode("utf-8")
    ).hexdigest()

    return {
        "_id": doc_id,
        "_source": {
            "timestamp": int(item["timestamp"].timestamp() * 1000),
            "upstream_addr": default_db_host,
            "client_ip": item["client_ip"],
            "cmd": "query",
            "query": item["sql"],
            "dbname": item["dbname"],
            "dbuser": item["dbuser"],
            "type": "mysql",
            "workgroup_name": source_tag,
            "client_port": item["client_port"],
            "query_time": query_time,
            "status": "success",
        },
    }
