from sqlalchemy.orm import Session
from datetime import datetime
import json
from typing import Any, Optional
import math
from app.models.analysis_task import AnalysisTask, TaskStatus
from app.schemas.analysis_task import AnalysisResultPayload, AnalysisTaskCreate, AnalysisTaskUpdate
import logging
logger = logging.getLogger(__name__)


class AnalysisTaskService:
    @staticmethod
    def _extract_sql_statements_from_section(sql_section: str) -> Optional[list[str]]:
        statements: list[str] = []
        in_sql_block = False
        sql_buffer: list[str] = []

        for line in sql_section.split("\n"):
            statement = line.strip()
            if statement.startswith("```sql") or statement == "```":
                in_sql_block = True
                sql_buffer = []
                continue
            if statement == "```" and in_sql_block:
                in_sql_block = False
                sql_text_value = "\n".join(sql_buffer).strip()
                if sql_text_value:
                    statements.append(sql_text_value)
                sql_buffer = []
                continue
            if in_sql_block:
                sql_buffer.append(line.rstrip())
                continue

            # Older tasks may serialize the SQL list as bullet lines:
            # - SQL 1: 表 account | select * from account ...
            if statement.startswith("- SQL ") and " | " in line:
                sql_text_value = line.split(" | ", 1)[1].strip()
                if sql_text_value:
                    statements.append(sql_text_value)

        return statements or None

    @staticmethod
    def _infer_compaction_level(sql_text: Optional[str]) -> str:
        text = sql_text or ""
        if "紧急压缩模式已省略 DDL" in text:
            return "emergency"
        if "## 【原始DDL】" in text or "## 原始 DDL 附录" in text:
            marker = "## 【原始DDL】" if "## 【原始DDL】" in text else "## 原始 DDL 附录"
            ddl_section = text.split(marker, 1)[-1]
            if "ddl_excerpt:" in ddl_section:
                return "ddl_excerpt"
            if "```sql" in ddl_section:
                return "full"
        return "unknown"

    @staticmethod
    def _has_meaningful_input_diagnostics(diagnostics: Optional[dict[str, Any]]) -> bool:
        if not diagnostics:
            return False
        workflow_input_length = diagnostics.get("workflow_input_length")
        authoritative_tables = diagnostics.get("authoritative_tables") or []
        return bool(workflow_input_length) or bool(authoritative_tables)

    @staticmethod
    def _append_mismatch_summary_note(summary: str, has_mismatch: bool) -> str:
        note = "远端报告与本地权威元数据不一致"
        if not has_mismatch or note in summary:
            return summary
        return f"{summary}（检测到{note}，请结合元数据摘要复核）"

    @staticmethod
    def _parse_analysis_context(sql_text: Optional[str]) -> Optional[dict[str, Any]]:
        if not sql_text or "分析上下文(JSON)：" not in sql_text:
            return None

        try:
            after_marker = sql_text.split("分析上下文(JSON)：\n", 1)[1]
            json_text = after_marker.split("\n\nSQL脚本：\n", 1)[0]
            return json.loads(json_text)
        except (IndexError, json.JSONDecodeError):
            return None

    @staticmethod
    def _parse_json_blob(blob: Optional[str]) -> Optional[dict[str, Any]]:
        if not blob:
            return None
        try:
            return json.loads(blob)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _parse_analysis_result(blob: Optional[str]) -> Optional[dict[str, Any]]:
        parsed = AnalysisTaskService._parse_json_blob(blob)
        if not parsed:
            return None

        try:
            return AnalysisResultPayload.model_validate(parsed).model_dump()
        except Exception:
            return None

    @staticmethod
    def _parse_sql_text(sql_text: Optional[str]) -> Optional[list[str]]:
        if not sql_text:
            return None

        sql_section_marker = None
        if "## 【SQL清单】" in sql_text:
            sql_section_marker = "## 【SQL清单】"
        elif "## SQL 列表" in sql_text:
            sql_section_marker = "## SQL 列表"

        if sql_section_marker:
            sql_section = sql_text.split(sql_section_marker, 1)[-1]
            if "\n## " in sql_section:
                sql_section = sql_section.split("\n## ", 1)[0]
            return AnalysisTaskService._extract_sql_statements_from_section(sql_section)

        if "SQL脚本：" in sql_text:
            sql_script_part = sql_text.split("SQL脚本：", 1)[-1]
            statements = [sql.strip() for sql in sql_script_part.split("\n") if sql.strip()]
            return statements or None

        if "SQL 清单：" in sql_text:
            sql_script_part = sql_text.split("SQL 清单：", 1)[-1]
            if "\n## " in sql_script_part:
                sql_script_part = sql_script_part.split("\n## ", 1)[0]
            return AnalysisTaskService._extract_sql_statements_from_section(sql_script_part)

        statements = [sql.strip() for sql in sql_text.split("\n") if sql.strip()]
        return statements or None

    @staticmethod
    def _serialize_task(item: AnalysisTask) -> dict[str, Any]:
        analysis_context = (
            AnalysisTaskService._parse_json_blob(item.analysis_context_json)
            or AnalysisTaskService._parse_analysis_context(item.sql_text)
        )
        analysis_result = AnalysisTaskService._parse_analysis_result(item.analysis_result_json)

        if analysis_result and analysis_context:
            from app.services.report_provider import build_consistency_flags, build_input_diagnostics

            if not AnalysisTaskService._has_meaningful_input_diagnostics(analysis_result.get("input_diagnostics")):
                analysis_result["input_diagnostics"] = build_input_diagnostics(
                    context=analysis_context,
                    sql_text=item.sql_text or "",
                    compaction_level=AnalysisTaskService._infer_compaction_level(item.sql_text),
                    workflow_input_mode="sql_text",
                )
            analysis_result["consistency_flags"] = build_consistency_flags(
                context=analysis_context,
                parsed_result=analysis_result,
            )
            analysis_result["summary"] = AnalysisTaskService._append_mismatch_summary_note(
                analysis_result.get("summary") or "",
                any((analysis_result.get("consistency_flags") or {}).values()),
            )

        return {
            "task_id": item.task_id,
            "status": item.status,
            "report_url": item.report_url,
            "sql_text": AnalysisTaskService._parse_sql_text(item.sql_text),
            "error_message": item.error_message,
            "risk_level": item.risk_level,
            "data_source_id": item.data_source_id,
            "data_source_name": item.data_source_name,
            "target_db_type": item.target_db_type,
            "target_host": item.target_host,
            "target_port": item.target_port,
            "target_db_name": item.target_db_name,
            "remote_session_id": item.remote_session_id,
            "remote_message_id": item.remote_message_id,
            "created_at": item.created_at,
            "finished_at": item.finished_at,
            "analysis_context": analysis_context,
            "analysis_result": analysis_result,
        }

    @staticmethod
    def create(db: Session, data: AnalysisTaskCreate) -> AnalysisTask:
        payload = data.model_dump()
        status = payload.get("status") or TaskStatus.pending
        if isinstance(status, str):
            status = TaskStatus(status)
        payload["status"] = status
        obj = AnalysisTask(**payload)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update_result_artifacts(
        db: Session,
        task_id: str,
        *,
        report_url: Optional[str] = None,
        analysis_result_json: Optional[str] = None,
        risk_level: Optional[int] = None,
    ) -> Optional[AnalysisTask]:
        obj = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if not obj:
            return None

        if report_url is not None:
            obj.report_url = report_url
        if analysis_result_json is not None:
            obj.analysis_result_json = analysis_result_json
        if risk_level is not None:
            obj.risk_level = risk_level

        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_list(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        task_id: Optional[str] = None,
        risk_level: Optional[int] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict:
        """
        获取分析任务列表（支持分页和筛选）
        """
        query = db.query(AnalysisTask).filter(AnalysisTask.is_hidden.is_(False))
        
        # 筛选条件
        if task_id:
            query = query.filter(AnalysisTask.task_id.like(f"%{task_id}%"))
        if risk_level:
            query = query.filter(AnalysisTask.risk_level == risk_level)
        if status:
            status = status.value if hasattr(status, "value") else status
            query = query.filter(AnalysisTask.status == status)
        if start_time:
            query = query.filter(AnalysisTask.created_at >= start_time)
        if end_time:
            query = query.filter(AnalysisTask.created_at <= end_time)
        
        # 获取总数
        total = query.count()
        
        # 分页并按创建时间倒序排列
        offset = (page - 1) * page_size
        items = query.order_by(AnalysisTask.created_at.desc()).offset(offset).limit(page_size).all()
        
        processed_items = [AnalysisTaskService._serialize_task(item) for item in items]
        
        # 计算总页数
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "totalPages": total_pages,
            "items": processed_items
        }

    @staticmethod
    def get_by_id(db: Session, task_id: str) -> Optional[dict[str, Any]]:
        """
        根据任务ID获取任务信息
        """
        item = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if not item:
            return None
        return AnalysisTaskService._serialize_task(item)

    @staticmethod
    def get_raw_by_id(db: Session, task_id: str) -> Optional[AnalysisTask]:
        return db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()

    @staticmethod
    def get_raw_by_ids(db: Session, task_ids: list[str]) -> list[AnalysisTask]:
        if not task_ids:
            return []
        return db.query(AnalysisTask).filter(AnalysisTask.task_id.in_(task_ids)).all()

    @staticmethod
    def update_status(
        db: Session,
        task_id: str,
        data: AnalysisTaskUpdate,
    ) -> Optional[AnalysisTask]:
        payload = data.model_dump(exclude_unset=True)
        
        # logger.info("update_status payload=%s", payload)

        obj = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if not obj:
            return None

        status_value = payload.get("status")
        if status_value is not None:
            if isinstance(status_value, str):
                status_value = TaskStatus(status_value)
            obj.status = status_value

        if "report_url" in payload:
            obj.report_url = payload.get("report_url")
        if "analysis_context_json" in payload:
            obj.analysis_context_json = payload.get("analysis_context_json")
        if "analysis_result_json" in payload:
            obj.analysis_result_json = payload.get("analysis_result_json")
        if "error_message" in payload:
            obj.error_message = payload.get("error_message")
        if "risk_level" in payload:
            obj.risk_level = payload.get("risk_level")
        if "is_hidden" in payload:
            obj.is_hidden = bool(payload.get("is_hidden"))
        if "data_source_id" in payload:
            obj.data_source_id = payload.get("data_source_id")
        if "data_source_name" in payload:
            obj.data_source_name = payload.get("data_source_name")
        if "target_db_type" in payload:
            obj.target_db_type = payload.get("target_db_type")
        if "target_host" in payload:
            obj.target_host = payload.get("target_host")
        if "target_port" in payload:
            obj.target_port = payload.get("target_port")
        if "target_db_name" in payload:
            obj.target_db_name = payload.get("target_db_name")
        if "remote_session_id" in payload:
            obj.remote_session_id = payload.get("remote_session_id")
        if "remote_message_id" in payload:
            obj.remote_message_id = payload.get("remote_message_id")

        # 完成或失败时记录完成时间；保持与此前逻辑一致（始终刷新时间）
        if status_value is not None:
            if status_value in (TaskStatus.completed, TaskStatus.failed):
                obj.finished_at = datetime.now()
            elif status_value == TaskStatus.pending:
                obj.finished_at = None
        else:
            obj.finished_at = datetime.now()

        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, task_id: str) -> bool:
        """
        根据任务ID删除任务记录
        """
        obj = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if not obj:
            return False
        
        db.delete(obj)
        db.commit()
        return True

    @staticmethod
    def hide(db: Session, task_id: str) -> Optional[AnalysisTask]:
        obj = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if not obj:
            return None

        obj.is_hidden = True
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def hide_many(db: Session, task_ids: list[str]) -> list[str]:
        if not task_ids:
            return []

        items = db.query(AnalysisTask).filter(AnalysisTask.task_id.in_(task_ids)).all()
        hidden_task_ids: list[str] = []
        for item in items:
            if not item.is_hidden:
                item.is_hidden = True
            hidden_task_ids.append(item.task_id)

        db.commit()
        return hidden_task_ids
