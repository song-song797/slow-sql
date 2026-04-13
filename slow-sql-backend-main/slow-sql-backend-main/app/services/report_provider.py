import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.data_source import DataSource
from app.schemas.analysis_task import AnalysisTaskCreate, AnalysisTaskUpdate
from app.schemas.sql_analysis import SQLAnalysisItem, SQLAnalysisItemResponse
from app.services.analysis_context_service import AnalysisContextService
from app.services.analysis_task_service import AnalysisTaskService

logger = logging.getLogger(__name__)
REMOTE_WORKFLOW_RESULT_PROVIDER = "remote_workflow"
REMOTE_WORKFLOW_INPUT_MODE = "sql_text"
WORKFLOW_DB_SECTION = "## 【数据库信息】"
WORKFLOW_SQL_SECTION = "## 【SQL清单】"
WORKFLOW_JSON_REFERENCE_SECTION = "## 【结构化抽取参考(JSON)】"
WORKFLOW_METADATA_SECTION = "## 【表结构与索引信息】"
WORKFLOW_OBSERVATION_SECTION = "## 【SQL观测统计】"
WORKFLOW_DDL_SECTION = "## 【原始DDL】"
WORKFLOW_MISSING_SECTION = "## 【元数据缺失说明】"


def _build_workflow_document_bundle(
    request: List[SQLAnalysisItem],
    context: Dict[str, Any],
) -> tuple[str, Dict[str, Any]]:
    document, compaction_level = compose_workflow_document(request, context, return_debug=True)
    return document, build_input_diagnostics(
        context=context,
        sql_text=document,
        compaction_level=compaction_level,
        workflow_input_mode=REMOTE_WORKFLOW_INPUT_MODE,
    )


def compose_sql_text(request: List[SQLAnalysisItem], context: Optional[Dict[str, Any]] = None) -> str:
    if context:
        return compose_workflow_document(request, context)

    db_lines: List[str] = []
    sql_sections: List[str] = []

    for index, item in enumerate(request, start=1):
        db_type = settings.normalize_db_type(item.db_type)
        db_port = item.db_port or settings.get_default_port_for_db_type(db_type)
        if item.db_ip and item.dbname:
            db_lines.append(f"{db_type}://{item.db_ip}:{db_port}/{item.dbname}")
        sql_sections.extend(
            [
                f"### SQL {index}",
                f"- 所属数据库: {db_type}://{item.db_ip or '-'}:{db_port}/{item.dbname or '-'}",
                f"- 表名: {', '.join(AnalysisContextService.extract_table_names(item.sql)) or '未识别到业务表'}",
                "```sql",
                item.sql.strip(),
                "```",
                "",
            ]
        )

    lines = [
        "# 慢 SQL 分析输入文档",
        "",
        "## 分析规则",
        "- 以下“权威表元数据摘要”优先级高于模型自行推测。",
        "- 若 table_rows_exact 有明确数值，禁止改写为 0、未知或空值。",
        "- 若 index_count > 0 或 has_indexes = yes，禁止写成“索引为空”“无索引”或“无法确认是否有索引”。",
        "- 若无法确认，请仅依据“元数据缺失说明”描述，不得凭空补默认值。",
        "",
        WORKFLOW_DB_SECTION,
        *(list(dict.fromkeys(db_lines)) or ["(未提供数据库连接信息)"]),
        "",
        WORKFLOW_METADATA_SECTION,
        "- 未命中任何表元数据",
        "",
        WORKFLOW_SQL_SECTION,
        *(sql_sections or ["- 未提供 SQL"]),
        WORKFLOW_OBSERVATION_SECTION,
        "- 未获取到 SQL 观测统计",
        "",
        WORKFLOW_DDL_SECTION,
        "- 未命中任何 DDL",
        "",
        WORKFLOW_MISSING_SECTION,
        "- 未提供分析上下文，未补充表结构、DDL 与索引元数据",
    ]
    return "\n".join(lines).strip()


def _format_timestamp(timestamp: Any) -> str:
    if timestamp in (None, ""):
        return "-"
    try:
        raw_value = int(timestamp)
        if raw_value > 10_000_000_000:
            return datetime.fromtimestamp(raw_value / 1000).strftime("%Y-%m-%d %H:%M:%S")
        return datetime.fromtimestamp(raw_value).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(timestamp)


def _truncate_text(value: str, limit: int) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 15)].rstrip() + "...(已截断)"


def _format_index_summary(index_definitions: List[Dict[str, Any]], *, limit: int) -> str:
    if not index_definitions:
        return "-"
    parts = []
    for item in index_definitions:
        name = item.get("name") or "unnamed"
        columns = ",".join(item.get("columns") or [])
        suffix = " unique" if item.get("unique") else ""
        parts.append(f"{name}[{columns}]{suffix}")
    return _truncate_text(" | ".join(parts), limit)


def _format_column_summary(column_definitions: List[Dict[str, Any]], *, max_columns: int, limit: int) -> str:
    if not column_definitions:
        return "-"
    parts = []
    for index, item in enumerate(column_definitions):
        if index >= max_columns:
            parts.append(f"... 共 {len(column_definitions)} 列")
            break
        nullable = "NOT NULL" if item.get("nullable") == "NO" else "NULL"
        default = item.get("default")
        default_text = f" DEFAULT {default}" if default not in (None, "", "NULL") else ""
        parts.append(f"{item.get('name')} {item.get('data_type')} {nullable}{default_text}".strip())
    return _truncate_text("; ".join(parts), limit)


def _format_index_names(index_definitions: List[Dict[str, Any]], *, limit: int) -> str:
    if not index_definitions:
        return "-"
    names = [str(item.get("name") or "unnamed").strip() for item in index_definitions]
    return _truncate_text(", ".join([name for name in names if name] or ["unnamed"]), limit)


def _format_index_columns(index_definitions: List[Dict[str, Any]], *, limit: int) -> str:
    if not index_definitions:
        return "-"
    parts = []
    for item in index_definitions:
        name = item.get("name") or "unnamed"
        columns = ",".join(item.get("columns") or [])
        parts.append(f"{name}({columns or '-'})")
    return _truncate_text(" | ".join(parts), limit)


def _build_workflow_json_reference(
    request: List[SQLAnalysisItem],
    context: Dict[str, Any],
    *,
    ddl_limit: int,
    column_limit: int,
    column_count_limit: int,
    sql_limit: int,
) -> str:
    table_map: Dict[tuple[str, str, int, str, str], Dict[str, Any]] = {}
    for row in context.get("matched_tables", []):
        key = (
            settings.normalize_db_type(row.get("db_type")),
            row.get("db_ip") or "",
            row.get("db_port") or settings.get_default_port_for_db_type(row.get("db_type")),
            row.get("db_name") or "",
            row.get("table_name") or "",
        )
        table_map[key] = row

    payload: Dict[str, Any] = {"sql": []}
    for item in request:
        db_type = settings.normalize_db_type(item.db_type)
        db_port = item.db_port or settings.get_default_port_for_db_type(db_type)
        related_tables = AnalysisContextService.extract_table_names(item.sql)
        ddl_list: List[str] = []
        index_structures: List[str] = []
        column_structures: List[str] = []

        for table_name in related_tables:
            table_info = table_map.get((db_type, item.db_ip or "", db_port, item.dbname or "", table_name))
            if not table_info:
                continue
            ddl_text = (table_info.get("ddl") or "").strip()
            if ddl_text:
                ddl_list.append(_truncate_text(ddl_text, ddl_limit))
            index_structures.append(
                _format_index_columns(table_info.get("index_definitions") or [], limit=320)
            )
            column_structures.append(
                _format_column_summary(
                    table_info.get("column_definitions") or [],
                    max_columns=column_count_limit,
                    limit=column_limit,
                )
            )

        payload["sql"].append(
            {
                "sql_content": _truncate_text(item.sql.strip(), sql_limit),
                "db_name": item.dbname or "",
                "db_ip": item.db_ip or "",
                "db_port": str(db_port),
                "table_names": related_tables,
                "ddl": ddl_list,
                "indexes_structure": [value for value in index_structures if value and value != "-"],
                "columns_structure": [value for value in column_structures if value and value != "-"],
            }
        )

    return json.dumps(payload, ensure_ascii=False, indent=2)


def _guess_key_columns_hint(
    table_name: str,
    index_definitions: List[Dict[str, Any]],
    column_definitions: List[Dict[str, Any]],
) -> str:
    if index_definitions:
        primary_index = next(
            (item for item in index_definitions if str(item.get("name") or "").upper() == "PRIMARY"),
            None,
        )
        if primary_index and primary_index.get("columns"):
            return ", ".join(primary_index["columns"])
        first_index = next((item for item in index_definitions if item.get("columns")), None)
        if first_index:
            return ", ".join(first_index["columns"])

    table_prefix = table_name.rstrip("s").lower()
    candidate_names = {"id", f"{table_prefix}_id"}
    inferred_columns = []
    for item in column_definitions:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        normalized = name.lower()
        if normalized in candidate_names or normalized.endswith("_id"):
            inferred_columns.append(name)
    return ", ".join(inferred_columns[:3]) if inferred_columns else "-"


def _build_workflow_document_with_mode(
    request: List[SQLAnalysisItem],
    context: Dict[str, Any],
    *,
    template_limit: int,
    include_observation_sql_block: bool,
    include_full_ddl: bool,
    ddl_limit: int,
    column_limit: int,
    column_count_limit: int,
    sql_limit: int,
) -> str:
    db_lines: List[str] = []
    rule_sections: List[str] = [
        "- 以下“权威表元数据摘要”来自本地元数据缓存或数据源补拉结果，优先级高于模型自行推测。",
        "- 若 table_rows_exact 为数值，禁止改写为 0、未知或空值。",
        "- 若 index_count > 0 或 has_indexes = yes，禁止写成“索引为空”“无索引”或“无法确认是否有索引”。",
        "- 若 ddl_available = yes，禁止写成“DDL 为空”或“未提供 DDL”。",
        "- 若无法确认，请仅依据“元数据缺失说明”描述，不得凭空补默认值。",
    ]
    authoritative_sections: List[str] = []
    sql_sections: List[str] = []
    observation_sections: List[str] = []
    json_reference_sections: List[str] = []
    ddl_sections: List[str] = []
    missing_sections: List[str] = []
    table_map: Dict[tuple[str, str, int, str, str], Dict[str, Any]] = {}

    for row in context.get("matched_tables", []):
        key = (
            settings.normalize_db_type(row.get("db_type")),
            row.get("db_ip") or "",
            row.get("db_port") or settings.get_default_port_for_db_type(row.get("db_type")),
            row.get("db_name") or "",
            row.get("table_name") or "",
        )
        table_map[key] = row

    for index, item in enumerate(request, start=1):
        db_type = settings.normalize_db_type(item.db_type)
        db_port = item.db_port or settings.get_default_port_for_db_type(db_type)
        related_tables = AnalysisContextService.extract_table_names(item.sql)

        if item.db_ip and item.dbname:
            db_lines.append(f"{db_type}://{item.db_ip}:{db_port}/{item.dbname}")

        sql_sections.extend(
            [
                f"### SQL {index}",
                f"- 所属数据库: {db_type}://{item.db_ip or '-'}:{db_port}/{item.dbname or '-'}",
                f"- 数据库类型: {db_type}",
                f"- 表名: {', '.join(related_tables) if related_tables else '未识别到业务表'}",
                f"- 模板SQL: {_truncate_text(item.template_sql or '-', template_limit)}",
                "```sql",
                _truncate_text(item.sql.strip(), sql_limit),
                "```",
                "",
            ]
        )

    db_lines = list(dict.fromkeys(db_lines))
    json_reference_sections.extend(
        [
            "以下 JSON 字段名与第一层抽取节点目标输出保持一致，请优先按此结构理解并提取：",
            "```json",
            _build_workflow_json_reference(
                request,
                context,
                ddl_limit=ddl_limit,
                column_limit=column_limit,
                column_count_limit=column_count_limit,
                sql_limit=sql_limit,
            ),
            "```",
            "",
        ]
    )

    seen_observation_keys: set[str] = set()
    for observation in context.get("sql_observations", []):
        sql_text = observation.get("sql") or observation.get("template_sql") or ""
        observation_key = f"{observation.get('db_type')}|{observation.get('db_name')}|{sql_text}"
        if observation_key in seen_observation_keys:
            continue
        seen_observation_keys.add(observation_key)
        observation_sections.extend(
            [
                f"### 观测项 {len(seen_observation_keys)}",
                f"- db_type: {settings.normalize_db_type(observation.get('db_type'))}",
                f"- db_name: {observation.get('db_name') or '-'}",
                f"- db_ip: {observation.get('db_ip') or '-'}",
                f"- cluster_count: {observation.get('cluster_count') or observation.get('exact_match_count') or 0}",
                f"- min_query_time_ms: {observation.get('min_query_time_ms') if observation.get('min_query_time_ms') is not None else '-'}",
                f"- avg_query_time_ms: {observation.get('avg_query_time_ms') if observation.get('avg_query_time_ms') is not None else '-'}",
                f"- max_query_time_ms: {observation.get('max_query_time_ms') if observation.get('max_query_time_ms') is not None else '-'}",
                f"- latest_timestamp: {_format_timestamp(observation.get('latest_timestamp'))}",
            ]
        )
        if include_observation_sql_block:
            observation_sections.extend(
                [
                    "```sql",
                    _truncate_text(sql_text or "-- 未提供 SQL 文本 --", sql_limit),
                    "```",
                ]
            )
        observation_sections.append("")

    seen_table_keys: set[tuple[str, str, int, str, str]] = set()
    for target in context.get("db_targets", []):
        target_db_type = settings.normalize_db_type(target.get("db_type"))
        target_db_port = target.get("db_port") or settings.get_default_port_for_db_type(target_db_type)
        target_db_ip = target.get("db_ip") or ""
        target_db_name = target.get("dbname") or ""
        target_tables = target.get("tables") or []
        if not target_tables:
            missing_sections.append(
                f"- {target_db_type}://{target_db_ip}:{target_db_port}/{target_db_name} 未识别到业务表"
            )
            continue

        for table_name in target_tables:
            table_key = (
                target_db_type,
                target_db_ip,
                target_db_port,
                target_db_name,
                table_name,
            )
            if table_key in seen_table_keys:
                continue
            seen_table_keys.add(table_key)

            table_info = table_map.get(table_key)
            if not table_info:
                missing_sections.append(
                    f"- 缺少表元数据：{target_db_type}://{target_db_ip}:{target_db_port}/{target_db_name}.{table_name}"
                )
                continue

            index_definitions = table_info.get("index_definitions") or []
            column_definitions = table_info.get("column_definitions") or []
            authoritative_sections.extend(
                [
                    f"### {table_name}",
                    f"- 数据库类型: {target_db_type}",
                    f"- 数据库信息: {target_db_type}://{target_db_ip or '-'}:{target_db_port}/{target_db_name or '-'}",
                    f"- 表名: {table_name}",
                    f"- table_name: {table_name}",
                    f"- 总行数: {table_info.get('table_rows') if table_info.get('table_rows') is not None else '-'}",
                    f"- table_rows_exact: {table_info.get('table_rows') if table_info.get('table_rows') is not None else '-'}",
                    f"- 索引数量: {len(index_definitions)}",
                    f"- index_count: {len(index_definitions)}",
                    f"- has_indexes: {'yes' if index_definitions else 'no'}",
                    f"- Indexes structure: {_format_index_columns(index_definitions, limit=520)}",
                    f"- index_names: {_format_index_names(index_definitions, limit=320)}",
                    f"- index_columns: {_format_index_columns(index_definitions, limit=520)}",
                    f"- 字段数量: {len(column_definitions)}",
                    f"- column_count: {len(column_definitions)}",
                    f"- 主键/关键列提示: {_guess_key_columns_hint(table_name, index_definitions, column_definitions)}",
                    f"- key_columns_hint: {_guess_key_columns_hint(table_name, index_definitions, column_definitions)}",
                    f"- ddl_available: {'yes' if (table_info.get('ddl') or '').strip() else 'no'}",
                    f"- db_version: {table_info.get('db_version') or '-'}",
                    f"- Columns structure: {_format_column_summary(column_definitions, max_columns=column_count_limit, limit=column_limit)}",
                    f"- column_definitions: {_format_column_summary(column_definitions, max_columns=column_count_limit, limit=column_limit)}",
                    "",
                ]
            )

            ddl_text = (table_info.get("ddl") or "").strip()
            if ddl_text:
                if include_full_ddl:
                    ddl_sections.extend(
                        [
                            f"### {table_name}",
                            "```sql",
                            _truncate_text(ddl_text, ddl_limit),
                            "```",
                            "",
                        ]
                    )
                else:
                    ddl_sections.extend(
                        [
                            f"### {table_name}",
                            f"- ddl_excerpt: {_truncate_text(ddl_text, ddl_limit)}",
                            "",
                        ]
                    )
            else:
                ddl_sections.extend(
                    [
                        f"### {table_name}",
                        "- ddl_excerpt: -- 未命中 DDL --",
                        "",
                    ]
                )

    for fetch_error in context.get("fetch_errors", []):
        missing_sections.append(
            f"- 自动补拉失败：{fetch_error.get('db_type')}://{fetch_error.get('db_ip')}:{fetch_error.get('db_port')}/{fetch_error.get('db_name')}.{fetch_error.get('table_name')} -> {fetch_error.get('error')}"
        )

    if not observation_sections:
        observation_sections.append("- 未获取到 SQL 观测统计")
    if not authoritative_sections:
        authoritative_sections.append("- 未命中任何表元数据")
    if not ddl_sections:
        ddl_sections.append("- 未命中任何 DDL")
    if not missing_sections:
        missing_sections.append("- 本次分析所涉及的表元数据已完整命中")

    lines = ["# 慢 SQL 分析输入文档", "", "## 分析规则"]
    lines.extend(rule_sections)
    lines.append("")
    lines.append(WORKFLOW_DB_SECTION)
    if db_lines:
        lines.extend(db_lines)
    else:
        lines.append("(未提供数据库信息)")

    lines.append("")
    lines.append(WORKFLOW_METADATA_SECTION)
    lines.extend(authoritative_sections)
    lines.append(WORKFLOW_SQL_SECTION)
    lines.extend(sql_sections)
    lines.append(WORKFLOW_JSON_REFERENCE_SECTION)
    lines.extend(json_reference_sections)
    lines.append(WORKFLOW_OBSERVATION_SECTION)
    lines.extend(observation_sections)
    lines.append(WORKFLOW_DDL_SECTION)
    lines.extend(ddl_sections)
    lines.append(WORKFLOW_MISSING_SECTION)
    lines.extend(missing_sections)
    return "\n".join(lines).strip()


def _build_emergency_authoritative_table_line(row: Dict[str, Any]) -> str:
    indexes = row.get("index_definitions") or []
    return (
        f"- {row.get('table_name')}: table_rows_exact={row.get('table_rows') if row.get('table_rows') is not None else '-'}, "
        f"index_count={len(indexes)}, has_indexes={'yes' if indexes else 'no'}, "
        f"index_names={_format_index_names(indexes, limit=120)}"
    )


def _build_emergency_workflow_document(
    request: List[SQLAnalysisItem],
    context: Dict[str, Any],
    *,
    max_chars: int,
) -> str:
    db_lines: List[str] = []
    sql_lines: List[str] = []
    json_reference_lines: List[str] = []
    observation_lines: List[str] = []
    authoritative_lines: List[str] = []
    missing_lines: List[str] = []

    sql_limit = max(180, min(420, max_chars // max(2, len(request) * 3)))

    for index, item in enumerate(request, start=1):
        db_type = settings.normalize_db_type(item.db_type)
        db_port = item.db_port or settings.get_default_port_for_db_type(db_type)
        if item.db_ip and item.dbname:
            db_lines.append(f"- {db_type}://{item.db_ip}:{db_port}/{item.dbname}")
        sql_lines.append(
            f"- SQL {index}: 表 {', '.join(AnalysisContextService.extract_table_names(item.sql)) or '未识别'} | {_truncate_text(item.sql, sql_limit)}"
        )

    for index, observation in enumerate(context.get("sql_observations", []), start=1):
        observation_lines.append(
            f"- 观测 {index}: count={observation.get('cluster_count') or observation.get('exact_match_count') or 0}, avg={observation.get('avg_query_time_ms') or '-'}ms, max={observation.get('max_query_time_ms') or '-'}ms"
        )

    json_reference_lines.extend(
        [
            "- 结构化抽取目标(JSON)如下：",
            "```json",
            _build_workflow_json_reference(
                request,
                context,
                ddl_limit=max(120, min(ddl_limit := max_chars // 4, 400)),
                column_limit=max(120, min(column_limit := max_chars // 5, 280)),
                column_count_limit=4,
                sql_limit=sql_limit,
            ),
            "```",
        ]
    )

    for row in context.get("matched_tables", []):
        authoritative_lines.append(_build_emergency_authoritative_table_line(row))

    for row in context.get("missing_tables", []):
        missing_lines.append(
            f"- 缺失表元数据: {row.get('db_name')}.{row.get('table_name')}"
        )
    for row in context.get("fetch_errors", []):
        missing_lines.append(
            f"- 自动补拉失败: {row.get('db_name')}.{row.get('table_name')} -> {row.get('error')}"
        )

    lines = [
        "# 慢 SQL 分析输入文档",
        "",
        "## 分析规则",
        "- 权威表元数据摘要优先于模型推测",
        "- table_rows_exact 不得改写为 0",
        "- index_count > 0 时不得写索引为空",
        "",
        WORKFLOW_DB_SECTION,
        *(list(dict.fromkeys(db_lines)) or ["(未提供数据库信息)"]),
        "",
        WORKFLOW_METADATA_SECTION,
        *(authoritative_lines or ["- 未命中任何表元数据"]),
        "",
        WORKFLOW_SQL_SECTION,
        *(sql_lines or ["- 未提供 SQL"]),
        "",
        WORKFLOW_JSON_REFERENCE_SECTION,
        *(json_reference_lines or ["- 未提供结构化抽取参考"]),
        "",
        WORKFLOW_OBSERVATION_SECTION,
        *(observation_lines or ["- 未获取到 SQL 观测统计"]),
        "",
        WORKFLOW_DDL_SECTION,
        "- 紧急压缩模式已省略 DDL，请仅依据权威表元数据摘要判断",
        "",
        WORKFLOW_MISSING_SECTION,
        *(missing_lines or ["- 本次分析所涉及的表元数据已完整命中"]),
    ]
    return _truncate_text("\n".join(lines).strip(), max_chars)


def compose_workflow_document(
    request: List[SQLAnalysisItem],
    context: Dict[str, Any],
    *,
    return_debug: bool = False,
) -> str | tuple[str, str]:
    max_chars = max(800, settings.workflow_file_content_max_chars)
    candidate_configs = [
        {
            "name": "full",
            "template_limit": 800,
            "include_observation_sql_block": True,
            "include_full_ddl": True,
            "ddl_limit": 1600,
            "column_limit": 1200,
            "column_count_limit": 24,
            "sql_limit": 4000,
        },
        {
            "name": "trimmed_ddl",
            "template_limit": 240,
            "include_observation_sql_block": False,
            "include_full_ddl": True,
            "ddl_limit": 600,
            "column_limit": 800,
            "column_count_limit": 12,
            "sql_limit": 2400,
        },
        {
            "name": "ddl_excerpt",
            "template_limit": 120,
            "include_observation_sql_block": False,
            "include_full_ddl": False,
            "ddl_limit": 280,
            "column_limit": 420,
            "column_count_limit": 8,
            "sql_limit": 1600,
        },
        {
            "name": "minimal",
            "template_limit": 60,
            "include_observation_sql_block": False,
            "include_full_ddl": False,
            "ddl_limit": 160,
            "column_limit": 260,
            "column_count_limit": 5,
            "sql_limit": 900,
        },
    ]

    last_document = ""
    last_compaction = "minimal"
    for config in candidate_configs:
        compaction_name = str(config["name"])
        runtime_config = {key: value for key, value in config.items() if key != "name"}
        candidate = _build_workflow_document_with_mode(request, context, **runtime_config)
        last_document = candidate
        last_compaction = compaction_name
        if len(candidate) <= max_chars:
            logger.info(
                "Workflow input document compacted to %s chars (limit=%s, config=%s)",
                len(candidate),
                max_chars,
                config,
            )
            return (candidate, compaction_name) if return_debug else candidate

    logger.warning(
        "Workflow input document still exceeds limit after compaction: len=%s limit=%s",
        len(last_document),
        max_chars,
    )
    emergency_document = _build_emergency_workflow_document(request, context, max_chars=max_chars)
    logger.warning(
        "Workflow input document switched to emergency compact mode: len=%s limit=%s",
        len(emergency_document),
        max_chars,
    )
    return (emergency_document, "emergency") if return_debug else emergency_document


def calculate_risk_level(sql_lines: List[str]) -> int:
    joined = "\n".join(sql_lines).upper()
    if "SELECT *" in joined or " JOIN " in joined:
        return 3
    if "UPDATE " in joined or "DELETE " in joined:
        return 2
    return 1


def build_metadata_summary(context: Dict[str, Any]) -> Dict[str, int]:
    matched_tables = context.get("matched_tables", [])
    return {
        "matched_tables_count": len(matched_tables),
        "auto_fetched_tables_count": len(context.get("auto_fetched_tables", [])),
        "missing_tables_count": len(context.get("missing_tables", [])),
        "fetch_errors_count": len(context.get("fetch_errors", [])),
        "sql_observation_count": len(context.get("sql_observations", [])),
        "tables_with_ddl_count": sum(1 for item in matched_tables if item.get("ddl")),
        "tables_with_indexes_count": sum(1 for item in matched_tables if item.get("index_definitions")),
    }


def build_input_diagnostics(
    *,
    context: Dict[str, Any],
    sql_text: str,
    compaction_level: str,
    workflow_input_mode: str,
) -> Dict[str, Any]:
    matched_tables = context.get("matched_tables", [])
    authoritative_tables = []
    for item in matched_tables:
        indexes = item.get("index_definitions") or []
        authoritative_tables.append(
            {
                "table_name": item.get("table_name"),
                "table_rows_exact": item.get("table_rows"),
                "index_count": len(indexes),
                "has_indexes": bool(indexes),
                "ddl_available": bool((item.get("ddl") or "").strip()),
            }
        )

    metadata_summary = build_metadata_summary(context)
    return {
        "workflow_input_mode": workflow_input_mode,
        "workflow_input_length": len(sql_text),
        "compaction_level": compaction_level,
        "matched_tables_count": metadata_summary["matched_tables_count"],
        "tables_with_ddl_count": metadata_summary["tables_with_ddl_count"],
        "tables_with_indexes_count": metadata_summary["tables_with_indexes_count"],
        "authoritative_tables": authoritative_tables,
    }


def _normalize_report_text_for_checks(text: str) -> str:
    normalized = text or ""
    normalized = normalized.replace("`", "")
    normalized = re.sub(r"\s+", "", normalized)
    return normalized.lower()


def build_consistency_flags(
    *,
    context: Dict[str, Any],
    parsed_result: Dict[str, Any],
) -> Dict[str, bool]:
    report_content = _normalize_report_text_for_checks(parsed_result.get("report_content") or "")
    matched_tables = context.get("matched_tables", [])

    has_positive_rows = any((item.get("table_rows") or 0) > 0 for item in matched_tables)
    has_indexes = any(bool(item.get("index_definitions")) for item in matched_tables)
    has_ddl = any(bool((item.get("ddl") or "").strip()) for item in matched_tables)

    row_zero_patterns = (
        "table_rows为0",
        "表行数为0",
        "数据量为0",
        "当前表数据量为0",
    )
    missing_index_patterns = (
        "索引信息在提供的ddl中为空",
        "主键及索引信息在提供的ddl中为空",
        "ddl中为空",
        "索引为空",
        "无索引",
        "无法确认是否有索引",
        "无法确认是否为主键或拥有索引",
    )
    missing_metadata_patterns = (
        "table_metadata为空",
        "未提供ddl",
        "未命中ddl",
        "ddl为空",
        "未提供表结构",
    )
    unknown_patterns = (
        "无法确认",
        "未知",
    )

    return {
        "report_mentions_zero_rows_despite_positive_rows": has_positive_rows
        and any(pattern in report_content for pattern in row_zero_patterns),
        "report_mentions_missing_indexes_despite_indexes_present": has_indexes
        and any(pattern in report_content for pattern in missing_index_patterns),
        "report_claims_metadata_missing_but_input_had_metadata": (has_indexes or has_ddl)
        and any(pattern in report_content for pattern in missing_metadata_patterns),
        "report_used_unknown_when_authoritative_value_present": (has_positive_rows or has_indexes or has_ddl)
        and any(pattern in report_content for pattern in unknown_patterns),
    }


def get_primary_db_type(request: List[SQLAnalysisItem], context: Dict[str, Any]) -> str:
    if request:
        return settings.normalize_db_type(request[0].db_type)
    db_targets = context.get("db_targets", [])
    if db_targets:
        return settings.normalize_db_type(db_targets[0].get("db_type"))
    return "mysql"


def build_remote_result_payload(
    request: List[SQLAnalysisItem],
    context: Dict[str, Any],
    parsed_result: Dict[str, Any],
    input_diagnostics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    consistency_flags = build_consistency_flags(context=context, parsed_result=parsed_result)
    summary = parsed_result["summary"]
    if any(consistency_flags.values()):
        summary = f"{summary}（检测到远端报告与本地权威元数据不一致，请结合元数据摘要复核）"
    return {
        "provider": REMOTE_WORKFLOW_RESULT_PROVIDER,
        "db_type": get_primary_db_type(request, context),
        "report_url": parsed_result["report_url"],
        "risk_level": parsed_result["risk_level"],
        "summary": summary,
        "report_content": parsed_result.get("report_content"),
        "messages": list(parsed_result.get("messages") or []),
        "metadata_summary": build_metadata_summary(context),
        "input_diagnostics": input_diagnostics or {},
        "consistency_flags": consistency_flags,
    }


class ReportProvider(Protocol):
    async def submit_analysis(
        self,
        request: List[SQLAnalysisItem],
        context: Dict[str, Any],
        data_source: Optional[DataSource],
        db: Session,
    ) -> SQLAnalysisItemResponse:
        ...

    async def check_health(self) -> tuple[bool, str]:
        ...


class RemoteWorkflowReportProvider:
    PDF_LINK_RETRY_ATTEMPTS = 3
    PDF_LINK_RETRY_DELAY_SECONDS = 5

    def __init__(self, *, file_input_mode: bool = False) -> None:
        self.base_url = settings.get_report_base_url()
        self.timeout = settings.report_api_timeout
        self.workflow_id = settings.workflow_id
        self.file_input_mode = file_input_mode

    async def submit_analysis(
        self,
        request: List[SQLAnalysisItem],
        context: Dict[str, Any],
        data_source: Optional[DataSource],
        db: Session,
    ) -> SQLAnalysisItemResponse:
        task_id = str(uuid.uuid4())
        sql_text, input_diagnostics = _build_workflow_document_bundle(request, context)
        sql_lines = [item.sql for item in request]

        AnalysisTaskService.create(
            db=db,
            data=AnalysisTaskCreate(
                task_id=task_id,
                status="pending",
                report_url=None,
                sql_text=json.dumps(sql_lines, ensure_ascii=False),  # 存储原始SQL数组
                analysis_context_json=json.dumps(context, ensure_ascii=False),
                error_message=None,
                risk_level=calculate_risk_level(sql_lines),
                data_source_id=data_source.id if data_source else None,
                data_source_name=data_source.name if data_source else None,
                target_db_type=(data_source.db_type if data_source else get_primary_db_type(request, context)),
                target_host=(data_source.host if data_source else (request[0].db_ip if request else None)),
                target_port=(data_source.port if data_source else (request[0].db_port if request else None)),
                target_db_name=(data_source.db_name if data_source else (request[0].dbname if request else None)),
            ),
        )

        logger.info("Composed workflow input text (task=%s):\n%s", task_id, sql_text)

        try:
            first_resp = await self.invoke_workflow(workflow_id=self.workflow_id, stream=False)
            workflow_input = self._extract_input_event(
                first_resp,
                sql_text=sql_text,
            )
        except Exception as exc:
            AnalysisTaskService.update_status(
                db=db,
                task_id=task_id,
                data=AnalysisTaskUpdate(
                    status="failed",
                    report_url=None,
                    error_message=str(exc),
                ),
            )
            raise RuntimeError(f"提交远程分析任务失败: {exc}") from exc

        self._schedule_remote_followup(
            task_id=task_id,
            request=request,
            context=context,
            input_diagnostics=input_diagnostics,
            input_payload=workflow_input["input_payload"],
            session_id=workflow_input["session_id"],
            message_id=workflow_input["message_id"],
        )

        AnalysisTaskService.update_status(
            db=db,
            task_id=task_id,
            data=AnalysisTaskUpdate(
                status="pending",
                remote_session_id=workflow_input["session_id"],
                remote_message_id=workflow_input["message_id"],
            ),
        )

        return SQLAnalysisItemResponse(
            task_id=task_id,
            status="pending",
            message="任务已成功提交，稍后可查询结果",
        )

    def _build_workflow_node_input(self, sql_text: str) -> Dict[str, Any]:
        if self.file_input_mode:
            raise RuntimeError("文件工作流不应调用 sql_text 节点输入构造")
        return {"sql_text": sql_text}

    @staticmethod
    def _build_file_input_candidates(document_text: str, *, field_key: str) -> List[Dict[str, Any]]:
        file_object = {
            "file_name": "slow-sql-input.md",
            "file_type": "text/markdown",
            "file_content": document_text,
        }
        return [
            {field_key: file_object},
            {
                field_key: {
                    **file_object,
                    "name": "slow-sql-input.md",
                    "content": document_text,
                }
            },
            {
                field_key: {
                    "file_path": "slow-sql-input.md",
                    "file_type": "file",
                    "image_file": "",
                    "file_content": document_text,
                }
            },
            {
                field_key: "slow-sql-input.md",
                "file_content": document_text,
            },
        ]

    def _resolve_input_field(self, input_event: Dict[str, Any]) -> Dict[str, str]:
        input_schema = input_event.get("input_schema") or {}
        values = input_schema.get("value") if isinstance(input_schema, dict) else None
        if isinstance(values, list):
            normalized_values = [item for item in values if isinstance(item, dict) and item.get("key")]
            text_field = next(
                (
                    item
                    for item in normalized_values
                    if str(item.get("key")).strip() == "sql_text"
                    or str(item.get("type", "")).strip().lower() in {"text", "textarea", "input"}
                ),
                None,
            )
            if text_field:
                return {
                    "mode": "text",
                    "field_key": str(text_field.get("key")).strip(),
                }

            file_field = next(
                (
                    item
                    for item in normalized_values
                    if str(item.get("type", "")).strip().lower() == "file"
                ),
                None,
            )
            if file_field:
                return {
                    "mode": "file",
                    "field_key": str(file_field.get("key")).strip(),
                }

        return {
            "mode": "file" if self.file_input_mode or input_event.get("input_type") == "file" else "text",
            "field_key": "file" if self.file_input_mode or input_event.get("input_type") == "file" else "sql_text",
        }

    def _extract_input_event(
        self,
        first_resp: Dict[str, Any],
        sql_text: str,
    ) -> Dict[str, Any]:
        data = first_resp.get("data", {}) if isinstance(first_resp, dict) else {}
        events = data.get("events", []) if isinstance(data, dict) else []
        session_id: Optional[str] = data.get("session_id") if isinstance(data, dict) else None
        input_event = next((e for e in events if isinstance(e, dict) and e.get("event") == "input"), None)
        if not input_event:
            raise RuntimeError("工作流未返回 input 事件，提交失败")

        node_id = input_event.get("node_id")
        message_id = input_event.get("message_id")
        if not node_id:
            raise RuntimeError("工作流 input 事件缺少 node_id")

        input_field = self._resolve_input_field(input_event)
        logger.info(
            "Workflow input resolved: node_id=%s field=%s mode=%s session_id=%s message_id=%s",
            node_id,
            input_field["field_key"],
            input_field["mode"],
            session_id,
            message_id,
        )

        if input_field["mode"] == "file":
            candidate_payloads = [
                {node_id: candidate}
                for candidate in self._build_file_input_candidates(
                    sql_text,
                    field_key=input_field["field_key"],
                )
            ]
        else:
            candidate_payloads = [
                {node_id: {input_field["field_key"]: sql_text}}
            ]

        return {
            "session_id": session_id,
            "message_id": message_id,
            "input_payload": candidate_payloads,
        }

    def _schedule_remote_followup(
        self,
        task_id: str,
        request: List[SQLAnalysisItem],
        context: Dict[str, Any],
        input_diagnostics: Dict[str, Any],
        input_payload: List[Dict[str, Any]],
        session_id: Optional[str],
        message_id: Optional[str],
    ) -> None:
        asyncio.create_task(
            self._follow_until_close(
                task_id=task_id,
                request=request,
                context=context,
                input_diagnostics=input_diagnostics,
                input_payload=input_payload,
                session_id=session_id,
                message_id=message_id,
            )
        )

    @staticmethod
    def _extract_string_values(value: Any) -> List[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, dict):
            results: List[str] = []
            for nested in value.values():
                results.extend(RemoteWorkflowReportProvider._extract_string_values(nested))
            return results
        if isinstance(value, list):
            results: List[str] = []
            for nested in value:
                results.extend(RemoteWorkflowReportProvider._extract_string_values(nested))
            return results
        return []

    @staticmethod
    def _normalize_report_markdown(text: str) -> str:
        normalized = text.strip()
        normalized = re.sub(
            r"#\s*慢\s*SQL\s*\n+\s*分析报告",
            "# 慢 SQL 分析报告",
            normalized,
            flags=re.IGNORECASE,
        )
        normalized = re.sub(
            r"\n{0,2}(?:慢\s*SQL\s*分析报告)?下载链接[:：]?\s*\n?https?://[^\s]+(?:\.pdf)?\s*$",
            "",
            normalized,
            flags=re.IGNORECASE,
        )
        normalized = re.sub(r"\n{0,2}https?://[^\s]+\.pdf\s*$", "", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"(?<!\n)(#{2,4}\s)", r"\n\n\1", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()

    @staticmethod
    def _is_report_noise_fragment(text: str) -> bool:
        candidate = text.strip()
        if not candidate:
            return True
        if re.fullmatch(r"https?://[^\s]+(?:\.pdf)?", candidate, flags=re.IGNORECASE):
            return True
        if re.search(r"(?:慢\s*SQL\s*分析报告)?下载链接[:：]?", candidate, flags=re.IGNORECASE):
            return True
        return False

    @staticmethod
    def _extract_report_content_from_fragments(fragments: List[str]) -> str:
        if not fragments:
            return ""

        marker_patterns = [
            re.compile(r"#\s*慢\s*SQL\s*分析报告", re.IGNORECASE),
            re.compile(r"##\s*一、分析概述", re.IGNORECASE),
            re.compile(r"##\s*二、整体风险评估等级", re.IGNORECASE),
            re.compile(r"##\s*三、分析结果详情", re.IGNORECASE),
            re.compile(r"##\s*四、共性问题和优化建议", re.IGNORECASE),
        ]

        filtered_fragments = [
            fragment
            for fragment in fragments
            if not RemoteWorkflowReportProvider._is_report_noise_fragment(fragment)
        ]
        if not filtered_fragments:
            return ""

        variants = [
            "\n".join(filtered_fragments),
            "".join(filtered_fragments),
        ]

        for variant in variants:
            candidate = variant.strip()
            if not candidate:
                continue
            matches = [
                match.start()
                for pattern in marker_patterns
                for match in [pattern.search(candidate)]
                if match
            ]
            if not matches:
                continue
            report = candidate[min(matches):]
            normalized = RemoteWorkflowReportProvider._normalize_report_markdown(report)
            if normalized:
                return normalized

        return ""

    def _parse_workflow_result(
        self,
        resp: Dict[str, Any],
        *,
        require_report_url: bool = True,
    ) -> Dict[str, Any]:
        events = resp.get("data", {}).get("events", []) if isinstance(resp, dict) else []
        link = None
        report_content = ""
        messages: List[str] = []
        text_fragments: List[str] = []
        url_pattern = re.compile(r"(https?://[^\s]+\.pdf)", re.IGNORECASE)

        for ev in events:
            if not isinstance(ev, dict):
                continue
            if ev.get("event") not in ["output_msg", "stream_msg"]:
                continue
            output_schema = ev.get("output_schema", {})
            string_values = self._extract_string_values(output_schema)
            for raw_text in string_values:
                msg = raw_text.strip()
                if not msg:
                    continue
                messages.append(msg)
                match = url_pattern.search(msg)
                if match:
                    link = match.group(1)
                text_fragments.append(raw_text)

        report_content = self._extract_report_content_from_fragments(text_fragments)

        risk_level = 3
        if report_content:
            risk_section = re.search(r"## 二、整体风险评估等级(.*?)## 三、分析结果详情", report_content, re.DOTALL)
            if risk_section:
                if "高风险 ■" in risk_section.group(1):
                    risk_level = 3
                elif "中风险 ■" in risk_section.group(1):
                    risk_level = 2
                elif "低风险 ■" in risk_section.group(1):
                    risk_level = 1

        if require_report_url and not link:
            if report_content:
                raise RuntimeError("工作流返回了分析正文，但未返回 PDF 报告链接")
            raise RuntimeError("工作流未返回 PDF 报告链接")

        summary = next(
            (
                line.strip()
                for msg in messages
                for line in msg.splitlines()
                if line.strip() and not line.strip().startswith("#")
            ),
            "远程工作流已生成分析结果",
        )

        return {
            "report_url": link,
            "risk_level": risk_level,
            "summary": summary,
            "report_content": report_content,
            "messages": messages,
        }

    async def _follow_until_close(
        self,
        task_id: str,
        request: List[SQLAnalysisItem],
        context: Dict[str, Any],
        input_diagnostics: Dict[str, Any],
        input_payload: List[Dict[str, Any]],
        session_id: Optional[str],
        message_id: Optional[str],
    ) -> None:
        db_bg: Session = SessionLocal()
        try:
            logger.info(
                "Workflow follow-up started: task=%s session_id=%s message_id=%s candidates=%s",
                task_id,
                session_id,
                message_id,
                len(input_payload),
            )
            parsed: Optional[Dict[str, Any]] = None
            for attempt in range(1, self.PDF_LINK_RETRY_ATTEMPTS + 1):
                resp = await self._invoke_followup_with_candidates(
                    input_candidates=input_payload,
                    session_id=session_id,
                    message_id=message_id,
                )
                parsed = self._parse_workflow_result(resp, require_report_url=False)
                if parsed.get("report_url"):
                    break
                if attempt < self.PDF_LINK_RETRY_ATTEMPTS:
                    logger.warning(
                        "Workflow follow-up missing PDF link: task=%s attempt=%s/%s, retrying in %ss",
                        task_id,
                        attempt,
                        self.PDF_LINK_RETRY_ATTEMPTS,
                        self.PDF_LINK_RETRY_DELAY_SECONDS,
                    )
                    await asyncio.sleep(self.PDF_LINK_RETRY_DELAY_SECONDS)

            if not parsed:
                raise RuntimeError("工作流在重试后仍未返回 PDF 报告链接")
            if not parsed.get("report_url") and not parsed.get("report_content"):
                raise RuntimeError("工作流在重试后仍未返回 PDF 报告链接")
            logger.info(
                "Workflow follow-up completed: task=%s report_url=%s",
                task_id,
                parsed["report_url"],
            )
            AnalysisTaskService.update_status(
                db=db_bg,
                task_id=task_id,
                data=AnalysisTaskUpdate(
                    status="completed",
                    report_url=parsed["report_url"],
                    analysis_result_json=json.dumps(
                        build_remote_result_payload(
                            request=request,
                            context=context,
                            parsed_result=parsed,
                            input_diagnostics=input_diagnostics,
                        ),
                        ensure_ascii=False,
                    ),
                    error_message=None,
                    risk_level=parsed["risk_level"],
                ),
            )
        except Exception as exc:  # pragma: no cover - 后台任务容错
            logger.exception("Workflow async follow failed: task=%s, err=%s", task_id, exc)
            AnalysisTaskService.update_status(
                db=db_bg,
                task_id=task_id,
                data=AnalysisTaskUpdate(
                    status="failed",
                    report_url=None,
                    error_message=str(exc),
                ),
            )
        finally:
            db_bg.close()

    async def _invoke_followup_with_candidates(
        self,
        *,
        input_candidates: List[Dict[str, Any]],
        session_id: Optional[str],
        message_id: Optional[str],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        for input_payload in input_candidates:
            try:
                logger.info("Submitting workflow input candidate: keys=%s", list(input_payload.keys()))
                return await self.invoke_workflow(
                    workflow_id=self.workflow_id,
                    stream=False,
                    input_payload=input_payload,
                    session_id=session_id,
                    message_id=message_id,
                )
            except Exception as exc:
                errors.append(str(exc))
        raise RuntimeError("工作流输入提交失败: " + " | ".join(errors))

    async def invoke_workflow(
        self,
        workflow_id: Optional[str],
        stream: bool = False,
        input_payload: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not workflow_id:
            raise RuntimeError("未配置 WORKFLOW_ID，无法调用远程工作流")

        payload: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "stream": stream,
        }
        if input_payload:
            payload["input"] = input_payload
        if session_id:
            payload["session_id"] = session_id
        if message_id:
            payload["message_id"] = message_id

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.base_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    async def check_health(self) -> tuple[bool, str]:
        if not self.workflow_id:
            return False, "missing workflow_id"

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(self.base_url)
                if response.status_code >= 500:
                    response.raise_for_status()
            return True, "ok"
        except Exception as exc:  # pragma: no cover - 运行时诊断逻辑
            return False, str(exc)


def get_report_provider() -> ReportProvider:
    provider = settings.report_provider.lower()
    if provider == "api1_file_workflow":
        return RemoteWorkflowReportProvider(file_input_mode=True)
    if provider in {"remote_workflow", "api1_workflow"}:
        return RemoteWorkflowReportProvider(file_input_mode=False)
    if provider not in {"remote_workflow", "api1_workflow", "api1_file_workflow"}:
        raise RuntimeError(f"不支持的 REPORT_PROVIDER: {settings.report_provider}")
    return RemoteWorkflowReportProvider(file_input_mode=False)
