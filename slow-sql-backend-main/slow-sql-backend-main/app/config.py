import json
from typing import Any, Optional
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "local"

    # API Configuration
    api_key: str = "dev-api-key"

    # Elasticsearch Configuration
    es_url: Optional[str] = "http://127.0.0.1:9200"
    es_host: str = "127.0.0.1"
    es_port: int = 9200
    es_index_pattern: str = "triangle-mysql-*"
    es_username: Optional[str] = None
    es_password: Optional[str] = None
    es_use_ssl: bool = False

    # MySQL Database Configuration
    database_url: Optional[str] = None
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "slow_sql"
    db_password: str = "slow_sql"
    db_name: str = "slow_sql_db"

    # Report Generation Configuration
    report_provider: str = "api1_workflow"
    report_api_base_url: str = "http://your-host/api/v2/workflow/invoke"
    report_api_timeout: int = 300
    workflow_id: Optional[str] = None
    workflow_file_content_max_chars: int = 14000
    data_source_secret_key: Optional[str] = None

    # Analysis context metadata auto-fetch
    metadata_auto_fetch_enabled: bool = True
    metadata_auto_fetch_db_type: str = "mysql"
    metadata_auto_fetch_username: Optional[str] = None
    metadata_auto_fetch_password: Optional[str] = None
    metadata_auto_fetch_mysql_username: Optional[str] = None
    metadata_auto_fetch_mysql_password: Optional[str] = None
    metadata_auto_fetch_postgresql_username: Optional[str] = None
    metadata_auto_fetch_postgresql_password: Optional[str] = None
    metadata_db_overrides: Optional[str] = None
    metadata_auto_fetch_max_workers: int = 4
    metadata_auto_fetch_max_tables_per_request: int = 8
    metadata_auto_fetch_total_timeout_seconds: float = 6.0
    metadata_auto_fetch_connect_timeout_seconds: int = 3
    metadata_auto_fetch_read_timeout_seconds: int = 3
    metadata_auto_fetch_write_timeout_seconds: int = 3

    def get_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        encoded_user = quote_plus(self.db_user)
        encoded_password = quote_plus(self.db_password)
        return (
            f"mysql+pymysql://{encoded_user}:{encoded_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset=utf8mb4"
        )

    def get_es_url(self) -> str:
        if self.es_url:
            return self.es_url

        scheme = "https" if self.es_use_ssl else "http"
        return f"{scheme}://{self.es_host}:{self.es_port}"

    def get_report_base_url(self) -> str:
        return self.report_api_base_url.rstrip("/")

    def get_metadata_fetch_username(self) -> str:
        return self.metadata_auto_fetch_username or self.db_user

    def get_metadata_fetch_password(self) -> str:
        return self.metadata_auto_fetch_password or self.db_password

    def normalize_db_type(self, db_type: Optional[str]) -> str:
        value = (db_type or self.metadata_auto_fetch_db_type or "mysql").strip().lower()
        if value in {"postgres", "postgresql", "pgsql"}:
            return "postgresql"
        return "mysql"

    def get_default_port_for_db_type(self, db_type: Optional[str]) -> int:
        normalized = self.normalize_db_type(db_type)
        if normalized == "postgresql":
            return 5432
        return 3306

    def get_metadata_fetch_username_for_db_type(self, db_type: Optional[str]) -> str:
        normalized = self.normalize_db_type(db_type)
        if normalized == "postgresql":
            return (
                self.metadata_auto_fetch_postgresql_username
                or self.metadata_auto_fetch_username
                or self.db_user
            )
        return (
            self.metadata_auto_fetch_mysql_username
            or self.metadata_auto_fetch_username
            or self.db_user
        )

    def get_metadata_fetch_password_for_db_type(self, db_type: Optional[str]) -> str:
        normalized = self.normalize_db_type(db_type)
        if normalized == "postgresql":
            return (
                self.metadata_auto_fetch_postgresql_password
                or self.metadata_auto_fetch_password
                or self.db_password
            )
        return (
            self.metadata_auto_fetch_mysql_password
            or self.metadata_auto_fetch_password
            or self.db_password
        )

    def _load_metadata_db_overrides(self) -> dict[str, dict[str, Any]]:
        raw_value = (self.metadata_db_overrides or "").strip()
        if not raw_value:
            return {}
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            return {}
        if not isinstance(parsed, dict):
            return {}
        return {
            str(key): value
            for key, value in parsed.items()
            if isinstance(value, dict)
        }

    def _override_matches_metadata_target(
        self,
        override: dict[str, Any],
        *,
        db_type: str,
        db_ip: Optional[str],
        db_port: int,
        db_name: Optional[str],
    ) -> bool:
        normalized_db_type = self.normalize_db_type(db_type)
        match_db_type = override.get("match_db_type")
        if match_db_type and self.normalize_db_type(match_db_type) != normalized_db_type:
            return False

        match_host = override.get("match_host")
        if match_host and str(match_host).strip() != (db_ip or ""):
            return False

        match_port = override.get("match_port")
        if match_port is not None and int(match_port) != int(db_port):
            return False

        match_db_name = override.get("match_db_name")
        if match_db_name and str(match_db_name).strip() != (db_name or ""):
            return False

        target_db_name = (
            override.get("fetch_db_name")
            or override.get("db_name")
            or db_name
        )
        allow_db_name_override = bool(override.get("allow_db_name_override"))
        if target_db_name and db_name and str(target_db_name).strip() != str(db_name).strip():
            if not allow_db_name_override:
                return False

        return True

    def resolve_metadata_fetch_target(
        self,
        db_type: Optional[str],
        db_ip: Optional[str],
        db_port: Optional[int],
        db_name: Optional[str],
    ) -> dict[str, Any]:
        normalized_db_type = self.normalize_db_type(db_type)
        target = {
            "db_type": normalized_db_type,
            "host": db_ip,
            "port": db_port or self.get_default_port_for_db_type(normalized_db_type),
            "db_name": db_name,
            "username": self.get_metadata_fetch_username_for_db_type(normalized_db_type),
            "password": self.get_metadata_fetch_password_for_db_type(normalized_db_type),
        }

        override = self.find_metadata_fetch_override(
            db_type=normalized_db_type,
            db_ip=db_ip,
            db_port=target["port"],
            db_name=db_name,
        )
        if not override:
            return target

        override_db_type = self.normalize_db_type(override.get("db_type") or normalized_db_type)
        target["db_type"] = override_db_type
        target["host"] = override.get("host") or target["host"]
        target["port"] = int(override.get("port") or target["port"])
        target["db_name"] = (
            override.get("fetch_db_name")
            or override.get("db_name")
            or target["db_name"]
        )
        target["username"] = (
            override.get("username")
            or self.get_metadata_fetch_username_for_db_type(override_db_type)
        )
        target["password"] = (
            override.get("password")
            or self.get_metadata_fetch_password_for_db_type(override_db_type)
        )
        return target

    def find_metadata_fetch_override(
        self,
        db_type: Optional[str],
        db_ip: Optional[str],
        db_port: Optional[int],
        db_name: Optional[str],
    ) -> Optional[dict[str, Any]]:
        normalized_db_type = self.normalize_db_type(db_type)
        target_port = db_port or self.get_default_port_for_db_type(normalized_db_type)
        overrides = self._load_metadata_db_overrides()
        if not db_name:
            return None

        candidate_keys = []
        if db_ip and target_port:
            candidate_keys.append(f"{normalized_db_type}:{db_ip}:{target_port}:{db_name}")
        candidate_keys.append(f"{normalized_db_type}:{db_name}")
        candidate_keys.append(str(db_name))

        for key in candidate_keys:
            candidate = overrides.get(key)
            if not candidate:
                continue
            if self._override_matches_metadata_target(
                candidate,
                db_type=normalized_db_type,
                db_ip=db_ip,
                db_port=target_port,
                db_name=db_name,
            ):
                return candidate
        return None


settings = Settings()
