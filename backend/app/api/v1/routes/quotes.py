from fastapi import APIRouter, HTTPException

from app.domain.compatibility_engine import validate_build
from app.domain.recommender import CATEGORY_ORDER, recommend_builds
from app.domain.sample_data import PARTS
from app.domain.schemas import CustomBuildPayload, QuoteItem, QuoteRequestPayload
from app.domain.scoring import score_build
from app.domain.store import delete_saved_quote, get_quote_bundle, get_quote_result, get_saved_quote, list_saved_quotes, save_quote


router = APIRouter()


def _part_by_id() -> dict[str, dict]:
    return {part["spec"]["id"]: part for part in PARTS}


def _item_reason(category: str, part: dict) -> str:
    spec = part["spec"]
    if category == "cpu" and spec.get("benchmark_score"):
        return f"CPU 벤치마크 {spec['benchmark_score']}점을 비교에 반영했습니다."
    if category == "gpu" and spec.get("benchmark_score"):
        return f"GPU 벤치마크 {spec['benchmark_score']}점과 VRAM {spec.get('vram_gb', 0)}GB를 반영했습니다."
    if category == "ram":
        return f"{spec.get('ram_type', 'RAM')} {spec.get('capacity_gb', 0)}GB 구성을 반영했습니다."
    if category == "psu":
        return f"{spec.get('watt', 0)}W 파워 용량을 반영했습니다."
    if category == "storage":
        return f"{spec.get('capacity_gb', 0)}GB 저장공간을 반영했습니다."
    return "사용자가 직접 선택한 부품입니다."


@router.post("/recommend")
def recommend_quote(payload: QuoteRequestPayload) -> dict:
    bundle = recommend_builds(payload)
    primary = bundle["primary"]
    return {
        "success": True,
        "data": {
            "quote_id": primary.quote_id,
            "request": bundle["request"],
            "summary": primary.summary,
            "total_price": primary.total_price,
            "score": round(primary.score, 2),
            "items": [item.model_dump() for item in primary.items],
            "checks": [check.model_dump() for check in primary.checks],
            "warnings": [check.message for check in primary.checks if check.status == "warn"],
            "generated_at": bundle["generated_at"],
        },
        "message": "견적을 생성했습니다.",
    }


@router.post("/custom-evaluate")
def evaluate_custom_build(payload: CustomBuildPayload) -> dict:
    parts_by_id = _part_by_id()
    missing_categories = [category for category in CATEGORY_ORDER if not payload.selected_part_ids.get(category)]
    if missing_categories:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "MISSING_CUSTOM_PARTS",
                "message": "전문가 견적의 필수 부품을 모두 선택해 주세요.",
                "details": missing_categories,
            },
        )

    build: dict[str, dict] = {}
    for category in CATEGORY_ORDER:
        part_id = payload.selected_part_ids[category]
        part = parts_by_id.get(part_id)
        if part is None or part["category"] != category:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INVALID_CUSTOM_PART",
                    "message": f"{category} 부품 선택값이 올바르지 않습니다.",
                    "details": [part_id],
                },
            )
        build[category] = part

    checks = validate_build(build)
    total_price = sum(part["price"] for part in build.values())
    score = score_build(build, payload.purpose, payload.budget)
    items = [
        QuoteItem(
            category=category,
            brand=build[category]["brand"],
            model=build[category]["model"],
            price=build[category]["price"],
            reason=_item_reason(category, build[category]),
        )
        for category in CATEGORY_ORDER
    ]

    return {
        "success": True,
        "data": {
            "quote_id": "expert_custom",
            "total_price": total_price,
            "score": round(score, 2),
            "summary": f"전문가가 직접 지정한 부품 조합입니다. 총액은 {total_price:,}원입니다.",
            "items": [item.model_dump() for item in items],
            "checks": [check.model_dump() for check in checks],
            "warnings": [check.message for check in checks if check.status == "warn"],
            "diff_points": [],
        },
        "message": "전문가 견적을 평가했습니다.",
    }


@router.get("/saved")
def get_saved_quotes() -> dict:
    return {
        "success": True,
        "data": {"items": list_saved_quotes()},
        "message": "저장한 견적을 불러왔습니다.",
    }


@router.post("/{quote_id}/save")
def save_quote_result(quote_id: str) -> dict:
    saved = save_quote(quote_id)
    if saved is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    return {
        "success": True,
        "data": saved,
        "message": "견적을 보관함에 저장했습니다.",
    }


@router.delete("/saved/{quote_id}")
def remove_saved_quote(quote_id: str) -> dict:
    deleted = delete_saved_quote(quote_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Saved quote not found")
    return {
        "success": True,
        "data": {"quote_id": quote_id},
        "message": "저장한 견적을 삭제했습니다.",
    }


@router.get("/{quote_id}")
def get_quote_detail(quote_id: str) -> dict:
    found = get_quote_result(quote_id)
    if found is None:
        saved = get_saved_quote(quote_id)
        if saved is None:
            raise HTTPException(status_code=404, detail="Quote not found")
        return {
            "success": True,
            "data": saved,
            "message": "저장한 견적 상세를 불러왔습니다.",
        }
    bundle, quote = found
    return {
        "success": True,
        "data": {
            "quote_id": quote.quote_id,
            "request": bundle["request"],
            "summary": quote.summary,
            "total_price": quote.total_price,
            "score": round(quote.score, 2),
            "items": [item.model_dump() for item in quote.items],
            "checks": [check.model_dump() for check in quote.checks],
            "warnings": [check.message for check in quote.checks if check.status == "warn"],
            "generated_at": bundle["generated_at"],
        },
        "message": "견적 상세를 불러왔습니다.",
    }


@router.get("/{quote_id}/validation")
def get_quote_validation(quote_id: str) -> dict:
    bundle = get_quote_bundle(quote_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    primary = bundle["primary"]
    return {
        "success": True,
        "data": {
            "quote_id": quote_id,
            "checks": [check.model_dump() for check in primary.checks],
            "warnings": [check.message for check in primary.checks if check.status == "warn"],
        },
        "message": "호환성 검증 결과를 불러왔습니다.",
    }


@router.get("/{quote_id}/alternatives")
def get_quote_alternatives(quote_id: str) -> dict:
    bundle = get_quote_bundle(quote_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    return {
        "success": True,
        "data": {
            "quote_id": quote_id,
            "alternatives": [alt.model_dump() for alt in bundle["alternatives"]],
        },
        "message": "대안 견적을 불러왔습니다.",
    }
