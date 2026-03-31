from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.models.database_info import DatabaseInfo
from app.schemas.database_info import DatabaseInfoCreate, DatabaseInfoUpdate
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """数据库信息CRUD服务"""
    
    @staticmethod
    def get_list(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        db_name: Optional[str] = None,
        table_name: Optional[str] = None,
    ) -> dict:
        """
        获取数据库信息列表（支持分页和筛选）
        """
        query = db.query(DatabaseInfo)
        
        # 筛选条件
        if db_name:
            query = query.filter(DatabaseInfo.db_name == db_name)
        if table_name:
            query = query.filter(DatabaseInfo.table_name == table_name)
        
        # 获取总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }
    
    @staticmethod
    def get_by_id(db: Session, id: int) -> Optional[DatabaseInfo]:
        """
        根据ID获取单条记录
        """
        return db.query(DatabaseInfo).filter(DatabaseInfo.id == id).first()

    @staticmethod
    def find_tables(
        db: Session,
        db_type: Optional[str],
        db_name: Optional[str],
        db_ip: Optional[str],
        db_port: Optional[int],
        table_names: List[str],
    ) -> List[DatabaseInfo]:
        if not table_names:
            return []

        base_query = db.query(DatabaseInfo)
        if db_type:
            exact_type_rows = base_query.filter(
                DatabaseInfo.db_type == db_type,
                DatabaseInfo.table_name.in_(table_names),
            )
            if db_name:
                exact_type_rows = exact_type_rows.filter(DatabaseInfo.db_name == db_name)
            if db_ip:
                exact_type_rows = exact_type_rows.filter(DatabaseInfo.db_ip == db_ip)
            if db_port is not None:
                exact_type_port_rows = exact_type_rows.filter(DatabaseInfo.db_port == db_port).all()
                if exact_type_port_rows:
                    return exact_type_port_rows
            exact_type_rows = exact_type_rows.all()
            if exact_type_rows:
                return exact_type_rows

        base_query = db.query(DatabaseInfo)
        if db_name:
            base_query = base_query.filter(DatabaseInfo.db_name == db_name)
        if db_ip:
            base_query = base_query.filter(DatabaseInfo.db_ip == db_ip)

        if db_port is not None:
            exact_rows = base_query.filter(
                DatabaseInfo.db_port == db_port,
                DatabaseInfo.table_name.in_(table_names),
            ).all()
            if exact_rows:
                return exact_rows

        return base_query.filter(DatabaseInfo.table_name.in_(table_names)).all()
    
    @staticmethod
    def create(db: Session, data: DatabaseInfoCreate) -> DatabaseInfo:
        """
        创建数据库信息记录
        """
        db_info = DatabaseInfo(**data.model_dump())
        db.add(db_info)
        db.commit()
        db.refresh(db_info)
        return db_info

    @staticmethod
    def upsert_table_info(db: Session, data: DatabaseInfoCreate) -> DatabaseInfo:
        existing = db.query(DatabaseInfo).filter(
            DatabaseInfo.db_type == data.db_type,
            DatabaseInfo.db_name == data.db_name,
            DatabaseInfo.db_ip == data.db_ip,
            DatabaseInfo.db_port == data.db_port,
            DatabaseInfo.table_name == data.table_name,
        ).first()

        if existing:
            update_data = DatabaseInfoUpdate(**data.model_dump())
            return DatabaseService.update(db, existing.id, update_data)

        return DatabaseService.create(db, data)
    
    @staticmethod
    def update(db: Session, id: int, data: DatabaseInfoUpdate) -> Optional[DatabaseInfo]:
        """
        更新数据库信息记录
        """
        db_info = db.query(DatabaseInfo).filter(DatabaseInfo.id == id).first()
        if not db_info:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_info, key, value)
        
        db.commit()
        db.refresh(db_info)
        return db_info
    
    @staticmethod
    def delete(db: Session, id: int) -> bool:
        """
        删除数据库信息记录
        """
        db_info = db.query(DatabaseInfo).filter(DatabaseInfo.id == id).first()
        if not db_info:
            return False
        
        db.delete(db_info)
        db.commit()
        return True
