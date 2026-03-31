from sqlalchemy import Column, BigInteger, String, Text
from app.database import Base


class DatabaseInfo(Base):
    """
    生产环境表结构信息模型
    对应数据库表: database_info
    """
    __tablename__ = "database_info"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    db_type = Column(String(32), nullable=True, comment="数据库类型(mysql/postgresql)")
    db_name = Column(String(64), nullable=True, comment="数据库名")
    db_desc = Column(String(255), nullable=True, comment="数据库描述")
    db_ip = Column(String(32), nullable=True, comment="数据库IP")
    db_port = Column(BigInteger, nullable=True, comment="数据库端口")
    db_version = Column(String(128), nullable=True, comment="数据库版本")
    table_name = Column(String(128), nullable=True, comment="表名")
    table_desc = Column(String(255), nullable=True, comment="表描述")
    table_rows = Column(BigInteger, nullable=True, comment="表总行数")
    ddl = Column(Text, nullable=True, comment="表结构DDL")
