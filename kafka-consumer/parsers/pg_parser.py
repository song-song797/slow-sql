"""PG 日志行解析器，复用 scripts/import_postgres_log_to_es.py 的核心逻辑"""

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional


# 日志行头部匹配（时间戳 + PID + 用户 + 客户端 + 数据库 + 级别 + 消息）
TIMESTAMP_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) "
    r"(?P<tz>[A-Z]+) "
    r"\[(?P<pid>\d+)\] "
    r"user:(?P<user>.*?), "
    r"client:(?P<client_host>[^,(]+)(?:\((?P<client_port>\d+)\))?, "
    r"database:(?P<database>.*?) "
    r"(?P<level>LOG|FATAL|ERROR|DETAIL|日志|致命错误|错误|详细信息):\s+(?P<message>.*)$"
)

# duration + statement 在同一行
DURATION_SQL_PREFIX_RE = re.compile(
    r"^(?:(?:duration|执行时间):\s*(?P<duration_ms>\d+(?:\.\d+)?)\s*ms\s+)?"
    r"(?:(?:execute\s+[^:]+)|statement|语句):\s*(?P<sql>.*)$",
    re.IGNORECASE | re.DOTALL,
)

# 单独的 duration 行
DURATION_ONLY_RE = re.compile(
    r"^(?:duration|执行时间):\s*(?P<duration_ms>\d+(?:\.\d+)?)\s*ms(?:\s.*)?$",
    re.IGNORECASE | re.DOTALL,
)

SQL_KEYWORDS = ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "GRANT", "REVOKE", "WITH")
SQL_EVENT_LEVELS = {"LOG", "DETAIL", "日志", "详细信息"}


@dataclass
class PgEvent:
    """解析后的 PG 日志事件"""
    timestamp: datetime
    pid: str
    user: str
    client_host: str
    client_port: str
    database: str
    level: str
    message: str


def parse_pg_line(line: str, tz_name: str = "Asia/Shanghai") -> Optional[PgEvent]:
    """解析单行 PG 日志，返回 PgEvent 或 None"""
    match = TIMESTAMP_RE.match(line.strip())
    if not match:
        return None

    zone = timezone(timedelta(hours=8 if tz_name in {"Asia/Shanghai", "CST"} else 0))
    timestamp = datetime.strptime(match.group("ts"), "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=zone)

    return PgEvent(
        timestamp=timestamp,
        pid=match.group("pid"),
        user=match.group("user"),
        client_host=match.group("client_host"),
        client_port=match.group("client_port") or "",
        database=match.group("database"),
        level=match.group("level"),
        message=match.group("message"),
    )


def normalize_sql(sql_text: str) -> Optional[str]:
    """标准化 SQL 文本"""
    sql = re.sub(r"\s+", " ", sql_text).strip().rstrip(";")
    if not sql:
        return None
    if not sql.upper().startswith(SQL_KEYWORDS):
        return None
    # 过滤不完整的 SQL（多行 SQL 截断后只剩一个关键字，如 "SELECT"、"WITH"）
    if len(sql.split()) < 3:
        return None
    return sql


# 心跳/测试 SQL 模式：SELECT 1, SELECT 'x', SELECT TRUE 等
HEARTBEAT_SQL_RE = re.compile(
    r"^SELECT\s+(?:\d+|'[^']*'|TRUE|FALSE|NULL)\s*$",
    re.IGNORECASE,
)

# 框架/中间件表名前缀，这些表的查询不属于业务 SQL
FRAMEWORK_TABLE_PREFIXES = (
    "xxl_job_",
)


def is_non_business_sql(sql: str) -> bool:
    """判断是否为非业务 SQL（心跳、框架表、不完整语句等）"""
    # 心跳/连接测试
    if HEARTBEAT_SQL_RE.match(sql):
        return True
    # 框架表查询（如 XXL-Job 调度框架）
    lower = sql.lower()
    for prefix in FRAMEWORK_TABLE_PREFIXES:
        if prefix in lower:
            return True
    return False


def duration_ms_to_seconds(duration_ms: str) -> Optional[str]:
    """将毫秒耗时转换为秒字符串"""
    try:
        seconds = Decimal(duration_ms) / Decimal("1000")
    except (InvalidOperation, ValueError):
        return None
    text = format(seconds, "f").rstrip("0").rstrip(".")
    return text or "0"


def extract_sql(message: str) -> Optional[str]:
    """从 message 中提取 SQL"""
    match = DURATION_SQL_PREFIX_RE.match(message.strip())
    if not match:
        return None
    return normalize_sql(match.group("sql"))


def extract_duration_ms(message: str) -> Optional[str]:
    """从 message 中提取耗时（毫秒）"""
    stripped = message.strip()
    match = DURATION_SQL_PREFIX_RE.match(stripped)
    if match and match.group("duration_ms"):
        return match.group("duration_ms")
    match = DURATION_ONLY_RE.match(stripped)
    if match:
        return match.group("duration_ms")
    return None


def extract_sql_and_query_time(message: str, default_query_time: str = "0.10") -> tuple[Optional[str], str]:
    """同时提取 SQL 和耗时"""
    sql = extract_sql(message)
    if not sql:
        return None, default_query_time
    duration_ms = extract_duration_ms(message)
    if not duration_ms:
        return sql, default_query_time
    query_time = duration_ms_to_seconds(duration_ms)
    return sql, query_time or default_query_time


def build_pg_es_doc(
    event: PgEvent,
    sql: str,
    default_db_host: str = "127.0.0.1",
    query_time: str = "0.10",
) -> dict:
    """构建 ES 文档"""
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
            "workgroup_name": "kafka-pg",
            "client_port": event.client_port,
            "query_time": query_time,
            "status": "success",
        },
    }
