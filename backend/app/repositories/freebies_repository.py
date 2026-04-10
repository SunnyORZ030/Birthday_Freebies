from datetime import datetime

import psycopg


def fetch_region_rows(connection_url: str) -> list[tuple[str, str]]:
    # Repository layer returns raw rows; shaping happens in the service layer.
    query = """
        SELECT code, name
        FROM regions
        ORDER BY code ASC
    """

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

    return rows


def fetch_freebie_rows(
    connection_url: str,
    region: str | None = None,
) -> list[
    # Tuple field order must match the SQL SELECT column order below.
    tuple[
        str,
        str,
        int,
        datetime,
        str | None,
        str | None,
        str | None,
        str | None,
        str | None,
        str | None,
        str | None,
        str | None,
        str | None,
        str | None,
    ]
]:
    # Returns active freebies with both zh/en text columns for service-level fallback logic.
    query = """
        SELECT
            r.code,
            f.category,
            f.sort_order,
            f.created_at,
            zh.name,
            en.name,
            zh.item,
            en.item,
            zh.member,
            en.member,
            zh.redemption_window,
            en.redemption_window,
            zh.note,
            en.note
        FROM freebies f
        JOIN regions r ON r.id = f.region_id
        LEFT JOIN freebie_texts zh ON zh.freebie_id = f.id AND zh.locale = 'zh'
        LEFT JOIN freebie_texts en ON en.freebie_id = f.id AND en.locale = 'en'
        WHERE
            f.is_active = TRUE
            AND (COALESCE(%s::text, r.code) = r.code)
        ORDER BY r.code ASC, f.sort_order ASC, f.created_at ASC
    """

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            # Region filter is optional; passing None returns all regions.
            cur.execute(query, (region,))
            rows = cur.fetchall()

    return rows