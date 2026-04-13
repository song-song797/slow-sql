"""UDAL 审计日志生产者"""

import json
import logging
import re
import time
from typing import Optional

from .base import LogFileProducer

logger = logging.getLogger(__name__)

LINE_RE = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?P<payload>\{.*\})$")


class UdalProducer(LogFileProducer):
    """UDAL 审计日志生产者：解析每行，发送到 Kafka"""

    def parse_line(self, line: str) -> Optional[dict]:
        match = LINE_RE.match(line.strip())
        if not match:
            return None
        try:
            payload = json.loads(match.group("payload"))
        except json.JSONDecodeError:
            return None
        return {
            "timestamp": match.group("ts"),
            "payload": payload,
            "source": "udal",
            "collected_at": time.time(),
        }

    def should_send(self, parsed: dict) -> bool:
        """只发送 RECEIVE_REQUEST 和 END_REQUEST 事件"""
        event_type = parsed.get("payload", {}).get("eventType")
        return event_type in ("RECEIVE_REQUEST", "END_REQUEST")
