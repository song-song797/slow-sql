"""PG 消费者：从 Kafka 消费 PG 原始日志行，合并 duration+statement，写入 ES"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from confluent_kafka import Message

from parsers.pg_parser import (
    PgEvent,
    build_pg_es_doc,
    duration_ms_to_seconds,
    extract_duration_ms,
    extract_sql,
    is_non_business_sql,
    parse_pg_line,
    SQL_EVENT_LEVELS,
)
from consumer.base import BaseConsumer
from es_writer import ESWriter

logger = logging.getLogger(__name__)


@dataclass
class PendingSql:
    event: PgEvent
    sql: str
    collected_at: float = field(default_factory=time.time)


class PgConsumer(BaseConsumer):
    """PG 消费者：按 PID 合并 duration + statement 行"""

    def __init__(
        self,
        kafka_servers: str,
        topic: str,
        group_id: str,
        auto_offset_reset: str,
        es_writer: ESWriter,
        default_db_host: str = "127.0.0.1",
        default_query_time: str = "0.10",
        pg_tz: str = "Asia/Shanghai",
        excluded_users: str = "",
    ):
        super().__init__(kafka_servers, topic, group_id, auto_offset_reset, es_writer)
        self.default_db_host = default_db_host
        self.default_query_time = default_query_time
        self.pg_tz = pg_tz
        self.pending_timeout = 30  # 等待 duration 的超时时间（秒）
        self.excluded_users = set(u.strip().lower() for u in excluded_users.split(",") if u.strip())

        # 按 PID 维护待合并的状态
        self.pending_sql_by_key: dict[str, PendingSql] = {}
        self.pending_duration_by_key: dict[str, str] = {}

    def process_message(self, msg: Message) -> Optional[dict]:
        data = json.loads(msg.value().decode("utf-8"))
        raw_line = data.get("raw_line", "")
        if not raw_line:
            return None

        event = parse_pg_line(raw_line, self.pg_tz)
        if not event:
            return None

        # 过滤监控/系统用户
        if self.excluded_users and event.user.lower() in self.excluded_users:
            return None

        if event.level not in SQL_EVENT_LEVELS:
            return None

        # 提取 SQL 和 duration
        sql = extract_sql(event.message)
        duration_ms = extract_duration_ms(event.message)
        key = event.pid or f"{event.user}|{event.database}|{event.client_host}"

        # 过滤非业务 SQL（心跳、框架表等）
        if sql and is_non_business_sql(sql):
            return None

        # 合并逻辑（复用 import_postgres_log_to_es.py 的 iter_docs_from_events）
        if sql and duration_ms:
            # 同一行包含 SQL + duration
            self._flush_pending(key)
            query_time = duration_ms_to_seconds(duration_ms) or self.default_query_time
            return build_pg_es_doc(event, sql, self.default_db_host, query_time)

        if sql:
            # 只有 SQL，没有 duration
            self._flush_pending(key)
            if key in self.pending_duration_by_key:
                # 有之前暂存的 duration
                query_time = self._pop_duration(key)
                return build_pg_es_doc(event, sql, self.default_db_host, query_time)
            else:
                # 暂存 SQL，等待后续 duration
                self.pending_sql_by_key[key] = PendingSql(event=event, sql=sql, collected_at=time.time())
                return None

        if duration_ms:
            # 只有 duration，没有 SQL
            pending = self.pending_sql_by_key.pop(key, None)
            if pending:
                query_time = duration_ms_to_seconds(duration_ms) or self.default_query_time
                return build_pg_es_doc(pending.event, pending.sql, self.default_db_host, query_time)
            else:
                # 暂存 duration，等待后续 SQL
                self.pending_duration_by_key[key] = duration_ms
                return None

        return None

    def _flush_pending(self, key: str) -> Optional[dict]:
        """清空某个 key 的暂存状态，返回未匹配的文档"""
        pending = self.pending_sql_by_key.pop(key, None)
        if pending:
            query_time = self._pop_duration(key)
            return build_pg_es_doc(pending.event, pending.sql, self.default_db_host, query_time)
        return None

    def _pop_duration(self, key: str) -> str:
        """取出暂存的 duration"""
        duration_ms = self.pending_duration_by_key.pop(key, None)
        if not duration_ms:
            return self.default_query_time
        return duration_ms_to_seconds(duration_ms) or self.default_query_time

    def flush_pending(self) -> None:
        """刷新超时未配对的 pending SQL，使用默认耗时写入 ES"""
        if not self.pending_sql_by_key:
            return

        now = time.time()
        expired_keys = [
            key for key, pending in self.pending_sql_by_key.items()
            if now - pending.collected_at >= self.pending_timeout
        ]

        for key in expired_keys:
            pending = self.pending_sql_by_key.pop(key)
            query_time = self._pop_duration(key)
            doc = build_pg_es_doc(pending.event, pending.sql, self.default_db_host, query_time)
            self.es_writer.add(doc)
            logger.debug(f"PG 超时刷新: {pending.sql[:50]}... (query_time={query_time}s)")

        if expired_keys:
            logger.info(f"PG 消费者: {len(expired_keys)} 条超时未配对 SQL 已用默认耗时写入")
