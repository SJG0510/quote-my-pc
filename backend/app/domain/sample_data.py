from __future__ import annotations

import csv
from pathlib import Path


DATASET_DIR = Path(__file__).resolve().parents[1] / "data" / "pc_dataset_augmented_price_compat_2026_05_csv"

PURPOSE_PRESETS = [
    {"key": "office", "label": "사무/인강/웹서핑", "budget_min": 500_000, "budget_max": 1_000_000},
    {"key": "gaming", "label": "캐주얼/온라인 게이밍", "budget_min": 900_000, "budget_max": 1_500_000},
    {"key": "video_edit", "label": "고사양 게이밍/영상 편집", "budget_min": 1_500_000, "budget_max": 2_500_000},
    {"key": "3d", "label": "하이엔드 3D/4K 게이밍", "budget_min": 2_500_000, "budget_max": 5_000_000},
    {"key": "deep_learning", "label": "딥러닝/초고해상도 렌더링", "budget_min": 5_000_000, "budget_max": 10_000_000},
]


def _read_csv(name: str) -> list[dict[str, str]]:
    path = DATASET_DIR / name
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _to_int(value: object, default: int = 0) -> int:
    try:
        text = str(value or "").strip().replace(",", "")
        return int(float(text)) if text else default
    except ValueError:
        return default


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value or "").strip().replace(",", "")
        return float(text) if text else default
    except ValueError:
        return default


def _split_ids(value: object) -> list[str]:
    return [item.strip() for item in str(value or "").split("|") if item.strip()]


def _benchmark(row: dict[str, str]) -> float:
    benchmark = _to_float(row.get("Benchmark"))
    if benchmark > 0:
        return benchmark
    rank = _to_int(row.get("Rank"), 9999)
    return max(1.0, 120.0 - rank * 0.2)


def _bounded_score(value: float, maximum: float = 180.0) -> float:
    return round(max(1.0, min(100.0, value / maximum * 100.0)), 2)


def _cpu_tdp(model: str, row_tdp: int) -> int:
    if row_tdp > 0:
        return row_tdp
    upper = model.upper()
    if any(token in upper for token in ["I9", "RYZEN 9", "THREADRIPPER"]):
        return 170
    if any(token in upper for token in ["I7", "RYZEN 7"]):
        return 125
    if any(token in upper for token in ["I5", "RYZEN 5"]):
        return 90
    return 65


def _has_integrated_graphics(row: dict[str, str]) -> bool:
    brand = row.get("Brand", "")
    model = row.get("Model", "")
    upper = model.upper()
    if brand == "Intel":
        return not upper.endswith("F") and " KF" not in f" {upper}"
    if brand == "AMD":
        if "APU" in upper or upper.endswith("G") or " G" in upper:
            return True
        return ("RYZEN 7" in upper or "RYZEN 9" in upper or "RYZEN 5" in upper) and (
            upper.startswith("RYZEN 5 7")
            or upper.startswith("RYZEN 7 7")
            or upper.startswith("RYZEN 9 7")
            or upper.startswith("RYZEN 5 8")
            or upper.startswith("RYZEN 7 8")
            or upper.startswith("RYZEN 9 8")
            or upper.startswith("RYZEN 5 9")
            or upper.startswith("RYZEN 7 9")
            or upper.startswith("RYZEN 9 9")
        ) and not upper.endswith("F")
    return False


def _consumer_cpu(row: dict[str, str], motherboard_ids: set[str]) -> bool:
    price = _to_int(row.get("price_krw_estimate"))
    if price <= 0:
        return False
    if not set(_split_ids(row.get("compatible_motherboard_ids"))) & motherboard_ids:
        return False
    model = row.get("Model", "").upper()
    if any(token in model for token in ["XEON", "EPYC", "OPTERON", "THREADRIPPER"]):
        return False
    rank = _to_int(row.get("Rank"), 9999)
    status = row.get("market_status", "")
    if status == "current_or_recent":
        return rank <= 320
    return rank <= 260


def _consumer_gpu(row: dict[str, str]) -> bool:
    price = _to_int(row.get("price_krw_estimate"))
    if price <= 0:
        return False
    rank = _to_int(row.get("Rank"), 9999)
    vram = _to_int(row.get("vram_gb_est"))
    return rank <= 360 and (vram >= 2 or price <= 120_000)


def _consumer_ram(row: dict[str, str]) -> bool:
    return _to_int(row.get("price_krw_estimate")) > 0 and _to_int(row.get("capacity_gb_total_est")) >= 8


def _consumer_storage(row: dict[str, str]) -> bool:
    return _to_int(row.get("price_krw_estimate")) > 0 and _to_int(row.get("capacity_gb_est")) >= 240


def _base_part(category: str, row: dict[str, str], scores: dict[str, float]) -> dict:
    return {
        "category": category,
        "brand": row.get("Brand") or row.get("brand") or "Unknown",
        "model": row.get("Model") or row.get("model") or "Unknown",
        "price": _to_int(row.get("price_krw_estimate")),
        "scores": scores,
        "spec": {"id": row.get("part_id", "")},
    }


def _common_scores(perf: float, category: str, extra: dict | None = None) -> dict[str, float]:
    extra = extra or {}
    if category == "cpu":
        return {
            "office": perf * 0.95,
            "gaming": perf * 0.9,
            "video_edit": perf,
            "3d": perf * 0.95,
            "deep_learning": perf * 0.85,
        }
    if category == "gpu":
        vram = min(extra.get("vram_gb", 0), 32)
        return {
            "office": perf * 0.2,
            "gaming": perf,
            "video_edit": perf * 0.9 + vram * 0.7,
            "3d": perf * 0.95 + vram,
            "deep_learning": perf * 0.85 + vram * 1.8,
        }
    if category == "ram":
        capacity = min(extra.get("capacity_gb", 0), 128)
        return {
            "office": perf * 0.35 + capacity * 0.8,
            "gaming": perf * 0.45 + capacity * 0.6,
            "video_edit": perf * 0.35 + capacity * 1.0,
            "3d": perf * 0.35 + capacity * 1.05,
            "deep_learning": perf * 0.25 + capacity * 1.2,
        }
    if category == "storage":
        capacity = min(extra.get("capacity_gb", 0), 4096)
        ssd_bonus = 18 if extra.get("is_ssd") else 0
        base = perf * 0.55 + capacity / 80 + ssd_bonus
        return {purpose: base for purpose in ["office", "gaming", "video_edit", "3d", "deep_learning"]}
    return {purpose: perf for purpose in ["office", "gaming", "video_edit", "3d", "deep_learning"]}


def _load_pair_compatibility() -> dict[tuple[str, str], bool]:
    pairs: dict[tuple[str, str], bool] = {}
    for row in _read_csv("Compatibility_Pairs.csv"):
        part_a = row.get("part_a_id", "")
        part_b = row.get("part_b_id", "")
        if not part_a or not part_b:
            continue
        compatible = str(row.get("compatible", "")).strip().upper() == "TRUE"
        pairs[(part_a, part_b)] = compatible
        pairs[(part_b, part_a)] = compatible
    return pairs


def _load_parts() -> list[dict]:
    parts: list[dict] = []
    motherboard_rows = _read_csv("Motherboard.csv")
    motherboard_ids = {row["part_id"] for row in motherboard_rows}

    for row in motherboard_rows:
        part = _base_part("motherboard", row, _common_scores(72, "motherboard"))
        part["spec"].update(
            {
                "id": row["part_id"],
                "socket": row["socket"],
                "ram_type": row["memory_type"],
                "form_factor": row["form_factor"],
                "m2_slots": _to_int(row.get("m2_slots")),
                "sata_ports": _to_int(row.get("sata_ports")),
                "max_gpu_length": 420,
                "compatible_cpu_ids": [],
                "compatible_ram_ids": [],
                "compatible_storage_ids": [],
                "compatible_case_ids": [],
            }
        )
        parts.append(part)

    for row in _read_csv("CPU_augmented.csv"):
        if not _consumer_cpu(row, motherboard_ids):
            continue
        benchmark = _bounded_score(_benchmark(row), 150)
        model = row["Model"]
        part = _base_part("cpu", row, _common_scores(benchmark, "cpu"))
        part["spec"].update(
            {
                "id": row["part_id"],
                "socket": row["socket"],
                "memory_support": row.get("memory_type_supported", ""),
                "tdp": _cpu_tdp(model, _to_int(row.get("tdp_w_est"))),
                "igpu": _has_integrated_graphics(row),
                "benchmark_score": round(_benchmark(row), 2),
                "rank": _to_int(row.get("Rank"), 9999),
                "compatible_motherboard_ids": _split_ids(row.get("compatible_motherboard_ids")),
                "compatible_cooler_ids": _split_ids(row.get("compatible_cooler_ids")),
            }
        )
        parts.append(part)
        if part["spec"]["igpu"]:
            igpu = _base_part(
                "gpu",
                {"Brand": part["brand"], "Model": f"{model} 내장 그래픽", "part_id": f"IGPU_{row['part_id']}", "price_krw_estimate": "0"},
                _common_scores(18, "gpu", {"vram_gb": 0}),
            )
            igpu["spec"].update(
                {
                    "id": f"IGPU_{row['part_id']}",
                    "integrated": True,
                    "requires_cpu_id": row["part_id"],
                    "vram_gb": 0,
                    "length_mm": 0,
                    "power_draw": 0,
                    "recommended_psu_w": 300,
                    "benchmark_score": 18,
                    "compatible_psu_ids": [],
                    "compatible_case_ids": [],
                    "compatible_motherboard_ids": part["spec"]["compatible_motherboard_ids"],
                }
            )
            parts.append(igpu)

    for row in _read_csv("GPU_augmented.csv"):
        if not _consumer_gpu(row):
            continue
        vram = _to_int(row.get("vram_gb_est"))
        benchmark = _bounded_score(_benchmark(row), 190)
        part = _base_part("gpu", row, _common_scores(benchmark, "gpu", {"vram_gb": vram}))
        recommended = _to_int(row.get("required_psu_w_est"), 450)
        part["spec"].update(
            {
                "id": row["part_id"],
                "integrated": False,
                "vram_gb": vram,
                "length_mm": _to_int(row.get("length_mm_est"), 260),
                "power_draw": max(75, int(recommended * 0.48)),
                "recommended_psu_w": recommended,
                "benchmark_score": round(_benchmark(row), 2),
                "compatible_psu_ids": _split_ids(row.get("compatible_psu_ids")),
                "compatible_case_ids": _split_ids(row.get("compatible_case_ids")),
                "compatible_motherboard_ids": [],
            }
        )
        parts.append(part)

    for row in _read_csv("RAM_augmented.csv"):
        if not _consumer_ram(row):
            continue
        capacity = _to_int(row.get("capacity_gb_total_est"))
        perf = _bounded_score(_benchmark(row), 260)
        part = _base_part("ram", row, _common_scores(perf, "ram", {"capacity_gb": capacity}))
        part["spec"].update(
            {
                "id": row["part_id"],
                "ram_type": row["memory_type"],
                "capacity_gb": capacity,
                "speed_mhz": _to_int(row.get("speed_mhz_est")),
                "benchmark_score": round(_benchmark(row), 2),
                "compatible_motherboard_ids": _split_ids(row.get("compatible_motherboard_ids")),
            }
        )
        parts.append(part)

    for filename in ["SSD_augmented.csv", "HDD_augmented.csv"]:
        for row in _read_csv(filename):
            if not _consumer_storage(row):
                continue
            capacity = _to_int(row.get("capacity_gb_est"))
            is_ssd = row.get("storage_type") == "SSD"
            perf = _bounded_score(_benchmark(row), 720 if is_ssd else 140)
            part = _base_part("storage", row, _common_scores(perf, "storage", {"capacity_gb": capacity, "is_ssd": is_ssd}))
            part["spec"].update(
                {
                    "id": row["part_id"],
                    "interface": row.get("storage_interface", ""),
                    "capacity_gb": capacity,
                    "benchmark_score": round(_benchmark(row), 2),
                    "is_ssd": is_ssd,
                    "compatible_motherboard_ids": _split_ids(row.get("compatible_motherboard_ids")),
                }
            )
            parts.append(part)

    for row in _read_csv("Cooler.csv"):
        price = _to_int(row.get("price_krw_estimate"))
        if price <= 0:
            continue
        cooling_tdp = _to_int(row.get("max_tdp_w"), 65)
        part = _base_part("cooler", row, _common_scores(min(100, cooling_tdp / 3), "cooler"))
        part["spec"].update(
            {
                "id": row["part_id"],
                "supported_sockets": _split_ids(row.get("supported_sockets")),
                "cooling_tdp": cooling_tdp,
                "height_mm": _to_int(row.get("height_mm")),
                "radiator_mm": _to_int(row.get("radiator_mm")),
                "compatible_cpu_ids": [],
            }
        )
        parts.append(part)

    for row in _read_csv("PSU.csv"):
        watt = _to_int(row.get("wattage_w"))
        part = _base_part("psu", row, _common_scores(min(100, watt / 12), "psu"))
        part["spec"].update(
            {
                "id": row["part_id"],
                "watt": watt,
                "form_factor": row.get("form_factor", "ATX"),
                "native_12vhpwr": row.get("native_12vhpwr", "").lower() == "true",
                "pcie_8pin_count": _to_int(row.get("pcie_8pin_count")),
                "length_mm": _to_int(row.get("length_mm"), 160),
                "compatible_gpu_ids": [],
                "compatible_case_ids": [],
            }
        )
        parts.append(part)

    for row in _read_csv("Case.csv"):
        part = _base_part("case", row, _common_scores(70, "case"))
        part["spec"].update(
            {
                "id": row["part_id"],
                "supported_mobo_form_factors": _split_ids(row.get("supported_motherboard_form_factors")),
                "max_gpu_length": _to_int(row.get("max_gpu_length_mm"), 320),
                "max_cpu_cooler_height": _to_int(row.get("max_cpu_cooler_height_mm"), 155),
                "max_radiator_length": _to_int(row.get("max_radiator_mm")),
                "supported_psu_form_factors": _split_ids(row.get("psu_form_factor")),
                "max_psu_length": _to_int(row.get("max_psu_length_mm"), 180),
                "compatible_motherboard_ids": [],
                "compatible_cooler_ids": [],
                "compatible_psu_ids": [],
                "compatible_gpu_ids": [],
            }
        )
        parts.append(part)

    return parts


PAIR_COMPATIBILITY = _load_pair_compatibility()
PARTS = _load_parts()


def are_pair_compatible(part_a_id: str, part_b_id: str) -> bool | None:
    return PAIR_COMPATIBILITY.get((part_a_id, part_b_id))


def get_available_brands() -> dict[str, list[str]]:
    brands: dict[str, set[str]] = {"cpu": set(), "gpu": set()}
    for part in PARTS:
        if part["category"] in brands and not part["spec"].get("integrated"):
            brands[part["category"]].add(part["brand"])
    return {category: sorted(values) for category, values in brands.items()}
