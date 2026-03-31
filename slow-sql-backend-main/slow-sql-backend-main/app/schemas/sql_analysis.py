from pydantic import BaseModel, Field
from typing import Optional, List


class SQLObservationOverride(BaseModel):
    cluster_count: int = Field(..., ge=1, description="聚类命中次数")
    min_query_time_ms: Optional[float] = Field(None, description="最短耗时（毫秒）")
    avg_query_time_ms: Optional[float] = Field(None, description="平均耗时（毫秒）")
    max_query_time_ms: Optional[float] = Field(None, description="最长耗时（毫秒）")
    latest_timestamp: Optional[int] = Field(None, description="最近命中时间（毫秒时间戳）")


class SQLAnalysisItem(BaseModel):
    """单个SQL分析项"""
    sql: str = Field(..., description="需要分析的SQL语句")
    db_type: Optional[str] = Field(None, description="数据库类型(mysql/postgresql)")
    dbname: Optional[str] = Field(None, description="数据库名")
    db_ip: Optional[str] = Field(None, description="数据库IP")
    db_port: Optional[int] = Field(None, description="数据库端口")
    source_record_id: Optional[str] = Field(None, description="源慢SQL记录ID")
    source_index: Optional[str] = Field(None, description="源索引名称")
    template_sql: Optional[str] = Field(None, description="聚类后的模板SQL")
    observation_override: Optional[SQLObservationOverride] = Field(None, description="聚类观测统计")


class SQLAnalysisSubmitRequest(BaseModel):
    data_source_id: int = Field(..., ge=1, description="数据源ID")
    items: List[SQLAnalysisItem] = Field(..., min_length=1, description="SQL分析项列表")


class SQLAnalysisItemResponse(BaseModel):
    """单个SQL分析任务提交响应"""
    task_id: str = Field(..., description="分析任务ID")
    status: str = Field(..., description="任务状态")
    message: Optional[str] = Field(None, description="提示信息")


class SQLAnalysisReportResponse(BaseModel):
    """SQL分析报告响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态（pending-处理中, completed-已完成, failed-失败）")
    report_url: Optional[str] = Field(None, description="PDF报告URL（任务完成时返回）")
    message: Optional[str] = Field(None, description="提示信息")
    risk_level: Optional[int] = Field(None, ge=1, le=3, description="风险等级：1-低风险，2-中风险，3-高风险")
    summary: Optional[str] = Field(None, description="报告摘要")


class PDFDownloadRequest(BaseModel):
    """PDF代理下载请求"""
    report_url: str = Field(..., description="报告地址")


class AnalysisTaskBatchRequest(BaseModel):
    task_ids: List[str] = Field(..., min_length=1, description="任务ID列表")
