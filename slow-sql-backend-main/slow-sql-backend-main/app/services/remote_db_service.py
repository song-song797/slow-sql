import logging
from typing import Any, Dict, Optional
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import settings
from app.database import SessionLocal
from app.schemas.database_info import DatabaseInfoCreate
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)


class RemoteDatabaseService:
    """远程数据库服务类，用于从远程数据库获取表信息。"""

    @staticmethod
    def get_connection_string(db_type: str, host: str, port: int, db_name: str, username: str, password: str) -> str:
        normalized_db_type = settings.normalize_db_type(db_type)
        if normalized_db_type == "mysql":
            encoded_username = quote_plus(username)
            encoded_password = quote_plus(password)
            return f"mysql+pymysql://{encoded_username}:{encoded_password}@{host}:{port}/{db_name}?charset=utf8mb4"
        if normalized_db_type == "postgresql":
            encoded_username = quote_plus(username)
            encoded_password = quote_plus(password)
            return f"postgresql+pg8000://{encoded_username}:{encoded_password}@{host}:{port}/{db_name}"
        raise ValueError(f"不支持的数据库类型: {db_type}")

    @staticmethod
    def _create_engine(
        db_type: str,
        host: str,
        port: int,
        db_name: str,
        username: str,
        password: str,
    ) -> Engine:
        conn_str = RemoteDatabaseService.get_connection_string(
            db_type=db_type,
            host=host,
            port=port,
            db_name=db_name,
            username=username,
            password=password,
        )
        connect_args: dict[str, Any]
        if settings.normalize_db_type(db_type) == "postgresql":
            connect_args = {
                "timeout": settings.metadata_auto_fetch_connect_timeout_seconds,
            }
        else:
            connect_args = {
                "connect_timeout": settings.metadata_auto_fetch_connect_timeout_seconds,
                "read_timeout": settings.metadata_auto_fetch_read_timeout_seconds,
                "write_timeout": settings.metadata_auto_fetch_write_timeout_seconds,
            }

        return create_engine(
            conn_str,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args=connect_args,
        )

    @staticmethod
    def _quote_mysql_identifier(identifier: str) -> str:
        return f"`{identifier.replace('`', '``')}`"

    @staticmethod
    def _quote_postgresql_identifier(identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'

    @staticmethod
    def _get_mysql_table_names(connection, db_name: str) -> list[str]:
        statement = text(
            "SELECT TABLE_NAME "
            "FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = :db_name"
        )
        return connection.execute(statement, {"db_name": db_name}).scalars().all()

    @staticmethod
    def _get_mysql_table_rows(connection, db_name: str, table_name: str) -> int:
        statement = text(
            "SELECT TABLE_ROWS "
            "FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = :table_name"
        )
        row_count = connection.execute(
            statement,
            {"db_name": db_name, "table_name": table_name},
        ).scalar()
        if row_count is not None and row_count >= 0:
            row_count_int = int(row_count)
            if row_count_int > 0:
                return row_count_int

        shadow_statement = text(
            "SELECT estimated_rows "
            "FROM __shadow_table_stats "
            "WHERE table_name = :table_name "
            "LIMIT 1"
        )
        try:
            shadow_rows = connection.execute(
                shadow_statement,
                {"table_name": table_name},
            ).scalar()
        except Exception:
            shadow_rows = None

        if shadow_rows is None or shadow_rows < 0:
            return 0
        return int(shadow_rows)

    @staticmethod
    def _get_mysql_table_ddl(connection, table_name: str) -> str:
        quoted_table = RemoteDatabaseService._quote_mysql_identifier(table_name)
        row = connection.execute(text(f"SHOW CREATE TABLE {quoted_table}")).fetchone()
        if not row or len(row) < 2:
            raise RuntimeError(f"未能获取表 {table_name} 的 DDL")
        return row[1]

    @staticmethod
    def _get_mysql_version(connection) -> str:
        return str(connection.execute(text("SELECT VERSION()")).scalar() or "")

    @staticmethod
    def _get_postgresql_table_names(connection) -> list[str]:
        statement = text(
            "SELECT tablename "
            "FROM pg_catalog.pg_tables "
            "WHERE schemaname NOT IN ('pg_catalog', 'information_schema')"
        )
        return connection.execute(statement).scalars().all()

    @staticmethod
    def _resolve_postgresql_table_schema(connection, table_name: str) -> Optional[str]:
        statement = text(
            "SELECT table_schema "
            "FROM information_schema.tables "
            "WHERE table_name = :table_name "
            "AND table_schema NOT IN ('pg_catalog', 'information_schema') "
            "ORDER BY CASE WHEN table_schema = 'public' THEN 0 ELSE 1 END, table_schema "
            "LIMIT 1"
        )
        return connection.execute(statement, {"table_name": table_name}).scalar()

    @staticmethod
    def _get_postgresql_table_rows(connection, table_name: str) -> int:
        schema_name = RemoteDatabaseService._resolve_postgresql_table_schema(connection, table_name)
        if not schema_name:
            return 0
        statement = text(
            "SELECT COALESCE(c.reltuples, 0) "
            "FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = :schema_name AND c.relname = :table_name "
            "AND c.relkind IN ('r', 'p') "
            "LIMIT 1"
        )
        row_count = connection.execute(
            statement,
            {"schema_name": schema_name, "table_name": table_name},
        ).scalar()
        return int(float(row_count or 0))

    @staticmethod
    def _get_postgresql_columns(connection, table_name: str) -> list[tuple]:
        schema_name = RemoteDatabaseService._resolve_postgresql_table_schema(connection, table_name)
        if not schema_name:
            return []
        statement = text(
            "SELECT column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns "
            "WHERE table_schema = :schema_name AND table_name = :table_name "
            "ORDER BY ordinal_position"
        )
        return connection.execute(
            statement,
            {"schema_name": schema_name, "table_name": table_name},
        ).fetchall()

    @staticmethod
    def _build_postgresql_ddl(table_name: str, columns: list[tuple]) -> str:
        if not columns:
            raise RuntimeError(f"未能获取表 {table_name} 的列信息")
        column_lines = []
        for column_name, data_type, is_nullable, column_default in columns:
            line = f'  "{column_name}" {data_type}'
            if column_default is not None:
                line += f" DEFAULT {column_default}"
            if is_nullable == "NO":
                line += " NOT NULL"
            column_lines.append(line)
        joined_columns = ",\n".join(column_lines)
        return f'CREATE TABLE "{table_name}" (\n{joined_columns}\n);'

    @staticmethod
    def _get_postgresql_table_ddl(connection, table_name: str) -> str:
        columns = RemoteDatabaseService._get_postgresql_columns(connection, table_name)
        return RemoteDatabaseService._build_postgresql_ddl(table_name, columns)

    @staticmethod
    def _get_postgresql_version(connection) -> str:
        return str(connection.execute(text("SHOW server_version")).scalar() or "")

    @staticmethod
    def _count_mysql_tables(connection, db_name: str) -> int:
        statement = text(
            "SELECT COUNT(*) "
            "FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = :db_name"
        )
        return int(connection.execute(statement, {"db_name": db_name}).scalar() or 0)

    @staticmethod
    def _count_postgresql_tables(connection) -> int:
        statement = text(
            "SELECT COUNT(*) "
            "FROM pg_catalog.pg_tables "
            "WHERE schemaname NOT IN ('pg_catalog', 'information_schema')"
        )
        return int(connection.execute(statement).scalar() or 0)

    @staticmethod
    def _persist_table_info(db, table_info: Dict[str, Any]) -> None:
        DatabaseService.upsert_table_info(db, DatabaseInfoCreate(**table_info))

    @staticmethod
    def _persist_table_info_list(table_info_list: list[Dict[str, Any]]) -> None:
        db = SessionLocal()
        try:
            for table_info in table_info_list:
                RemoteDatabaseService._persist_table_info(db, table_info)
        finally:
            db.close()

    @staticmethod
    def fetch_database_info(
        db_type: str,
        host: str,
        port: int,
        db_name: str,
        username: str,
        password: str,
        table_name: Optional[str] = None,
    ) -> list[Dict[str, Any]]:
        normalized_db_type = settings.normalize_db_type(db_type)

        if table_name:
            result = [
                RemoteDatabaseService.fetch_table_info(
                    db_type=normalized_db_type,
                    host=host,
                    port=port,
                    db_name=db_name,
                    username=username,
                    password=password,
                    table_name=table_name,
                )
            ]
            RemoteDatabaseService._persist_table_info_list(result)
            return result

        logger.info("开始获取远程数据库所有表信息: %s@%s:%s/%s", db_type, host, port, db_name)
        engine = RemoteDatabaseService._create_engine(
            db_type=normalized_db_type,
            host=host,
            port=port,
            db_name=db_name,
            username=username,
            password=password,
        )

        try:
            with engine.connect() as connection:
                if normalized_db_type == "postgresql":
                    table_names = RemoteDatabaseService._get_postgresql_table_names(connection)
                else:
                    table_names = RemoteDatabaseService._get_mysql_table_names(connection, db_name)

            all_tables_info = [
                RemoteDatabaseService.fetch_table_info(
                    db_type=normalized_db_type,
                    host=host,
                    port=port,
                    db_name=db_name,
                    username=username,
                    password=password,
                    table_name=current_table_name,
                )
                for current_table_name in table_names
            ]
            logger.info("成功获取远程数据库 %s 的所有表信息，共 %s 个表", db_name, len(all_tables_info))
            RemoteDatabaseService._persist_table_info_list(all_tables_info)
            return all_tables_info
        finally:
            engine.dispose()

    @staticmethod
    def fetch_table_info(
        db_type: str,
        host: str,
        port: int,
        db_name: str,
        username: str,
        password: str,
        table_name: str,
    ) -> Dict[str, Any]:
        normalized_db_type = settings.normalize_db_type(db_type)

        logger.info("开始从远程数据库获取表信息: %s@%s:%s/%s/%s", db_type, host, port, db_name, table_name)
        engine = RemoteDatabaseService._create_engine(
            db_type=normalized_db_type,
            host=host,
            port=port,
            db_name=db_name,
            username=username,
            password=password,
        )

        try:
            with engine.connect() as connection:
                if normalized_db_type == "postgresql":
                    row_count = RemoteDatabaseService._get_postgresql_table_rows(connection, table_name)
                    ddl = RemoteDatabaseService._get_postgresql_table_ddl(connection, table_name)
                    version = RemoteDatabaseService._get_postgresql_version(connection)
                else:
                    row_count = RemoteDatabaseService._get_mysql_table_rows(connection, db_name, table_name)
                    ddl = RemoteDatabaseService._get_mysql_table_ddl(connection, table_name)
                    version = RemoteDatabaseService._get_mysql_version(connection)

            return {
                "db_type": normalized_db_type,
                "db_name": db_name,
                "db_ip": host,
                "db_port": port,
                "db_version": version,
                "table_name": table_name,
                "table_rows": row_count,
                "ddl": ddl,
            }
        except Exception as exc:
            logger.error("获取表信息失败: %s", exc)
            raise
        finally:
            engine.dispose()

    @staticmethod
    def test_connection(
        db_type: str,
        host: str,
        port: int,
        db_name: str,
        username: str,
        password: str,
    ) -> Dict[str, Any]:
        normalized_db_type = settings.normalize_db_type(db_type)
        engine = RemoteDatabaseService._create_engine(
            db_type=normalized_db_type,
            host=host,
            port=port,
            db_name=db_name,
            username=username,
            password=password,
        )

        try:
            with engine.connect() as connection:
                if normalized_db_type == "postgresql":
                    version = RemoteDatabaseService._get_postgresql_version(connection)
                    table_count = RemoteDatabaseService._count_postgresql_tables(connection)
                else:
                    version = RemoteDatabaseService._get_mysql_version(connection)
                    table_count = RemoteDatabaseService._count_mysql_tables(connection, db_name)

            return {
                "success": True,
                "message": f"连接成功，共检测到 {table_count} 张表",
                "db_version": version,
                "table_count": table_count,
            }
        finally:
            engine.dispose()
