import hashlib
import os
import time
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import httpx

from app.crawlers.starbucks_crawler import STARBUCKS_REWARDS_TERMS_URL
from app.repositories.ingestion_repository import (
    ensure_ingestion_tables,
    fetch_source_state,
    upsert_source_state,
)
from app.services.starbucks_ingestion_service import run_starbucks_ingestion


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _send_webhook_alert(webhook_url: str, message: str) -> None:
    # Best-effort alert; ingestion state is already persisted even if alerting fails.
    httpx.post(webhook_url, json={"text": message}, timeout=10.0).raise_for_status()


def _parse_backoff_seconds(raw: str) -> list[int]:
    values: list[int] = []
    for piece in raw.split(","):
        piece = piece.strip()
        if not piece:
            continue
        values.append(max(0, int(piece)))
    return values or [60, 300, 900]


def run_starbucks_watch_once(
    connection_url: str,
    *,
    region_code: str,
    max_retries: int = 3,
    retry_backoff_seconds: list[int] | None = None,
    stale_after_minutes: int = 30,
    alert_failure_threshold: int = 2,
    webhook_url: str | None = None,
    http_get: Callable[..., httpx.Response] = httpx.get,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    """Run one conditional-fetch cycle and promote only when source content changed."""
    ensure_ingestion_tables(connection_url)

    source_system = "starbucks"
    source_key = "rewards_terms_page"
    state = fetch_source_state(
        connection_url,
        source_system=source_system,
        source_key=source_key,
    )

    retries = max(1, max_retries)
    backoffs = retry_backoff_seconds or [60, 300, 900]
    previous_failures = int((state or {}).get("consecutive_failures") or 0)
    now_utc = datetime.now(timezone.utc)

    headers: dict[str, str] = {}
    if state and state.get("etag"):
        headers["If-None-Match"] = str(state["etag"])
    if state and state.get("last_modified"):
        headers["If-Modified-Since"] = str(state["last_modified"])

    last_exception: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = http_get(STARBUCKS_REWARDS_TERMS_URL, headers=headers, timeout=20.0)

            # Source not changed; this still counts as a successful freshness check.
            if response.status_code == 304:
                upsert_source_state(
                    connection_url,
                    source_system=source_system,
                    source_key=source_key,
                    etag=response.headers.get("ETag") or (state or {}).get("etag"),
                    last_modified=response.headers.get("Last-Modified") or (state or {}).get("last_modified"),
                    last_checked_at=now_utc,
                    last_success_at=now_utc,
                    last_changed_at=(state or {}).get("last_changed_at"),
                    last_content_hash=(state or {}).get("last_content_hash"),
                    consecutive_failures=0,
                    last_error=None,
                )
                return {
                    "status": "not_modified",
                    "attempt": attempt,
                    "retries": retries,
                    "stale_after_minutes": stale_after_minutes,
                }

            response.raise_for_status()
            html = response.text
            page_hash = _hash_text(html)
            prior_hash = (state or {}).get("last_content_hash")
            changed = page_hash != prior_hash

            if changed:
                result = run_starbucks_ingestion(
                    connection_url,
                    region_code=region_code,
                    fetch_html=lambda: html,
                )
            else:
                # Response can be 200 even when content is unchanged (no ETag/Last-Modified support).
                result = {
                    "discovered": 0,
                    "staged": 0,
                    "promoted": 0,
                    "skipped_unchanged": 0,
                }

            upsert_source_state(
                connection_url,
                source_system=source_system,
                source_key=source_key,
                etag=response.headers.get("ETag") or (state or {}).get("etag"),
                last_modified=response.headers.get("Last-Modified") or (state or {}).get("last_modified"),
                last_checked_at=now_utc,
                last_success_at=now_utc,
                last_changed_at=now_utc if changed else (state or {}).get("last_changed_at"),
                last_content_hash=page_hash,
                consecutive_failures=0,
                last_error=None,
            )

            return {
                "status": "changed" if changed else "unchanged_body",
                "attempt": attempt,
                "retries": retries,
                "stale_after_minutes": stale_after_minutes,
                "ingestion": result,
            }
        except Exception as exc:  # noqa: BLE001 - we want to persist state on any failure.
            last_exception = exc
            if attempt < retries:
                sleep_for = backoffs[min(attempt - 1, len(backoffs) - 1)]
                sleep_fn(sleep_for)

    failures = previous_failures + 1
    error_text = str(last_exception) if last_exception else "Unknown crawler error"
    upsert_source_state(
        connection_url,
        source_system=source_system,
        source_key=source_key,
        etag=(state or {}).get("etag"),
        last_modified=(state or {}).get("last_modified"),
        last_checked_at=now_utc,
        last_success_at=(state or {}).get("last_success_at"),
        last_changed_at=(state or {}).get("last_changed_at"),
        last_content_hash=(state or {}).get("last_content_hash"),
        consecutive_failures=failures,
        last_error=error_text,
    )

    if webhook_url and failures >= alert_failure_threshold:
        stale_since = (state or {}).get("last_success_at")
        stale_note = "unknown"
        if isinstance(stale_since, datetime):
            stale_note = f"{int((now_utc - stale_since).total_seconds() // 60)} minutes"
        _send_webhook_alert(
            webhook_url,
            (
                "[Birthday Freebies] Starbucks watch failed "
                f"({failures} consecutive failures). "
                f"Last success age: {stale_note}. Error: {error_text}"
            ),
        )

    raise RuntimeError(f"Starbucks watch failed after {retries} attempts: {error_text}")


def get_starbucks_watch_health(
    connection_url: str,
    *,
    stale_after_minutes: int = 30,
) -> dict[str, object]:
    ensure_ingestion_tables(connection_url)
    state = fetch_source_state(
        connection_url,
        source_system="starbucks",
        source_key="rewards_terms_page",
    )

    now_utc = datetime.now(timezone.utc)
    stale_threshold = now_utc - timedelta(minutes=max(1, stale_after_minutes))

    if not state:
        return {
            "source": "starbucks",
            "status": "never_checked",
            "is_stale": True,
            "consecutive_failures": 0,
            "last_checked_at": None,
            "last_success_at": None,
            "last_changed_at": None,
            "last_error": None,
            "stale_after_minutes": stale_after_minutes,
        }

    last_success_at = state.get("last_success_at")
    # Ensure DB-fetched datetime has timezone info for safe comparison.
    if isinstance(last_success_at, datetime) and last_success_at.tzinfo is None:
        last_success_at = last_success_at.replace(tzinfo=timezone.utc)
    is_stale = not isinstance(last_success_at, datetime) or last_success_at < stale_threshold

    return {
        "source": "starbucks",
        "status": "ok" if not is_stale else "stale",
        "is_stale": is_stale,
        "consecutive_failures": int(state.get("consecutive_failures") or 0),
        "last_checked_at": state.get("last_checked_at"),
        "last_success_at": last_success_at,
        "last_changed_at": state.get("last_changed_at"),
        "last_error": state.get("last_error"),
        "stale_after_minutes": stale_after_minutes,
    }


def run_starbucks_watch_once_from_env(connection_url: str) -> dict[str, object]:
    region_code = os.getenv("STARBUCKS_INGEST_REGION", "bay_area")
    max_retries = int(os.getenv("STARBUCKS_WATCH_MAX_RETRIES", "3"))
    stale_after_minutes = int(os.getenv("STARBUCKS_WATCH_STALE_AFTER_MINUTES", "30"))
    alert_failure_threshold = int(os.getenv("STARBUCKS_WATCH_ALERT_FAILURE_THRESHOLD", "2"))
    backoff = _parse_backoff_seconds(os.getenv("STARBUCKS_WATCH_BACKOFF_SECONDS", "60,300,900"))
    webhook_url = os.getenv("STARBUCKS_ALERT_WEBHOOK_URL")

    return run_starbucks_watch_once(
        connection_url,
        region_code=region_code,
        max_retries=max_retries,
        retry_backoff_seconds=backoff,
        stale_after_minutes=stale_after_minutes,
        alert_failure_threshold=alert_failure_threshold,
        webhook_url=webhook_url,
    )
