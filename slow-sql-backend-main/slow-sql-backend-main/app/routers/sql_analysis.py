from fastapi import APIRouter, Body, Depends, HTTPException, status, Query
from fastapi.responses import Response
from typing import List, Optional
import logging
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from sqlalchemy.orm import Session
import httpx
from app.dependencies import verify_api_key
from app.schemas.sql_analysis import (
    AnalysisTaskBatchRequest,
    PDFDownloadRequest,
    SQLAnalysisItem,
    SQLAnalysisItemResponse,
    SQLAnalysisSubmitRequest,
    SQLAnalysisReportResponse,
)
from app.schemas.analysis_task import (
    AnalysisTaskBatchHideResponse,
    AnalysisTaskDetailResponse,
    AnalysisTaskHideResponse,
    AnalysisTaskListResponse,
    TaskStatus,
)
from app.database import get_db
from app.services.analysis_task_service import AnalysisTaskService
from app.services.report_service import ReportService
from datetime import datetime

router = APIRouter(prefix="/api/v1/sql-analysis", tags=["SQL分析"])
logger = logging.getLogger(__name__)


@router.post("/submit", response_model=SQLAnalysisItemResponse, summary="提交SQL进行分析")
async def submit_sql_analysis(
    request: List[SQLAnalysisItem] | SQLAnalysisSubmitRequest = Body(...),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """
    提交SQL语句进行分析（支持批量提交）
    
    接收SQL分析项数组，调用外部报告生成API进行分析
    返回成功提交任务的报文
    """
    try:
        service = ReportService()
        if isinstance(request, list):
            items = [SQLAnalysisItem.model_validate(item) for item in request]
            data_source_id = None
        else:
            submit_request = SQLAnalysisSubmitRequest.model_validate(request)
            items = submit_request.items
            data_source_id = submit_request.data_source_id
        return await service.submit_analysis(request=items, data_source_id=data_source_id, db=db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get("/report/{task_id}", response_model=SQLAnalysisReportResponse, summary="获取PDF报告")
async def get_pdf_report(
    task_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """
    根据任务ID获取PDF报告URL
    
    返回PDF的URL地址和任务状态
    """
    report_service = ReportService()
    try:
        result = await report_service.get_report(task_id, db)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get("/tasks", response_model=AnalysisTaskListResponse, summary="获取分析任务列表")
async def get_analysis_tasks(
    task_id: Optional[str] = Query(None, description="任务ID筛选（模糊查询）"),
    risk_level: Optional[int] = Query(None, ge=1, le=3, description="风险等级筛选（1-低风险，2-中风险，3-高风险）"),
    page: int = Query(1, ge=1, description="分页页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    status: Optional[TaskStatus] = Query(None, description="任务状态筛选（pending/completed/failed）"),
    start_time: Optional[datetime] = Query(None, description="创建时间开始范围"),
    end_time: Optional[datetime] = Query(None, description="创建时间结束范围"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """
    获取分析任务列表，支持分页和筛选
    """
    service = ReportService()
    result = await service.get_task_list(
        db=db,
        page=page,
        page_size=page_size,
        task_id=task_id,
        risk_level=risk_level,
        status=status,
        start_time=start_time,
        end_time=end_time,
    )
    return result


@router.get("/tasks/{task_id}", response_model=AnalysisTaskDetailResponse, summary="获取分析任务详情")
async def get_analysis_task_detail(
    task_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    service = ReportService()
    try:
        return await service.get_task_detail(task_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        ) from e


@router.post("/tasks/{task_id}/hide", response_model=AnalysisTaskHideResponse, summary="从列表中隐藏分析任务")
async def hide_analysis_task(
    task_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    task = AnalysisTaskService.hide(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务 {task_id} 不存在",
        )

    return AnalysisTaskHideResponse(
        task_id=task_id,
        hidden=True,
        message="任务已从结果列表中移除",
    )


@router.post("/tasks/hide", response_model=AnalysisTaskBatchHideResponse, summary="批量从列表中隐藏分析任务")
async def hide_analysis_tasks(
    request: AnalysisTaskBatchRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    hidden_task_ids = AnalysisTaskService.hide_many(db, request.task_ids)
    if not hidden_task_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到可移除的任务",
        )

    return AnalysisTaskBatchHideResponse(
        hidden_count=len(hidden_task_ids),
        task_ids=hidden_task_ids,
        message=f"已从列表移除 {len(hidden_task_ids)} 条任务",
    )


@router.post("/download-pdf", summary="代理下载PDF报告")
async def download_pdf_report(
    request: PDFDownloadRequest,
    api_key: str = Depends(verify_api_key),
):
    if not request.report_url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="报告地址必须是 http 或 https URL",
        )

    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            response = await client.get(request.report_url)
            response.raise_for_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"下载报告失败: {exc}",
        ) from exc

    return Response(
        content=response.content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="analysis-report.pdf"',
        },
    )


@router.post("/download-pdfs", summary="批量打包下载PDF报告")
async def download_pdf_reports(
    request: AnalysisTaskBatchRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    report_service = ReportService()
    downloadable: list[tuple[str, str]] = []
    skipped: list[str] = []

    for task_id in request.task_ids:
        try:
            task = await report_service.get_task_detail(task_id, db)
        except ValueError:
            skipped.append(f"{task_id}: 任务不存在")
            continue

        report_url = task.get("report_url")
        if not report_url:
            skipped.append(f"{task_id}: 报告暂不可下载")
            continue
        downloadable.append((task_id, report_url))

    if not downloadable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="选中的任务中没有可下载的报告",
        )

    zip_buffer = BytesIO()

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        with ZipFile(zip_buffer, mode="w", compression=ZIP_DEFLATED) as zip_file:
            for task_id, report_url in downloadable:
                try:
                    response = await client.get(report_url)
                    response.raise_for_status()
                    zip_file.writestr(f"analysis-report-{task_id}.pdf", response.content)
                except Exception as exc:
                    skipped.append(f"{task_id}: 下载失败 - {exc}")

            if skipped:
                zip_file.writestr(
                    "README.txt",
                    "以下任务未被打包：\n" + "\n".join(skipped),
                )

    filename = f'analysis-reports-{datetime.now().strftime("%Y%m%d-%H%M%S")}.zip'
    zip_buffer.seek(0)
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
