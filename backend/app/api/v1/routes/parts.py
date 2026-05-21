from fastapi import APIRouter

from app.domain.sample_data import PARTS, PURPOSE_PRESETS, get_available_brands


router = APIRouter()


def _part_option(part: dict) -> dict:
    spec = part["spec"]
    return {
        "id": spec["id"],
        "category": part["category"],
        "brand": part["brand"],
        "model": part["model"],
        "price": part["price"],
        "benchmark_score": spec.get("benchmark_score"),
        "spec": {
            key: value
            for key, value in spec.items()
            if key
            in {
                "socket",
                "ram_type",
                "capacity_gb",
                "speed_mhz",
                "vram_gb",
                "watt",
                "form_factor",
                "interface",
                "integrated",
                "recommended_psu_w",
            }
        },
    }


@router.get("/filters")
def get_filters() -> dict:
    return {
        "success": True,
        "data": {
            "brands": get_available_brands(),
            "categories": ["cpu", "cooler", "motherboard", "ram", "gpu", "psu", "case", "storage"],
            "purpose_presets": PURPOSE_PRESETS,
        },
        "message": "필터 목록을 불러왔습니다.",
    }


@router.get("/catalog")
def get_parts_catalog() -> dict:
    grouped: dict[str, list[dict]] = {}
    for part in PARTS:
        grouped.setdefault(part["category"], []).append(_part_option(part))

    for category, items in grouped.items():
        grouped[category] = sorted(
            items,
            key=lambda item: (
                item["price"] <= 0,
                item["price"],
                item["brand"].lower(),
                item["model"].lower(),
            ),
        )

    return {
        "success": True,
        "data": {"parts": grouped},
        "message": "부품 카탈로그를 불러왔습니다.",
    }
