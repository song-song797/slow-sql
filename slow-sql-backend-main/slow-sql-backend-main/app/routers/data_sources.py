import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import verify_api_key
from app.schemas.data_source import (
    DataSourceCreate,
    DataSourceListResponse,
    DataSourceResponse,
    DataSourceSyncRequest,
    DataSourceSyncResponse,
    DataSourceTestResponse,
    DataSourceUpdate,
)
from app.services.data_source_service import DataSourceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/data-sources", tags=["数据源管理"])


@router.get("", response_model=DataSourceListResponse, summary="获取数据源列表")
async def list_data_sources(
    enabled: Optional[bool] = Query(None),
    db_type: Optional[str] = Query(None),
    host: Optional[str] = Query(None),
    port: Optional[int] = Query(None),
    db_name: Optional[str] = Query(None),
    last_test_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    return DataSourceService.list(
        db=db,
        enabled=enabled,
        db_type=db_type,
        host=host,
        port=port,
        db_name=db_name,
        last_test_status=last_test_status,
    )


@router.get("/{data_source_id}", response_model=DataSourceResponse, summary="获取单个数据源")
async def get_data_source(
    data_source_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    item = DataSourceService.get_by_id(db, data_source_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据源不存在")
    return item


@router.post("", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED, summary="创建数据源")
async def create_data_source(
    request: DataSourceCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    try:
        return DataSourceService.create(db, request)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{data_source_id}", response_model=DataSourceResponse, summary="更新数据源")
async def update_data_source(
    data_source_id: int,
    request: DataSourceUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    try:
        item = DataSourceService.update(db, data_source_id, request)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据源不存在")
    return item


@router.post("/{data_source_id}/test", response_model=DataSourceTestResponse, summary="测试数据源连接")
async def test_data_source(
    data_source_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    item = DataSourceService.get_by_id(db, data_source_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据源不存在")

    try:
        return DataSourceService.test_connection(db, item)
    except Exception as exc:
        DataSourceService.mark_test_failed(db, item, str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"测试连接失败: {exc}",
        ) from exc


@router.post("/{data_source_id}/sync-metadata", response_model=DataSourceSyncResponse, summary="同步数据源元数据")
async def sync_data_source_metadata(
    data_source_id: int,
    request: DataSourceSyncRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    item = DataSourceService.get_by_id(db, data_source_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据源不存在")

    try:
        records = DataSourceService.sync_metadata(db, item, table_name=request.table_name)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"同步元数据失败: {exc}",
        ) from exc

    return DataSourceSyncResponse(
        success=True,
        message="元数据同步成功",
        synced_count=len(records),
    )


@router.post("/{data_source_id}/enable", response_model=DataSourceResponse, summary="启用数据源")
async def enable_data_source(
    data_source_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    item = DataSourceService.set_enabled(db, data_source_id, True)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据源不存在")
    return item


@router.post("/{data_source_id}/disable", response_model=DataSourceResponse, summary="停用数据源")
async def disable_data_source(
    data_source_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    item = DataSourceService.set_enabled(db, data_source_id, False)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据源不存在")
    return item
