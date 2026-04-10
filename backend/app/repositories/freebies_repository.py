from collections import defaultdict

import psycopg


def fetch_regions(connection_url: str) -> list[dict[str, str]]:
    query = """
        SELECT code, name
        FROM regions
        ORDER BY code ASC
    """

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

    return [{"code": code, "name": name} for code, name in rows]


def fetch_freebies_by_region(
    connection_url: str,
    region: str | None = None,
) -> dict[str, list[dict[str, str | bool]]]:
    query = """
        SELECT
            r.code,
            f.category,
            f.sort_order,
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

    grouped: dict[str, list[dict[str, str | bool]]] = defaultdict(list)

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (region,))
            rows = cur.fetchall()

    for (
        region_code,
        category,
        _sort_order,
        zh_name,
        en_name,
        zh_item,
        en_item,
        zh_member,
        en_member,
        zh_window,
        en_window,
        zh_note,
        en_note,
    ) in rows:
        # Keep response backward-compatible with current frontend field names.
        grouped[region_code].append(
            {
                "name": zh_name or en_name or "",
                "name_en": en_name or zh_name or "",
                "cat": category,
                "u": False,
                "item": zh_item or en_item or "",
                "item_en": en_item or zh_item or "",
                "member": zh_member or en_member or "",
                "member_en": en_member or zh_member or "",
                "window": zh_window or en_window or "",
                "window_en": en_window or zh_window or "",
                "note": zh_note or en_note or "",
                "note_en": en_note or zh_note or "",
            }
        )

    return dict(grouped)