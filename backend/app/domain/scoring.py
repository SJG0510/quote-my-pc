PURPOSE_WEIGHTS = {
    "gaming": {"cpu": 0.24, "gpu": 0.32, "ram": 0.1, "storage": 0.08, "motherboard": 0.08, "psu": 0.06, "case": 0.04, "cooler": 0.08},
    "office": {"cpu": 0.28, "gpu": 0.05, "ram": 0.16, "storage": 0.14, "motherboard": 0.14, "psu": 0.08, "case": 0.05, "cooler": 0.1},
    "video_edit": {"cpu": 0.28, "gpu": 0.18, "ram": 0.18, "storage": 0.12, "motherboard": 0.08, "psu": 0.05, "case": 0.03, "cooler": 0.08},
    "3d": {"cpu": 0.24, "gpu": 0.24, "ram": 0.18, "storage": 0.1, "motherboard": 0.08, "psu": 0.05, "case": 0.03, "cooler": 0.08},
    "deep_learning": {"cpu": 0.18, "gpu": 0.34, "ram": 0.16, "storage": 0.12, "motherboard": 0.07, "psu": 0.06, "case": 0.02, "cooler": 0.05},
}


def score_build(build: dict, purpose: str, budget: int) -> float:
    weights = PURPOSE_WEIGHTS[purpose]
    weighted = 0.0
    for category, weight in weights.items():
        weighted += build[category]["scores"][purpose] * weight

    total_price = sum(part["price"] for part in build.values())
    budget_efficiency = max(0.0, min(10.0, ((budget - total_price) / budget) * 12 + 5))
    workload_bonus = 0.0
    if purpose == "deep_learning":
        workload_bonus += min(build["gpu"]["spec"].get("vram_gb", 0), 48) * 0.35
        workload_bonus += min(build["ram"]["spec"].get("capacity_gb", 0), 192) * 0.04
    elif purpose in {"video_edit", "3d"}:
        workload_bonus += min(build["gpu"]["spec"].get("vram_gb", 0), 24) * 0.12
        workload_bonus += min(build["ram"]["spec"].get("capacity_gb", 0), 128) * 0.025
    return weighted + budget_efficiency + workload_bonus
