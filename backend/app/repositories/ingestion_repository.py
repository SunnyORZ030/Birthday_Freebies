import json
from datetime import datetime

import psycopg


def ensure_ingestion_tables(connection_url: str) -> None:
    # Runtime guard for local/dev runs before explicit Prisma migration is applied.
    ddl = """
        CREATE TABLE IF NOT EXISTS crawler_staging_freebies (
            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            source_system TEXT NOT NULL,
            source_key TEXT NOT NULL,
            region_code TEXT NOT NULL,
            category TEXT NOT NULL,
            payload_json JSONB NOT NULL,
            content_hash TEXT NOT NULL,
            fetched_at TIMESTAMP NOT NULL,
            normalized_at TIMESTAMP NOT NULL DEFAULT now(),
            promoted_at TIMESTAMP,
            promoted_freebie_id TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now(),
            UNIQUE (source_system, source_key)
        );

        CREATE TABLE IF NOT EXISTS crawler_promoted_mappings (
            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            source_system TEXT NOT NULL,
            source_key TEXT NOT NULL,
            freebie_id TEXT NOT NULL REFERENCES freebies(id) ON DELETE CASCADE,
            content_hash TEXT NOT NULL,
            last_promoted_at TIMESTAMP NOT NULL DEFAULT now(),
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now(),
            UNIQUE (source_system, source_key)
        );

        CREATE TABLE IF NOT EXISTS crawler_source_states (
            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            source_system TEXT NOT NULL,
            source_key TEXT NOT NULL,
            etag TEXT,
            last_modified TEXT,
            last_checked_at TIMESTAMP,
            last_success_at TIMESTAMP,
            last_changed_at TIMESTAMP,
            last_content_hash TEXT,
            consecutive_failures INT NOT NULL DEFAULT 0,
            last_error TEXT,
            updated_at TIMESTAMP NOT NULL DEFAULT now(),
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            UNIQUE (source_system, source_key)
        );
    """

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()


def upsert_staging_row(
    connection_url: str,
    *,
    source_system: str,
    source_key: str,
    region_code: str,
    category: str,
    payload: dict,
    content_hash: str,
    fetched_at: datetime,
) -> None:
    # Staging keeps the latest normalized payload per source key for traceability.
    query = """
        INSERT INTO crawler_staging_freebies (
            source_system,
            source_key,
            region_code,
            category,
            payload_json,
            content_hash,
            fetched_at,
            normalized_at,
            updated_at
        )
        VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, now(), now())
        ON CONFLICT (source_system, source_key)
        DO UPDATE SET
            region_code = EXCLUDED.region_code,
            category = EXCLUDED.category,
            payload_json = EXCLUDED.payload_json,
            content_hash = EXCLUDED.content_hash,
            fetched_at = EXCLUDED.fetched_at,
            normalized_at = now(),
            updated_at = now()
    """

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    source_system,
                    source_key,
                    region_code,
                    category,
                    json.dumps(payload, ensure_ascii=False),
                    content_hash,
                    fetched_at,
                ),
            )
        conn.commit()


def fetch_promoted_mapping(
    connection_url: str,
    *,
    source_system: str,
    source_key: str,
) -> tuple[str, str] | None:
    # Mapping stores which freebie row a source key currently points to.
    query = """
        SELECT freebie_id, content_hash
        FROM crawler_promoted_mappings
        WHERE source_system = %s AND source_key = %s
    """

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (source_system, source_key))
            row = cur.fetchone()

    return (row[0], row[1]) if row else None


def upsert_promoted_mapping(
    connection_url: str,
    *,
    source_system: str,
    source_key: str,
    freebie_id: str,
    content_hash: str,
) -> None:
    # Promotion writes are idempotent: same source key always converges to one mapping row.
    query = """
        INSERT INTO crawler_promoted_mappings (
            source_system,
            source_key,
            freebie_id,
            content_hash,
            last_promoted_at,
            updated_at
        )
        VALUES (%s, %s, %s, %s, now(), now())
        ON CONFLICT (source_system, source_key)
        DO UPDATE SET
            freebie_id = EXCLUDED.freebie_id,
            content_hash = EXCLUDED.content_hash,
            last_promoted_at = now(),
            updated_at = now()
    """

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (source_system, source_key, freebie_id, content_hash))
        conn.commit()


def mark_staging_promoted(
    connection_url: str,
    *,
    source_system: str,
    source_key: str,
    freebie_id: str,
) -> None:
    # Marking staged rows helps audits distinguish discovered-only vs promoted records.
    query = """
        UPDATE crawler_staging_freebies
        SET promoted_at = now(), promoted_freebie_id = %s, updated_at = now()
        WHERE source_system = %s AND source_key = %s
    """

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (freebie_id, source_system, source_key))
        conn.commit()


def fetch_source_state(
    connection_url: str,
    *,
    source_system: str,
    source_key: str,
) -> dict[str, object] | None:
    query = """
        SELECT
            etag,
            last_modified,
            last_checked_at,
            last_success_at,
            last_changed_at,
            last_content_hash,
            consecutive_failures,
            last_error
        FROM crawler_source_states
        WHERE source_system = %s AND source_key = %s
    """

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (source_system, source_key))
            row = cur.fetchone()

    if not row:
        return None

    return {
        "etag": row[0],
        "last_modified": row[1],
        "last_checked_at": row[2],
        "last_success_at": row[3],
        "last_changed_at": row[4],
        "last_content_hash": row[5],
        "consecutive_failures": row[6],
        "last_error": row[7],
    }


def upsert_source_state(
    connection_url: str,
    *,
    source_system: str,
    source_key: str,
    etag: str | None,
    last_modified: str | None,
    last_checked_at: datetime | None,
    last_success_at: datetime | None,
    last_changed_at: datetime | None,
    last_content_hash: str | None,
    consecutive_failures: int,
    last_error: str | None,
) -> None:
    query = """
        INSERT INTO crawler_source_states (
            source_system,
            source_key,
            etag,
            last_modified,
            last_checked_at,
            last_success_at,
            last_changed_at,
            last_content_hash,
            consecutive_failures,
            last_error,
            updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
        ON CONFLICT (source_system, source_key)
        DO UPDATE SET
            etag = EXCLUDED.etag,
            last_modified = EXCLUDED.last_modified,
            last_checked_at = EXCLUDED.last_checked_at,
            last_success_at = EXCLUDED.last_success_at,
            last_changed_at = EXCLUDED.last_changed_at,
            last_content_hash = EXCLUDED.last_content_hash,
            consecutive_failures = EXCLUDED.consecutive_failures,
            last_error = EXCLUDED.last_error,
            updated_at = now()
    """

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    source_system,
                    source_key,
                    etag,
                    last_modified,
                    last_checked_at,
                    last_success_at,
                    last_changed_at,
                    last_content_hash,
                    consecutive_failures,
                    last_error,
                ),
            )
        conn.commit()
