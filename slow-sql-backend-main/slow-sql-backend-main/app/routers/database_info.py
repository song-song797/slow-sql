from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)
from app.dependencies import verify_api_key
from app.database import get_db
from app.services.database_service import DatabaseService
from app.services.remote_db_service import RemoteDatabaseService
from app.schemas.database_info import (
    DatabaseInfoCreate,
    DatabaseInfoUpdate,
    DatabaseInfoResponse,
    DatabaseInfoListResponse,
    RemoteDatabaseConnection,
)

router = APIRouter(prefix="/api/v1/database-info", tags=["数据库信息管理"])


@router.get("", response_model=DatabaseInfoListResponse, summary="获取数据库信息列表")
async def get_database_info_list(
    page: int = Query(1, ge=1, description="分页页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db_name: Optional[str] = Query(None, description="数据库名筛选"),
    table_name: Optional[str] = Query(None, description="表名筛选"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    获取数据库信息列表，支持分页和筛选
    """
    result = DatabaseService.get_list(
        db=db,
        page=page,
        page_size=page_size,
        db_name=db_name,
        table_name=table_name,
    )
    return result


@router.get("/{id}", response_model=DatabaseInfoResponse, summary="获取单条数据库信息")
async def get_database_info(
    id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    根据ID获取单条数据库信息记录
    """
    db_info = DatabaseService.get_by_id(db, id)
    if not db_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"数据库信息记录 {id} 不存在"
        )
    return db_info


@router.post("", response_model=DatabaseInfoResponse, status_code=status.HTTP_201_CREATED, summary="创建数据库信息")
async def create_database_info(
    data: DatabaseInfoCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    创建新的数据库信息记录
    """
    db_info = DatabaseService.create(db, data)
    return db_info


@router.put("/{id}", response_model=DatabaseInfoResponse, summary="更新数据库信息")
async def update_database_info(
    id: int,
    data: DatabaseInfoUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    更新数据库信息记录
    """
    db_info = DatabaseService.update(db, id, data)
    if not db_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"数据库信息记录 {id} 不存在"
        )
    return db_info


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除数据库信息")
async def delete_database_info(
    id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    删除数据库信息记录
    """
    success = DatabaseService.delete(db, id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"数据库信息记录 {id} 不存在"
        )
    return None


@router.post("/fetch-remote", response_model=Dict[str, Any], summary="从远程数据库获取表信息")
async def fetch_remote_table_info(
    connection_params: RemoteDatabaseConnection,
    api_key: str = Depends(verify_api_key),
):
    """
    从远程MySQL数据库获取表信息（表行数、DDL等）
    """
    try:
        # 使用新的fetch_database_info方法，支持获取单个表或整个数据库的所有表
        table_info_list = RemoteDatabaseService.fetch_database_info(
            db_type=connection_params.db_type,
            host=connection_params.host,
            port=connection_params.port,
            db_name=connection_params.db_name,
            username=connection_params.username,
            password=connection_params.password,
            table_name=connection_params.table_name
        )
        return {
            "success": True,
            "message": "成功获取远程数据库表信息",
            "data": table_info_list
        }
    except Exception as e:
        logger.error(f"获取远程数据库表信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取远程数据库表信息失败: {str(e)}"
        ) from e

