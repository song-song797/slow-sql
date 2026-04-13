"""消费者基类：Kafka 消费 + 手动提交 offset"""

import json
import logging
import threading
from abc import ABC, abstractmethod
from typing import Optional

from confluent_kafka import Consumer, KafkaError, Message

from es_writer import ESWriter

logger = logging.getLogger(__name__)


class BaseConsumer(ABC):
    """Kafka 消费者基类"""

    def __init__(
        self,
        kafka_servers: str,
        topic: str,
        group_id: str,
        auto_offset_reset: str,
        es_writer: ESWriter,
    ):
        self.topic = topic
        self.es_writer = es_writer
        self._stop_event = threading.Event()
        self._message_count = 0
        self._error_count = 0

        self.consumer = Consumer({
            "bootstrap.servers": kafka_servers,
            "group.id": group_id,
            "auto.offset.reset": auto_offset_reset,
            "enable.auto.commit": False,
            "max.poll.interval.ms": 300000,
            "session.timeout.ms": 30000,
        })

    @abstractmethod
    def process_message(self, msg: Message) -> Optional[dict]:
        """子类实现：处理单条 Kafka 消息，返回 ES 文档或 None"""

    def run(self) -> None:
        """主消费循环"""
        logger.info(f"[{self.topic}] 消费者启动, group: {self.consumer._consumer_group_name if hasattr(self.consumer, '_consumer_group_name') else 'unknown'}")
        self.consumer.subscribe([self.topic])

        while not self._stop_event.is_set():
            msg = self.consumer.poll(timeout=1.0)

            if msg is None:
                self.es_writer.maybe_flush()
                self.flush_pending()
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error(f"[{self.topic}] Kafka 错误: {msg.error()}")
                self._error_count += 1
                continue

            try:
                doc = self.process_message(msg)
                if doc:
                    self.es_writer.add(doc)
                    self._message_count += 1

                # 手动提交 offset
                self.consumer.commit(asynchronous=False)
            except Exception as e:
                logger.error(f"[{self.topic}] 处理消息异常: {e}", exc_info=True)
                self._error_count += 1

        # 停止前刷新所有缓冲数据
        self.es_writer.flush()
        self.consumer.close()
        logger.info(f"[{self.topic}] 消费者停止, 共处理 {self._message_count} 条消息, 错误 {self._error_count} 条")

    def flush_pending(self) -> None:
        """子类可重写：刷新超时未配对的暂存数据"""
        pass

    def stop(self) -> None:
        """优雅停止"""
        logger.info(f"[{self.topic}] 消费者停止中...")
        self._stop_event.set()

    @property
    def message_count(self) -> int:
        return self._message_count

    @property
    def error_count(self) -> int:
        return self._error_count
