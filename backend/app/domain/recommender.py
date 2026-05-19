from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from app.domain.compatibility_engine import is_valid, validate_build
from app.domain.sample_data import PARTS, are_pair_compatible
from app.domain.schemas import CompatibilityCheck, QuoteItem, QuoteRequestPayload, QuoteResult
from app.domain.scoring import score_build
from app.domain.store import save_quote_bundle


CATEGORY_ORDER = ["cpu", "cooler", "motherboard", "ram", "gpu", "storage", "psu", "case"]
MAX_CANDIDATE_BUILDS = 700
DEFAULT_CATEGORY_LIMITS = {
    "cpu": 14,
    "cooler": 4,
    "motherboard": 7,
    "ram": 16,
    "gpu": 14,
    "storage": 6,
    "psu": 7,
    "case": 6,
}


def _group_parts() -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {category: [] for category in CATEGORY_ORDER}
    for part in PARTS:
        grouped[part["category"]].append(part)
    return grouped


def _candidate_rank(part: dict, purpose: str, budget: int) -> float:
    score = part["scores"][purpose]
    affordability_penalty = (part["price"] / max(budget, 1)) * 28
    return score - affordability_penalty


def _linked_cpu_price(integrated_gpu: dict) -> int:
    cpu_id = integrated_gpu["spec"].get("requires_cpu_id")
    for part in PARTS:
        if part["category"] == "cpu" and part["spec"]["id"] == cpu_id:
            return part["price"]
    return integrated_gpu["price"]


def _pair_allows(part_a: dict, part_b: dict) -> bool:
    pair_value = are_pair_compatible(part_a["spec"]["id"], part_b["spec"]["id"])
    return pair_value is not False


def _representatives(pool: list[dict], category: str, purpose: str) -> list[dict]:
    selected: list[dict] = []

    def add(items: list[dict]) -> None:
        selected.extend(items)

    if category == "cpu":
        sockets = sorted({part["spec"].get("socket", "") for part in pool})
        for socket in sockets:
            same_socket = [part for part in pool if part["spec"].get("socket") == socket]
            add(sorted(same_socket, key=lambda part: part["price"])[:2])
            add(sorted(same_socket, key=lambda part: (-part["scores"][purpose], part["price"]))[:2])
    elif category == "motherboard":
        keys = sorted({(part["spec"].get("socket", ""), part["spec"].get("ram_type", "")) for part in pool})
        for socket, ram_type in keys:
            same_key = [part for part in pool if part["spec"].get("socket") == socket and part["spec"].get("ram_type") == ram_type]
            add(sorted(same_key, key=lambda part: part["price"])[:2])
    elif category == "ram":
        type_order = {"DDR5": 0, "DDR4": 1, "DDR3": 2}
        ram_types = sorted({part["spec"].get("ram_type", "") for part in pool}, key=lambda item: type_order.get(item, 9))
        for ram_type in ram_types:
            same_type = [part for part in pool if part["spec"].get("ram_type") == ram_type]
            add(sorted(same_type, key=lambda part: part["price"])[:3])
            for target in [16, 32, 64, 128]:
                fit = [part for part in same_type if part["spec"].get("capacity_gb", 0) >= target]
                add(sorted(fit, key=lambda part: (part["price"], -part["scores"][purpose]))[:1])
    elif category == "storage":
        ssds = [part for part in pool if part["spec"].get("is_ssd")]
        add(sorted(ssds, key=lambda part: part["price"])[:3])
        for target in [500, 1000, 2000, 4000]:
            fit = [part for part in ssds if part["spec"].get("capacity_gb", 0) >= target]
            add(sorted(fit, key=lambda part: (part["price"], -part["scores"][purpose]))[:1])
    elif category == "psu":
        for target in [500, 600, 650, 750, 850, 1000, 1200]:
            fit = [part for part in pool if part["spec"].get("watt", 0) >= target]
            add(sorted(fit, key=lambda part: (part["price"], part["spec"].get("watt", 0)))[:1])
    else:
        add(sorted(pool, key=lambda part: part["price"])[:4])

    return selected


def _select_candidates(parts: list[dict], category: str, payload: QuoteRequestPayload) -> list[dict]:
    brand_filtered = [part for part in parts if _brand_matches(part, payload.preferred_brands)]
    if not brand_filtered:
        return []

    affordable = [part for part in brand_filtered if part["price"] <= payload.budget]
    pool = affordable or brand_filtered
    if category == "ram":
        usable_ram = [part for part in pool if part["spec"].get("capacity_gb", 0) >= 8]
        if usable_ram:
            pool = usable_ram
    if category == "storage":
        usable_storage = [part for part in pool if part["spec"].get("capacity_gb", 0) >= 240]
        if usable_storage:
            pool = usable_storage
    if category == "gpu" and payload.purpose != "office":
        discrete_pool = [part for part in pool if not part["spec"].get("integrated")]
        quality_discrete_pool = [
            part
            for part in discrete_pool
            if part["spec"].get("benchmark_score", 0) >= 50 and part["spec"].get("vram_gb", 0) >= 4
        ]
        if quality_discrete_pool:
            discrete_pool = quality_discrete_pool
        if discrete_pool:
            pool = discrete_pool
    limit = DEFAULT_CATEGORY_LIMITS[category]

    # Keep cheap, spec-representative, and purpose-ranked parts. The dataset is
    # broad enough that pure score ranking can drop the only matching RAM/socket tier.
    cheapest = sorted(pool, key=lambda part: part["price"])[:4]
    representative = _representatives(pool, category, payload.purpose)
    if category == "cpu" and payload.purpose == "office":
        office_igpu = [
            part
            for part in pool
            if part["spec"].get("igpu") and part["spec"].get("compatible_motherboard_ids")
        ]
        cheapest = [
            *sorted(office_igpu, key=lambda part: part["price"])[:8],
            *cheapest,
            *sorted(office_igpu, key=lambda part: (-part["scores"][payload.purpose], part["price"]))[:4],
        ]
    if category == "gpu" and payload.purpose == "office":
        cheapest = [
            *cheapest,
            *sorted((part for part in pool if part["spec"].get("integrated")), key=_linked_cpu_price)[:8],
        ]
    if category == "gpu" and payload.purpose == "deep_learning":
        cheapest = [
            *cheapest,
            *sorted(pool, key=lambda part: (-part["spec"].get("vram_gb", 0), part["price"]))[:3],
        ]
    if category == "psu" and payload.purpose == "deep_learning":
        cheapest = [
            *cheapest,
            *sorted(pool, key=lambda part: (-part["spec"].get("watt", 0), part["price"]))[:3],
        ]
    if category == "case" and payload.purpose == "deep_learning":
        cheapest = [
            *cheapest,
            *sorted(pool, key=lambda part: (-part["spec"].get("max_gpu_length", 0), part["price"]))[:3],
        ]
    ranked = sorted(pool, key=lambda part: (-_candidate_rank(part, payload.purpose, payload.budget), part["price"]))[:limit]

    selected: list[dict] = []
    seen: set[str] = set()
    for part in [*cheapest, *representative, *ranked]:
        key = f"{part['category']}::{part['brand']}::{part['model']}"
        if key in seen:
            continue
        selected.append(part)
        seen.add(key)
        if len(selected) >= limit:
            break
    return selected


def _sort_for_search(parts: list[dict], category: str, payload: QuoteRequestPayload) -> list[dict]:
    purpose = payload.purpose
    if category == "cpu" and purpose == "office":
        return sorted(parts, key=lambda part: (part["price"], -part["scores"][purpose]))
    if category == "ram" and purpose in {"video_edit", "3d", "deep_learning"}:
        return sorted(parts, key=lambda part: (-part["spec"].get("capacity_gb", 0), part["price"]))
    if category == "storage" and purpose in {"video_edit", "3d", "deep_learning"}:
        return sorted(parts, key=lambda part: (-part["spec"].get("capacity_gb", 0), -part["scores"][purpose], part["price"]))
    if category == "gpu":
        return sorted(parts, key=lambda part: (-part["scores"][purpose], -part["spec"].get("vram_gb", 0), part["price"]))
    if category == "cpu":
        return sorted(parts, key=lambda part: (-part["scores"][purpose], part["price"]))
    return sorted(parts, key=lambda part: (part["price"], -part["scores"][purpose]))


def _cpu_motherboard_ok(cpu: dict, motherboard: dict) -> bool:
    cpu_spec = cpu["spec"]
    board_spec = motherboard["spec"]
    return (
        cpu_spec["socket"] == board_spec["socket"]
        and (not cpu_spec.get("compatible_motherboard_ids") or board_spec["id"] in cpu_spec["compatible_motherboard_ids"])
        and _pair_allows(cpu, motherboard)
    )


def _ram_motherboard_ok(ram: dict, motherboard: dict) -> bool:
    ram_spec = ram["spec"]
    board_spec = motherboard["spec"]
    return (
        ram_spec["ram_type"] == board_spec["ram_type"]
        and (not ram_spec.get("compatible_motherboard_ids") or board_spec["id"] in ram_spec["compatible_motherboard_ids"])
        and _pair_allows(ram, motherboard)
    )


def _cooler_cpu_ok(cooler: dict, cpu: dict) -> bool:
    cooler_spec = cooler["spec"]
    cpu_spec = cpu["spec"]
    return (
        cpu_spec["socket"] in cooler_spec["supported_sockets"]
        and cooler_spec["cooling_tdp"] >= cpu_spec["tdp"]
        and (not cpu_spec.get("compatible_cooler_ids") or cooler_spec["id"] in cpu_spec["compatible_cooler_ids"])
        and _pair_allows(cpu, cooler)
    )


def _storage_motherboard_ok(storage: dict, motherboard: dict) -> bool:
    storage_spec = storage["spec"]
    board_spec = motherboard["spec"]
    return (
        (not storage_spec.get("compatible_motherboard_ids") or board_spec["id"] in storage_spec["compatible_motherboard_ids"])
        and _pair_allows(storage, motherboard)
    )


def _case_base_ok(case: dict, motherboard: dict, cooler: dict) -> bool:
    case_spec = case["spec"]
    board_spec = motherboard["spec"]
    cooler_spec = cooler["spec"]
    air_ok = cooler_spec["height_mm"] == 0 or cooler_spec["height_mm"] <= case_spec["max_cpu_cooler_height"]
    radiator_ok = cooler_spec["radiator_mm"] == 0 or cooler_spec["radiator_mm"] <= case_spec["max_radiator_length"]
    return (
        board_spec["form_factor"] in case_spec["supported_mobo_form_factors"]
        and air_ok
        and radiator_ok
        and _pair_allows(motherboard, case)
        and _pair_allows(cooler, case)
    )


def _gpu_cpu_ok(gpu: dict, cpu: dict) -> bool:
    required_cpu_id = gpu["spec"].get("requires_cpu_id")
    return not required_cpu_id or required_cpu_id == cpu["spec"]["id"]


def _gpu_case_ok(gpu: dict, case: dict, motherboard: dict) -> bool:
    gpu_spec = gpu["spec"]
    if gpu_spec.get("integrated"):
        return True
    case_spec = case["spec"]
    board_spec = motherboard["spec"]
    return (
        gpu_spec["length_mm"] <= min(case_spec["max_gpu_length"], board_spec["max_gpu_length"])
        and (not gpu_spec.get("compatible_case_ids") or case_spec["id"] in gpu_spec["compatible_case_ids"])
        and _pair_allows(gpu, case)
    )


def _psu_ok(psu: dict, gpu: dict, cpu: dict, case: dict) -> bool:
    psu_spec = psu["spec"]
    gpu_spec = gpu["spec"]
    cpu_spec = cpu["spec"]
    case_spec = case["spec"]
    estimated_draw = cpu_spec["tdp"] + gpu_spec["power_draw"] + 180
    recommended_watt = max(gpu_spec.get("recommended_psu_w", 0), int(estimated_draw * 1.25))
    return (
        psu_spec["watt"] >= recommended_watt
        and psu_spec["form_factor"] in case_spec["supported_psu_form_factors"]
        and psu_spec["length_mm"] <= case_spec["max_psu_length"]
        and (gpu_spec.get("integrated") or not gpu_spec.get("compatible_psu_ids") or psu_spec["id"] in gpu_spec["compatible_psu_ids"])
        and _pair_allows(psu, case)
        and (gpu_spec.get("integrated") or _pair_allows(gpu, psu))
    )


def _brand_matches(part: dict, preferred_brands: list[str]) -> bool:
    if not preferred_brands:
        return True
    category = part["category"]
    if category in {"cpu", "gpu"}:
        normalized_brand = part["brand"].lower()
        normalized_preferred = {brand.lower() for brand in preferred_brands}
        if normalized_brand == "nvidia":
            normalized_brand = "nvidia"
        if normalized_brand == "nvidia" and "nvidia" in normalized_preferred:
            return True
        return normalized_brand in normalized_preferred
    return True


def _build_summary(purpose: str, build: dict, total_price: int) -> str:
    gpu = build["gpu"]["model"]
    cpu = build["cpu"]["model"]
    purpose_labels = {
        "gaming": "게임 중심",
        "office": "사무 중심",
        "video_edit": "영상 편집 중심",
        "3d": "3D 작업 중심",
        "deep_learning": "딥러닝/렌더링 중심",
    }
    return f"{purpose_labels[purpose]} 구성으로 {cpu} + {gpu} 조합을 사용했고, 총액은 {total_price:,}원입니다."


def _build_diff_points(primary_build: dict, alternative_build: dict) -> list[str]:
    points: list[str] = []
    for category in ["cpu", "gpu", "ram", "storage"]:
        if primary_build[category]["model"] != alternative_build[category]["model"]:
            points.append(f"{category.upper()} 변경: {alternative_build[category]['model']}")
    return points[:3]


def _checks_to_reason_map(checks: list[CompatibilityCheck]) -> dict[str, str]:
    return {
        "cpu": "목적 대비 연산 성능을 우선 배치했습니다.",
        "cooler": "CPU 발열을 감당할 수 있는 쿨러를 선택했습니다.",
        "motherboard": "CPU 소켓과 메모리 규격에 맞는 보드를 골랐습니다.",
        "ram": "목적에 맞는 메모리 용량과 규격을 반영했습니다.",
        "gpu": "그래픽 성능과 예산 균형을 고려했습니다.",
        "storage": "시스템 반응성과 작업 공간을 함께 고려했습니다.",
        "psu": next((check.message for check in checks if check.rule == "psu_capacity"), "전력 여유를 고려했습니다."),
        "case": next((check.message for check in checks if check.rule == "gpu_length"), "부품 장착 공간을 고려했습니다."),
    }


def _item_reason(category: str, part: dict, fallback: str) -> str:
    spec = part["spec"]
    if category in {"cpu", "gpu", "ram", "storage"} and spec.get("benchmark_score"):
        return f"벤치마크 데이터셋 기준 성능 점수 {spec['benchmark_score']}점을 반영했습니다."
    return fallback


def recommend_builds(payload: QuoteRequestPayload) -> dict:
    grouped = _group_parts()
    grouped = {
        category: _select_candidates(parts, category, payload)
        for category, parts in grouped.items()
    }
    grouped = {
        category: _sort_for_search(parts, category, payload)
        for category, parts in grouped.items()
    }

    if any(not parts for parts in grouped.values()):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "NO_COMPATIBLE_BUILD",
                "message": "입력 조건에서 호환 가능한 조합을 찾지 못했습니다.",
                "details": ["예산을 조금 높이거나 선호 브랜드 조건을 줄여 보세요."],
            },
        )

    candidate_builds: list[dict] = []
    for cpu in grouped["cpu"]:
        if len(candidate_builds) >= MAX_CANDIDATE_BUILDS:
            break
        for motherboard in grouped["motherboard"]:
            if len(candidate_builds) >= MAX_CANDIDATE_BUILDS:
                break
            if not _cpu_motherboard_ok(cpu, motherboard):
                continue
            for cooler in grouped["cooler"]:
                if len(candidate_builds) >= MAX_CANDIDATE_BUILDS:
                    break
                if not _cooler_cpu_ok(cooler, cpu):
                    continue
                for ram in grouped["ram"]:
                    if len(candidate_builds) >= MAX_CANDIDATE_BUILDS:
                        break
                    if not _ram_motherboard_ok(ram, motherboard):
                        continue
                    for storage in grouped["storage"]:
                        if len(candidate_builds) >= MAX_CANDIDATE_BUILDS:
                            break
                        if not _storage_motherboard_ok(storage, motherboard):
                            continue
                        base_price = sum(part["price"] for part in [cpu, motherboard, cooler, ram, storage])
                        if base_price > payload.budget:
                            continue
                        for case in grouped["case"]:
                            if len(candidate_builds) >= MAX_CANDIDATE_BUILDS:
                                break
                            if not _case_base_ok(case, motherboard, cooler):
                                continue
                            for gpu in grouped["gpu"]:
                                if len(candidate_builds) >= MAX_CANDIDATE_BUILDS:
                                    break
                                if not _gpu_cpu_ok(gpu, cpu) or not _gpu_case_ok(gpu, case, motherboard):
                                    continue
                                for psu in grouped["psu"]:
                                    if len(candidate_builds) >= MAX_CANDIDATE_BUILDS:
                                        break
                                    if not _psu_ok(psu, gpu, cpu, case):
                                        continue

                                    build = {
                                        "cpu": cpu,
                                        "cooler": cooler,
                                        "motherboard": motherboard,
                                        "ram": ram,
                                        "gpu": gpu,
                                        "storage": storage,
                                        "psu": psu,
                                        "case": case,
                                    }
                                    total_price = sum(part["price"] for part in build.values())
                                    if total_price > payload.budget:
                                        continue

                                    checks = validate_build(build)
                                    if not is_valid(checks):
                                        continue

                                    candidate_builds.append(
                                        {
                                            "build": build,
                                            "checks": checks,
                                            "total_price": total_price,
                                            "score": score_build(build, payload.purpose, payload.budget),
                                        }
                                    )

    if not candidate_builds:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "NO_COMPATIBLE_BUILD",
                "message": "입력 조건에서 호환 가능한 조합을 찾지 못했습니다.",
                "details": ["예산을 조금 높이거나 선호 브랜드 조건을 줄여 보세요."],
            },
        )

    ranked = sorted(candidate_builds, key=lambda item: (-item["score"], item["total_price"]))[:5]
    quote_results: list[QuoteResult] = []

    for index, item in enumerate(ranked, start=1):
        build = item["build"]
        checks = item["checks"]
        reasons = _checks_to_reason_map(checks)
        quote_id = f"qt_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{index}"
        quote_results.append(
            QuoteResult(
                quote_id=quote_id,
                total_price=item["total_price"],
                score=item["score"],
                summary=_build_summary(payload.purpose, build, item["total_price"]),
                items=[
                    QuoteItem(
                        category=category,
                        brand=build[category]["brand"],
                        model=build[category]["model"],
                        price=build[category]["price"],
                        reason=_item_reason(category, build[category], reasons[category]),
                    )
                    for category in CATEGORY_ORDER
                ],
                checks=checks,
            )
        )

    primary_build = ranked[0]["build"]
    for result, ranked_item in zip(quote_results[1:], ranked[1:], strict=False):
        result.diff_points = _build_diff_points(primary_build, ranked_item["build"])

    bundle = {
        "request": payload.model_dump(),
        "primary": quote_results[0],
        "alternatives": quote_results[1:],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    save_quote_bundle([result.quote_id for result in quote_results], bundle)
    return bundle
