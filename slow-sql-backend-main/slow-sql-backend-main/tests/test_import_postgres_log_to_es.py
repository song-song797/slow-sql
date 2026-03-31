import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent


MODULE_NAME = "import_postgres_log_to_es_test_module"
SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "import_postgres_log_to_es.py"


def load_module():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def make_event(module, message: str, pid: str = "1001"):
    return module.Event(
        timestamp=datetime(2026, 3, 12, 12, 0, 0, tzinfo=timezone.utc),
        pid=pid,
        user="postgres",
        client_host="127.0.0.1",
        client_port="5432",
        database="demo",
        level="LOG",
        message=message,
    )


def test_extract_sql_and_query_time_parses_real_duration_from_statement() -> None:
    module = load_module()

    sql, query_time = module.extract_sql_and_query_time(
        "duration: 12.345 ms  statement: SELECT *\nFROM audit_log\nWHERE user_id = 1;",
        "0.10",
    )

    assert sql == "SELECT * FROM audit_log WHERE user_id = 1"
    assert query_time == "0.012345"


def test_extract_sql_and_query_time_parses_real_duration_from_execute() -> None:
    module = load_module()

    sql, query_time = module.extract_sql_and_query_time(
        "duration: 100.000 ms  execute <unnamed>: UPDATE xxl_job_log_report SET running_count = 1",
        "0.10",
    )

    assert sql == "UPDATE xxl_job_log_report SET running_count = 1"
    assert query_time == "0.1"


def test_extract_sql_and_query_time_parses_localized_duration_and_statement() -> None:
    module = load_module()

    sql, query_time = module.extract_sql_and_query_time(
        "执行时间: 231.456 ms 语句: SELECT * FROM users ORDER BY id LIMIT 3",
        "0.10",
    )

    assert sql == "SELECT * FROM users ORDER BY id LIMIT 3"
    assert query_time == "0.231456"


def test_extract_sql_and_query_time_falls_back_when_duration_missing() -> None:
    module = load_module()

    sql, query_time = module.extract_sql_and_query_time("statement: SELECT 1", "0.10")

    assert sql == "SELECT 1"
    assert query_time == "0.10"


def test_iter_docs_from_events_pairs_statement_with_following_duration() -> None:
    module = load_module()

    docs = list(
        module.iter_docs_from_events(
            [
                make_event(module, "statement: SELECT * FROM audit_log WHERE user_id = 1"),
                make_event(module, "duration: 250.500 ms"),
            ],
            default_db_host="127.0.0.1",
            default_query_time="0.10",
        )
    )

    assert len(docs) == 1
    assert docs[0]["_source"]["query"] == "SELECT * FROM audit_log WHERE user_id = 1"
    assert docs[0]["_source"]["query_time"] == "0.2505"


def test_iter_docs_from_events_skips_error_level_sql_lines() -> None:
    module = load_module()

    docs = list(
        module.iter_docs_from_events(
            [
                make_event(module, "SELECT * FROM missing_table", pid="2001"),
                module.Event(
                    timestamp=datetime(2026, 3, 12, 12, 0, 0, tzinfo=timezone.utc),
                    pid="2001",
                    user="postgres",
                    client_host="127.0.0.1",
                    client_port="5432",
                    database="demo",
                    level="错误",
                    message='字段 "opened_at" 不存在',
                ),
            ],
            default_db_host="127.0.0.1",
            default_query_time="0.10",
        )
    )

    assert docs == []


def test_iter_events_supports_localized_chinese_log_levels(tmp_path: Path) -> None:
    module = load_module()
    log_path = tmp_path / "postgresql-chinese.log"
    log_path.write_text(
        dedent(
            """
            2026-03-12 19:30:01.123 CST [2048] user:postgres, client:127.0.0.1(5432), database:demo 日志: duration: 15.5 ms  statement: SELECT 1
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    events = list(module.iter_events(log_path, "Asia/Shanghai"))

    assert len(events) == 1
    assert events[0].level == "日志"
    assert events[0].message == "duration: 15.5 ms  statement: SELECT 1"
