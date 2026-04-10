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


# ========== Write Service Functions ==========


class FreebieCreationError(Exception):
    """Raised when freebie creation fails due to validation or data issues."""

    pass


def create_freebie_service(
    connection_url: str,
    region_code: str,
    category: str,
    sort_order: int,
    zh_text: dict[str, str],
    en_text: dict[str, str],
) -> dict[str, str]:
    """
    Create a new freebie with both language texts.
    Validates that region exists and all text fields are provided.
    Returns a dict with id, region_code, category, created_at ISO string.
    """
    from app.repositories.freebies_repository import (
        create_freebie,
        create_or_update_freebie_text,
        fetch_region_id_by_code,
    )

    # Validate region exists.
    region_id = fetch_region_id_by_code(connection_url, region_code)
    if not region_id:
        raise FreebieCreationError(f"Region '{region_code}' not found.")

    # Create the freebie entry.
    try:
        freebie_id, created_at = create_freebie(
            connection_url,
            region_id,
            category,
            sort_order,
        )
    except Exception as e:
        raise FreebieCreationError(f"Failed to create freebie: {str(e)}") from e

    # Create or update language texts.
    try:
        create_or_update_freebie_text(
            connection_url,
            freebie_id,
            "zh",
            zh_text["name"],
            zh_text["item"],
            zh_text["member"],
            zh_text["redemption_window"],
            zh_text.get("note", ""),
        )
        create_or_update_freebie_text(
            connection_url,
            freebie_id,
            "en",
            en_text["name"],
            en_text["item"],
            en_text["member"],
            en_text["redemption_window"],
            en_text.get("note", ""),
        )
    except Exception as e:
        # If text creation fails, we should ideally rollback the freebie.
        # For now, we'll raise and let the caller handle cleanup if needed.
        raise FreebieCreationError(f"Failed to create freebie texts: {str(e)}") from e

    return {
        "id": freebie_id,
        "region_code": region_code,
        "category": category,
        "created_at": created_at.isoformat(),
    }


def update_freebie_service(
    connection_url: str,
    freebie_id: str,
    category: str | None = None,
    sort_order: int | None = None,
    is_active: bool | None = None,
    zh_text: dict[str, str] | None = None,
    en_text: dict[str, str] | None = None,
) -> dict[str, str]:
    """
    Update a freebie's metadata and/or texts.
    Only updates fields that are provided (not None).
    Returns a dict with id and updated_at ISO string.
    """
    from app.repositories.freebies_repository import (
        create_or_update_freebie_text,
        update_freebie,
    )

    # Check if freebie exists by attempting to update it.
    # If no metadata fields are provided, we still need to verify it exists.
    if category is None and sort_order is None and is_active is None:
        # At least one text must be provided if no metadata updates.
        if not zh_text and not en_text:
            raise FreebieCreationError("No fields provided for update.")
    
    try:
        # Update metadata if any fields were provided.
        updated_at = None
        if category is not None or sort_order is not None or is_active is not None:
            updated_at = update_freebie(
                connection_url,
                freebie_id,
                category=category,
                sort_order=sort_order,
                is_active=is_active,
            )

        # If no metadata was updated, we got None back; still proceed with text updates.
        if updated_at is None and not (zh_text or en_text):
            # Nothing was actually updated; this shouldn't happen due to earlier check.
            raise FreebieCreationError("Freebie not found or no updates applied.")

        # Update texts if provided.
        if zh_text:
            create_or_update_freebie_text(
                connection_url,
                freebie_id,
                "zh",
                zh_text["name"],
                zh_text["item"],
                zh_text["member"],
                zh_text["redemption_window"],
                zh_text.get("note", ""),
            )
            # Always update timestamp when text changes.
            if updated_at is None:
                updated_at = datetime.utcnow()

        if en_text:
            create_or_update_freebie_text(
                connection_url,
                freebie_id,
                "en",
                en_text["name"],
                en_text["item"],
                en_text["member"],
                en_text["redemption_window"],
                en_text.get("note", ""),
            )
            if updated_at is None:
                updated_at = datetime.utcnow()

        # Format final response.
        if updated_at is None:
            updated_at = datetime.utcnow()

        return {
            "id": freebie_id,
            "updated_at": updated_at.isoformat() if isinstance(updated_at, datetime) else str(updated_at),
        }

    except FreebieCreationError:
        raise
    except Exception as e:
        raise FreebieCreationError(f"Failed to update freebie: {str(e)}") from e


def delete_freebie_service(connection_url: str, freebie_id: str) -> bool:
    """
    Delete a freebie and cascade its freebie_texts.
    Returns True if deleted, False if not found.
    """
    from app.repositories.freebies_repository import delete_freebie

    try:
        return delete_freebie(connection_url, freebie_id)
    except Exception as e:
        raise FreebieCreationError(f"Failed to delete freebie: {str(e)}") from e