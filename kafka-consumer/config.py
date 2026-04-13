"""Kafka 消费者/生产者配置管理"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Kafka 配置
    kafka_bootstrap_servers: str = "172.20.40.166:9094"
    kafka_topic_pg: str = "log_push_pg"
    kafka_topic_udal: str = "log_push_udal"
    kafka_consumer_group_pg: str = "slow-sql-pg-consumer"
    kafka_consumer_group_udal: str = "slow-sql-udal-consumer"
    kafka_auto_offset_reset: str = "earliest"

    # ES 配置
    es_url: str = "http://127.0.0.1:9200"
    es_index_pattern: str = "triangle-mysql-*"
    es_username: Optional[str] = None
    es_password: Optional[str] = None
    es_use_ssl: bool = False

    # 生产者配置 - PG
    pg_log_path: str = "/var/log/postgresql/slow.log"
    pg_default_db_host: str = "127.0.0.1"
    pg_default_query_time: str = "0.10"
    pg_tz: str = "Asia/Shanghai"

    # PG 消费者过滤：排除监控/系统用户（逗号分隔）
    pg_excluded_users: str = "ctgmonitor,ctgadmin"

    # 生产者配置 - UDAL
    udal_log_path: str = "/var/log/udal/audit.log"
    udal_default_db_host: str = "127.0.0.1"
    udal_default_schema: str = "unknown"
    udal_default_cost_ms: int = 100

    # 消费者配置
    es_batch_size: int = 500
    es_flush_interval_seconds: float = 5.0
    udal_merge_timeout_seconds: int = 60

    # 断点续传配置
    checkpoint_dir: str = "/data/checkpoints"
    checkpoint_save_interval_seconds: int = 30

    # 运行模式: producer / consumer / all
    run_mode: str = "all"

    # 健康检查端口
    health_port: int = 10801
