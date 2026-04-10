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


# ========== Write Operations ==========


def fetch_region_id_by_code(connection_url: str, region_code: str) -> str | None:
    # Lookup region ID by code; returns None if not found.
    query = "SELECT id FROM regions WHERE code = %s"
    
    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (region_code,))
            row = cur.fetchone()
    
    return row[0] if row else None


def create_freebie(
    connection_url: str,
    region_id: str,
    category: str,
    sort_order: int = 0,
) -> tuple[str, datetime]:
    # Create a new freebie and return (id, created_at).
    # PostgreSQL gen_random_uuid() generates a UUID for the @default(uuid()) field.
    query = """
        INSERT INTO freebies (id, region_id, category, is_active, sort_order, created_at, updated_at)
        VALUES (gen_random_uuid(), %s, %s, true, %s, now(), now())
        RETURNING id, created_at
    """
    
    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (region_id, category, sort_order))
            row = cur.fetchone()
            conn.commit()
    
    return (row[0], row[1]) if row else None


def create_or_update_freebie_text(
    connection_url: str,
    freebie_id: str,
    locale: str,
    name: str,
    item: str,
    member: str,
    redemption_window: str,
    note: str = "",
) -> None:
    # Idempotent upsert: insert or update freebie text for the given locale.
    query = """
        INSERT INTO freebie_texts (
            id, freebie_id, locale, name, item, member, redemption_window, note, created_at, updated_at
        )
        VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, now(), now())
        ON CONFLICT (freebie_id, locale)
        DO UPDATE SET
            name = EXCLUDED.name,
            item = EXCLUDED.item,
            member = EXCLUDED.member,
            redemption_window = EXCLUDED.redemption_window,
            note = EXCLUDED.note,
            updated_at = now()
    """
    
    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (
                freebie_id,
                locale,
                name,
                item,
                member,
                redemption_window,
                note,
            ))
            conn.commit()


def update_freebie(
    connection_url: str,
    freebie_id: str,
    category: str | None = None,
    sort_order: int | None = None,
    is_active: bool | None = None,
) -> datetime | None:
    # Update selective freebie fields; returns updated_at timestamp if found.
    updates: list[str] = []
    params: list = []
    
    if category is not None:
        updates.append("category = %s")
        params.append(category)
    
    if sort_order is not None:
        updates.append("sort_order = %s")
        params.append(sort_order)
    
    if is_active is not None:
        updates.append("is_active = %s")
        params.append(is_active)
    
    if not updates:
        # No fields to update; return None to signal no-op.
        return None
    
    # Always update the timestamp.
    updates.append("updated_at = now()")
    params.append(freebie_id)
    
    query = f"""
        UPDATE freebies
        SET {', '.join(updates)}
        WHERE id = %s
        RETURNING updated_at
    """
    
    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            conn.commit()
    
    return row[0] if row else None


def delete_freebie(connection_url: str, freebie_id: str) -> bool:
    # Delete a freebie and its associated texts (cascading).
    # Returns True if a row was deleted, False if ID not found.
    query = "DELETE FROM freebies WHERE id = %s"
    
    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (freebie_id,))
            conn.commit()
            # rowcount after DELETE shows how many rows were deleted.
            return cur.rowcount > 0