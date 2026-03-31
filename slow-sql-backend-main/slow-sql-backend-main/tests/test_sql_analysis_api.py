import json
import asyncio
import time
import zipfile
from io import BytesIO
from pathlib import Path

import app.models  # noqa: F401
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.dependencies import verify_api_key
from app.models.analysis_task import AnalysisTask
from app.routers import data_sources, sql_analysis
from app.schemas.analysis_task import AnalysisTaskCreate
from app.schemas.sql_analysis import SQLAnalysisItem
from app.services.analysis_context_service import AnalysisContextService
from app.services.analysis_task_service import AnalysisTaskService
from app.services.report_provider import (
    RemoteWorkflowReportProvider,
    build_remote_result_payload,
    compose_sql_text,
    compose_workflow_document,
)
import app.services.report_provider as report_provider_module
import app.services.data_source_service as data_source_service_module


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def fake_context(*, request, db, data_source=None):
        return {
            "sql_list": [item.sql for item in request],
            "db_targets": [
                {
                    "db_type": "mysql",
                    "dbname": "demo",
                    "db_ip": "127.0.0.1",
                    "db_port": 3306,
                    "tables": ["audit_log"],
                }
            ],
            "matched_tables": [
                {
                    "db_type": "mysql",
                    "db_name": "demo",
                    "db_ip": "127.0.0.1",
                    "db_port": 3306,
                    "db_version": "8.0.36",
                    "table_name": "audit_log",
                    "table_rows": 128,
                    "ddl": (
                        "CREATE TABLE `audit_log` (\n"
                        "  `id` bigint NOT NULL,\n"
                        "  `user_id` bigint NOT NULL,\n"
                        "  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,\n"
                        "  PRIMARY KEY (`id`),\n"
                        "  KEY `idx_user_created` (`user_id`,`created_at`)\n"
                        ") ENGINE=InnoDB"
                    ),
                    "index_definitions": [
                        {
                            "name": "PRIMARY",
                            "index_type": "PRIMARY KEY",
                            "columns": ["id"],
                            "unique": True,
                        },
                        {
                            "name": "idx_user_created",
                            "index_type": "INDEX",
                            "columns": ["user_id", "created_at"],
                            "unique": False,
                        },
                    ],
                    "column_definitions": [
                        {
                            "name": "id",
                            "data_type": "bigint",
                            "nullable": "NO",
                            "default": None,
                        },
                        {
                            "name": "user_id",
                            "data_type": "bigint",
                            "nullable": "NO",
                            "default": None,
                        },
                    ],
                }
            ],
            "missing_tables": [],
            "auto_fetched_tables": [],
            "fetch_errors": [],
            "sql_observations": [
                {
                    "sql": "select * from audit_log where user_id = 1 order by created_at desc",
                    "db_name": "demo",
                    "db_type": "mysql",
                    "exact_match_count": 3,
                    "avg_query_time_ms": 1200,
                    "max_query_time_ms": 3800,
                }
            ],
        }

    monkeypatch.setattr(report_provider_module, "SessionLocal", testing_session_local)
    monkeypatch.setattr(AnalysisContextService, "build_context", staticmethod(fake_context))
    monkeypatch.setattr(report_provider_module.settings, "report_provider", "api1_file_workflow")
    monkeypatch.setattr(
        report_provider_module.settings,
        "report_api_base_url",
        "http://172.20.20.128:3001/api/v2/workflow/invoke",
    )
    monkeypatch.setattr(
        report_provider_module.settings,
        "workflow_id",
        "07a3623111bd4bbcb8a7d80450199f3f",
    )
    monkeypatch.setattr(
        report_provider_module.settings,
        "data_source_secret_key",
        "unit-test-secret",
    )

    app = FastAPI()
    app.include_router(data_sources.router)
    app.include_router(sql_analysis.router)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key] = lambda: "test-api-key"

    with TestClient(app) as test_client:
        yield test_client


def create_data_source(client: TestClient, *, mark_tested: bool = False) -> int:
    response = client.post(
        "/api/v1/data-sources",
        headers={"X-API-Key": "test-api-key"},
        json={
            "name": "demo-mysql",
            "db_type": "mysql",
            "host": "127.0.0.1",
            "port": 3306,
            "db_name": "demo",
            "username": "reader",
            "password": "secret",
            "enabled": True,
        },
    )
    assert response.status_code == 201
    data_source_id = response.json()["id"]

    if mark_tested:
        db_gen = client.app.dependency_overrides[get_db]()
        db = next(db_gen)
        try:
            item = data_source_service_module.DataSourceService.get_by_id(db, data_source_id)
            assert item is not None
            item.last_test_status = "success"
            item.last_test_message = "测试通过"
            db.commit()
        finally:
            db.close()
            try:
                next(db_gen)
            except StopIteration:
                pass

    return data_source_id


def test_submit_then_fetch_remote_detail(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    data_source_id = create_data_source(client, mark_tested=True)

    async def fake_invoke_workflow(
        self,
        workflow_id,
        stream=False,
        input_payload=None,
        session_id=None,
        message_id=None,
    ):
        assert workflow_id == "07a3623111bd4bbcb8a7d80450199f3f"
        if input_payload is None:
            return {
                "data": {
                    "session_id": "session-1",
                    "events": [
                        {
                            "event": "input",
                            "node_id": "node-1",
                            "message_id": "message-1",
                        }
                    ],
                }
            }

        assert session_id == "session-1"
        assert message_id == "message-1"
        payload = input_payload["node-1"]["file"]
        assert payload["file_name"] == "slow-sql-input.md"
        assert payload["file_type"] == "text/markdown"
        assert "## 【SQL清单】" in payload["file_content"]
        assert "## 【结构化抽取参考(JSON)】" in payload["file_content"]
        assert "## 【SQL观测统计】" in payload["file_content"]
        assert "## 【表结构与索引信息】" in payload["file_content"]
        assert '"sql": [' in payload["file_content"]
        assert '"sql_content": "select * from audit_log where user_id = 1 order by created_at desc"' in payload["file_content"]
        assert "table_rows_exact" in payload["file_content"]
        assert "index_count" in payload["file_content"]
        assert "idx_user_created" in payload["file_content"]
        assert "CREATE TABLE `audit_log`" in payload["file_content"]
        return {
            "data": {
                "events": [
                    {
                        "event": "output_msg",
                        "output_schema": {
                            "message": "分析完成，报告地址 https://example.com/reports/remote-task.pdf"
                        },
                    },
                    {
                        "event": "output_msg",
                        "output_schema": {
                            "message": (
                                "# 慢 SQL 分析报告\n\n"
                                "## 二、整体风险评估等级\n"
                                "高风险 ■\n\n"
                                "## 三、分析结果详情\n"
                                "这里是远端报告正文"
                            )
                        },
                    },
                ]
            }
        }

    monkeypatch.setattr(
        report_provider_module.RemoteWorkflowReportProvider,
        "invoke_workflow",
        fake_invoke_workflow,
    )

    response = client.post(
        "/api/v1/sql-analysis/submit",
        headers={"X-API-Key": "test-api-key"},
        json={
            "data_source_id": data_source_id,
            "items": [
                {
                    "sql": "select * from audit_log where user_id = 1 order by created_at desc",
                    "db_type": "mysql",
                    "dbname": "demo",
                    "db_ip": "127.0.0.1",
                    "db_port": 3306,
                }
            ],
        },
    )

    assert response.status_code == 200
    task_id = response.json()["task_id"]

    detail = None
    for _ in range(30):
        time.sleep(0.1)
        detail_response = client.get(
            f"/api/v1/sql-analysis/tasks/{task_id}",
            headers={"X-API-Key": "test-api-key"},
        )
        assert detail_response.status_code == 200
        detail = detail_response.json()
        if detail["status"] == "completed":
            break

    assert detail is not None
    assert detail["status"] == "completed"
    assert detail["report_url"] == "https://example.com/reports/remote-task.pdf"
    assert detail["data_source_id"] == data_source_id
    assert detail["data_source_name"] == "demo-mysql"
    assert detail["analysis_result"]["provider"] == "remote_workflow"
    assert detail["analysis_result"]["report_content"].startswith("# 慢 SQL 分析报告")
    assert "report_document" not in detail["analysis_result"]
    assert detail["analysis_result"]["metadata_summary"]["matched_tables_count"] == 1
    assert detail["analysis_result"]["metadata_summary"]["tables_with_ddl_count"] == 1
    assert detail["analysis_result"]["metadata_summary"]["tables_with_indexes_count"] == 1
    assert detail["analysis_result"]["input_diagnostics"]["workflow_input_mode"] == "sql_text"
    assert detail["analysis_result"]["input_diagnostics"]["matched_tables_count"] == 1
    assert detail["analysis_result"]["consistency_flags"]["report_mentions_zero_rows_despite_positive_rows"] is False

    list_response = client.get(
        f"/api/v1/sql-analysis/tasks?page=1&page_size=5&task_id={task_id}",
        headers={"X-API-Key": "test-api-key"},
    )
    assert list_response.status_code == 200
    listed = list_response.json()["items"][0]
    assert listed["analysis_result"]["input_diagnostics"]["workflow_input_mode"] == "sql_text"
    assert listed["analysis_result"]["metadata_summary"]["matched_tables_count"] == 1


def test_submit_sql_text_workflow_includes_metadata_document(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(report_provider_module.settings, "report_provider", "api1_workflow")
    monkeypatch.setattr(
        report_provider_module.settings,
        "workflow_id",
        "fb594dae47c5440dbea05725ebec6674",
    )

    async def fake_invoke_workflow(
        self,
        workflow_id,
        stream=False,
        input_payload=None,
        session_id=None,
        message_id=None,
    ):
        assert workflow_id == "fb594dae47c5440dbea05725ebec6674"
        if input_payload is None:
            return {
                "data": {
                    "session_id": "session-sql-text",
                    "events": [
                        {
                            "event": "input",
                            "node_id": "node-1",
                            "message_id": "message-1",
                        }
                    ],
                }
            }

        assert session_id == "session-sql-text"
        assert message_id == "message-1"
        sql_text = input_payload["node-1"]["sql_text"]
        assert "# 慢 SQL 分析输入文档" in sql_text
        assert "## 【数据库信息】" in sql_text
        assert "## 【SQL清单】" in sql_text
        assert "## 【结构化抽取参考(JSON)】" in sql_text
        assert "## 【SQL观测统计】" in sql_text
        assert "## 【表结构与索引信息】" in sql_text
        assert "所属数据库:" in sql_text
        assert "Indexes structure:" in sql_text
        assert '"ddl": [' in sql_text
        assert "table_rows_exact" in sql_text
        assert "index_count" in sql_text
        assert "idx_user_created" in sql_text
        assert "CREATE TABLE `audit_log`" in sql_text
        assert "分析上下文(JSON)" not in sql_text

        return {
            "data": {
                "events": [
                    {
                        "event": "output_msg",
                        "output_schema": {
                            "message": "慢 SQL 分析报告下载链接：\nhttps://example.com/reports/sql-text.pdf"
                        },
                    },
                    {
                        "event": "output_msg",
                        "output_schema": {
                            "message": (
                                "# 慢 SQL 分析报告\n\n"
                                "## 二、整体风险评估等级\n"
                                "低风险 ■\n\n"
                                "## 三、分析结果详情\n"
                                "这里是 SQL Text 工作流正文"
                            )
                        },
                    },
                ]
            }
        }

    monkeypatch.setattr(
        report_provider_module.RemoteWorkflowReportProvider,
        "invoke_workflow",
        fake_invoke_workflow,
    )

    response = client.post(
        "/api/v1/sql-analysis/submit",
        headers={"X-API-Key": "test-api-key"},
        json=[
            {
                "sql": "select * from audit_log where user_id = 1 order by created_at desc",
                "db_type": "mysql",
                "dbname": "demo",
                "db_ip": "127.0.0.1",
                "db_port": 3306,
                "template_sql": "SELECT * FROM audit_log WHERE user_id = ? ORDER BY created_at DESC",
            }
        ],
    )

    assert response.status_code == 200
    task_id = response.json()["task_id"]

    detail = None
    for _ in range(30):
        time.sleep(0.1)
        detail_response = client.get(
            f"/api/v1/sql-analysis/tasks/{task_id}",
            headers={"X-API-Key": "test-api-key"},
        )
        assert detail_response.status_code == 200
        detail = detail_response.json()
        if detail["status"] == "completed":
            break

    assert detail is not None
    assert detail["status"] == "completed"
    assert detail["report_url"] == "https://example.com/reports/sql-text.pdf"
    assert detail["analysis_result"]["report_content"].startswith("# 慢 SQL 分析报告")


def test_sql_text_input_schema_takes_precedence_over_file_provider(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(report_provider_module.settings, "report_provider", "api1_file_workflow")
    monkeypatch.setattr(
        report_provider_module.settings,
        "workflow_id",
        "fb594dae47c5440dbea05725ebec6674",
    )

    async def fake_invoke_workflow(
        self,
        workflow_id,
        stream=False,
        input_payload=None,
        session_id=None,
        message_id=None,
    ):
        if input_payload is None:
            return {
                "data": {
                    "session_id": "session-dynamic",
                    "events": [
                        {
                            "event": "input",
                            "node_id": "node-1",
                            "message_id": "message-1",
                            "input_schema": {
                                "input_type": "form_input",
                                "value": [
                                    {
                                        "key": "sql_text",
                                        "type": "text",
                                        "required": True,
                                    }
                                ],
                            },
                        }
                    ],
                }
            }

        assert "sql_text" in input_payload["node-1"]
        assert "file" not in input_payload["node-1"]
        assert "## 【表结构与索引信息】" in input_payload["node-1"]["sql_text"]
        assert "## 【结构化抽取参考(JSON)】" in input_payload["node-1"]["sql_text"]
        return {
            "data": {
                "events": [
                    {
                        "event": "output_msg",
                        "output_schema": {
                            "message": "慢 SQL 分析报告下载链接：\nhttps://example.com/reports/dynamic-schema.pdf"
                        },
                    }
                ]
            }
        }

    monkeypatch.setattr(
        report_provider_module.RemoteWorkflowReportProvider,
        "invoke_workflow",
        fake_invoke_workflow,
    )

    response = client.post(
        "/api/v1/sql-analysis/submit",
        headers={"X-API-Key": "test-api-key"},
        json=[
            {
                "sql": "select * from audit_log where user_id = 1 order by created_at desc",
                "db_type": "mysql",
                "dbname": "demo",
                "db_ip": "127.0.0.1",
                "db_port": 3306,
            }
        ],
    )

    assert response.status_code == 200
    task_id = response.json()["task_id"]

    detail = None
    for _ in range(30):
        time.sleep(0.1)
        detail_response = client.get(
            f"/api/v1/sql-analysis/tasks/{task_id}",
            headers={"X-API-Key": "test-api-key"},
        )
        assert detail_response.status_code == 200
        detail = detail_response.json()
        if detail["status"] == "completed":
            break

    assert detail is not None
    assert detail["status"] == "completed"
    assert detail["report_url"] == "https://example.com/reports/dynamic-schema.pdf"


def test_data_source_test_and_sync_metadata(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    data_source_id = create_data_source(client)

    monkeypatch.setattr(
        data_source_service_module.RemoteDatabaseService,
        "test_connection",
        staticmethod(
            lambda **kwargs: {
                "success": True,
                "message": "连接成功，共检测到 3 张表",
                "db_version": "8.0.36",
                "table_count": 3,
            }
        ),
    )
    monkeypatch.setattr(
        data_source_service_module.RemoteDatabaseService,
        "fetch_database_info",
        staticmethod(
            lambda **kwargs: [
                {
                    "db_type": "mysql",
                    "db_name": "demo",
                    "db_ip": "127.0.0.1",
                    "db_port": 3306,
                    "db_version": "8.0.36",
                    "table_name": "audit_log",
                    "table_rows": 12,
                    "ddl": "CREATE TABLE audit_log(id bigint primary key)",
                }
            ]
        ),
    )

    test_response = client.post(
        f"/api/v1/data-sources/{data_source_id}/test",
        headers={"X-API-Key": "test-api-key"},
    )
    assert test_response.status_code == 200
    assert test_response.json()["last_test_status"] == "success"

    sync_response = client.post(
        f"/api/v1/data-sources/{data_source_id}/sync-metadata",
        headers={"X-API-Key": "test-api-key"},
        json={},
    )
    assert sync_response.status_code == 200
    assert sync_response.json()["synced_count"] == 1


def test_remote_legacy_payload_is_sanitized_on_detail_fetch(client: TestClient) -> None:
    task_id = "remote-legacy-task"
    request = [
        SQLAnalysisItem(
            sql="select * from audit_log where user_id = 1 order by created_at desc",
            db_type="mysql",
            dbname="demo",
            db_ip="127.0.0.1",
            db_port=3306,
        )
    ]
    context = AnalysisContextService.build_context(request=request, db=None)

    db_gen = client.app.dependency_overrides[get_db]()
    db = next(db_gen)
    try:
        AnalysisTaskService.create(
            db=db,
            data=AnalysisTaskCreate(
                task_id=task_id,
                status="completed",
                report_url="https://example.com/reports/legacy.pdf",
                sql_text=compose_sql_text(request, context=context),
                analysis_context_json=json.dumps(context, ensure_ascii=False),
                analysis_result_json=json.dumps(
                    {
                        "provider": "remote_workflow",
                        "db_type": "mysql",
                        "report_url": "https://example.com/reports/legacy.pdf",
                        "risk_level": 3,
                        "summary": "远端摘要",
                        "report_content": "# 慢 SQL 分析报告\n\n远端正文",
                        "messages": ["远端摘要", "本地残留说明", "https://example.com/reports/legacy.pdf"],
                        "metadata_summary": {
                            "matched_tables_count": 0,
                            "auto_fetched_tables_count": 0,
                            "missing_tables_count": 0,
                            "fetch_errors_count": 0,
                            "sql_observation_count": 1,
                        },
                        "report_document": {"title": "旧本地模板"},
                    },
                    ensure_ascii=False,
                ),
                risk_level=3,
            ),
        )
    finally:
        db.close()
        try:
            next(db_gen)
        except StopIteration:
            pass

    detail_response = client.get(
        f"/api/v1/sql-analysis/tasks/{task_id}",
        headers={"X-API-Key": "test-api-key"},
    )

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["analysis_result"]["provider"] == "remote_workflow"
    assert detail["analysis_result"]["messages"] == [
        "远端摘要",
        "# 慢 SQL 分析报告\n\n远端正文",
        "慢 SQL 分析报告下载链接：\nhttps://example.com/reports/legacy.pdf",
    ]
    assert detail["analysis_result"]["input_diagnostics"]["workflow_input_mode"] == "sql_text"
    assert detail["analysis_result"]["consistency_flags"]["report_mentions_zero_rows_despite_positive_rows"] is False
    assert "report_document" not in detail["analysis_result"]


def test_local_result_is_hidden_from_list_and_detail(client: TestClient) -> None:
    task_id = "local-history-task"
    request = [
        SQLAnalysisItem(
            sql="select * from audit_log where user_id = 1 order by created_at desc",
            db_type="mysql",
            dbname="demo",
            db_ip="127.0.0.1",
            db_port=3306,
        )
    ]
    context = AnalysisContextService.build_context(request=request, db=None)

    db_gen = client.app.dependency_overrides[get_db]()
    db = next(db_gen)
    try:
        AnalysisTaskService.create(
            db=db,
            data=AnalysisTaskCreate(
                task_id=task_id,
                status="completed",
                report_url="/static/reports/local-history-task.pdf",
                sql_text=compose_sql_text(request, context=context),
                analysis_context_json=json.dumps(context, ensure_ascii=False),
                analysis_result_json=json.dumps(
                    {
                        "provider": "local_structured",
                        "db_type": "mysql",
                        "report_url": "/static/reports/local-history-task.pdf",
                        "risk_level": 3,
                        "summary": "旧本地结果",
                        "report_content": None,
                        "messages": ["旧本地结果"],
                        "metadata_summary": {
                            "matched_tables_count": 0,
                            "auto_fetched_tables_count": 0,
                            "missing_tables_count": 0,
                            "fetch_errors_count": 0,
                            "sql_observation_count": 1,
                        },
                    },
                    ensure_ascii=False,
                ),
                risk_level=3,
            ),
        )
    finally:
        db.close()
        try:
            next(db_gen)
        except StopIteration:
            pass

    detail_response = client.get(
        f"/api/v1/sql-analysis/tasks/{task_id}",
        headers={"X-API-Key": "test-api-key"},
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["report_url"] is None
    assert detail["analysis_result"] is None
    assert detail["message"] == "本地分析结果已下线，请重新提交远端分析任务"

    list_response = client.get(
        "/api/v1/sql-analysis/tasks?page=1&page_size=10",
        headers={"X-API-Key": "test-api-key"},
    )
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    current = next(item for item in items if item["task_id"] == task_id)
    assert current["report_url"] is None


def test_hide_task_removes_it_from_list_only(client: TestClient) -> None:
    task_id = "hide-from-list-task"
    request = [
        SQLAnalysisItem(
            sql="select 1",
            db_type="mysql",
            dbname="demo",
            db_ip="127.0.0.1",
            db_port=3306,
        )
    ]
    context = AnalysisContextService.build_context(request=request, db=None)

    db_gen = client.app.dependency_overrides[get_db]()
    db = next(db_gen)
    try:
        AnalysisTaskService.create(
            db=db,
            data=AnalysisTaskCreate(
                task_id=task_id,
                status="completed",
                report_url="https://example.com/reports/hide.pdf",
                sql_text=compose_sql_text(request, context=context),
                analysis_context_json=json.dumps(context, ensure_ascii=False),
                analysis_result_json=json.dumps(
                    {
                        "provider": "remote_workflow",
                        "db_type": "mysql",
                        "report_url": "https://example.com/reports/hide.pdf",
                        "risk_level": 1,
                        "summary": "远端摘要",
                        "report_content": "# 慢 SQL 分析报告\n\n正文",
                        "messages": ["远端摘要"],
                        "metadata_summary": {
                            "matched_tables_count": 0,
                            "auto_fetched_tables_count": 0,
                            "missing_tables_count": 0,
                            "fetch_errors_count": 0,
                            "sql_observation_count": 1,
                        },
                    },
                    ensure_ascii=False,
                ),
                risk_level=1,
            ),
        )
    finally:
        db.close()
        try:
            next(db_gen)
        except StopIteration:
            pass

    hide_response = client.post(
        f"/api/v1/sql-analysis/tasks/{task_id}/hide",
        headers={"X-API-Key": "test-api-key"},
    )
    assert hide_response.status_code == 200
    assert hide_response.json()["hidden"] is True

    list_response = client.get(
        "/api/v1/sql-analysis/tasks?page=1&page_size=20",
        headers={"X-API-Key": "test-api-key"},
    )
    assert list_response.status_code == 200
    assert all(item["task_id"] != task_id for item in list_response.json()["items"])

    detail_response = client.get(
        f"/api/v1/sql-analysis/tasks/{task_id}",
        headers={"X-API-Key": "test-api-key"},
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["task_id"] == task_id


def test_batch_hide_tasks(client: TestClient) -> None:
    task_ids = ["batch-hide-1", "batch-hide-2"]
    request = [
        SQLAnalysisItem(
            sql="select 1",
            db_type="mysql",
            dbname="demo",
            db_ip="127.0.0.1",
            db_port=3306,
        )
    ]
    context = AnalysisContextService.build_context(request=request, db=None)

    db_gen = client.app.dependency_overrides[get_db]()
    db = next(db_gen)
    try:
        for task_id in task_ids:
            AnalysisTaskService.create(
                db=db,
                data=AnalysisTaskCreate(
                    task_id=task_id,
                    status="completed",
                    report_url=f"https://example.com/reports/{task_id}.pdf",
                    sql_text=compose_sql_text(request, context=context),
                    analysis_context_json=json.dumps(context, ensure_ascii=False),
                    analysis_result_json=json.dumps(
                        {
                            "provider": "remote_workflow",
                            "db_type": "mysql",
                            "report_url": f"https://example.com/reports/{task_id}.pdf",
                            "risk_level": 1,
                            "summary": "远端摘要",
                            "report_content": "# 慢 SQL 分析报告\n\n正文",
                            "messages": ["远端摘要"],
                            "metadata_summary": {
                                "matched_tables_count": 0,
                                "auto_fetched_tables_count": 0,
                                "missing_tables_count": 0,
                                "fetch_errors_count": 0,
                                "sql_observation_count": 1,
                            },
                        },
                        ensure_ascii=False,
                    ),
                    risk_level=1,
                ),
            )
    finally:
        db.close()
        try:
            next(db_gen)
        except StopIteration:
            pass

    hide_response = client.post(
        "/api/v1/sql-analysis/tasks/hide",
        headers={"X-API-Key": "test-api-key"},
        json={"task_ids": task_ids},
    )
    assert hide_response.status_code == 200
    assert hide_response.json()["hidden_count"] == 2

    list_response = client.get(
        "/api/v1/sql-analysis/tasks?page=1&page_size=20",
        headers={"X-API-Key": "test-api-key"},
    )
    assert list_response.status_code == 200
    visible_ids = {item["task_id"] for item in list_response.json()["items"]}
    assert visible_ids.isdisjoint(task_ids)


def test_batch_download_pdfs_returns_zip(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    task_ids = ["zip-task-1", "zip-task-2", "zip-task-pending"]
    request = [
        SQLAnalysisItem(
            sql="select 1",
            db_type="mysql",
            dbname="demo",
            db_ip="127.0.0.1",
            db_port=3306,
        )
    ]
    context = AnalysisContextService.build_context(request=request, db=None)

    db_gen = client.app.dependency_overrides[get_db]()
    db = next(db_gen)
    try:
        for task_id in task_ids:
            AnalysisTaskService.create(
                db=db,
                data=AnalysisTaskCreate(
                    task_id=task_id,
                    status="completed",
                    report_url=(
                        None if task_id == "zip-task-pending" else f"https://example.com/reports/{task_id}.pdf"
                    ),
                    sql_text=compose_sql_text(request, context=context),
                    analysis_context_json=json.dumps(context, ensure_ascii=False),
                    analysis_result_json=json.dumps(
                        {
                            "provider": "remote_workflow",
                            "db_type": "mysql",
                            "report_url": (
                                None
                                if task_id == "zip-task-pending"
                                else f"https://example.com/reports/{task_id}.pdf"
                            ),
                            "risk_level": 1,
                            "summary": "远端摘要",
                            "report_content": "# 慢 SQL 分析报告\n\n正文",
                            "messages": ["远端摘要"],
                            "metadata_summary": {
                                "matched_tables_count": 0,
                                "auto_fetched_tables_count": 0,
                                "missing_tables_count": 0,
                                "fetch_errors_count": 0,
                                "sql_observation_count": 1,
                            },
                        },
                        ensure_ascii=False,
                    ),
                    risk_level=1,
                ),
            )
    finally:
        db.close()
        try:
            next(db_gen)
        except StopIteration:
            pass

    class FakeResponse:
        def __init__(self, content: bytes) -> None:
            self.content = content

        def raise_for_status(self) -> None:
            return None

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url):
            return FakeResponse(f"PDF:{url}".encode("utf-8"))

    monkeypatch.setattr(sql_analysis.httpx, "AsyncClient", FakeAsyncClient)

    response = client.post(
        "/api/v1/sql-analysis/download-pdfs",
        headers={"X-API-Key": "test-api-key"},
        json={"task_ids": task_ids},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    zip_file = zipfile.ZipFile(BytesIO(response.content))
    names = set(zip_file.namelist())
    assert "analysis-report-zip-task-1.pdf" in names
    assert "analysis-report-zip-task-2.pdf" in names
    assert "README.txt" in names
    assert "zip-task-pending" in zip_file.read("README.txt").decode("utf-8")


def test_remote_parser_handles_split_stream_messages() -> None:
    provider = RemoteWorkflowReportProvider()
    result = provider._parse_workflow_result(
        {
            "data": {
                "events": [
                    {
                        "event": "output_msg",
                        "output_schema": {
                            "message": "结果处理完毕，下一步准备汇总批次数据，请稍后。"
                        },
                    },
                    {
                        "event": "stream_msg",
                        "output_schema": {
                            "delta": {
                                "content": "# 慢 SQL"
                            }
                        },
                    },
                    {
                        "event": "stream_msg",
                        "output_schema": {
                            "chunks": [
                                " 分析报告\n\n## 一、分析概述\n\n这是概述。",
                                "\n\n## 二、整体风险评估等级\n\n- 高风险 □ (存在严重缺陷，可能导致服务不可用)\n- 中风险 ■ (存在明显性能问题，需纳入优化计划)\n- 低风险 □ (性能表现可接受，或问题可忽略)\n\n## 三、分析结果详情\n\n这里是详情内容。",
                            ]
                        },
                    },
                    {
                        "event": "output_msg",
                        "output_schema": {
                            "message": "慢 SQL 分析报告下载链接：\nhttps://example.com/reports/split.pdf"
                        },
                    },
                ]
            }
        }
    )

    assert result["report_url"] == "https://example.com/reports/split.pdf"
    assert result["risk_level"] == 2
    assert result["report_content"].startswith("# 慢 SQL 分析报告")
    assert "## 三、分析结果详情" in result["report_content"]


def test_extract_mysql_metadata_from_ddl() -> None:
    ddl = """
    CREATE TABLE `audit_log` (
      `id` bigint NOT NULL,
      `user_id` bigint NOT NULL,
      `detail` varchar(255) DEFAULT NULL,
      PRIMARY KEY (`id`),
      UNIQUE KEY `uniq_user_id` (`user_id`),
      KEY `idx_detail` (`detail`)
    ) ENGINE=InnoDB
    """

    metadata = AnalysisContextService._build_metadata_details(
        {
            "db_type": "mysql",
            "db_name": "demo",
            "db_ip": "127.0.0.1",
            "db_port": 3306,
            "db_version": "8.0.36",
            "table_name": "audit_log",
            "table_rows": 12,
            "ddl": ddl,
        }
    )

    assert [item["name"] for item in metadata["index_definitions"]] == [
        "PRIMARY",
        "uniq_user_id",
        "idx_detail",
    ]
    assert metadata["column_definitions"][0]["name"] == "id"
    assert metadata["column_definitions"][0]["nullable"] == "NO"


def test_extract_postgresql_indexes_from_ddl() -> None:
    ddl = """
    CREATE TABLE public.orders (
      id bigint NOT NULL,
      user_id bigint NOT NULL,
      created_at timestamp without time zone DEFAULT now()
    );
    CREATE UNIQUE INDEX orders_user_uidx ON orders USING btree (user_id);
    CREATE INDEX orders_created_idx ON orders (created_at);
    """

    metadata = AnalysisContextService._build_metadata_details(
        {
            "db_type": "postgresql",
            "db_name": "demo",
            "db_ip": "127.0.0.1",
            "db_port": 5432,
            "db_version": "15.3",
            "table_name": "orders",
            "table_rows": 50,
            "ddl": ddl,
        }
    )

    assert [item["name"] for item in metadata["index_definitions"]] == [
        "orders_user_uidx",
        "orders_created_idx",
    ]
    assert metadata["index_definitions"][0]["unique"] is True
    assert metadata["column_definitions"][2]["name"] == "created_at"


def test_compose_workflow_document_compacts_when_too_long(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(report_provider_module.settings, "workflow_file_content_max_chars", 1200)

    long_sql = "select * from audit_log where " + " or ".join(
        f"user_id = {index}" for index in range(1, 80)
    )
    request = [
        SQLAnalysisItem(
            sql=long_sql,
            db_type="mysql",
            dbname="demo",
            db_ip="127.0.0.1",
            db_port=3306,
            template_sql=long_sql,
        )
    ]
    context = {
        "db_targets": [
            {
                "db_type": "mysql",
                "dbname": "demo",
                "db_ip": "127.0.0.1",
                "db_port": 3306,
                "tables": ["audit_log"],
            }
        ],
        "matched_tables": [
            {
                "db_type": "mysql",
                "db_name": "demo",
                "db_ip": "127.0.0.1",
                "db_port": 3306,
                "db_version": "8.0.36",
                "table_name": "audit_log",
                "table_rows": 128,
                "ddl": "CREATE TABLE audit_log(id bigint primary key, user_id bigint, created_at datetime, KEY idx_user_created(user_id, created_at))",
                "index_definitions": [
                    {
                        "name": "idx_user_created",
                        "index_type": "INDEX",
                        "columns": ["user_id", "created_at"],
                        "unique": False,
                    }
                ],
                "column_definitions": [
                    {"name": "id", "data_type": "bigint", "nullable": "NO", "default": None},
                    {"name": "user_id", "data_type": "bigint", "nullable": "YES", "default": None},
                    {"name": "created_at", "data_type": "datetime", "nullable": "YES", "default": None},
                ],
            }
        ],
        "missing_tables": [],
        "auto_fetched_tables": [],
        "fetch_errors": [],
        "sql_observations": [
            {
                "sql": long_sql,
                "db_name": "demo",
                "db_type": "mysql",
                "exact_match_count": 2,
                "avg_query_time_ms": 2200,
                "max_query_time_ms": 4200,
            }
        ],
    }

    document = compose_workflow_document(request, context)

    assert len(document) <= 1200
    assert "## 【数据库信息】" in document
    assert "## 【SQL清单】" in document
    assert "## 【结构化抽取参考(JSON)】" in document
    assert "## 【表结构与索引信息】" in document
    assert '"sql": [' in document
    assert "table_rows_exact" in document
    assert "index_count" in document
    assert "idx_user_created" in document
    assert "...(已截断)" in document


def test_compose_sql_text_uses_structured_metadata_document() -> None:
    request = [
        SQLAnalysisItem(
            sql="select * from audit_log where user_id = 1 order by created_at desc",
            db_type="mysql",
            dbname="demo",
            db_ip="127.0.0.1",
            db_port=3306,
            template_sql="SELECT * FROM audit_log WHERE user_id = ? ORDER BY created_at DESC",
        )
    ]
    context = {
        "db_targets": [
            {
                "db_type": "mysql",
                "dbname": "demo",
                "db_ip": "127.0.0.1",
                "db_port": 3306,
                "tables": ["audit_log"],
            }
        ],
        "matched_tables": [
            {
                "db_type": "mysql",
                "db_name": "demo",
                "db_ip": "127.0.0.1",
                "db_port": 3306,
                "db_version": "8.0.36",
                "table_name": "audit_log",
                "table_rows": 128,
                "ddl": "CREATE TABLE audit_log(id bigint primary key, user_id bigint, created_at datetime, KEY idx_user_created(user_id, created_at))",
                "index_definitions": [
                    {
                        "name": "idx_user_created",
                        "index_type": "INDEX",
                        "columns": ["user_id", "created_at"],
                        "unique": False,
                    }
                ],
                "column_definitions": [
                    {"name": "id", "data_type": "bigint", "nullable": "NO", "default": None},
                    {"name": "user_id", "data_type": "bigint", "nullable": "YES", "default": None},
                ],
            }
        ],
        "missing_tables": [],
        "auto_fetched_tables": [],
        "fetch_errors": [],
        "sql_observations": [
            {
                "sql": "select * from audit_log where user_id = 1 order by created_at desc",
                "db_name": "demo",
                "db_type": "mysql",
                "exact_match_count": 2,
                "avg_query_time_ms": 2200,
                "max_query_time_ms": 4200,
            }
        ],
    }

    sql_text = compose_sql_text(request, context=context)

    assert "# 慢 SQL 分析输入文档" in sql_text
    assert "## 【数据库信息】" in sql_text
    assert "## 【结构化抽取参考(JSON)】" in sql_text
    assert "## 【SQL观测统计】" in sql_text
    assert "## 【表结构与索引信息】" in sql_text
    assert '"table_names": [' in sql_text
    assert "table_rows_exact: 128" in sql_text
    assert "index_count: 1" in sql_text
    assert "idx_user_created" in sql_text
    assert "CREATE TABLE audit_log" in sql_text
    assert "分析上下文(JSON)" not in sql_text


def test_build_remote_result_payload_marks_metadata_mismatch() -> None:
    request = [
        SQLAnalysisItem(
            sql="select * from account where acct_id = 1",
            db_type="mysql",
            dbname="CUSDBX",
            db_ip="127.0.0.1",
            db_port=3306,
        )
    ]
    context = {
        "db_targets": [
            {
                "db_type": "mysql",
                "dbname": "CUSDBX",
                "db_ip": "127.0.0.1",
                "db_port": 3306,
                "tables": ["account"],
            }
        ],
        "matched_tables": [
            {
                "db_type": "mysql",
                "db_name": "CUSDBX",
                "db_ip": "127.0.0.1",
                "db_port": 3306,
                "db_version": "8.0.36",
                "table_name": "account",
                "table_rows": 150000,
                "ddl": "CREATE TABLE account(acct_id bigint primary key, user_id bigint, KEY idx_acct_id(acct_id))",
                "index_definitions": [
                    {
                        "name": "idx_acct_id",
                        "index_type": "INDEX",
                        "columns": ["acct_id"],
                        "unique": False,
                    }
                ],
                "column_definitions": [
                    {"name": "acct_id", "data_type": "bigint", "nullable": "NO", "default": None},
                ],
            }
        ],
        "missing_tables": [],
        "auto_fetched_tables": [],
        "fetch_errors": [],
        "sql_observations": [],
    }
    payload = build_remote_result_payload(
        request=request,
        context=context,
        parsed_result={
            "report_url": "https://example.com/reports/mismatch.pdf",
            "risk_level": 1,
            "summary": "远端摘要",
            "report_content": (
                "# 慢 SQL 分析报告\n\n"
                "根据提供的元数据，当前表行数 `table_rows` 为 0。"
                "主键及索引信息在提供的 DDL 中为空，无法确认是否有索引。"
            ),
            "messages": ["远端摘要"],
        },
        input_diagnostics={
            "workflow_input_mode": "sql_text",
            "workflow_input_length": 1024,
            "compaction_level": "full",
            "matched_tables_count": 1,
            "tables_with_ddl_count": 1,
            "tables_with_indexes_count": 1,
            "authoritative_tables": [
                {
                    "table_name": "account",
                    "table_rows_exact": 150000,
                    "index_count": 1,
                    "has_indexes": True,
                    "ddl_available": True,
                }
            ],
        },
    )

    assert payload["consistency_flags"]["report_mentions_zero_rows_despite_positive_rows"] is True
    assert payload["consistency_flags"]["report_mentions_missing_indexes_despite_indexes_present"] is True
    assert "远端报告与本地权威元数据不一致" in payload["summary"]


def test_serialize_task_backfills_diagnostics_for_legacy_result_payload() -> None:
    request = [
        SQLAnalysisItem(
            sql="select * from account where acct_id = 1",
            db_type="mysql",
            dbname="CUSDBX",
            db_ip="127.0.0.1",
            db_port=3306,
        )
    ]
    context = {
        "sql_list": [request[0].sql],
        "db_targets": [
            {
                "db_type": "mysql",
                "dbname": "CUSDBX",
                "db_ip": "127.0.0.1",
                "db_port": 3306,
                "tables": ["account"],
            }
        ],
        "matched_tables": [
            {
                "db_type": "mysql",
                "db_name": "CUSDBX",
                "db_ip": "127.0.0.1",
                "db_port": 3306,
                "db_version": "8.0.36",
                "table_name": "account",
                "table_rows": 150000,
                "ddl": (
                    "CREATE TABLE `account` (\n"
                    "  `acct_id` bigint NOT NULL,\n"
                    "  `cust_id` bigint NOT NULL,\n"
                    "  PRIMARY KEY (`acct_id`),\n"
                    "  KEY `idx_cust_id` (`cust_id`)\n"
                    ") ENGINE=InnoDB"
                ),
                "index_definitions": [
                    {
                        "name": "PRIMARY",
                        "index_type": "PRIMARY KEY",
                        "columns": ["acct_id"],
                        "unique": True,
                    },
                    {
                        "name": "idx_cust_id",
                        "index_type": "INDEX",
                        "columns": ["cust_id"],
                        "unique": False,
                    },
                ],
                "column_definitions": [
                    {"name": "acct_id", "data_type": "bigint", "nullable": "NO", "default": None},
                    {"name": "cust_id", "data_type": "bigint", "nullable": "NO", "default": None},
                ],
            }
        ],
        "missing_tables": [],
        "auto_fetched_tables": [],
        "fetch_errors": [],
        "sql_observations": [],
    }
    sql_text = compose_workflow_document(request, context)
    legacy_result_json = json.dumps(
        {
            "provider": "remote_workflow",
            "db_type": "mysql",
            "report_url": "https://example.com/reports/legacy.pdf",
            "risk_level": 1,
            "summary": "远端摘要",
            "report_content": (
                "# 慢 SQL 分析报告\n\n"
                "account 表当前 table_rows 为 0。"
                "DDL 中索引为空，无法确认是否有索引。"
            ),
            "messages": ["远端摘要"],
            "metadata_summary": {
                "matched_tables_count": 1,
                "auto_fetched_tables_count": 0,
                "missing_tables_count": 0,
                "fetch_errors_count": 0,
                "sql_observation_count": 0,
                "tables_with_ddl_count": 1,
                "tables_with_indexes_count": 1,
            },
        },
        ensure_ascii=False,
    )
    task = AnalysisTask(
        task_id="legacy-task",
        status="completed",
        sql_text=sql_text,
        analysis_context_json=json.dumps(context, ensure_ascii=False),
        analysis_result_json=legacy_result_json,
    )

    serialized = AnalysisTaskService._serialize_task(task)
    diagnostics = serialized["analysis_result"]["input_diagnostics"]
    flags = serialized["analysis_result"]["consistency_flags"]

    assert diagnostics["workflow_input_length"] == len(sql_text)
    assert diagnostics["matched_tables_count"] == 1
    assert diagnostics["tables_with_indexes_count"] == 1
    assert diagnostics["authoritative_tables"][0]["table_rows_exact"] == 150000
    assert flags["report_mentions_zero_rows_despite_positive_rows"] is True
    assert flags["report_mentions_missing_indexes_despite_indexes_present"] is True
    assert "远端报告与本地权威元数据不一致" in serialized["analysis_result"]["summary"]


def test_parse_structured_sql_text_returns_only_sql_blocks() -> None:
    sql_text = """# 慢 SQL 分析输入文档

## 【数据库信息】
mysql://127.0.0.1:3306/demo

## 【SQL清单】
### SQL 1
```sql
select * from audit_log where user_id = 1
```

### SQL 2
```sql
update audit_log set created_at = now() where id = 1
```

## 【SQL观测统计】
- count: 2
"""

    statements = AnalysisTaskService._parse_sql_text(sql_text)

    assert statements == [
        "select * from audit_log where user_id = 1",
        "update audit_log set created_at = now() where id = 1",
    ]


def test_parse_workflow_result_can_keep_report_without_pdf_link_when_requested() -> None:
    provider = RemoteWorkflowReportProvider()

    result = provider._parse_workflow_result(
        {
            "data": {
                "events": [
                    {
                        "event": "output_msg",
                        "output_schema": {
                            "message": "结果处理完毕，下一步准备汇总批次数据，请稍后。"
                        },
                    },
                    {
                        "event": "stream_msg",
                        "output_schema": {
                            "chunks": [
                                "# 慢 SQL 分析报告\n\n## 一、分析概述\n\n这是概述。",
                                "\n\n## 二、整体风险评估等级\n\n- 高风险 □\n- 中风险 ■\n- 低风险 □\n\n## 三、分析结果详情\n\n这里是详情内容。",
                            ]
                        },
                    },
                ]
            }
        },
        require_report_url=False,
    )

    assert result["report_url"] is None
    assert result["risk_level"] == 2
    assert "这里是详情内容" in result["report_content"]


def test_follow_until_close_retries_until_pdf_link_arrives(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = RemoteWorkflowReportProvider()
    provider.PDF_LINK_RETRY_ATTEMPTS = 2
    provider.PDF_LINK_RETRY_DELAY_SECONDS = 0
    task_id = "retry-task-with-pdf"

    db = report_provider_module.SessionLocal()
    try:
        AnalysisTaskService.create(
            db=db,
            data=AnalysisTaskCreate(
                task_id=task_id,
                status="pending",
                report_url=None,
                sql_text="select 1",
                analysis_context_json=json.dumps({}, ensure_ascii=False),
                error_message=None,
                risk_level=1,
            ),
        )
    finally:
        db.close()

    responses = iter(
        [
            {
                "data": {
                    "events": [
                        {
                            "event": "stream_msg",
                            "output_schema": {
                                "chunks": [
                                    "# 慢 SQL 分析报告\n\n## 一、分析概述\n\n第一次只返回正文。",
                                    "\n\n## 二、整体风险评估等级\n\n- 高风险 □\n- 中风险 □\n- 低风险 ■\n\n## 三、分析结果详情\n\n等待 PDF。",
                                ]
                            },
                        }
                    ]
                }
            },
            {
                "data": {
                    "events": [
                        {
                            "event": "stream_msg",
                            "output_schema": {
                                "chunks": [
                                    "# 慢 SQL 分析报告\n\n## 一、分析概述\n\n第二次返回完整结果。",
                                    "\n\n## 二、整体风险评估等级\n\n- 高风险 □\n- 中风险 □\n- 低风险 ■\n\n## 三、分析结果详情\n\nPDF 已生成。",
                                ]
                            },
                        },
                        {
                            "event": "output_msg",
                            "output_schema": {
                                "message": "慢 SQL 分析报告下载链接：\nhttps://example.com/reports/retry.pdf"
                            },
                        },
                    ]
                }
            },
        ]
    )

    async def fake_invoke_followup_with_candidates(self, **kwargs):
        return next(responses)

    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(
        report_provider_module.RemoteWorkflowReportProvider,
        "_invoke_followup_with_candidates",
        fake_invoke_followup_with_candidates,
    )
    monkeypatch.setattr(report_provider_module.asyncio, "sleep", fake_sleep)

    asyncio.run(
        provider._follow_until_close(
            task_id=task_id,
            request=[],
            context={},
            input_diagnostics={},
            input_payload=[{"input": "payload"}],
            session_id="session-1",
            message_id="message-1",
        )
    )

    db = report_provider_module.SessionLocal()
    try:
        task = AnalysisTaskService.get_by_id(db, task_id)
    finally:
        db.close()

    assert task is not None
    assert task["status"] == "completed"
    assert task["report_url"] == "https://example.com/reports/retry.pdf"


def test_follow_until_close_completes_without_pdf_when_report_content_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = RemoteWorkflowReportProvider()
    provider.PDF_LINK_RETRY_ATTEMPTS = 2
    provider.PDF_LINK_RETRY_DELAY_SECONDS = 0
    task_id = "retry-task-no-pdf"

    db = report_provider_module.SessionLocal()
    try:
        AnalysisTaskService.create(
            db=db,
            data=AnalysisTaskCreate(
                task_id=task_id,
                status="pending",
                report_url=None,
                sql_text="select 1",
                analysis_context_json=json.dumps({}, ensure_ascii=False),
                error_message=None,
                risk_level=1,
            ),
        )
    finally:
        db.close()

    response = {
        "data": {
            "events": [
                {
                    "event": "stream_msg",
                    "output_schema": {
                        "chunks": [
                            "# 慢 SQL 分析报告\n\n## 一、分析概述\n\n已生成正文。",
                            "\n\n## 二、整体风险评估等级\n\n- 高风险 □\n- 中风险 □\n- 低风险 ■\n\n## 三、分析结果详情\n\n当前仅返回正文。",
                        ]
                    },
                }
            ]
        }
    }

    async def fake_invoke_followup_with_candidates(self, **kwargs):
        return response

    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(
        report_provider_module.RemoteWorkflowReportProvider,
        "_invoke_followup_with_candidates",
        fake_invoke_followup_with_candidates,
    )
    monkeypatch.setattr(report_provider_module.asyncio, "sleep", fake_sleep)

    asyncio.run(
        provider._follow_until_close(
            task_id=task_id,
            request=[],
            context={},
            input_diagnostics={},
            input_payload=[{"input": "payload"}],
            session_id="session-1",
            message_id="message-1",
        )
    )

    db = report_provider_module.SessionLocal()
    try:
        task = AnalysisTaskService.get_by_id(db, task_id)
    finally:
        db.close()

    assert task is not None
    assert task["status"] == "completed"
    assert task["report_url"] is None
    assert task["analysis_result"]["report_content"]
