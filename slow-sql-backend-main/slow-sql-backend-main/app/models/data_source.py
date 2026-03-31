from sqlalchemy import Boolean, Column, Integer, String, Text, TIMESTAMP, func

from app.database import Base


class DataSource(Base):
    __tablename__ = "data_source"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(128), nullable=False, unique=True, comment="数据源名称")
    db_type = Column(String(32), nullable=False, comment="数据库类型(mysql/postgresql)")
    host = Column(String(255), nullable=False, comment="数据库主机地址")
    port = Column(Integer, nullable=False, comment="数据库端口")
    db_name = Column(String(128), nullable=False, comment="数据库名称")
    username = Column(String(128), nullable=False, comment="数据库用户名")
    encrypted_password = Column(Text, nullable=False, comment="加密后的数据库密码")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
    last_test_status = Column(String(32), nullable=True, comment="最近一次测试状态")
    last_test_message = Column(Text, nullable=True, comment="最近一次测试结果")
    last_test_at = Column(TIMESTAMP, nullable=True, comment="最近一次测试时间")
    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="创建时间",
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间",
    )
