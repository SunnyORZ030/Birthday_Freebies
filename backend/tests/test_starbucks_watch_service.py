from datetime import datetime, timezone

import pytest

from app.services.starbucks_watch_service import run_starbucks_watch_once


class _FakeResponse:
    def __init__(self, status_code: int, text: str = "", headers: dict[str, str] | None = None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_watch_not_modified_updates_success_state(monkeypatch) -> None:
    captured_state: dict[str, object] = {}

    monkeypatch.setattr("app.services.starbucks_watch_service.ensure_ingestion_tables", lambda _url: None)
    monkeypatch.setattr(
        "app.services.starbucks_watch_service.fetch_source_state",
        lambda _url, source_system, source_key: {
            "etag": '"abc"',
            "last_modified": "Tue, 01 Apr 2026 00:00:00 GMT",
            "last_changed_at": datetime(2026, 4, 1, tzinfo=timezone.utc),
            "last_content_hash": "hash-1",
            "consecutive_failures": 1,
        },
    )

    def fake_upsert(_url: str, **kwargs) -> None:
        captured_state.update(kwargs)

    monkeypatch.setattr("app.services.starbucks_watch_service.upsert_source_state", fake_upsert)

    def fake_get(_url: str, headers: dict[str, str], timeout: float):
        assert headers["If-None-Match"] == '"abc"'
        return _FakeResponse(304, headers={"ETag": '"abc"'})

    result = run_starbucks_watch_once(
        "postgresql://placeholder",
        region_code="bay_area",
        max_retries=1,
        http_get=fake_get,
    )

    assert result["status"] == "not_modified"
    assert captured_state["consecutive_failures"] == 0
    assert captured_state["last_error"] is None


def test_watch_changed_runs_ingestion(monkeypatch) -> None:
    monkeypatch.setattr("app.services.starbucks_watch_service.ensure_ingestion_tables", lambda _url: None)
    monkeypatch.setattr(
        "app.services.starbucks_watch_service.fetch_source_state",
        lambda _url, source_system, source_key: {
            "etag": None,
            "last_modified": None,
            "last_changed_at": None,
            "last_content_hash": "old-hash",
            "consecutive_failures": 0,
        },
    )
    monkeypatch.setattr("app.services.starbucks_watch_service.upsert_source_state", lambda _url, **kwargs: None)

    captured: dict[str, object] = {}

    def fake_run_ingestion(_url: str, *, region_code: str, fetch_html):
        captured["region_code"] = region_code
        captured["html"] = fetch_html()
        return {
            "discovered": 1,
            "staged": 1,
            "promoted": 1,
            "skipped_unchanged": 0,
        }

    monkeypatch.setattr("app.services.starbucks_watch_service.run_starbucks_ingestion", fake_run_ingestion)

    result = run_starbucks_watch_once(
        "postgresql://placeholder",
        region_code="bay_area",
        max_retries=1,
        http_get=lambda _url, headers, timeout: _FakeResponse(200, text="<html>new body</html>"),
    )

    assert result["status"] == "changed"
    assert captured["region_code"] == "bay_area"
    assert "new body" in str(captured["html"])


def test_watch_retries_then_alerts(monkeypatch) -> None:
    monkeypatch.setattr("app.services.starbucks_watch_service.ensure_ingestion_tables", lambda _url: None)
    monkeypatch.setattr(
        "app.services.starbucks_watch_service.fetch_source_state",
        lambda _url, source_system, source_key: {
            "etag": None,
            "last_modified": None,
            "last_success_at": datetime(2026, 4, 1, tzinfo=timezone.utc),
            "last_changed_at": None,
            "last_content_hash": None,
            "consecutive_failures": 1,
        },
    )

    captured: dict[str, object] = {"upsert_calls": 0, "sleep_calls": 0, "alerts": 0}

    def fake_upsert(_url: str, **kwargs) -> None:
        captured["upsert_calls"] = int(captured["upsert_calls"]) + 1
        captured["last_failures"] = kwargs["consecutive_failures"]

    monkeypatch.setattr("app.services.starbucks_watch_service.upsert_source_state", fake_upsert)
    monkeypatch.setattr(
        "app.services.starbucks_watch_service._send_webhook_alert",
        lambda webhook_url, message: captured.__setitem__("alerts", int(captured["alerts"]) + 1),
    )

    def fake_sleep(_seconds: float) -> None:
        captured["sleep_calls"] = int(captured["sleep_calls"]) + 1

    def always_fail(_url: str, headers: dict[str, str], timeout: float):
        raise RuntimeError("network down")

    with pytest.raises(RuntimeError):
        run_starbucks_watch_once(
            "postgresql://placeholder",
            region_code="bay_area",
            max_retries=2,
            retry_backoff_seconds=[0],
            alert_failure_threshold=2,
            webhook_url="https://example.com/webhook",
            http_get=always_fail,
            sleep_fn=fake_sleep,
        )

    assert captured["sleep_calls"] == 1
    assert captured["upsert_calls"] == 1
    assert captured["last_failures"] == 2
    assert captured["alerts"] == 1
