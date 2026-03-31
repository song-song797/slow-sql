from sqlalchemy import Boolean, Column, String, Enum, Text, TIMESTAMP, func, Integer
from sqlalchemy.dialects import mysql
import enum
from app.database import Base


LARGE_TEXT = Text().with_variant(mysql.LONGTEXT(), "mysql")


class TaskStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class AnalysisTask(Base):
    __tablename__ = "analysis_task"

    task_id = Column(String(36), primary_key=True, comment="任务ID(UUID)")
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.pending, comment="任务状态")
    report_url = Column(String(512), nullable=True, comment="报告下载链接")
    sql_text = Column(LARGE_TEXT, nullable=True, comment="拼接后的SQL文本")
    analysis_context_json = Column(LARGE_TEXT, nullable=True, comment="结构化分析上下文(JSON)")
    analysis_result_json = Column(LARGE_TEXT, nullable=True, comment="结构化分析结果(JSON)")
    error_message = Column(LARGE_TEXT, nullable=True, comment="失败原因")
    risk_level = Column(Integer, nullable=True, default=3, comment="风险等级：1-低风险，2-中风险，3-高风险")
    is_hidden = Column(Boolean, nullable=False, default=False, comment="是否从列表中隐藏")
    data_source_id = Column(Integer, nullable=True, comment="数据源ID")
    data_source_name = Column(String(128), nullable=True, comment="数据源名称")
    target_db_type = Column(String(32), nullable=True, comment="目标数据库类型")
    target_host = Column(String(255), nullable=True, comment="目标数据库主机")
    target_port = Column(Integer, nullable=True, comment="目标数据库端口")
    target_db_name = Column(String(128), nullable=True, comment="目标数据库名称")
    remote_session_id = Column(String(128), nullable=True, comment="远端工作流会话ID")
    remote_message_id = Column(String(128), nullable=True, comment="远端工作流消息ID")
    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="创建时间",
    )
    finished_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="完成/失败时间",
    )
