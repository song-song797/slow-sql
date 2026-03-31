import app.models  # noqa: F401
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.schemas.database_info import DatabaseInfoCreate
from app.config import settings
from app.database import Base
from app.models.data_source import DataSource
from app.services.analysis_context_service import AnalysisContextService
from app.services.database_service import DatabaseService
from app.services.data_source_crypto import DataSourceCryptoService
from app.services.es_service import ESService
from app.services.remote_db_service import RemoteDatabaseService
from app.schemas.sql_analysis import SQLAnalysisItem


def test_auto_fetch_uses_db_name_override_and_persists_under_original_target(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = testing_session_local()

    calls: list[dict] = []
    persisted: list[DatabaseInfoCreate] = []

    def fake_fetch_table_info(
        db_type: str,
        host: str,
        port: int,
        db_name: str,
        username: str,
        password: str,
        table_name: str,
    ) -> dict:
        calls.append(
            {
                "db_type": db_type,
                "host": host,
                "port": port,
                "db_name": db_name,
                "username": username,
                "password": password,
                "table_name": table_name,
            }
        )
        return {
            "db_type": db_type,
            "db_name": db_name,
            "db_ip": host,
            "db_port": port,
            "db_version": "8.0.34",
            "table_name": table_name,
            "table_rows": 180000,
            "ddl": (
                "CREATE TABLE party_cert ("
                "party_cert_id bigint,"
                "cert_num varchar(255),"
                "cert_type varchar(32),"
                "PRIMARY KEY (party_cert_id),"
                "KEY idx_party_cert_num (cert_num)"
                ")"
            ),
        }

    monkeypatch.setattr(
        RemoteDatabaseService,
        "fetch_table_info",
        staticmethod(fake_fetch_table_info),
    )
    monkeypatch.setattr(
        DatabaseService,
        "upsert_table_info",
        staticmethod(lambda db_session, data: persisted.append(data)),
    )
    monkeypatch.setattr(
        settings,
        "metadata_db_overrides",
        (
            '{"mysql:CUSDBX": {'
            '"host": "127.0.0.1", '
            '"port": 3307, '
            '"fetch_db_name": "CUSDBX", '
            '"username": "slow_sql", '
            '"password": "slow_sql"'
            "}}"
        ),
    )

    try:
        auto_fetched_tables, fetch_errors = AnalysisContextService._auto_fetch_missing_tables(
            db=db,
            missing_tables=[
                {
                    "db_type": "mysql",
                    "db_name": "CUSDBX",
                    "db_ip": "127.0.0.1",
                    "db_port": 3306,
                    "table_name": "party_cert",
                }
            ],
        )

        assert not fetch_errors
        assert calls == [
            {
                "db_type": "mysql",
                "host": "127.0.0.1",
                "port": 3307,
                "db_name": "CUSDBX",
                "username": "slow_sql",
                "password": "slow_sql",
                "table_name": "party_cert",
            }
        ]

        assert auto_fetched_tables[0]["db_name"] == "CUSDBX"
        assert auto_fetched_tables[0]["db_ip"] == "127.0.0.1"
        assert auto_fetched_tables[0]["db_port"] == 3306
        assert len(persisted) == 1
        assert persisted[0].db_name == "CUSDBX"
        assert persisted[0].db_ip == "127.0.0.1"
        assert persisted[0].db_port == 3306
        assert persisted[0].table_rows == 180000
    finally:
        monkeypatch.setattr(settings, "metadata_db_overrides", None)
        db.close()


def test_build_context_uses_observation_override_without_exact_lookup(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = testing_session_local()

    monkeypatch.setattr(
        DatabaseService,
        "find_tables",
        staticmethod(lambda **kwargs: []),
    )
    monkeypatch.setattr(
        ESService,
        "get_sql_observability",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not query exact SQL observability")),
    )

    request = [
        SQLAnalysisItem(
            sql="select * from audit_log where user_id = 42 order by created_at desc",
            db_type="mysql",
            dbname="demo",
            db_ip="127.0.0.1",
            db_port=3306,
            template_sql="SELECT * FROM AUDIT_LOG WHERE USER_ID = ? ORDER BY CREATED_AT DESC",
            observation_override={
                "cluster_count": 12,
                "min_query_time_ms": 120.0,
                "avg_query_time_ms": 456.7,
                "max_query_time_ms": 980.0,
                "latest_timestamp": 1741852800000,
            },
        )
    ]

    try:
        context = AnalysisContextService.build_context(request=request, db=db)
    finally:
        db.close()

    assert context["sql_observations"] == [
        {
            "cluster_count": 12,
            "exact_match_count": 12,
            "min_query_time_ms": 120.0,
            "avg_query_time_ms": 456.7,
            "max_query_time_ms": 980.0,
            "latest_timestamp": 1741852800000,
            "sql": "select * from audit_log where user_id = 42 order by created_at desc",
            "template_sql": "SELECT * FROM AUDIT_LOG WHERE USER_ID = ? ORDER BY CREATED_AT DESC",
            "db_name": "demo",
            "db_type": "mysql",
            "db_ip": "127.0.0.1",
        }
    ]


def test_auto_fetch_with_data_source_still_honors_metadata_override(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = testing_session_local()

    calls: list[dict] = []
    persisted: list[DatabaseInfoCreate] = []

    def fake_fetch_table_info(
        db_type: str,
        host: str,
        port: int,
        db_name: str,
        username: str,
        password: str,
        table_name: str,
    ) -> dict:
        calls.append(
            {
                "db_type": db_type,
                "host": host,
                "port": port,
                "db_name": db_name,
                "username": username,
                "password": password,
                "table_name": table_name,
            }
        )
        return {
            "db_type": db_type,
            "db_name": db_name,
            "db_ip": host,
            "db_port": port,
            "db_version": "8.0.34",
            "table_name": table_name,
            "table_rows": 32000,
            "ddl": "CREATE TABLE audit_log(id bigint primary key)",
        }

    monkeypatch.setattr(
        RemoteDatabaseService,
        "fetch_table_info",
        staticmethod(fake_fetch_table_info),
    )
    monkeypatch.setattr(
        DatabaseService,
        "upsert_table_info",
        staticmethod(lambda db_session, data: persisted.append(data)),
    )
    monkeypatch.setattr(
        settings,
        "metadata_db_overrides",
        (
            '{"mysql:CUSDBX": {'
            '"host": "127.0.0.1", '
            '"port": 3307, '
            '"fetch_db_name": "slow_sql_db", '
            '"allow_db_name_override": true'
            "}}"
        ),
    )

    data_source = DataSource(
        name="cusdbx-reader",
        db_type="mysql",
        host="127.0.0.1",
        port=3307,
        db_name="CUSDBX",
        username="reader",
        encrypted_password=DataSourceCryptoService.encrypt("reader-secret"),
        enabled=True,
    )

    try:
        auto_fetched_tables, fetch_errors = AnalysisContextService._auto_fetch_missing_tables(
            db=db,
            missing_tables=[
                {
                    "db_type": "mysql",
                    "db_name": "CUSDBX",
                    "db_ip": "127.0.0.1",
                    "db_port": 3307,
                    "table_name": "audit_log",
                }
            ],
            data_source=data_source,
        )

        assert not fetch_errors
        assert calls == [
            {
                "db_type": "mysql",
                "host": "127.0.0.1",
                "port": 3307,
                "db_name": "slow_sql_db",
                "username": "reader",
                "password": "reader-secret",
                "table_name": "audit_log",
            }
        ]
        assert auto_fetched_tables[0]["db_name"] == "CUSDBX"
        assert auto_fetched_tables[0]["db_port"] == 3307
        assert len(persisted) == 1
        assert persisted[0].db_name == "CUSDBX"
        assert persisted[0].db_port == 3307
    finally:
        monkeypatch.setattr(settings, "metadata_db_overrides", None)
        db.close()


def test_db_name_override_requires_explicit_opt_in(monkeypatch) -> None:
    monkeypatch.setattr(
        settings,
        "metadata_db_overrides",
        (
            '{"mysql:CUSDBX": {'
            '"host": "127.0.0.1", '
            '"port": 3307, '
            '"fetch_db_name": "slow_sql_db", '
            '"username": "slow_sql", '
            '"password": "slow_sql"'
            "}}"
        ),
    )

    try:
        target = settings.resolve_metadata_fetch_target(
            db_type="mysql",
            db_ip="127.0.0.1",
            db_port=3306,
            db_name="CUSDBX",
        )
    finally:
        monkeypatch.setattr(settings, "metadata_db_overrides", None)

    assert target["host"] == "127.0.0.1"
    assert target["port"] == 3306
    assert target["db_name"] == "CUSDBX"


def test_db_name_override_can_remap_when_explicitly_enabled(monkeypatch) -> None:
    monkeypatch.setattr(
        settings,
        "metadata_db_overrides",
        (
            '{"mysql:CUSDBX": {'
            '"host": "127.0.0.1", '
            '"port": 3307, '
            '"fetch_db_name": "slow_sql_db", '
            '"username": "slow_sql", '
            '"password": "slow_sql", '
            '"allow_db_name_override": true'
            "}}"
        ),
    )

    try:
        target = settings.resolve_metadata_fetch_target(
            db_type="mysql",
            db_ip="127.0.0.1",
            db_port=3306,
            db_name="CUSDBX",
        )
    finally:
        monkeypatch.setattr(settings, "metadata_db_overrides", None)

    assert target["host"] == "127.0.0.1"
    assert target["port"] == 3307
    assert target["db_name"] == "slow_sql_db"
