from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DataSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="数据源名称")
    db_type: str = Field(..., description="数据库类型(mysql/postgresql)")
    host: str = Field(..., min_length=1, max_length=255, description="数据库主机地址")
    port: int = Field(..., ge=1, le=65535, description="数据库端口")
    db_name: str = Field(..., min_length=1, max_length=128, description="数据库名称")
    username: str = Field(..., min_length=1, max_length=128, description="数据库用户名")
    enabled: bool = Field(True, description="是否启用")


class DataSourceCreate(DataSourceBase):
    password: str = Field(..., min_length=1, description="数据库密码")


class DataSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    db_type: Optional[str] = None
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    db_name: Optional[str] = Field(None, min_length=1, max_length=128)
    username: Optional[str] = Field(None, min_length=1, max_length=128)
    password: Optional[str] = Field(None, min_length=1)
    enabled: Optional[bool] = None


class DataSourceResponse(DataSourceBase):
    id: int
    last_test_status: Optional[str] = None
    last_test_message: Optional[str] = None
    last_test_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DataSourceListResponse(BaseModel):
    total: int
    items: list[DataSourceResponse]


class DataSourceTestResponse(BaseModel):
    success: bool
    message: str
    db_version: Optional[str] = None
    table_count: Optional[int] = None
    last_test_status: str
    last_test_at: Optional[datetime] = None


class DataSourceSyncRequest(BaseModel):
    table_name: Optional[str] = Field(None, description="指定同步单表；为空时同步全库")


class DataSourceSyncResponse(BaseModel):
    success: bool
    message: str
    synced_count: int

