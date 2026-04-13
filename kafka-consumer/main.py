"""Kafka 消费者/生产者入口脚本"""

import logging
import os
import signal
import sys
import threading

from config import Settings
from es_writer import ESWriter
from health import HealthServer
from producer.pg_producer import PgProducer
from producer.udal_producer import UdalProducer
from consumer.pg_consumer import PgConsumer
from consumer.udal_consumer import UdalConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


def main():
    config = Settings()
    logger.info(f"运行模式: {config.run_mode}")

    # 确保断点续传目录存在
    os.makedirs(config.checkpoint_dir, exist_ok=True)

    # ES 写入器（消费者共用）
    es_writer = ESWriter(
        es_url=config.es_url,
        index_pattern=config.es_index_pattern,
        es_username=config.es_username,
        es_password=config.es_password,
        es_use_ssl=config.es_use_ssl,
        batch_size=config.es_batch_size,
        flush_interval=config.es_flush_interval_seconds,
    )

    components: list = []
    threads: list = []

    # 生产者
    if config.run_mode in ("producer", "all"):
        # PG 生产者
        if config.pg_log_path:
            pg_producer = PgProducer(
                kafka_servers=config.kafka_bootstrap_servers,
                topic=config.kafka_topic_pg,
                log_path=config.pg_log_path,
                checkpoint_dir=config.checkpoint_dir,
            )
            components.append(pg_producer)
            threads.append(threading.Thread(target=pg_producer.run, name="pg-producer", daemon=True))

        # UDAL 生产者
        if config.udal_log_path:
            udal_producer = UdalProducer(
                kafka_servers=config.kafka_bootstrap_servers,
                topic=config.kafka_topic_udal,
                log_path=config.udal_log_path,
                checkpoint_dir=config.checkpoint_dir,
            )
            components.append(udal_producer)
            threads.append(threading.Thread(target=udal_producer.run, name="udal-producer", daemon=True))

    # 消费者
    if config.run_mode in ("consumer", "all"):
        # PG 消费者
        pg_consumer = PgConsumer(
            kafka_servers=config.kafka_bootstrap_servers,
            topic=config.kafka_topic_pg,
            group_id=config.kafka_consumer_group_pg,
            auto_offset_reset=config.kafka_auto_offset_reset,
            es_writer=es_writer,
            default_db_host=config.pg_default_db_host,
            default_query_time=config.pg_default_query_time,
            pg_tz=config.pg_tz,
            excluded_users=config.pg_excluded_users,
        )
        components.append(pg_consumer)
        threads.append(threading.Thread(target=pg_consumer.run, name="pg-consumer", daemon=True))

        # UDAL 消费者
        udal_consumer = UdalConsumer(
            kafka_servers=config.kafka_bootstrap_servers,
            topic=config.kafka_topic_udal,
            group_id=config.kafka_consumer_group_udal,
            auto_offset_reset=config.kafka_auto_offset_reset,
            es_writer=es_writer,
            default_db_host=config.udal_default_db_host,
            default_schema=config.udal_default_schema,
            default_cost_ms=config.udal_default_cost_ms,
            merge_timeout=config.udal_merge_timeout_seconds,
        )
        components.append(udal_consumer)
        threads.append(threading.Thread(target=udal_consumer.run, name="udal-consumer", daemon=True))

    if not threads:
        logger.error("没有可启动的组件，请检查 RUN_MODE 配置")
        sys.exit(1)

    # 健康检查服务
    health_server = HealthServer(config.health_port, threads, es_writer)
    health_server.start()

    # 信号处理：优雅停止
    stop_event = threading.Event()

    def signal_handler(sig, frame):
        logger.info(f"收到信号 {sig}，正在停止...")
        for comp in components:
            comp.stop()
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动所有线程
    for t in threads:
        t.start()
        logger.info(f"线程已启动: {t.name}")

    logger.info(f"所有组件已启动，共 {len(threads)} 个线程")
    logger.info(f"健康检查: http://0.0.0.0:{config.health_port}/health")

    # 等待停止信号
    stop_event.wait()

    # 等待线程退出
    for t in threads:
        t.join(timeout=15)

    logger.info("所有组件已停止")


if __name__ == "__main__":
    main()
