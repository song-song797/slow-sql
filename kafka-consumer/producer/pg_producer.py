"""PG 慢日志生产者"""

import logging
import time
from typing import Optional

from .base import LogFileProducer

logger = logging.getLogger(__name__)


class PgProducer(LogFileProducer):
    """PG 日志生产者：逐行发送原始日志到 Kafka"""

    def parse_line(self, line: str) -> Optional[dict]:
        stripped = line.strip()
        if not stripped:
            return None
        return {
            "raw_line": stripped,
            "source": "postgresql",
            "collected_at": time.time(),
        }

    def should_send(self, parsed: dict) -> bool:
        """发送所有非空行，过滤逻辑交给消费者"""
        return True
