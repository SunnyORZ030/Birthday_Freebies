from __future__ import annotations

from collections.abc import Generator
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.db import get_connection_url
from app.main import app


client = TestClient(app)


EXPECTED_FREEBIE_ITEM_KEYS = {
    "name",
    "name_en",
    "cat",
    "u",
    "item",
    "item_en",
    "member",
    "member_en",
    "window",
    "window_en",
    "note",
    "note_en",
}


def assert_frontend_freebie_item_contract(item: dict[str, object]) -> None:
    assert set(item.keys()) == EXPECTED_FREEBIE_ITEM_KEYS
    assert isinstance(item["u"], bool)
    for key in EXPECTED_FREEBIE_ITEM_KEYS - {"u"}:
        assert isinstance(item[key], str)


@pytest.fixture()
def seeded_region() -> Generator[dict[str, str], None, None]:
    try:
        connection_url = get_connection_url()
    except RuntimeError as exc:
        pytest.skip(str(exc))

    region_id = f"test-region-{uuid4().hex}"
    region_code = f"it_region_{uuid4().hex[:8]}"
    freebie_primary_id = f"test-freebie-primary-{uuid4().hex}"
    freebie_fallback_id = f"test-freebie-fallback-{uuid4().hex}"

    try:
        with psycopg.connect(connection_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO regions (id, code, name, created_at, updated_at)
                    VALUES (%s, %s, %s, now(), now())
                    """,
                    (region_id, region_code, "Integration Region"),
                )

                cur.execute(
                    """
                    INSERT INTO freebies (id, region_id, category, is_active, sort_order, created_at, updated_at)
                    VALUES
                        (%s, %s, %s, true, 2, now(), now()),
                        (%s, %s, %s, true, 1, now(), now())
                    """,
                    (
                        freebie_primary_id,
                        region_id,
                        "drink",
                        freebie_fallback_id,
                        region_id,
                        "food",
                    ),
                )

                # Primary freebie has both locales.
                cur.execute(
                    """
                    INSERT INTO freebie_texts
                        (id, freebie_id, locale, name, item, member, redemption_window, note, created_at, updated_at)
                    VALUES
                        (%s, %s, 'zh', %s, %s, %s, %s, %s, now(), now()),
                        (%s, %s, 'en', %s, %s, %s, %s, %s, now(), now())
                    """,
                    (
                        f"test-text-zh-{uuid4().hex}",
                        freebie_primary_id,
                        "主測試品牌",
                        "主測試贈品",
                        "需註冊",
                        "生日當天",
                        "主測試備註",
                        f"test-text-en-{uuid4().hex}",
                        freebie_primary_id,
                        "Primary Test Brand",
                        "Primary Test Item",
                        "Membership required",
                        "Birthday only",
                        "Primary note",
                    ),
                )

                # Fallback freebie has only English texts, service should fallback to en for zh-facing fields.
                cur.execute(
                    """
                    INSERT INTO freebie_texts
                        (id, freebie_id, locale, name, item, member, redemption_window, note, created_at, updated_at)
                    VALUES (%s, %s, 'en', %s, %s, %s, %s, %s, now(), now())
                    """,
                    (
                        f"test-text-fallback-en-{uuid4().hex}",
                        freebie_fallback_id,
                        "Fallback EN Brand",
                        "Fallback EN Item",
                        "No member needed",
                        "Whole month",
                        "Fallback note",
                    ),
                )

            conn.commit()
    except psycopg.Error as exc:
        pytest.skip(f"Cannot prepare integration test data: {exc}")

    yield {
        "connection_url": connection_url,
        "region_id": region_id,
        "region_code": region_code,
    }

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM regions WHERE id = %s", (region_id,))
        conn.commit()


def test_freebies_api_reads_db_and_matches_frontend_shape(seeded_region: dict[str, str]) -> None:
    response = client.get("/api/freebies", params={"region": seeded_region["region_code"]})

    assert response.status_code == 200
    payload = response.json()

    assert payload == {
        "dataByRegion": {
            seeded_region["region_code"]: [
                {
                    "name": "Fallback EN Brand",
                    "name_en": "Fallback EN Brand",
                    "cat": "food",
                    "u": False,
                    "item": "Fallback EN Item",
                    "item_en": "Fallback EN Item",
                    "member": "No member needed",
                    "member_en": "No member needed",
                    "window": "Whole month",
                    "window_en": "Whole month",
                    "note": "Fallback note",
                    "note_en": "Fallback note",
                },
                {
                    "name": "主測試品牌",
                    "name_en": "Primary Test Brand",
                    "cat": "drink",
                    "u": False,
                    "item": "主測試贈品",
                    "item_en": "Primary Test Item",
                    "member": "需註冊",
                    "member_en": "Membership required",
                    "window": "生日當天",
                    "window_en": "Birthday only",
                    "note": "主測試備註",
                    "note_en": "Primary note",
                },
            ]
        }
    }


def test_regions_api_includes_seeded_region(seeded_region: dict[str, str]) -> None:
    response = client.get("/api/regions")

    assert response.status_code == 200
    regions = response.json()["regions"]

    assert {
        "code": seeded_region["region_code"],
        "name": "Integration Region",
    } in regions


def test_freebies_region_filter_invalid_returns_422_error_envelope() -> None:
    response = client.get("/api/freebies", params={"region": "Bay-Area"})

    assert response.status_code == 422
    payload = response.json()

    assert payload["error"]["code"] == "invalid_request"
    assert payload["error"]["message"] == "Request validation failed."
    assert isinstance(payload["error"]["details"], list)
    assert payload["error"]["details"][0]["field"] == "region"


@pytest.fixture()
def seeded_multi_regions() -> Generator[dict[str, str], None, None]:
    try:
        connection_url = get_connection_url()
    except RuntimeError as exc:
        pytest.skip(str(exc))

    region_alpha_id = f"test-region-alpha-{uuid4().hex}"
    region_beta_id = f"test-region-beta-{uuid4().hex}"
    region_alpha_code = f"it_multi_a_{uuid4().hex[:8]}"
    region_beta_code = f"it_multi_b_{uuid4().hex[:8]}"

    freebie_alpha_late_id = f"test-freebie-alpha-late-{uuid4().hex}"
    freebie_alpha_early_id = f"test-freebie-alpha-early-{uuid4().hex}"
    freebie_beta_id = f"test-freebie-beta-{uuid4().hex}"

    try:
        with psycopg.connect(connection_url) as conn:
            with conn.cursor() as cur:
                # Insert beta first to ensure API grouping order follows region code, not insertion order.
                cur.execute(
                    """
                    INSERT INTO regions (id, code, name, created_at, updated_at)
                    VALUES
                        (%s, %s, %s, now(), now()),
                        (%s, %s, %s, now(), now())
                    """,
                    (
                        region_beta_id,
                        region_beta_code,
                        "Integration Region Beta",
                        region_alpha_id,
                        region_alpha_code,
                        "Integration Region Alpha",
                    ),
                )

                # Insert out of order; service should sort by sort_order ascending within each region.
                cur.execute(
                    """
                    INSERT INTO freebies (id, region_id, category, is_active, sort_order, created_at, updated_at)
                    VALUES
                        (%s, %s, %s, true, 3, now(), now()),
                        (%s, %s, %s, true, 1, now(), now()),
                        (%s, %s, %s, true, 2, now(), now())
                    """,
                    (
                        freebie_alpha_late_id,
                        region_alpha_id,
                        "dessert",
                        freebie_alpha_early_id,
                        region_alpha_id,
                        "drink",
                        freebie_beta_id,
                        region_beta_id,
                        "food",
                    ),
                )

                cur.execute(
                    """
                    INSERT INTO freebie_texts
                        (id, freebie_id, locale, name, item, member, redemption_window, note, created_at, updated_at)
                    VALUES
                        (%s, %s, 'en', %s, %s, %s, %s, %s, now(), now()),
                        (%s, %s, 'en', %s, %s, %s, %s, %s, now(), now()),
                        (%s, %s, 'en', %s, %s, %s, %s, %s, now(), now())
                    """,
                    (
                        f"test-text-alpha-late-{uuid4().hex}",
                        freebie_alpha_late_id,
                        "Alpha Later",
                        "Alpha Later Item",
                        "Alpha Later Member",
                        "Alpha Later Window",
                        "Alpha Later Note",
                        f"test-text-alpha-early-{uuid4().hex}",
                        freebie_alpha_early_id,
                        "Alpha Earlier",
                        "Alpha Earlier Item",
                        "Alpha Earlier Member",
                        "Alpha Earlier Window",
                        "Alpha Earlier Note",
                        f"test-text-beta-{uuid4().hex}",
                        freebie_beta_id,
                        "Beta Item",
                        "Beta Item Detail",
                        "Beta Member",
                        "Beta Window",
                        "Beta Note",
                    ),
                )

            conn.commit()
    except psycopg.Error as exc:
        pytest.skip(f"Cannot prepare multi-region integration data: {exc}")

    yield {
        "region_alpha_id": region_alpha_id,
        "region_beta_id": region_beta_id,
        "region_alpha_code": region_alpha_code,
        "region_beta_code": region_beta_code,
    }

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM regions WHERE id = %s", (region_alpha_id,))
            cur.execute("DELETE FROM regions WHERE id = %s", (region_beta_id,))
        conn.commit()


def test_freebies_without_region_groups_by_region_and_sorts(seeded_multi_regions: dict[str, str]) -> None:
    response = client.get("/api/freebies")

    assert response.status_code == 200
    payload = response.json()
    data_by_region = payload["dataByRegion"]

    alpha_code = seeded_multi_regions["region_alpha_code"]
    beta_code = seeded_multi_regions["region_beta_code"]

    assert alpha_code in data_by_region
    assert beta_code in data_by_region

    seeded_order = [code for code in data_by_region.keys() if code in {alpha_code, beta_code}]
    assert seeded_order == [alpha_code, beta_code]

    alpha_names_in_order = [item["name_en"] for item in data_by_region[alpha_code]]
    assert alpha_names_in_order == ["Alpha Earlier", "Alpha Later"]


def test_freebies_response_schema_level_contract() -> None:
    response = client.get("/api/freebies")

    assert response.status_code == 200
    payload = response.json()

    assert set(payload.keys()) == {"dataByRegion"}
    assert isinstance(payload["dataByRegion"], dict)

    for freebies in payload["dataByRegion"].values():
        assert isinstance(freebies, list)
        for item in freebies:
            assert_frontend_freebie_item_contract(item)


def test_freebies_region_filtered_response_schema_level_contract(
    seeded_region: dict[str, str],
) -> None:
    response = client.get("/api/freebies", params={"region": seeded_region["region_code"]})

    assert response.status_code == 200
    payload = response.json()

    assert set(payload.keys()) == {"dataByRegion"}
    assert isinstance(payload["dataByRegion"], dict)
    assert set(payload["dataByRegion"].keys()) == {seeded_region["region_code"]}

    for item in payload["dataByRegion"][seeded_region["region_code"]]:
        assert_frontend_freebie_item_contract(item)


@pytest.fixture()
def seeded_empty_region() -> Generator[dict[str, str], None, None]:
    try:
        connection_url = get_connection_url()
    except RuntimeError as exc:
        pytest.skip(str(exc))

    region_id = f"test-empty-region-{uuid4().hex}"
    region_code = f"it_empty_{uuid4().hex[:8]}"

    try:
        with psycopg.connect(connection_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO regions (id, code, name, created_at, updated_at)
                    VALUES (%s, %s, %s, now(), now())
                    """,
                    (region_id, region_code, "Integration Empty Region"),
                )
            conn.commit()
    except psycopg.Error as exc:
        pytest.skip(f"Cannot prepare empty-region integration data: {exc}")

    yield {
        "region_id": region_id,
        "region_code": region_code,
    }

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM regions WHERE id = %s", (region_id,))
        conn.commit()


def test_freebies_empty_region_filter_returns_stable_empty_contract(
    seeded_empty_region: dict[str, str],
) -> None:
    response = client.get("/api/freebies", params={"region": seeded_empty_region["region_code"]})

    assert response.status_code == 200
    payload = response.json()
    assert payload == {"dataByRegion": {}}