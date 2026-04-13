"""生产者基类：文件 tail + 断点续传 + Kafka 发送"""

import json
import logging
import os
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from confluent_kafka import Producer

logger = logging.getLogger(__name__)


class LogFileProducer(ABC):
    """日志文件生产者基类，监控文件变化并发送到 Kafka"""

    def __init__(self, kafka_servers: str, topic: str, log_path: str, checkpoint_dir: str):
        self.topic = topic
        self.log_path = log_path
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_path = os.path.join(checkpoint_dir, f"{topic}.json")
        self._stop_event = threading.Event()

        # Kafka 生产者
        self.producer = Producer({
            "bootstrap.servers": kafka_servers,
            "linger.ms": 100,
            "retry.backoff.ms": 500,
            "message.timeout.ms": 30000,
        })

        # 断点续传状态
        self._checkpoint_inode: Optional[int] = None
        self._checkpoint_pos: int = 0
        self._last_save_time: float = 0
        self._load_checkpoint()

    def _load_checkpoint(self) -> None:
        """加载断点续传信息"""
        try:
            if os.path.exists(self.checkpoint_path):
                with open(self.checkpoint_path, "r") as f:
                    data = json.load(f)
                    self._checkpoint_inode = data.get("inode")
                    self._checkpoint_pos = data.get("position", 0)
                    logger.info(f"[{self.topic}] 加载断点: inode={self._checkpoint_inode}, pos={self._checkpoint_pos}")
        except Exception as e:
            logger.warning(f"[{self.topic}] 加载断点失败，从头开始: {e}")
            self._checkpoint_inode = None
            self._checkpoint_pos = 0

    def _save_checkpoint(self, inode: int, position: int) -> None:
        """保存断点续传信息"""
        try:
            os.makedirs(self.checkpoint_dir, exist_ok=True)
            with open(self.checkpoint_path, "w") as f:
                json.dump({"inode": inode, "position": position}, f)
            self._checkpoint_inode = inode
            self._checkpoint_pos = position
        except Exception as e:
            logger.error(f"[{self.topic}] 保存断点失败: {e}")

    def _detect_rotation(self, current_inode: int) -> bool:
        """检测文件是否被轮转（inode 变化）"""
        if self._checkpoint_inode is None:
            return False
        return current_inode != self._checkpoint_inode

    @abstractmethod
    def parse_line(self, line: str) -> Optional[dict]:
        """子类实现：解析日志行，返回 dict 或 None"""

    @abstractmethod
    def should_send(self, parsed: dict) -> bool:
        """子类实现：判断是否值得发送"""

    def _delivery_report(self, err, msg) -> None:
        """Kafka 发送回调"""
        if err:
            logger.error(f"[{self.topic}] 发送失败: {err}")
        # msg对象在回调中被释放，不持有引用

    def _send(self, data: dict) -> None:
        """发送消息到 Kafka"""
        try:
            value = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
            self.producer.produce(self.topic, value=value, callback=self._delivery_report)
        except Exception as e:
            logger.error(f"[{self.topic}] produce 异常: {e}")

    def run(self) -> None:
        """主循环：tail 文件 → 解析 → 发送"""
        logger.info(f"[{self.topic}] 生产者启动，监控文件: {self.log_path}")

        while not self._stop_event.is_set():
            try:
                self._tail_file()
            except FileNotFoundError:
                logger.warning(f"[{self.topic}] 文件不存在: {self.log_path}，等待重试...")
                self._stop_event.wait(5.0)
            except Exception as e:
                logger.error(f"[{self.topic}] tail 异常: {e}", exc_info=True)
                self._stop_event.wait(5.0)

    def _tail_file(self) -> None:
        """尾随文件读取"""
        path = Path(self.log_path)

        # 等待文件出现
        while not path.exists():
            if self._stop_event.is_set():
                return
            logger.info(f"[{self.topic}] 等待文件: {self.log_path}")
            self._stop_event.wait(5.0)

        current_inode = path.stat().st_ino

        # 检测文件轮转
        if self._detect_rotation(current_inode):
            logger.info(f"[{self.topic}] 检测到文件轮转，从头读取新文件")
            self._checkpoint_pos = 0

        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            # seek 到断点位置
            fh.seek(self._checkpoint_pos)

            while not self._stop_event.is_set():
                line = fh.readline()

                if line:
                    parsed = self.parse_line(line)
                    if parsed and self.should_send(parsed):
                        self._send(parsed)

                    # 更新位置
                    self._checkpoint_pos = fh.tell()

                    # 定期保存断点
                    now = time.time()
                    if now - self._last_save_time >= 30:
                        self._save_checkpoint(current_inode, self._checkpoint_pos)
                        self._last_save_time = now
                        # 同时 flush Kafka 缓冲
                        self.producer.poll(0)
                else:
                    # 没有新数据，短暂等待
                    self._stop_event.wait(0.5)

                    # 检查文件是否被轮转
                    try:
                        new_inode = path.stat().st_ino
                        if new_inode != current_inode:
                            logger.info(f"[{self.topic}] 检测到文件轮转")
                            self._save_checkpoint(current_inode, self._checkpoint_pos)
                            return  # 退出重新打开文件
                    except FileNotFoundError:
                        return

        # 最终保存断点
        self._save_checkpoint(current_inode, self._checkpoint_pos)

    def stop(self) -> None:
        """优雅停止"""
        logger.info(f"[{self.topic}] 生产者停止中...")
        self._stop_event.set()
        try:
            self.producer.flush(timeout=10)
        except Exception as e:
            logger.error(f"[{self.topic}] flush 失败: {e}")
