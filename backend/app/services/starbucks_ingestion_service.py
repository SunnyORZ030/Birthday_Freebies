import hashlib
import json
from datetime import datetime, timezone
from typing import Callable

from app.crawlers.starbucks_crawler import RawStarbucksOffer, crawl_starbucks_birthday_offers
from app.repositories.ingestion_repository import (
    ensure_ingestion_tables,
    fetch_promoted_mapping,
    mark_staging_promoted,
    upsert_promoted_mapping,
    upsert_staging_row,
)
from app.services.freebies_service import (
    FreebieCreationError,
    create_freebie_service,
    update_freebie_service,
)


def _normalize_offer(
    offer: RawStarbucksOffer,
    *,
    region_code: str,
    sort_order: int,
) -> dict:
    # Keep an API-contract-shaped payload so promotion and test assertions stay stable.
    return {
        "region_code": region_code,
        "category": offer.category,
        "sort_order": sort_order,
        "source_system": "starbucks",
        "source_key": f"{offer.source_key}::{region_code}",
        "zh": {
            "name": "星巴克",
            "item": "任一手工飲品或食品",
            "member": "需要 Starbucks Rewards 會員",
            "window": "Green: 當天 | Gold: 7 天 | Reserve: 30 天",
            "note": "生日優惠可能依帳號等級調整，請以 APP 條款為準。",
        },
        "en": {
            "name": offer.name_en,
            "item": offer.item_en,
            "member": offer.member_en,
            "window": offer.window_en,
            "note": offer.note_en,
        },
    }


def _payload_hash(payload: dict) -> str:
    # Hash over canonical JSON is used as the change detector for reruns.
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _to_service_text(text: dict[str, str]) -> dict[str, str]:
    # Convert crawler/window naming into existing service-layer text contract.
    return {
        "name": text["name"],
        "item": text["item"],
        "member": text["member"],
        "redemption_window": text["window"],
        "note": text.get("note", ""),
    }


def run_starbucks_ingestion(
    connection_url: str,
    *,
    region_code: str,
    fetch_html: Callable[[], str] | None = None,
) -> dict[str, int]:
    # Ensure tables exist so one-command PoC runs work in fresh local environments.
    ensure_ingestion_tables(connection_url)

    offers = crawl_starbucks_birthday_offers(fetch_html=fetch_html)
    normalized_payloads = [
        _normalize_offer(offer, region_code=region_code, sort_order=index + 1)
        for index, offer in enumerate(offers)
    ]

    counters = {
        "discovered": len(normalized_payloads),
        "staged": 0,
        "promoted": 0,
        "skipped_unchanged": 0,
    }

    for payload in normalized_payloads:
        content_hash = _payload_hash(payload)
        source_system = payload["source_system"]
        source_key = payload["source_key"]

        upsert_staging_row(
            connection_url,
            source_system=source_system,
            source_key=source_key,
            region_code=payload["region_code"],
            category=payload["category"],
            payload=payload,
            content_hash=content_hash,
            fetched_at=datetime.now(timezone.utc),
        )
        counters["staged"] += 1

        mapping = fetch_promoted_mapping(
            connection_url,
            source_system=source_system,
            source_key=source_key,
        )

        # Same source key + same content hash means no DB promotion is needed.
        if mapping and mapping[1] == content_hash:
            counters["skipped_unchanged"] += 1
            continue

        try:
            if mapping:
                # Existing mapping: update in place to preserve stable freebie identity.
                freebie_id = mapping[0]
                update_freebie_service(
                    connection_url,
                    freebie_id=freebie_id,
                    category=payload["category"],
                    sort_order=payload["sort_order"],
                    is_active=True,
                    zh_text=_to_service_text(payload["zh"]),
                    en_text=_to_service_text(payload["en"]),
                )
            else:
                # First promotion for this source key: create new freebie row.
                result = create_freebie_service(
                    connection_url,
                    region_code=payload["region_code"],
                    category=payload["category"],
                    sort_order=payload["sort_order"],
                    zh_text=_to_service_text(payload["zh"]),
                    en_text=_to_service_text(payload["en"]),
                )
                freebie_id = result["id"]
        except FreebieCreationError as exc:
            raise FreebieCreationError(f"Starbucks ingestion promotion failed: {exc}") from exc

        upsert_promoted_mapping(
            connection_url,
            source_system=source_system,
            source_key=source_key,
            freebie_id=freebie_id,
            content_hash=content_hash,
        )
        mark_staging_promoted(
            connection_url,
            source_system=source_system,
            source_key=source_key,
            freebie_id=freebie_id,
        )
        counters["promoted"] += 1

    return counters