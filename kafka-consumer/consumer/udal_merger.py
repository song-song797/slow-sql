"""UDAL 事件合并器：通过 requestId 配对 RECEIVE_REQUEST 和 END_REQUEST"""

import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)


class UdalEventMerger:
    """合并 UDAL 的 RECEIVE_REQUEST 和 END_REQUEST 事件"""

    def __init__(self, timeout_seconds: int = 60, default_cost_ms: int = 100):
        self.timeout = timeout_seconds
        self.default_cost_ms = default_cost_ms
        self.pending: dict[int, dict] = {}  # requestId -> RECEIVE_REQUEST 数据
        self._lock = threading.Lock()

    def add_event(self, event: dict) -> Optional[dict]:
        """添加事件，如果配对成功返回完整文档，否则返回 None"""
        request_id = event.get("request_id")
        event_type = event.get("event_type")

        if request_id is None:
            return None

        with self._lock:
            if event_type == "RECEIVE_REQUEST":
                self.pending[request_id] = event
                return None
            elif event_type == "END_REQUEST":
                receive = self.pending.pop(request_id, None)
                if receive:
                    return self._merge(receive, event)
                # END 先到但没有对应的 REQUEST，忽略
                logger.debug(f"END_REQUEST 无配对的 RECEIVE_REQUEST: requestId={request_id}")
                return None
            return None

    def flush_expired(self) -> list[dict]:
        """返回超时未配对的 RECEIVE_REQUEST，使用默认耗时"""
        now = time.time()
        expired = []

        with self._lock:
            expired_ids = []
            for request_id, item in self.pending.items():
                event_time = item.get("collected_at", now)
                if now - event_time >= self.timeout:
                    expired.append(self._apply_default_cost(item))
                    expired_ids.append(request_id)

            for rid in expired_ids:
                del self.pending[rid]

        if expired:
            logger.info(f"UDAL 合并器: {len(expired)} 条超时未配对，使用默认耗时")

        return expired

    def _merge(self, receive: dict, end: dict) -> dict:
        """合并 REQUEST + END 事件"""
        cost_ms = end.get("cost", self.default_cost_ms)
        receive["query_time"] = f"{max(float(cost_ms), 0.0) / 1000:.3f}"
        return receive

    def _apply_default_cost(self, item: dict) -> dict:
        """对超时未配对的事件使用默认耗时"""
        item["query_time"] = f"{self.default_cost_ms / 1000:.3f}"
        return item

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self.pending)
