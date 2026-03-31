import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.schemas.sql_analysis import SQLAnalysisItem, SQLAnalysisItemResponse
from app.services.analysis_context_service import AnalysisContextService
from app.services.analysis_task_service import AnalysisTaskService
from app.services.data_source_service import DataSourceService
from app.services.report_provider import (
    REMOTE_WORKFLOW_RESULT_PROVIDER,
    build_metadata_summary,
    get_primary_db_type,
    get_report_provider,
)

logger = logging.getLogger(__name__)


class ReportService:
    """统一管理远端报告提交流程与任务详情输出。"""

    def __init__(self) -> None:
        self.provider = get_report_provider()

    async def submit_analysis(
        self,
        request: List[SQLAnalysisItem],
        data_source_id: Optional[int],
        db: Session,
    ) -> SQLAnalysisItemResponse:
        if not request:
            raise ValueError("至少需要提交一条 SQL 进行分析")

        for index, item in enumerate(request, start=1):
            if not item.sql or not item.sql.strip():
                raise ValueError(f"第 {index} 条 SQL 不能为空")

        data_source = None
        normalized_request = request
        if data_source_id is not None:
            data_source = DataSourceService.require_ready_for_analysis(
                DataSourceService.get_by_id(db, data_source_id)
            )
            self._ensure_same_target(request=request)
            self._ensure_data_source_matches_request(request=request, data_source=data_source)
            normalized_request = self._apply_data_source_to_request(request=request, data_source=data_source)

        if data_source is not None:
            context = AnalysisContextService.build_context(
                request=normalized_request,
                db=db,
                data_source=data_source,
            )
        else:
            context = AnalysisContextService.build_context(
                request=normalized_request,
                db=db,
            )
        return await self.provider.submit_analysis(
            request=normalized_request,
            context=context,
            data_source=data_source,
            db=db,
        )

    @staticmethod
    def _target_key(item: SQLAnalysisItem) -> tuple[str, str, int, str]:
        db_type = get_primary_db_type([item], {"db_targets": []})
        db_port = item.db_port or (5432 if db_type == "postgresql" else 3306)
        return (db_type, item.db_ip or "", db_port, item.dbname or "")

    @classmethod
    def _ensure_same_target(cls, request: List[SQLAnalysisItem]) -> None:
        keys = {cls._target_key(item) for item in request}
        if len(keys) > 1:
            raise ValueError("一次分析仅支持同一个数据库的数据，请拆分后重新提交")

    @classmethod
    def _ensure_data_source_matches_request(cls, request: List[SQLAnalysisItem], data_source: Any) -> None:
        if not request:
            return
        expected = (
            data_source.db_type,
            data_source.host,
            data_source.port,
            data_source.db_name,
        )
        actual = cls._target_key(request[0])
        if all(actual[1:]) and actual != expected:
            raise ValueError("所选数据源与当前聚类对应的数据库不一致，请重新选择")

    @staticmethod
    def _apply_data_source_to_request(
        request: List[SQLAnalysisItem],
        data_source: Any,
    ) -> List[SQLAnalysisItem]:
        normalized_items: List[SQLAnalysisItem] = []
        for item in request:
            normalized_items.append(
                item.model_copy(
                    update={
                        "db_type": data_source.db_type,
                        "dbname": data_source.db_name,
                        "db_ip": data_source.host,
                        "db_port": data_source.port,
                    }
                )
            )
        return normalized_items

    @staticmethod
    def _build_task_message(task: Dict[str, Any]) -> str:
        status_str = task["status"].value if hasattr(task["status"], "value") else str(task["status"])
        if status_str == "completed":
            if not task.get("report_url"):
                return "分析已完成，PDF 暂未生成，可先查看正文"
            return "报告已生成"
        if status_str == "failed":
            return f"任务失败: {task.get('error_message') or '未知错误'}"
        if status_str == "pending":
            return "任务处理中，请稍后查询"
        return "任务状态未知"

    @staticmethod
    def _build_remote_messages(
        summary: str,
        report_content: str,
        report_url: str | None,
    ) -> List[str]:
        messages: List[str] = []
        if summary:
            messages.append(summary)
        if report_content and report_content not in messages:
            messages.append(report_content)
        if report_url:
            messages.append(f"慢 SQL 分析报告下载链接：\n{report_url}")
        return messages

    def _normalize_remote_task(self, task_id: str, task: Dict[str, Any], db: Session) -> Dict[str, Any]:
        analysis_result = task.get("analysis_result") or {}
        provider = analysis_result.get("provider")
        if provider != REMOTE_WORKFLOW_RESULT_PROVIDER:
            sanitized = dict(task)
            sanitized["report_url"] = None
            sanitized["analysis_result"] = None
            return sanitized

        context = task.get("analysis_context") or {}
        summary = analysis_result.get("summary") or self._build_task_message(task)
        report_content = (analysis_result.get("report_content") or "").strip()
        report_url = task.get("report_url") or analysis_result.get("report_url")
        normalized = {
            "provider": REMOTE_WORKFLOW_RESULT_PROVIDER,
            "db_type": analysis_result.get("db_type") or get_primary_db_type([], context),
            "report_url": report_url,
            "risk_level": analysis_result.get("risk_level") or task.get("risk_level"),
            "summary": summary,
            "report_content": report_content or None,
            "messages": self._build_remote_messages(summary, report_content, report_url),
            "metadata_summary": analysis_result.get("metadata_summary") or build_metadata_summary(context),
            "input_diagnostics": analysis_result.get("input_diagnostics"),
            "consistency_flags": analysis_result.get("consistency_flags"),
        }

        if analysis_result != normalized:
            AnalysisTaskService.update_result_artifacts(
                db=db,
                task_id=task_id,
                report_url=report_url,
                analysis_result_json=json.dumps(normalized, ensure_ascii=False),
                risk_level=normalized.get("risk_level"),
            )

        sanitized = dict(task)
        sanitized["report_url"] = report_url
        sanitized["risk_level"] = normalized.get("risk_level")
        sanitized["analysis_result"] = normalized
        return sanitized

    async def get_task_detail(self, task_id: str, db: Session) -> Dict[str, Any]:
        task = AnalysisTaskService.get_by_id(db, task_id)
        if not task:
            raise ValueError(f"任务 {task_id} 不存在")

        normalized = self._normalize_remote_task(task_id=task_id, task=task, db=db)
        normalized["message"] = self._build_task_message(task)

        if task.get("analysis_result") and (task.get("analysis_result") or {}).get("provider") != REMOTE_WORKFLOW_RESULT_PROVIDER:
            normalized["message"] = "本地分析结果已下线，请重新提交远端分析任务"

        return normalized

    async def get_task_list(self, db: Session, **kwargs: Any) -> Dict[str, Any]:
        result = AnalysisTaskService.get_list(db=db, **kwargs)
        result["items"] = [
            self._normalize_remote_task(task_id=item["task_id"], task=item, db=db)
            for item in result.get("items", [])
        ]
        return result

    async def get_report(self, task_id: str, db: Session) -> Dict[str, Any]:
        task = await self.get_task_detail(task_id, db)
        status_str = task["status"].value if hasattr(task["status"], "value") else str(task["status"])
        result: Dict[str, Any] = {
            "task_id": task["task_id"],
            "status": status_str,
            "report_url": task["report_url"],
            "message": task["message"],
        }
        if task.get("risk_level") is not None:
            result["risk_level"] = task["risk_level"]
        if task.get("analysis_result"):
            summary = task["analysis_result"].get("summary")
            if summary:
                result["summary"] = summary
        return result

    async def check_provider_health(self) -> tuple[bool, str]:
        return await self.provider.check_health()
