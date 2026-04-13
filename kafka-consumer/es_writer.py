"""ES 批量写入器"""

import hashlib
import logging
import time
from typing import Optional

from elasticsearch import Elasticsearch, helpers

logger = logging.getLogger(__name__)

# ES 索引 mapping，与 seed.sh 保持一致
INDEX_MAPPING = {
    "properties": {
        "timestamp": {"type": "long"},
        "query_time": {"type": "keyword"},
    }
}


class ESWriter:
    """批量写入 ES，与现有 es_service.py 的 ensure_index 模式一致"""

    def __init__(
        self,
        es_url: str = "http://127.0.0.1:9200",
        index_pattern: str = "triangle-mysql-*",
        es_username: Optional[str] = None,
        es_password: Optional[str] = None,
        es_use_ssl: bool = False,
        batch_size: int = 500,
        flush_interval: float = 5.0,
    ):
        self.index_pattern = index_pattern
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        # ES 客户端
        es_config = {"verify_certs": es_use_ssl}
        if es_username and es_password:
            es_config["basic_auth"] = (es_username, es_password)
        self.client = Elasticsearch(es_url, **es_config)

        self.actions: list[dict] = []
        self._last_flush = time.time()
        self._total_written = 0
        self._ensure_base_index()

    def _ensure_base_index(self) -> None:
        """确保基础索引存在"""
        base_index = self.index_pattern.replace("*", "local")
        try:
            if not self.client.indices.exists(index=base_index):
                self.client.indices.create(index=base_index, mappings=INDEX_MAPPING)
                logger.info(f"ES 索引已创建: {base_index}")
        except Exception as e:
            logger.warning(f"确保 ES 索引存在时出错: {e}")

    def _resolve_index(self, doc: dict) -> str:
        """根据文档内容确定写入哪个索引"""
        source = doc.get("_source", {})
        doc_type = source.get("type", "unknown")
        ts = source.get("timestamp", 0)

        # 按月分索引：triangle-mysql-pg-2026.04
        if ts > 0:
            from datetime import datetime
            dt = datetime.fromtimestamp(ts / 1000)
            month_str = dt.strftime("%Y.%m")
            return f"triangle-mysql-{doc_type}-{month_str}"

        return f"triangle-mysql-{doc_type}-local"

    def add(self, doc: dict) -> None:
        """添加文档到缓冲区"""
        index = doc.pop("_index", None) or self._resolve_index(doc)

        action = {
            "_op_type": "index",
            "_index": index,
            "_id": doc.get("_id") or hashlib.sha1(str(doc).encode()).hexdigest(),
            "_source": doc.get("_source", doc),
        }

        self.actions.append(action)

        if len(self.actions) >= self.batch_size:
            self.flush()

    def maybe_flush(self) -> None:
        """定时刷新，在消费空闲时调用"""
        if self.actions and time.time() - self._last_flush >= self.flush_interval:
            self.flush()

    def flush(self) -> None:
        """刷新缓冲区，批量写入 ES"""
        if not self.actions:
            return

        try:
            success, errors = helpers.bulk(self.client, self.actions, refresh=False)
            self._total_written += success
            if errors:
                logger.warning(f"ES bulk 写入部分失败: {len(errors)} 条错误")
            logger.debug(f"ES 写入 {success} 条，累计 {self._total_written} 条")
        except Exception as e:
            logger.error(f"ES bulk 写入异常: {e}", exc_info=True)
        finally:
            self.actions.clear()
            self._last_flush = time.time()

    @property
    def total_written(self) -> int:
        return self._total_written

    @property
    def buffered_count(self) -> int:
        return len(self.actions)
