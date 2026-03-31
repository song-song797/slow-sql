from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

DATABASE_URL = settings.get_database_url()

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def init_database() -> None:
    """
    初始化数据库表结构。
    """
    import app.models  # noqa: F401  # 确保所有模型都被注册

    Base.metadata.create_all(bind=engine)
    _ensure_analysis_task_columns()
    _ensure_database_info_columns()
    _ensure_data_source_columns()


def _ensure_analysis_task_columns() -> None:
    inspector = inspect(engine)
    if "analysis_task" not in inspector.get_table_names():
        return

    existing_columns = {column["name"]: column for column in inspector.get_columns("analysis_task")}
    is_mysql = engine.dialect.name == "mysql"
    column_statements = {
        "analysis_context_json": (
            "ALTER TABLE analysis_task "
            f"ADD COLUMN analysis_context_json {'LONGTEXT' if is_mysql else 'TEXT'} NULL COMMENT '结构化分析上下文(JSON)'"
        ),
        "analysis_result_json": (
            "ALTER TABLE analysis_task "
            f"ADD COLUMN analysis_result_json {'LONGTEXT' if is_mysql else 'TEXT'} NULL COMMENT '结构化分析结果(JSON)'"
        ),
        "is_hidden": (
            "ALTER TABLE analysis_task "
            f"ADD COLUMN is_hidden {'TINYINT(1)' if is_mysql else 'BOOLEAN'} NOT NULL DEFAULT 0 COMMENT '是否从列表中隐藏'"
        ),
        "data_source_id": (
            "ALTER TABLE analysis_task "
            "ADD COLUMN data_source_id INTEGER NULL COMMENT '数据源ID'"
        ),
        "data_source_name": (
            "ALTER TABLE analysis_task "
            "ADD COLUMN data_source_name VARCHAR(128) NULL COMMENT '数据源名称'"
        ),
        "target_db_type": (
            "ALTER TABLE analysis_task "
            "ADD COLUMN target_db_type VARCHAR(32) NULL COMMENT '目标数据库类型'"
        ),
        "target_host": (
            "ALTER TABLE analysis_task "
            "ADD COLUMN target_host VARCHAR(255) NULL COMMENT '目标数据库主机'"
        ),
        "target_port": (
            "ALTER TABLE analysis_task "
            "ADD COLUMN target_port INTEGER NULL COMMENT '目标数据库端口'"
        ),
        "target_db_name": (
            "ALTER TABLE analysis_task "
            "ADD COLUMN target_db_name VARCHAR(128) NULL COMMENT '目标数据库名称'"
        ),
        "remote_session_id": (
            "ALTER TABLE analysis_task "
            "ADD COLUMN remote_session_id VARCHAR(128) NULL COMMENT '远端工作流会话ID'"
        ),
        "remote_message_id": (
            "ALTER TABLE analysis_task "
            "ADD COLUMN remote_message_id VARCHAR(128) NULL COMMENT '远端工作流消息ID'"
        ),
    }
    large_text_columns = {
        "sql_text": "拼接后的SQL文本",
        "analysis_context_json": "结构化分析上下文(JSON)",
        "analysis_result_json": "结构化分析结果(JSON)",
        "error_message": "失败原因",
    }

    with engine.begin() as connection:
        for column_name, statement in column_statements.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))
        if "is_hidden" not in existing_columns:
            connection.execute(text("UPDATE analysis_task SET is_hidden = 0 WHERE is_hidden IS NULL"))

        if is_mysql:
            refreshed_columns = {column["name"]: column for column in inspect(engine).get_columns("analysis_task")}
            for column_name, comment in large_text_columns.items():
                column_info = refreshed_columns.get(column_name)
                if not column_info:
                    continue
                type_name = type(column_info["type"]).__name__.lower()
                if type_name == "longtext":
                    continue
                connection.execute(
                    text(
                        "ALTER TABLE analysis_task "
                        f"MODIFY COLUMN {column_name} LONGTEXT NULL COMMENT '{comment}'"
                    )
                )


def _ensure_database_info_columns() -> None:
    inspector = inspect(engine)
    if "database_info" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("database_info")}
    column_statements = {
        "db_type": (
            "ALTER TABLE database_info "
            "ADD COLUMN db_type VARCHAR(32) NULL COMMENT '数据库类型(mysql/postgresql)'"
        ),
    }

    with engine.begin() as connection:
        for column_name, statement in column_statements.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))
        if "db_type" not in existing_columns:
            connection.execute(text("UPDATE database_info SET db_type = 'mysql' WHERE db_type IS NULL"))


def _ensure_data_source_columns() -> None:
    inspector = inspect(engine)
    if "data_source" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("data_source")}
    is_mysql = engine.dialect.name == "mysql"
    timestamp_type = "TIMESTAMP NULL" if is_mysql else "TIMESTAMP NULL"
    column_statements = {
        "enabled": (
            "ALTER TABLE data_source "
            f"ADD COLUMN enabled {'TINYINT(1)' if is_mysql else 'BOOLEAN'} NOT NULL DEFAULT 1 COMMENT '是否启用'"
        ),
        "last_test_status": (
            "ALTER TABLE data_source "
            "ADD COLUMN last_test_status VARCHAR(32) NULL COMMENT '最近一次测试状态'"
        ),
        "last_test_message": (
            "ALTER TABLE data_source "
            f"ADD COLUMN last_test_message {'LONGTEXT' if is_mysql else 'TEXT'} NULL COMMENT '最近一次测试结果'"
        ),
        "last_test_at": (
            "ALTER TABLE data_source "
            f"ADD COLUMN last_test_at {timestamp_type} COMMENT '最近一次测试时间'"
        ),
        "created_at": (
            "ALTER TABLE data_source "
            "ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'"
        ),
        "updated_at": (
            "ALTER TABLE data_source "
            "ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间'"
        ),
    }

    with engine.begin() as connection:
        for column_name, statement in column_statements.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))


def check_database_connection() -> tuple[bool, str]:
    """
    检查数据库连通性。
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as exc:  # pragma: no cover - 运行时诊断逻辑
        return False, str(exc)


def get_db():
    """
    数据库会话依赖
    用于FastAPI的依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
