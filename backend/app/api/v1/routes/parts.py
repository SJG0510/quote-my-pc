from fastapi import APIRouter

from app.domain.sample_data import PURPOSE_PRESETS, get_available_brands


router = APIRouter()


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
