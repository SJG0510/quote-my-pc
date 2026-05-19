from fastapi import APIRouter, HTTPException

from app.domain.recommender import recommend_builds
from app.domain.schemas import QuoteRequestPayload
from app.domain.store import delete_saved_quote, get_quote_bundle, get_quote_result, get_saved_quote, list_saved_quotes, save_quote


router = APIRouter()


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
