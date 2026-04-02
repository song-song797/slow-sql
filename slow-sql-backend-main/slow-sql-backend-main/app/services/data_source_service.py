from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.data_source import DataSource
from app.schemas.database_info import DatabaseInfoCreate
from app.schemas.data_source import DataSourceCreate, DataSourceUpdate
from app.services.database_service import DatabaseService
from app.services.data_source_crypto import DataSourceCryptoService
from app.services.remote_db_service import RemoteDatabaseService


class DataSourceService:
    @staticmethod
    def _resolve_runtime_connection_target(data_source: DataSource) -> dict:
        password = DataSourceService.get_password(data_source)
        override = settings.find_metadata_fetch_override(
            db_type=data_source.db_type,
            db_ip=data_source.host,
            db_port=data_source.port,
            db_name=data_source.db_name,
        )
        if not override:
            return {
                "db_type": data_source.db_type,
                "host": data_source.host,
                "port": data_source.port,
                "db_name": data_source.db_name,
                "username": data_source.username,
                "password": password,
            }

        resolved_target = settings.resolve_metadata_fetch_target(
            db_type=data_source.db_type,
            db_ip=data_source.host,
            db_port=data_source.port,
            db_name=data_source.db_name,
        )
        return {
            "db_type": resolved_target["db_type"],
            "host": resolved_target["host"],
            "port": resolved_target["port"],
            "db_name": resolved_target["db_name"],
            "username": resolved_target.get("username") or data_source.username,
            "password": resolved_target.get("password") or password,
        }

    @staticmethod
    def _normalize_payload(payload: dict) -> dict:
        normalized = dict(payload)
        if normalized.get("db_type"):
            normalized["db_type"] = normalized["db_type"].strip().lower()
        if normalized.get("host"):
            normalized["host"] = normalized["host"].strip()
        if normalized.get("db_name"):
            normalized["db_name"] = normalized["db_name"].strip()
        if normalized.get("username"):
            normalized["username"] = normalized["username"].strip()
        if normalized.get("name"):
            normalized["name"] = normalized["name"].strip()
        return normalized

    @staticmethod
    def list(
        db: Session,
        *,
        enabled: Optional[bool] = None,
        db_type: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db_name: Optional[str] = None,
        last_test_status: Optional[str] = None,
    ) -> dict:
        query = db.query(DataSource)
        if enabled is not None:
            query = query.filter(DataSource.enabled == enabled)
        if db_type:
            query = query.filter(DataSource.db_type == db_type.strip().lower())
        if host:
            query = query.filter(DataSource.host == host.strip())
        if port is not None:
            query = query.filter(DataSource.port == port)
        if db_name:
            query = query.filter(DataSource.db_name == db_name.strip())
        if last_test_status:
            query = query.filter(DataSource.last_test_status == last_test_status.strip().lower())

        items = query.order_by(DataSource.updated_at.desc(), DataSource.id.desc()).all()
        return {"total": len(items), "items": items}

    @staticmethod
    def get_by_id(db: Session, data_source_id: int) -> Optional[DataSource]:
        return db.query(DataSource).filter(DataSource.id == data_source_id).first()

    @staticmethod
    def create(db: Session, data: DataSourceCreate) -> DataSource:
        payload = DataSourceService._normalize_payload(data.model_dump(exclude={"password"}))
        payload["encrypted_password"] = DataSourceCryptoService.encrypt(data.password)
        obj = DataSource(**payload)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, data_source_id: int, data: DataSourceUpdate) -> Optional[DataSource]:
        obj = DataSourceService.get_by_id(db, data_source_id)
        if not obj:
            return None

        payload = DataSourceService._normalize_payload(data.model_dump(exclude_unset=True, exclude={"password"}))
        for key, value in payload.items():
            setattr(obj, key, value)
        if data.password is not None:
            obj.encrypted_password = DataSourceCryptoService.encrypt(data.password)
            obj.last_test_status = None
            obj.last_test_message = "密码已更新，请重新测试连接"
            obj.last_test_at = None

        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def set_enabled(db: Session, data_source_id: int, enabled: bool) -> Optional[DataSource]:
        obj = DataSourceService.get_by_id(db, data_source_id)
        if not obj:
            return None
        obj.enabled = enabled
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_password(data_source: DataSource) -> str:
        return DataSourceCryptoService.decrypt(data_source.encrypted_password)

    @staticmethod
    def test_connection(db: Session, data_source: DataSource) -> dict:
        connection_target = DataSourceService._resolve_runtime_connection_target(data_source)
        result = RemoteDatabaseService.test_connection(
            db_type=connection_target["db_type"],
            host=connection_target["host"],
            port=connection_target["port"],
            db_name=connection_target["db_name"],
            username=connection_target["username"],
            password=connection_target["password"],
        )
        data_source.last_test_status = "success"
        data_source.last_test_message = result["message"]
        data_source.last_test_at = datetime.now()
        db.commit()
        db.refresh(data_source)
        result["last_test_status"] = data_source.last_test_status
        result["last_test_at"] = data_source.last_test_at
        return result

    @staticmethod
    def mark_test_failed(db: Session, data_source: DataSource, message: str) -> None:
        data_source.last_test_status = "failed"
        data_source.last_test_message = message
        data_source.last_test_at = datetime.now()
        db.commit()

    @staticmethod
    def sync_metadata(
        db: Session,
        data_source: DataSource,
        *,
        table_name: Optional[str] = None,
    ) -> List[Dict]:
        connection_target = DataSourceService._resolve_runtime_connection_target(data_source)
        records = RemoteDatabaseService.fetch_database_info(
            db_type=connection_target["db_type"],
            host=connection_target["host"],
            port=connection_target["port"],
            db_name=connection_target["db_name"],
            username=connection_target["username"],
            password=connection_target["password"],
            table_name=table_name,
        )
        for record in records:
            logical_record = dict(record)
            logical_record["db_type"] = settings.normalize_db_type(data_source.db_type)
            logical_record["db_name"] = data_source.db_name
            logical_record["db_ip"] = data_source.host
            logical_record["db_port"] = data_source.port
            DatabaseService.upsert_table_info(db, DatabaseInfoCreate(**logical_record))
        return records

    @staticmethod
    def require_ready_for_analysis(data_source: Optional[DataSource]) -> DataSource:
        if not data_source:
            raise ValueError("所选数据源不存在")
        if not data_source.enabled:
            raise ValueError("所选数据源已停用，请先启用后再分析")
        if data_source.last_test_status != "success":
            raise ValueError("所选数据源尚未通过连接测试，请先测试连接")
        return data_source
