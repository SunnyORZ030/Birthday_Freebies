from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_regions_shape(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_connection_url", lambda: "postgresql://placeholder")
    monkeypatch.setattr(
        "app.main.fetch_regions",
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
        "app.main.fetch_freebies_by_region",
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