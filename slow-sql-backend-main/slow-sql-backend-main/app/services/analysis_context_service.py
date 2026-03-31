from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import re
import time
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.data_source import DataSource
from app.schemas.database_info import DatabaseInfoCreate
from app.schemas.sql_analysis import SQLAnalysisItem
from app.services.data_source_crypto import DataSourceCryptoService
from app.services.database_service import DatabaseService
from app.services.es_service import ESService
from app.services.remote_db_service import RemoteDatabaseService


class AnalysisContextService:
    TABLE_PATTERNS = (
        r"\bFROM\s+([`\"\w\.]+)",
        r"\bJOIN\s+([`\"\w\.]+)",
        r"\bUPDATE\s+([`\"\w\.]+)",
        r"\bINTO\s+([`\"\w\.]+)",
        r"\bDELETE\s+FROM\s+([`\"\w\.]+)",
    )

    @staticmethod
    def _normalize_identifier(raw_name: str) -> str:
        identifier = raw_name.strip().strip(",;")
        identifier = identifier.split()[0]
        identifier = identifier.replace("`", "").replace('"', "")
        if "." in identifier:
            identifier = identifier.split(".")[-1]
        return identifier.lower()

    @staticmethod
    def _normalize_whitespace(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    @classmethod
    def _extract_mysql_columns(cls, ddl: str) -> List[Dict[str, Any]]:
        columns: List[Dict[str, Any]] = []
        inside_columns = False

        for raw_line in ddl.splitlines():
            line = raw_line.strip().rstrip(",")
            if not line:
                continue
            if line.upper().startswith("CREATE TABLE"):
                inside_columns = True
                continue
            if inside_columns and line.startswith(")"):
                break
            if not inside_columns:
                continue
            upper_line = line.upper()
            if upper_line.startswith(("PRIMARY KEY", "UNIQUE KEY", "KEY ", "INDEX ", "CONSTRAINT ")):
                continue

            match = re.match(
                r"^`?(?P<name>[\w]+)`?\s+(?P<type>[^\s,]+(?:\([^)]+\))?)(?P<rest>.*)$",
                line,
                flags=re.IGNORECASE,
            )
            if not match:
                continue

            rest = match.group("rest") or ""
            default_match = re.search(r"\bDEFAULT\s+((?:'[^']*')|(?:\"[^\"]*\")|(?:[^\s,]+))", rest, flags=re.IGNORECASE)
            columns.append(
                {
                    "name": match.group("name"),
                    "data_type": cls._normalize_whitespace(match.group("type")),
                    "nullable": "NO" if "NOT NULL" in rest.upper() else "YES",
                    "default": default_match.group(1) if default_match else None,
                }
            )

        return columns

    @classmethod
    def _extract_postgresql_columns(cls, ddl: str) -> List[Dict[str, Any]]:
        columns: List[Dict[str, Any]] = []
        collecting = False

        for raw_line in ddl.splitlines():
            stripped = raw_line.strip().rstrip(",")
            if not stripped:
                continue
            if stripped.upper().startswith("CREATE TABLE"):
                collecting = True
                continue
            if collecting and stripped.startswith(")"):
                break
            if not collecting:
                continue

            definition = cls._normalize_whitespace(stripped)
            upper_definition = definition.upper()
            if upper_definition.startswith(("CONSTRAINT ", "PRIMARY KEY", "UNIQUE ", "FOREIGN KEY", "CHECK ")):
                continue

            match = re.match(
                r'^"?(?P<name>[\w]+)"?\s+(?P<type>.+?)(?=(?:\s+COLLATE|\s+DEFAULT|\s+NOT\s+NULL|\s+NULL|\s+CONSTRAINT|\s+PRIMARY\s+KEY|\s+REFERENCES|\s+CHECK|$))(?P<rest>.*)$',
                definition,
                flags=re.IGNORECASE,
            )
            if not match:
                continue

            rest = match.group("rest") or ""
            default_match = re.search(
                r"\bDEFAULT\s+(.+?)(?=(?:\s+NOT\s+NULL|\s+NULL|\s+CONSTRAINT|\s+REFERENCES|\s+CHECK|$))",
                rest,
                flags=re.IGNORECASE,
            )
            columns.append(
                {
                    "name": match.group("name"),
                    "data_type": cls._normalize_whitespace(match.group("type")),
                    "nullable": "NO" if "NOT NULL" in rest.upper() else "YES",
                    "default": cls._normalize_whitespace(default_match.group(1)) if default_match else None,
                }
            )

        return columns

    @classmethod
    def _extract_mysql_indexes(cls, ddl: str) -> List[Dict[str, Any]]:
        indexes: List[Dict[str, Any]] = []
        for raw_line in ddl.splitlines():
            line = raw_line.strip().rstrip(",")
            if not line:
                continue
            primary_match = re.match(r"PRIMARY KEY\s*\((?P<columns>[^)]+)\)", line, flags=re.IGNORECASE)
            if primary_match:
                columns = [col.strip(" `\"") for col in primary_match.group("columns").split(",")]
                indexes.append(
                    {
                        "name": "PRIMARY",
                        "index_type": "PRIMARY KEY",
                        "columns": columns,
                        "unique": True,
                    }
                )
                continue

            unique_match = re.match(
                r"UNIQUE\s+(?:KEY|INDEX)\s+`?(?P<name>[\w]+)`?\s*\((?P<columns>[^)]+)\)",
                line,
                flags=re.IGNORECASE,
            )
            if unique_match:
                columns = [col.strip(" `\"") for col in unique_match.group("columns").split(",")]
                indexes.append(
                    {
                        "name": unique_match.group("name"),
                        "index_type": "UNIQUE",
                        "columns": columns,
                        "unique": True,
                    }
                )
                continue

            key_match = re.match(
                r"(?:KEY|INDEX)\s+`?(?P<name>[\w]+)`?\s*\((?P<columns>[^)]+)\)",
                line,
                flags=re.IGNORECASE,
            )
            if key_match:
                columns = [col.strip(" `\"") for col in key_match.group("columns").split(",")]
                indexes.append(
                    {
                        "name": key_match.group("name"),
                        "index_type": "INDEX",
                        "columns": columns,
                        "unique": False,
                    }
                )
        return indexes

    @classmethod
    def _extract_postgresql_indexes(cls, ddl: str) -> List[Dict[str, Any]]:
        indexes: List[Dict[str, Any]] = []
        for raw_line in ddl.splitlines():
            line = cls._normalize_whitespace(raw_line)
            if not line or "CREATE" not in line.upper() or "INDEX" not in line.upper():
                continue
            match = re.match(
                r'CREATE\s+(?P<unique>UNIQUE\s+)?INDEX\s+"?(?P<name>[\w]+)"?\s+ON\s+"?(?P<table>[\w]+)"?(?:\s+USING\s+(?P<method>[\w]+))?\s*\((?P<columns>[^)]+)\)',
                line,
                flags=re.IGNORECASE,
            )
            if not match:
                continue
            columns = [col.strip().strip('"') for col in match.group("columns").split(",")]
            indexes.append(
                {
                    "name": match.group("name"),
                    "index_type": (match.group("method") or "INDEX").upper(),
                    "columns": columns,
                    "unique": bool(match.group("unique")),
                }
            )
        return indexes

    @classmethod
    def _build_metadata_details(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        ddl = row.get("ddl") or ""
        db_type = settings.normalize_db_type(row.get("db_type"))

        if db_type == "postgresql":
            index_definitions = cls._extract_postgresql_indexes(ddl)
            column_definitions = cls._extract_postgresql_columns(ddl)
        else:
            index_definitions = cls._extract_mysql_indexes(ddl)
            column_definitions = cls._extract_mysql_columns(ddl)

        normalized = dict(row)
        normalized["db_type"] = db_type
        normalized["index_definitions"] = index_definitions
        normalized["column_definitions"] = column_definitions
        return normalized

    @classmethod
    def extract_table_names(cls, sql: str) -> List[str]:
        sql_text = sql or ""
        tables: List[str] = []
        for pattern in cls.TABLE_PATTERNS:
            for raw_name in re.findall(pattern, sql_text, flags=re.IGNORECASE):
                name = cls._normalize_identifier(raw_name)
                if name and name not in tables:
                    tables.append(name)
        return tables

    @staticmethod
    def _target_key(
        db_type: Optional[str],
        db_ip: Optional[str],
        db_port: Optional[int],
        dbname: Optional[str],
    ) -> tuple[str, str, int, str]:
        return (
            settings.normalize_db_type(db_type),
            db_ip or "",
            db_port or 0,
            dbname or "",
        )

    @classmethod
    def build_context(
        cls,
        request: List[SQLAnalysisItem],
        db: Session,
        data_source: Optional[DataSource] = None,
    ) -> Dict[str, Any]:
        grouped_targets: Dict[tuple[str, str, int, str], Dict[str, Any]] = {}
        es_service = ESService()
        source_records: List[Dict[str, Any]] = []
        sql_observations: List[Dict[str, Any]] = []
        seen_observations: set[tuple[str, str, str]] = set()

        for item in request:
            db_type = settings.normalize_db_type(item.db_type)
            db_port = item.db_port or settings.get_default_port_for_db_type(db_type)
            tables = cls.extract_table_names(item.sql)
            key = cls._target_key(db_type, item.db_ip, db_port, item.dbname)

            if key not in grouped_targets:
                grouped_targets[key] = {
                    "db_type": db_type,
                    "dbname": item.dbname,
                    "db_ip": item.db_ip,
                    "db_port": db_port,
                    "tables": [],
                }

            target_tables = grouped_targets[key]["tables"]
            for table in tables:
                if table not in target_tables:
                    target_tables.append(table)

            if item.source_record_id and item.source_index:
                source_record = es_service.get_record_by_id(item.source_index, item.source_record_id)
                if source_record:
                    source_records.append(source_record)

            observation_key = (item.template_sql or item.sql, item.dbname or "", db_type, item.db_ip or "")
            if observation_key not in seen_observations:
                seen_observations.add(observation_key)
                if item.observation_override:
                    observation = {
                        "cluster_count": item.observation_override.cluster_count,
                        "exact_match_count": item.observation_override.cluster_count,
                        "min_query_time_ms": item.observation_override.min_query_time_ms,
                        "avg_query_time_ms": item.observation_override.avg_query_time_ms or 0.0,
                        "max_query_time_ms": item.observation_override.max_query_time_ms or 0.0,
                        "latest_timestamp": item.observation_override.latest_timestamp,
                    }
                else:
                    observation = es_service.get_sql_observability(
                        sql=item.sql,
                        dbname=item.dbname,
                        db_type=db_type,
                        upstream_addr=item.db_ip,
                    )
                observation.update(
                    {
                        "sql": item.sql,
                        "template_sql": item.template_sql,
                        "db_name": item.dbname,
                        "db_type": db_type,
                        "db_ip": item.db_ip,
                    }
                )
                sql_observations.append(observation)

        matched_tables: List[Dict[str, Any]] = []
        missing_tables: List[Dict[str, Any]] = []
        auto_fetched_tables: List[Dict[str, Any]] = []
        fetch_errors: List[Dict[str, Any]] = []

        for target in grouped_targets.values():
            table_names = target["tables"]
            if not table_names:
                continue

            metadata_rows = DatabaseService.find_tables(
                db=db,
                db_type=target["db_type"],
                db_name=target["dbname"],
                db_ip=target["db_ip"],
                db_port=target["db_port"],
                table_names=table_names,
            )
            found_names = set()
            for row in metadata_rows:
                found_names.add(row.table_name)
                matched_tables.append(
                    {
                        "db_type": row.db_type,
                        "db_name": row.db_name,
                        "db_ip": row.db_ip,
                        "db_port": row.db_port,
                        "db_version": row.db_version,
                        "table_name": row.table_name,
                        "table_rows": row.table_rows,
                        "ddl": row.ddl,
                    }
                )

            for table_name in table_names:
                if table_name not in found_names:
                    missing_tables.append(
                        {
                            "db_type": target["db_type"],
                            "db_name": target["dbname"],
                            "db_ip": target["db_ip"],
                            "db_port": target["db_port"],
                            "table_name": table_name,
                        }
                    )

        if settings.metadata_auto_fetch_enabled and missing_tables:
            auto_fetched_tables, fetch_errors = cls._auto_fetch_missing_tables(
                db=db,
                missing_tables=missing_tables,
                data_source=data_source,
            )
            if auto_fetched_tables:
                matched_tables, missing_tables = cls._reload_metadata(
                    db=db,
                    grouped_targets=list(grouped_targets.values()),
                )

        matched_tables = [cls._build_metadata_details(row) for row in matched_tables]
        auto_fetched_tables = [cls._build_metadata_details(row) for row in auto_fetched_tables]

        return {
            "sql_list": [item.sql for item in request],
            "db_targets": list(grouped_targets.values()),
            "matched_tables": matched_tables,
            "missing_tables": missing_tables,
            "auto_fetched_tables": auto_fetched_tables,
            "fetch_errors": fetch_errors,
            "source_records": source_records,
            "sql_observations": sql_observations,
        }

    @classmethod
    def _reload_metadata(
        cls,
        db: Session,
        grouped_targets: List[Dict[str, Any]],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        matched_tables: List[Dict[str, Any]] = []
        missing_tables: List[Dict[str, Any]] = []

        for target in grouped_targets:
            table_names = target["tables"]
            if not table_names:
                continue

            metadata_rows = DatabaseService.find_tables(
                db=db,
                db_type=target["db_type"],
                db_name=target["dbname"],
                db_ip=target["db_ip"],
                db_port=target["db_port"],
                table_names=table_names,
            )
            found_names = set()
            for row in metadata_rows:
                found_names.add(row.table_name)
                matched_tables.append(
                    {
                        "db_type": row.db_type,
                        "db_name": row.db_name,
                        "db_ip": row.db_ip,
                        "db_port": row.db_port,
                        "db_version": row.db_version,
                        "table_name": row.table_name,
                        "table_rows": row.table_rows,
                        "ddl": row.ddl,
                    }
                )

            for table_name in table_names:
                if table_name not in found_names:
                    missing_tables.append(
                        {
                            "db_type": target["db_type"],
                            "db_name": target["dbname"],
                            "db_ip": target["db_ip"],
                            "db_port": target["db_port"],
                            "table_name": table_name,
                        }
                    )

        return matched_tables, missing_tables

    @classmethod
    def _auto_fetch_missing_tables(
        cls,
        db: Session,
        missing_tables: List[Dict[str, Any]],
        data_source: Optional[DataSource] = None,
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        auto_fetched_tables: List[Dict[str, Any]] = []
        fetch_errors: List[Dict[str, Any]] = []
        unique_missing_tables: List[Dict[str, Any]] = []
        seen_keys: set[tuple[Any, Any, Any, Any, Any]] = set()

        for table in missing_tables:
            table_key = (
                table.get("db_type"),
                table.get("db_name"),
                table.get("db_ip"),
                table.get("db_port"),
                table.get("table_name"),
            )
            if table_key in seen_keys:
                continue
            seen_keys.add(table_key)
            unique_missing_tables.append(table)

        max_tables = max(1, settings.metadata_auto_fetch_max_tables_per_request)
        fetch_candidates = unique_missing_tables[:max_tables]
        skipped_tables = unique_missing_tables[max_tables:]
        for table in skipped_tables:
            fetch_errors.append(
                {
                    **table,
                    "error": f"自动补拉数量超出单次请求上限 {max_tables}",
                }
            )

        if not fetch_candidates:
            return auto_fetched_tables, fetch_errors

        worker_count = max(1, min(settings.metadata_auto_fetch_max_workers, len(fetch_candidates)))
        future_map = {}
        executor = ThreadPoolExecutor(max_workers=worker_count)
        budget_seconds = max(0.1, settings.metadata_auto_fetch_total_timeout_seconds)
        started_at = time.monotonic()

        try:
            for table in fetch_candidates:
                db_type = settings.normalize_db_type(table.get("db_type"))
                db_name = table.get("db_name")
                db_ip = table.get("db_ip")
                db_port = table.get("db_port")
                table_name = table.get("table_name")

                if not (db_name and db_ip and db_port and table_name):
                    fetch_errors.append(
                        {
                            **table,
                            "error": "缺少自动补拉所需的数据库连接信息",
                        }
                    )
                    continue

                if data_source is not None:
                    # Respect metadata overrides even when a data source is explicitly selected.
                    # This keeps local logical库名到真实元数据库的映射生效，同时默认沿用数据源凭据。
                    fetch_target = settings.resolve_metadata_fetch_target(
                        db_type=db_type,
                        db_ip=db_ip,
                        db_port=db_port,
                        db_name=db_name,
                    )
                    fetch_target["username"] = data_source.username
                    fetch_target["password"] = DataSourceCryptoService.decrypt(data_source.encrypted_password)
                else:
                    fetch_target = settings.resolve_metadata_fetch_target(
                        db_type=db_type,
                        db_ip=db_ip,
                        db_port=db_port,
                        db_name=db_name,
                    )
                future = executor.submit(
                    RemoteDatabaseService.fetch_table_info,
                    fetch_target["db_type"],
                    fetch_target["host"],
                    fetch_target["port"],
                    fetch_target["db_name"],
                    fetch_target["username"],
                    fetch_target["password"],
                    table_name,
                )
                future_map[future] = {
                    "request_table": table,
                    "fetch_target": fetch_target,
                }

            pending = set(future_map.keys())
            while pending:
                remaining_budget = budget_seconds - (time.monotonic() - started_at)
                if remaining_budget <= 0:
                    for future in pending:
                        table = future_map[future]
                        future.cancel()
                        fetch_errors.append(
                            {
                                **table,
                                "error": f"自动补拉超时，超过总预算 {budget_seconds:.1f} 秒",
                            }
                        )
                    break

                done, pending = wait(
                    pending,
                    timeout=min(remaining_budget, 0.2),
                    return_when=FIRST_COMPLETED,
                )
                if not done:
                    continue

                for future in done:
                    future_metadata = future_map[future]
                    table = future_metadata["request_table"]
                    try:
                        table_info = future.result()
                        table_info.update(
                            {
                                "db_type": settings.normalize_db_type(table.get("db_type")),
                                "db_name": table.get("db_name"),
                                "db_ip": table.get("db_ip"),
                                "db_port": table.get("db_port"),
                            }
                        )
                        DatabaseService.upsert_table_info(db, DatabaseInfoCreate(**table_info))
                        auto_fetched_tables.append(table_info)
                    except Exception as exc:
                        fetch_errors.append(
                            {
                                **table,
                                "error": str(exc),
                            }
                        )
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        return auto_fetched_tables, fetch_errors
