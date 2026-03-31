from pydantic import BaseModel, Field
from typing import Optional


class DatabaseInfoBase(BaseModel):
    """数据库信息基础模型"""
    db_type: Optional[str] = Field(None, max_length=32, description="数据库类型(mysql/postgresql)")
    db_name: Optional[str] = Field(None, max_length=64, description="数据库名")
    db_desc: Optional[str] = Field(None, max_length=255, description="数据库描述")
    db_ip: Optional[str] = Field(None, max_length=32, description="数据库IP")
    db_port: Optional[int] = Field(None, description="数据库端口")
    db_version: Optional[str] = Field(None, max_length=128, description="数据库版本")
    table_name: Optional[str] = Field(None, max_length=128, description="表名")
    table_desc: Optional[str] = Field(None, max_length=255, description="表描述")
    table_rows: Optional[int] = Field(None, description="表总行数")
    ddl: Optional[str] = Field(None, description="表结构DDL")


class DatabaseInfoCreate(DatabaseInfoBase):
    """创建数据库信息请求"""
    pass


class DatabaseInfoUpdate(DatabaseInfoBase):
    """更新数据库信息请求"""
    pass


class DatabaseInfoResponse(DatabaseInfoBase):
    """数据库信息响应"""
    id: int

    class Config:
        from_attributes = True


class DatabaseInfoListResponse(BaseModel):
    """数据库信息列表响应"""
    total: int
    page: int
    page_size: int
    items: list[DatabaseInfoResponse]


class RemoteDatabaseConnection(BaseModel):
    """远程数据库连接请求"""
    db_type: str = Field(..., description="数据库类型 (mysql/postgresql)")
    host: str = Field(..., description="数据库主机地址")
    port: int = Field(..., description="数据库端口")
    db_name: str = Field(..., description="数据库名称")
    username: str = Field(..., description="数据库用户名")
    password: str = Field(..., description="数据库密码")
    table_name: Optional[str] = Field(None, description="表名称")
