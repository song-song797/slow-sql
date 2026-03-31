from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ESQueryRequest(BaseModel):
    """ES查询请求参数"""
    query_time_min: Optional[float] = Field(None, description="执行耗时最小值（秒）")
    query_time_max: Optional[float] = Field(None, description="执行耗时最大值（秒）")
    timestamp_start: Optional[str] = Field(None, description="记录时间起始（ISO格式或时间戳）")
    timestamp_end: Optional[str] = Field(None, description="记录时间结束（ISO格式或时间戳）")
    keyword: Optional[str] = Field(None, description="关键词模糊匹配（匹配query字段）")
    dbname: Optional[str] = Field(None, description="数据库名精确匹配")
    dbuser: Optional[str] = Field(None, description="数据库用户精确匹配")
    page: int = Field(1, ge=1, description="分页页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")


class ESQueryResponse(BaseModel):
    """ES查询响应"""
    id: str
    timestamp: int
    upstream_addr: Optional[str] = None
    client_ip: Optional[str] = None
    cmd: Optional[str] = None
    query: Optional[str] = None
    dbname: Optional[str] = None
    dbuser: Optional[str] = None
    type: Optional[str] = None
    workgroup_name: Optional[str] = None
    client_port: Optional[str] = None
    query_time: Optional[str] = None
    resplen: Optional[str] = None
    rows_num: Optional[str] = None
    session_time: Optional[float] = None
    upstream_name: Optional[str] = None
    realtime: Optional[str] = None
    fields_num: Optional[str] = None
    status: Optional[str] = None
    workgroup_id: Optional[int] = None
    dbtable: Optional[str] = None
    is_slow_sql: Optional[bool] = Field(None, description="是否为慢SQL（执行时间>1秒）")


class ESQueryListResponse(BaseModel):
    """ES查询列表响应"""
    total: int
    page: int
    page_size: int
    items: List[ESQueryResponse]


class ESClusterQueryResponse(BaseModel):
    """聚类后的SQL检索响应"""
    cluster_id: str
    template_sql: str
    sample_sql: str
    dbname: Optional[str] = None
    dbuser: Optional[str] = None
    type: Optional[str] = None
    upstream_addr: Optional[str] = None
    cluster_count: int = 0
    first_timestamp: int = 0
    min_query_time_ms: Optional[float] = None
    avg_query_time_ms: Optional[float] = None
    max_query_time_ms: Optional[float] = None
    latest_timestamp: int = 0
    is_slow_sql: Optional[bool] = None


class ESClusterQueryListResponse(BaseModel):
    """聚类列表响应"""
    total: int
    page: int
    page_size: int
    total_record_count: int = 0
    scanned_record_count: int = 0
    truncated: bool = False
    items: List[ESClusterQueryResponse]
