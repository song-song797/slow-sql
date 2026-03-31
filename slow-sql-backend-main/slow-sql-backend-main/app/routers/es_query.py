from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.dependencies import verify_api_key
from app.services.es_service import ESService
from app.schemas.es_query import ESClusterQueryListResponse, ESQueryListResponse

router = APIRouter(prefix="/api/v1/es-query", tags=["ES查询"])


@router.get("", response_model=ESQueryListResponse, summary="查询ES中的SQL执行记录")
async def query_es(
    query_time_min: Optional[float] = Query(None, description="执行耗时最小值（秒）"),
    query_time_max: Optional[float] = Query(None, description="执行耗时最大值（秒）"),
    timestamp_start: Optional[str] = Query(None, description="记录时间起始（ISO格式或时间戳）"),
    timestamp_end: Optional[str] = Query(None, description="记录时间结束（ISO格式或时间戳）"),
    keyword: Optional[str] = Query(None, description="关键词模糊匹配（匹配query字段）"),
    dbname: Optional[str] = Query(None, description="数据库名精确匹配"),
    dbuser: Optional[str] = Query(None, description="数据库用户精确匹配"),
    type: Optional[str] = Query(None, description="数据库类型精确匹配"),
    upstream_addr: Optional[str] = Query(None, description="数据库地址精确匹配"),
    is_slow_sql: Optional[bool] = Query(None, description="是否只查询慢SQL（执行时间>1秒），true-是, false-否"),
    page: int = Query(1, ge=1, description="分页页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    api_key: str = Depends(verify_api_key),
):
    """
    查询Elasticsearch中的SQL执行记录
    
    支持以下查询条件：
    - 执行耗时范围查询（query_time_min, query_time_max）
    - 记录时间范围查询（timestamp_start, timestamp_end）
    - 关键词模糊匹配（keyword，匹配query字段）
    - 数据库名精确匹配（dbname）
    - 数据库用户精确匹配（dbuser）
    - 数据库类型精确匹配（type）
    - 数据库地址精确匹配（upstream_addr）
    - 慢SQL过滤（is_slow_sql=True时，自动设置query_time_min=1.0）
    - 分页查询（page, page_size）
    
    注意：返回结果中包含is_slow_sql字段，标识是否为慢SQL（执行时间>1秒）
    """
    # 是否慢 SQL 的语义：
    # - true: 执行时间 > 1 秒
    # - false: 执行时间 <= 1 秒
    # 仅在用户没有显式提供对应边界时才自动补充。
    if is_slow_sql is True and query_time_min is None:
        query_time_min = 1.0
    if is_slow_sql is False and query_time_max is None:
        query_time_max = 1.0
    
    es_service = ESService()
    result = es_service.search(
        query_time_min=query_time_min,
        query_time_max=query_time_max,
        timestamp_start=timestamp_start,
        timestamp_end=timestamp_end,
        keyword=keyword,
        dbname=dbname,
        dbuser=dbuser,
        type=type,
        upstream_addr=upstream_addr,
        page=page,
        page_size=page_size,
    )
    return result


@router.get("/clusters", response_model=ESClusterQueryListResponse, summary="按SQL模板聚类查询ES记录")
async def query_es_clusters(
    query_time_min: Optional[float] = Query(None, description="执行耗时最小值（秒）"),
    query_time_max: Optional[float] = Query(None, description="执行耗时最大值（秒）"),
    timestamp_start: Optional[str] = Query(None, description="记录时间起始（ISO格式或时间戳）"),
    timestamp_end: Optional[str] = Query(None, description="记录时间结束（ISO格式或时间戳）"),
    keyword: Optional[str] = Query(None, description="关键词模糊匹配（匹配query字段）"),
    dbname: Optional[str] = Query(None, description="数据库名精确匹配"),
    dbuser: Optional[str] = Query(None, description="数据库用户精确匹配"),
    type: Optional[str] = Query(None, description="数据库类型精确匹配"),
    upstream_addr: Optional[str] = Query(None, description="数据库地址精确匹配"),
    is_slow_sql: Optional[bool] = Query(None, description="是否只查询慢SQL（执行时间>1秒），true-是, false-否"),
    sort_by: Optional[str] = Query(None, description="排序字段(cluster_count/share/avg_query_time_ms/latest_timestamp/dbname/type/dbuser/upstream_addr)"),
    sort_order: Optional[str] = Query(None, description="排序方向(asc/desc)"),
    page: int = Query(1, ge=1, description="分页页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    api_key: str = Depends(verify_api_key),
):
    if is_slow_sql is True and query_time_min is None:
        query_time_min = 1.0
    if is_slow_sql is False and query_time_max is None:
        query_time_max = 1.0

    es_service = ESService()
    result = es_service.search_clusters(
        query_time_min=query_time_min,
        query_time_max=query_time_max,
        timestamp_start=timestamp_start,
        timestamp_end=timestamp_end,
        keyword=keyword,
        dbname=dbname,
        dbuser=dbuser,
        type=type,
        upstream_addr=upstream_addr,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return result
