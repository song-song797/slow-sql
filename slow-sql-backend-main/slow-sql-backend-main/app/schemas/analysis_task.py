from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class AnalysisTaskCreate(BaseModel):
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field("pending", description="任务状态")
    report_url: Optional[str] = None
    sql_text: Optional[str] = None
    analysis_context_json: Optional[str] = None
    analysis_result_json: Optional[str] = None
    error_message: Optional[str] = None
    risk_level: Optional[int] = Field(3, ge=1, le=3, description="风险等级：1-低风险，2-中风险，3-高风险")
    data_source_id: Optional[int] = None
    data_source_name: Optional[str] = None
    target_db_type: Optional[str] = None
    target_host: Optional[str] = None
    target_port: Optional[int] = None
    target_db_name: Optional[str] = None
    remote_session_id: Optional[str] = None
    remote_message_id: Optional[str] = None


class AnalysisTaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    report_url: Optional[str] = None
    analysis_context_json: Optional[str] = None
    analysis_result_json: Optional[str] = None
    error_message: Optional[str] = None
    risk_level: Optional[int] = Field(None, ge=1, le=3, description="风险等级：1-低风险，2-中风险，3-高风险")
    is_hidden: Optional[bool] = None
    data_source_id: Optional[int] = None
    data_source_name: Optional[str] = None
    target_db_type: Optional[str] = None
    target_host: Optional[str] = None
    target_port: Optional[int] = None
    target_db_name: Optional[str] = None
    remote_session_id: Optional[str] = None
    remote_message_id: Optional[str] = None


class AnalysisTaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    report_url: Optional[str] = None
    sql_text: Optional[List[str]] = None
    error_message: Optional[str] = None
    risk_level: Optional[int] = Field(3, ge=1, le=3, description="风险等级：1-低风险，2-中风险，3-高风险")
    data_source_id: Optional[int] = None
    data_source_name: Optional[str] = None
    target_db_type: Optional[str] = None
    target_host: Optional[str] = None
    target_port: Optional[int] = None
    target_db_name: Optional[str] = None
    analysis_result: Optional["AnalysisResultPayload"] = None
    created_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisContextTargetResponse(BaseModel):
    db_type: Optional[str] = None
    dbname: Optional[str] = None
    db_ip: Optional[str] = None
    db_port: Optional[int] = None
    tables: List[str] = Field(default_factory=list)


class AnalysisContextTableResponse(BaseModel):
    db_type: Optional[str] = None
    db_name: Optional[str] = None
    db_ip: Optional[str] = None
    db_port: Optional[int] = None
    db_version: Optional[str] = None
    table_name: str
    table_rows: Optional[int] = None
    ddl: Optional[str] = None
    index_definitions: List[dict] = Field(default_factory=list)
    column_definitions: List[dict] = Field(default_factory=list)


class MissingAnalysisContextTableResponse(BaseModel):
    db_type: Optional[str] = None
    db_name: Optional[str] = None
    db_ip: Optional[str] = None
    db_port: Optional[int] = None
    table_name: str


class AutoFetchedAnalysisContextTableResponse(AnalysisContextTableResponse):
    pass


class AnalysisContextFetchErrorResponse(BaseModel):
    db_type: Optional[str] = None
    db_name: Optional[str] = None
    db_ip: Optional[str] = None
    db_port: Optional[int] = None
    table_name: str
    error: str


class AnalysisContextResponse(BaseModel):
    sql_list: List[str] = Field(default_factory=list)
    db_targets: List[AnalysisContextTargetResponse] = Field(default_factory=list)
    matched_tables: List[AnalysisContextTableResponse] = Field(default_factory=list)
    missing_tables: List[MissingAnalysisContextTableResponse] = Field(default_factory=list)
    auto_fetched_tables: List[AutoFetchedAnalysisContextTableResponse] = Field(default_factory=list)
    fetch_errors: List[AnalysisContextFetchErrorResponse] = Field(default_factory=list)


class AnalysisResultMetadataSummary(BaseModel):
    matched_tables_count: int = 0
    auto_fetched_tables_count: int = 0
    missing_tables_count: int = 0
    fetch_errors_count: int = 0
    sql_observation_count: int = 0
    tables_with_ddl_count: int = 0
    tables_with_indexes_count: int = 0


class AnalysisResultAuthoritativeTable(BaseModel):
    table_name: Optional[str] = None
    table_rows_exact: Optional[int] = None
    index_count: int = 0
    has_indexes: bool = False
    ddl_available: bool = False


class AnalysisResultInputDiagnostics(BaseModel):
    workflow_input_mode: str = "sql_text"
    workflow_input_length: int = 0
    compaction_level: str = "full"
    matched_tables_count: int = 0
    tables_with_ddl_count: int = 0
    tables_with_indexes_count: int = 0
    authoritative_tables: List[AnalysisResultAuthoritativeTable] = Field(default_factory=list)


class AnalysisResultConsistencyFlags(BaseModel):
    report_mentions_zero_rows_despite_positive_rows: bool = False
    report_mentions_missing_indexes_despite_indexes_present: bool = False
    report_claims_metadata_missing_but_input_had_metadata: bool = False
    report_used_unknown_when_authoritative_value_present: bool = False


class AnalysisResultPayload(BaseModel):
    provider: str
    db_type: Optional[str] = None
    report_url: Optional[str] = None
    risk_level: Optional[int] = Field(None, ge=1, le=3)
    summary: str
    report_content: Optional[str] = None
    messages: List[str] = Field(default_factory=list)
    metadata_summary: AnalysisResultMetadataSummary = Field(default_factory=AnalysisResultMetadataSummary)
    input_diagnostics: AnalysisResultInputDiagnostics = Field(default_factory=AnalysisResultInputDiagnostics)
    consistency_flags: AnalysisResultConsistencyFlags = Field(default_factory=AnalysisResultConsistencyFlags)


class AnalysisTaskDetailResponse(AnalysisTaskResponse):
    message: Optional[str] = None
    analysis_context: Optional[AnalysisContextResponse] = None


class AnalysisTaskListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    totalPages: int = Field(..., description="总页数")
    items: List[AnalysisTaskResponse] = Field(..., description="任务列表")


class AnalysisTaskHideResponse(BaseModel):
    task_id: str
    hidden: bool = True
    message: str


class AnalysisTaskBatchHideResponse(BaseModel):
    hidden_count: int
    task_ids: List[str] = Field(default_factory=list)
    message: str


AnalysisTaskResponse.model_rebuild()
AnalysisTaskDetailResponse.model_rebuild()
