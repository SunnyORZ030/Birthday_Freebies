import re
from collections import defaultdict
from datetime import datetime

from app.repositories.freebies_repository import fetch_freebie_rows, fetch_region_rows


_REGION_PATTERN = re.compile(r"^[a-z0-9_]+$")


def _normalize_region_filter(region: str | None) -> str | None:
    # Normalize and validate optional region filter before querying the repository.
    if region is None:
        return None
    normalized = region.strip().lower()
    if not normalized:
        return None
    if len(normalized) > 50 or not _REGION_PATTERN.match(normalized):
        raise ValueError("Invalid region format.")
    return normalized


def _fallback(primary: str | None, secondary: str | None) -> str:
    # Prefer locale-specific text and gracefully fall back to the other locale.
    return primary or secondary or ""


def get_regions_service(connection_url: str) -> list[dict[str, str]]:
    # Service returns contract-friendly dict rows instead of raw DB tuples.
    rows = fetch_region_rows(connection_url)
    regions = [{"code": code, "name": name} for code, name in rows]
    # Keep response ordering deterministic even if the query changes later.
    return sorted(regions, key=lambda region: region["code"])


def get_freebies_by_region_service(
    connection_url: str,
    region: str | None = None,
) -> dict[str, list[dict[str, str | bool]]]:
    # Apply service-level filter normalization before data access.
    region_filter = _normalize_region_filter(region)
    rows = fetch_freebie_rows(connection_url, region_filter)

    # Store sortable metadata alongside the mapped frontend-compatible payload.
    grouped_entries: dict[str, list[tuple[int, datetime, dict[str, str | bool]]]] = defaultdict(list)

    for (
        region_code,
        category,
        sort_order,
        created_at,
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
        grouped_entries[region_code].append(
            (
                sort_order,
                created_at,
                {
                    # Keep frontend shape stable while centralizing locale fallback.
                    "name": _fallback(zh_name, en_name),
                    "name_en": _fallback(en_name, zh_name),
                    "cat": category,
                    "u": False,
                    "item": _fallback(zh_item, en_item),
                    "item_en": _fallback(en_item, zh_item),
                    "member": _fallback(zh_member, en_member),
                    "member_en": _fallback(en_member, zh_member),
                    "window": _fallback(zh_window, en_window),
                    "window_en": _fallback(en_window, zh_window),
                    "note": _fallback(zh_note, en_note),
                    "note_en": _fallback(en_note, zh_note),
                },
            )
        )

    output: dict[str, list[dict[str, str | bool]]] = {}
    for region_code, entries in grouped_entries.items():
        # Apply service-level ordering rules.
        entries.sort(key=lambda item: (item[0], item[1]))
        output[region_code] = [entry for _sort, _created, entry in entries]

    # Keep region grouping order deterministic for stable API responses.
    return dict(sorted(output.items(), key=lambda item: item[0]))