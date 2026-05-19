from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
import json
from pathlib import Path

from app.domain.schemas import QuoteResult


QUOTE_STORE: dict[str, dict] = {}
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SAVED_QUOTES_FILE = DATA_DIR / "saved_quotes.json"
SAVED_QUOTES: dict[str, dict] = {}


def _load_saved_quotes() -> None:
    if not SAVED_QUOTES_FILE.exists():
        return
    try:
        SAVED_QUOTES.update(json.loads(SAVED_QUOTES_FILE.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        SAVED_QUOTES.clear()


def _persist_saved_quotes() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SAVED_QUOTES_FILE.write_text(json.dumps(SAVED_QUOTES, ensure_ascii=False, indent=2), encoding="utf-8")


_load_saved_quotes()


def save_quote_bundle(quote_ids: Iterable[str], bundle: dict) -> None:
    for quote_id in quote_ids:
        QUOTE_STORE[quote_id] = bundle


def get_quote_bundle(quote_id: str) -> dict | None:
    return QUOTE_STORE.get(quote_id)


def get_quote_result(quote_id: str) -> tuple[dict, QuoteResult] | None:
    bundle = get_quote_bundle(quote_id)
    if bundle is None:
        return None

    candidates = [bundle["primary"], *bundle["alternatives"]]
    for quote in candidates:
        if quote.quote_id == quote_id:
            return bundle, quote
    return None


def save_quote(quote_id: str) -> dict | None:
    found = get_quote_result(quote_id)
    if found is None:
        return None

    bundle, quote = found
    saved = {
        "quote_id": quote.quote_id,
        "request": bundle["request"],
        "summary": quote.summary,
        "total_price": quote.total_price,
        "score": round(quote.score, 2),
        "items": [item.model_dump() for item in quote.items],
        "checks": [check.model_dump() for check in quote.checks],
        "warnings": [check.message for check in quote.checks if check.status == "warn"],
        "generated_at": bundle["generated_at"],
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    SAVED_QUOTES[quote.quote_id] = saved
    _persist_saved_quotes()
    return saved


def list_saved_quotes() -> list[dict]:
    return sorted(SAVED_QUOTES.values(), key=lambda quote: quote["saved_at"], reverse=True)


def get_saved_quote(quote_id: str) -> dict | None:
    return SAVED_QUOTES.get(quote_id)


def delete_saved_quote(quote_id: str) -> bool:
    if quote_id not in SAVED_QUOTES:
        return False
    del SAVED_QUOTES[quote_id]
    _persist_saved_quotes()
    return True
