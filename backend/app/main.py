import os
from collections import defaultdict
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import psycopg

# Load backend/.env so DATABASE_URL is available in local development.
load_dotenv()


# Prisma URLs can include ?schema=public; psycopg does not need this value.
def _normalized_database_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    query_params = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key != "schema"]
    return urlunparse(parsed._replace(query=urlencode(query_params)))


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required to start the FastAPI server.")

CONNECTION_URL = _normalized_database_url(DATABASE_URL)

# Main API app used by uvicorn.
app = FastAPI(title="Birthday Freebies API")

# Allow local frontend pages to call this API without extra proxy configuration.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Basic health probe for startup checks and quick diagnostics.
@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


# Regions endpoint used by the frontend region dropdown.
@app.get("/api/regions")
def get_regions() -> dict[str, list[dict[str, str]]]:
    query = """
        SELECT code, name
        FROM regions
        ORDER BY code ASC
    """

    with psycopg.connect(CONNECTION_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

    return {
        # Keep response shape simple and stable for the frontend.
        "regions": [
            {"code": code, "name": name}
            for code, name in rows
        ]
    }


# Main freebies endpoint. Returns entries grouped by region to match existing UI state.
@app.get("/api/freebies")
def get_freebies(region: str | None = Query(default=None)) -> dict[str, dict[str, list[dict[str, Any]]]]:
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

    # Build the final API payload keyed by region code.
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    with psycopg.connect(CONNECTION_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (region,))
            rows = cur.fetchall()

    # Normalize database rows into the legacy frontend field names.
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
        # Prefer zh text for display fields and use en as fallback.
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

    return {"dataByRegion": dict(grouped)}