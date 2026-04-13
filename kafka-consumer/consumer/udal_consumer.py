"""UDAL 消费者：从 Kafka 消费，合并 REQUEST+END 事件，写入 ES"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from confluent_kafka import Message

from parsers.udal_parser import build_udal_es_doc, clean_sql, parse_user_field
from consumer.base import BaseConsumer
from consumer.udal_merger import UdalEventMerger
from es_writer import ESWriter

logger = logging.getLogger(__name__)


class UdalConsumer(BaseConsumer):
    """UDAL 消费者：通过 requestId 配对 REQUEST+END 事件"""

    def __init__(
        self,
        kafka_servers: str,
        topic: str,
        group_id: str,
        auto_offset_reset: str,
        es_writer: ESWriter,
        default_db_host: str = "127.0.0.1",
        default_schema: str = "unknown",
        default_cost_ms: int = 100,
        merge_timeout: int = 60,
        tz_offset_hours: int = 8,
    ):
        super().__init__(kafka_servers, topic, group_id, auto_offset_reset, es_writer)
        self.default_db_host = default_db_host
        self.default_schema = default_schema
        self.tz_offset_hours = tz_offset_hours

        self.merger = UdalEventMerger(
            timeout_seconds=merge_timeout,
            default_cost_ms=default_cost_ms,
        )

    def process_message(self, msg: Message) -> Optional[dict]:
        data = json.loads(msg.value().decode("utf-8"))
        payload = data.get("payload", {})
        event_type = payload.get("eventType")
        request_id = payload.get("requestId")

        if not request_id or not event_type:
            return None

        if event_type == "RECEIVE_REQUEST":
            return self._handle_receive(payload, data.get("timestamp", ""), request_id)
        elif event_type == "END_REQUEST":
            return self._handle_end(payload, request_id)

        return None

    def _handle_receive(self, payload: dict, ts_str: str, request_id: int) -> Optional[dict]:
        """处理 RECEIVE_REQUEST 事件"""
        sql = clean_sql(payload.get("sql", ""))
        if not sql:
            return None

        dbuser, client_ip, client_port = parse_user_field(payload.get("user", ""))

        # 解析时间戳
        timestamp = self._parse_timestamp(ts_str)

        event_data = {
            "timestamp": timestamp,
            "sql": sql,
            "dbname": payload.get("schema") or self.default_schema,
            "dbuser": dbuser,
            "client_ip": client_ip,
            "client_port": client_port,
            "request_id": request_id,
            "event_type": "RECEIVE_REQUEST",
            "source_tag": "kafka-udal",
            "collected_at": __import__("time").time(),
        }

        # 尝试配对
        merged = self.merger.add_event(event_data)
        if merged:
            return build_udal_es_doc(merged, self.default_db_host, "kafka-udal")
        return None

    def _handle_end(self, payload: dict, request_id: int) -> Optional[dict]:
        """处理 END_REQUEST 事件"""
        event_data = {
            "request_id": request_id,
            "event_type": "END_REQUEST",
            "cost": payload.get("cost", 0),
            "collected_at": __import__("time").time(),
        }

        merged = self.merger.add_event(event_data)
        if merged:
            return build_udal_es_doc(merged, self.default_db_host, "kafka-udal")
        return None

    def _parse_timestamp(self, ts_str: str) -> datetime:
        """解析时间戳字符串"""
        if not ts_str:
            return datetime.now(tz=timezone(timedelta(hours=self.tz_offset_hours)))
        try:
            return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone(timedelta(hours=self.tz_offset_hours))
            )
        except ValueError:
            return datetime.now(tz=timezone(timedelta(hours=self.tz_offset_hours)))

    def flush_pending(self) -> None:
        """刷新超时未配对的 UDAL 事件"""
        expired = self.merger.flush_expired()
        for item in expired:
            doc = build_udal_es_doc(item, self.default_db_host, "kafka-udal")
            self.es_writer.add(doc)
        if expired:
            logger.info(f"UDAL 消费者: {len(expired)} 条超时未配对事件已用默认耗时写入")
