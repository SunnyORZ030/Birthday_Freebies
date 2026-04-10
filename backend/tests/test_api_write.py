from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_freebie_wires_payload(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr("app.main.get_connection_url", lambda: "postgresql://placeholder")

    def fake_create_freebie_service(
        connection_url: str,
        *,
        region_code: str,
        category: str,
        sort_order: int,
        zh_text: dict[str, str],
        en_text: dict[str, str],
    ) -> dict[str, str]:
        captured["connection_url"] = connection_url
        captured["region_code"] = region_code
        captured["category"] = category
        captured["sort_order"] = sort_order
        captured["zh_text"] = zh_text
        captured["en_text"] = en_text
        return {
            "id": "freebie-123",
            "region_code": region_code,
            "category": category,
            "created_at": "2026-04-10T20:00:00",
        }

    monkeypatch.setattr("app.main.create_freebie_service", fake_create_freebie_service)

    response = client.post(
        "/api/freebies",
        json={
            "region_code": "bay_area",
            "category": "drink",
            "sort_order": 2,
            "zh": {
                "name": "星巴克",
                "item": "任意手工製飲品",
                "member": "需要會員卡",
                "window": "生日當天",
                "note": "各分店條款可能不同",
            },
            "en": {
                "name": "Starbucks",
                "item": "Any handcrafted drink",
                "member": "Membership required",
                "window": "On birthday",
                "note": "Terms may vary by store",
            },
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": "freebie-123",
        "region_code": "bay_area",
        "category": "drink",
        "created_at": "2026-04-10T20:00:00",
    }
    assert captured == {
        "connection_url": "postgresql://placeholder",
        "region_code": "bay_area",
        "category": "drink",
        "sort_order": 2,
        "zh_text": {
            "name": "星巴克",
            "item": "任意手工製飲品",
            "member": "需要會員卡",
            "redemption_window": "生日當天",
            "note": "各分店條款可能不同",
        },
        "en_text": {
            "name": "Starbucks",
            "item": "Any handcrafted drink",
            "member": "Membership required",
            "redemption_window": "On birthday",
            "note": "Terms may vary by store",
        },
    }


def test_create_freebie_missing_region_maps_to_404(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_connection_url", lambda: "postgresql://placeholder")

    def fake_create_freebie_service(*_args, **_kwargs) -> dict[str, str]:
        from app.services.freebies_service import FreebieCreationError

        raise FreebieCreationError("Region 'moon_base' not found.")

    monkeypatch.setattr("app.main.create_freebie_service", fake_create_freebie_service)

    response = client.post(
        "/api/freebies",
        json={
            "region_code": "moon_base",
            "category": "drink",
            "zh": {
                "name": "測試",
                "item": "測試",
                "member": "測試",
                "window": "測試",
                "note": "",
            },
            "en": {
                "name": "Test",
                "item": "Test",
                "member": "Test",
                "window": "Test",
                "note": "",
            },
        },
    )

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "not_found"
    assert payload["error"]["message"] == "Region 'moon_base' not found."


def test_update_freebie_wires_payload(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr("app.main.get_connection_url", lambda: "postgresql://placeholder")

    def fake_update_freebie_service(
        connection_url: str,
        *,
        freebie_id: str,
        category: str | None = None,
        sort_order: int | None = None,
        is_active: bool | None = None,
        zh_text: dict[str, str] | None = None,
        en_text: dict[str, str] | None = None,
    ) -> dict[str, str]:
        captured["connection_url"] = connection_url
        captured["freebie_id"] = freebie_id
        captured["category"] = category
        captured["sort_order"] = sort_order
        captured["is_active"] = is_active
        captured["zh_text"] = zh_text
        captured["en_text"] = en_text
        return {"id": freebie_id, "updated_at": "2026-04-10T20:00:00"}

    monkeypatch.setattr("app.main.update_freebie_service", fake_update_freebie_service)

    response = client.put(
        "/api/freebies/freebie-123",
        json={
            "category": "drink",
            "sort_order": 7,
            "is_active": False,
            "en": {
                "name": "Starbucks Updated",
                "item": "Any handcrafted drink",
                "member": "Membership required",
                "window": "On birthday",
                "note": "Updated note",
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "freebie-123",
        "updated_at": "2026-04-10T20:00:00",
    }
    assert captured == {
        "connection_url": "postgresql://placeholder",
        "freebie_id": "freebie-123",
        "category": "drink",
        "sort_order": 7,
        "is_active": False,
        "zh_text": None,
        "en_text": {
            "name": "Starbucks Updated",
            "item": "Any handcrafted drink",
            "member": "Membership required",
            "redemption_window": "On birthday",
            "note": "Updated note",
        },
    }


def test_delete_freebie_returns_204(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr("app.main.get_connection_url", lambda: "postgresql://placeholder")

    def fake_delete_freebie_service(connection_url: str, freebie_id: str) -> bool:
        captured["connection_url"] = connection_url
        captured["freebie_id"] = freebie_id
        return True

    monkeypatch.setattr("app.main.delete_freebie_service", fake_delete_freebie_service)

    response = client.delete("/api/freebies/freebie-123")

    assert response.status_code == 204
    assert response.content == b""
    assert captured == {
        "connection_url": "postgresql://placeholder",
        "freebie_id": "freebie-123",
    }