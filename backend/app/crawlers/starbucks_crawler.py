import re
from dataclasses import dataclass
from typing import Callable

import httpx


STARBUCKS_REWARDS_TERMS_URL = "https://www.starbucks.com/rewards/terms/"


@dataclass(frozen=True)
class RawStarbucksOffer:
    source_key: str
    name_en: str
    category: str
    item_en: str
    member_en: str
    window_en: str
    note_en: str


def _fetch_starbucks_terms_html() -> str:
    # Single fetch point so tests can swap this behavior via fetch_html.
    response = httpx.get(STARBUCKS_REWARDS_TERMS_URL, timeout=20.0)
    response.raise_for_status()
    return response.text


def _flatten_html_to_text(html_content: str) -> str:
    # For a PoC parser we only need broad keyword detection, not full DOM extraction.
    without_scripts = re.sub(r"<script[\\s\\S]*?</script>", " ", html_content, flags=re.IGNORECASE)
    without_styles = re.sub(r"<style[\\s\\S]*?</style>", " ", without_scripts, flags=re.IGNORECASE)
    plain = re.sub(r"<[^>]+>", " ", without_styles)
    return re.sub(r"\\s+", " ", plain).strip().lower()


def crawl_starbucks_birthday_offers(fetch_html: Callable[[], str] | None = None) -> list[RawStarbucksOffer]:
    html_loader = fetch_html or _fetch_starbucks_terms_html
    text = _flatten_html_to_text(html_loader())

    has_birthday_keywords = "birthday" in text and ("reward" in text or "offer" in text)
    if not has_birthday_keywords:
        return []

    if "30" in text and "7" in text:
        # Keep the output stable for downstream idempotency hashing.
        window_en = "Green: same day | Gold: 7 days | Reserve: 30 days"
        note_en = "Window can vary by account tier; verify in-app before redeeming."
    else:
        window_en = "On birthday (check current rewards terms)."
        note_en = "Birthday offer terms can change and may vary by account status."

    return [
        RawStarbucksOffer(
            source_key="birthday_reward",
            name_en="Starbucks",
            category="drink",
            item_en="Any handcrafted drink or food item",
            member_en="Starbucks Rewards membership required",
            window_en=window_en,
            note_en=note_en,
        )
    ]
