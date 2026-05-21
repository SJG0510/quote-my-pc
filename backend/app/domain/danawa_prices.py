from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path


DANAWA_PRICE_DIR = Path(__file__).resolve().parents[2] / "data" / "danawa_prices"


def _normalize(value: object) -> str:
    text = str(value or "").lower()
    return re.sub(r"[^0-9a-z가-힣]+", "", text)


def _model_keys(component_type: str, brand: str, model: str) -> list[tuple[str, str, str]]:
    normalized_type = _normalize(component_type)
    normalized_brand = _normalize(brand)
    normalized_model = _normalize(model)
    keys = [(normalized_type, normalized_brand, normalized_model)]

    if normalized_brand and normalized_model.startswith(normalized_brand):
        stripped_model = normalized_model[len(normalized_brand) :]
        if stripped_model:
            keys.append((normalized_type, normalized_brand, stripped_model))

    return keys


def _price_from_row(row: dict[str, str]) -> int:
    try:
        return int(float(str(row.get("price_krw") or "").replace(",", "").strip()))
    except ValueError:
        return 0


def _row_to_price(row: dict[str, str], inferred_type: str) -> dict | None:
    price = _price_from_row(row)
    brand = row.get("brand", "")
    model = row.get("model", "")
    if price <= 0 or not brand or not model:
        return None

    return {
        "component_type": row.get("type") or inferred_type,
        "brand": brand,
        "model": model,
        "price_krw": price,
        "product_name": row.get("product_name", ""),
        "danawa_url": row.get("danawa_url", ""),
        "scraped_at": row.get("scraped_at", ""),
    }


@lru_cache(maxsize=1)
def _load_price_index() -> dict[tuple[str, str, str], dict]:
    index: dict[tuple[str, str, str], dict] = {}
    if not DANAWA_PRICE_DIR.exists():
        return index

    for path in DANAWA_PRICE_DIR.glob("*_prices.csv"):
        inferred_type = path.stem.removesuffix("_prices")
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as file:
                rows = csv.DictReader(file)
                for row in rows:
                    price = _row_to_price(row, inferred_type)
                    if not price:
                        continue
                    for key in _model_keys(price["component_type"], price["brand"], price["model"]):
                        previous = index.get(key)
                        if not previous or price["scraped_at"] >= previous.get("scraped_at", ""):
                            index[key] = price
        except OSError:
            continue

    return index


def get_danawa_price(component_type: str, brand: str, model: str) -> dict | None:
    index = _load_price_index()
    for key in _model_keys(component_type, brand, model):
        price = index.get(key)
        if price:
            return price
    return None
