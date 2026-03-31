import app.main as main_module
from fastapi.testclient import TestClient


def test_ready_returns_degraded_when_dependency_check_times_out(monkeypatch) -> None:
    app = main_module.app

    async def fake_report_health():
        raise TimeoutError("simulated timeout")

    monkeypatch.setattr(main_module, "check_database_connection", lambda: (True, "ok"))
    monkeypatch.setattr(main_module.ESService, "check_connection", staticmethod(lambda: (True, "ok")))
    monkeypatch.setattr(main_module.ReportService, "check_provider_health", fake_report_health)

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["dependencies"]["database"]["ok"] is True
    assert payload["dependencies"]["elasticsearch"]["ok"] is True
    assert payload["dependencies"]["report_provider"]["ok"] is False


def test_startup_schedules_database_init_without_blocking(monkeypatch) -> None:
    app = main_module.app
    scheduled = {}

    def fake_create_task(coro):
        scheduled["created"] = True
        scheduled["coroutine_name"] = coro.cr_code.co_name
        coro.close()
        return object()

    monkeypatch.setattr(main_module.asyncio, "create_task", fake_create_task)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert scheduled["created"] is True
    assert scheduled["coroutine_name"] == "_initialize_database_in_background"
