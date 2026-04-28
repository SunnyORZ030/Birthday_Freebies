from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_health_ingestion_starbucks_shape(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_connection_url", lambda: "postgresql://placeholder")
    monkeypatch.setattr(
        "app.main.get_starbucks_watch_health",
        lambda _connection_url: {
            "source": "starbucks",
            "status": "ok",
            "is_stale": False,
            "consecutive_failures": 0,
            "last_checked_at": None,
            "last_success_at": None,
            "last_changed_at": None,
            "last_error": None,
            "stale_after_minutes": 30,
        },
    )

    response = client.get("/health/ingestion/starbucks")
    assert response.status_code == 200
    assert response.json() == {
        "source": "starbucks",
        "status": "ok",
        "is_stale": False,
        "consecutive_failures": 0,
        "last_checked_at": None,
        "last_success_at": None,
        "last_changed_at": None,
        "last_error": None,
        "stale_after_minutes": 30,
    }


def test_regions_shape(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_connection_url", lambda: "postgresql://placeholder")
    monkeypatch.setattr(
        "app.main.get_regions_service",
        lambda _connection_url: [{"code": "bay_area", "name": "Bay Area"}],
    )

    response = client.get("/api/regions")
    assert response.status_code == 200
    assert response.json() == {
        "regions": [{"code": "bay_area", "name": "Bay Area"}],
    }


def test_freebies_shape(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_connection_url", lambda: "postgresql://placeholder")
    monkeypatch.setattr(
        "app.main.get_freebies_by_region_service",
        lambda _connection_url, _region=None: {
            "bay_area": [
                {
                    "name": "Starbucks",
                    "name_en": "Starbucks",
                    "cat": "drink",
                    "u": False,
                    "item": "Any handcrafted drink",
                    "item_en": "Any handcrafted drink",
                    "member": "Membership required",
                    "member_en": "Membership required",
                    "window": "On birthday",
                    "window_en": "On birthday",
                    "note": "Terms may vary by store",
                    "note_en": "Terms may vary by store",
                }
            ]
        },
    )

    response = client.get("/api/freebies")
    assert response.status_code == 200
    payload = response.json()

    assert "dataByRegion" in payload
    assert "bay_area" in payload["dataByRegion"]
    assert payload["dataByRegion"]["bay_area"][0]["name_en"] == "Starbucks"


def test_freebies_invalid_region_contract() -> None:
    response = client.get("/api/freebies", params={"region": "Bay-Area"})

    assert response.status_code == 422
    payload = response.json()

    assert payload["error"]["code"] == "invalid_request"
    assert payload["error"]["message"] == "Request validation failed."
    assert isinstance(payload["error"]["details"], list)
    assert payload["error"]["details"][0]["field"] == "region"