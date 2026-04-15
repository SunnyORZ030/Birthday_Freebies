from __future__ import annotations

from collections.abc import Generator
from uuid import uuid4

import psycopg
import pytest

from app.db import get_connection_url
from app.services.starbucks_ingestion_service import run_starbucks_ingestion


@pytest.fixture()
def ingestion_region() -> Generator[dict[str, str], None, None]:
    try:
        connection_url = get_connection_url()
    except RuntimeError as exc:
        pytest.skip(str(exc))

    region_id = f"ingestion-region-{uuid4().hex}"
    region_code = f"ingest_region_{uuid4().hex[:8]}"

    try:
        with psycopg.connect(connection_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO regions (id, code, name, created_at, updated_at)
                    VALUES (%s, %s, %s, now(), now())
                    """,
                    (region_id, region_code, "Ingestion Test Region"),
                )
            conn.commit()
    except psycopg.Error as exc:
        pytest.skip(f"Cannot prepare ingestion region fixture: {exc}")

    yield {
        "connection_url": connection_url,
        "region_id": region_id,
        "region_code": region_code,
    }

    # Region delete cascades to promoted freebies/texts; staging tables are cleaned explicitly.
    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM crawler_staging_freebies WHERE region_code = %s", (region_code,))
            cur.execute(
                "DELETE FROM crawler_promoted_mappings WHERE source_system = 'starbucks' AND source_key LIKE %s",
                (f"%::{region_code}",),
            )
            cur.execute("DELETE FROM regions WHERE id = %s", (region_id,))
        conn.commit()


def test_starbucks_ingestion_rerun_is_idempotent(ingestion_region: dict[str, str]) -> None:
    html_fixture = """
    <html>
      <body>
        <h1>Starbucks Rewards Terms</h1>
        <p>Birthday reward is available for Starbucks Rewards members.</p>
        <p>Green gets same-day, Gold gets 7 days, Reserve gets 30 days.</p>
      </body>
    </html>
    """

    first = run_starbucks_ingestion(
        ingestion_region["connection_url"],
        region_code=ingestion_region["region_code"],
        fetch_html=lambda: html_fixture,
    )
    second = run_starbucks_ingestion(
        ingestion_region["connection_url"],
        region_code=ingestion_region["region_code"],
        fetch_html=lambda: html_fixture,
    )

    # First run should stage and promote.
    assert first["discovered"] == 1
    assert first["staged"] == 1
    assert first["promoted"] == 1
    assert first["skipped_unchanged"] == 0

    # Second run with identical payload should skip promotion.
    assert second["discovered"] == 1
    assert second["staged"] == 1
    assert second["promoted"] == 0
    assert second["skipped_unchanged"] == 1

    with psycopg.connect(ingestion_region["connection_url"]) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM crawler_staging_freebies
                WHERE source_system = 'starbucks' AND source_key = %s
                """,
                (f"birthday_reward::{ingestion_region['region_code']}",),
            )
            staging_count = cur.fetchone()[0]

            cur.execute(
                """
                SELECT m.freebie_id
                FROM crawler_promoted_mappings m
                WHERE m.source_system = 'starbucks' AND m.source_key = %s
                """,
                (f"birthday_reward::{ingestion_region['region_code']}",),
            )
            mapping_row = cur.fetchone()
            assert mapping_row is not None
            mapped_freebie_id = mapping_row[0]

            cur.execute(
                """
                SELECT COUNT(*)
                FROM freebies
                WHERE id = %s
                """,
                (mapped_freebie_id,),
            )
            freebie_count = cur.fetchone()[0]

            cur.execute(
                """
                SELECT COUNT(*)
                FROM freebie_texts
                WHERE freebie_id = %s
                """,
                (mapped_freebie_id,),
            )
            text_count = cur.fetchone()[0]

            # Idempotency check: no duplicated promoted freebie rows/text rows.
    assert staging_count == 1
    assert freebie_count == 1
    assert text_count == 2