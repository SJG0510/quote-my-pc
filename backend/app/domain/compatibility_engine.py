from app.domain.schemas import CompatibilityCheck
from app.domain.sample_data import are_pair_compatible


def _pair_allows(part_a_id: str, part_b_id: str) -> bool:
    pair_value = are_pair_compatible(part_a_id, part_b_id)
    return pair_value is not False


def validate_build(build: dict) -> list[CompatibilityCheck]:
    cpu = build["cpu"]
    cooler = build["cooler"]
    motherboard = build["motherboard"]
    ram = build["ram"]
    gpu = build["gpu"]
    storage = build["storage"]
    psu = build["psu"]
    case = build["case"]

    checks: list[CompatibilityCheck] = []

    cpu_spec = cpu["spec"]
    cooler_spec = cooler["spec"]
    board_spec = motherboard["spec"]
    ram_spec = ram["spec"]
    gpu_spec = gpu["spec"]
    storage_spec = storage["spec"]
    psu_spec = psu["spec"]
    case_spec = case["spec"]

    cpu_socket = cpu_spec["socket"]
    board_socket = board_spec["socket"]
    cpu_board_ids_match = not cpu_spec.get("compatible_motherboard_ids") or board_spec["id"] in cpu_spec["compatible_motherboard_ids"]
    board_cpu_ids_match = not board_spec.get("compatible_cpu_ids") or cpu_spec["id"] in board_spec["compatible_cpu_ids"]
    cpu_board_pair_match = _pair_allows(cpu_spec["id"], board_spec["id"])
    if cpu_socket == board_socket and cpu_board_ids_match and board_cpu_ids_match and cpu_board_pair_match:
        checks.append(CompatibilityCheck(rule="cpu_motherboard_socket", status="pass", message="CPU와 메인보드 소켓이 일치합니다."))
    else:
        checks.append(CompatibilityCheck(rule="cpu_motherboard_socket", status="fail", message="CPU 소켓과 메인보드 소켓이 맞지 않습니다."))

    board_ram_ids_match = not board_spec.get("compatible_ram_ids") or ram_spec["id"] in board_spec["compatible_ram_ids"]
    ram_board_ids_match = not ram_spec.get("compatible_motherboard_ids") or board_spec["id"] in ram_spec["compatible_motherboard_ids"]
    ram_board_pair_match = _pair_allows(ram_spec["id"], board_spec["id"])
    if ram_spec["ram_type"] == board_spec["ram_type"] and board_ram_ids_match and ram_board_ids_match and ram_board_pair_match:
        checks.append(CompatibilityCheck(rule="ram_standard", status="pass", message="RAM 규격이 메인보드와 호환됩니다."))
    else:
        checks.append(CompatibilityCheck(rule="ram_standard", status="fail", message="RAM 규격이 메인보드와 맞지 않습니다."))

    cpu_cooler_ids_match = not cpu_spec.get("compatible_cooler_ids") or cooler_spec["id"] in cpu_spec["compatible_cooler_ids"]
    cooler_cpu_ids_match = not cooler_spec.get("compatible_cpu_ids") or cpu_spec["id"] in cooler_spec["compatible_cpu_ids"]
    cpu_cooler_pair_match = _pair_allows(cpu_spec["id"], cooler_spec["id"])
    if cpu_socket in cooler_spec["supported_sockets"] and cpu_cooler_ids_match and cooler_cpu_ids_match and cpu_cooler_pair_match:
        checks.append(CompatibilityCheck(rule="cooler_socket", status="pass", message="쿨러 장착 규격이 맞습니다."))
    else:
        checks.append(CompatibilityCheck(rule="cooler_socket", status="fail", message="선택한 쿨러가 CPU 소켓을 지원하지 않습니다."))

    if cooler_spec["cooling_tdp"] >= cpu_spec["tdp"]:
        checks.append(CompatibilityCheck(rule="cooling_capacity", status="pass", message="쿨러 냉각 성능이 CPU 발열을 감당합니다."))
    else:
        checks.append(CompatibilityCheck(rule="cooling_capacity", status="warn", message="쿨러 여유가 적어 장시간 고부하 작업에 불리합니다."))

    if gpu_spec.get("requires_cpu_id") and gpu_spec["requires_cpu_id"] != cpu_spec["id"]:
        checks.append(CompatibilityCheck(rule="integrated_gpu_cpu", status="fail", message="내장 그래픽은 해당 CPU와만 사용할 수 있습니다."))
    elif gpu_spec.get("integrated"):
        checks.append(CompatibilityCheck(rule="integrated_gpu_cpu", status="pass", message="CPU 내장 그래픽을 사용합니다."))

    board_gpu_ids_match = gpu_spec.get("integrated") or not gpu_spec.get("compatible_motherboard_ids") or board_spec["id"] in gpu_spec["compatible_motherboard_ids"]
    case_gpu_ids_match = gpu_spec.get("integrated") or not case_spec.get("compatible_gpu_ids") or gpu_spec["id"] in case_spec["compatible_gpu_ids"]
    gpu_case_pair_match = gpu_spec.get("integrated") or _pair_allows(gpu_spec["id"], case_spec["id"])
    if gpu_spec["length_mm"] <= min(case_spec["max_gpu_length"], board_spec["max_gpu_length"]) and board_gpu_ids_match and case_gpu_ids_match and gpu_case_pair_match:
        checks.append(CompatibilityCheck(rule="gpu_length", status="pass", message="그래픽카드 길이가 케이스 공간 안에 들어갑니다."))
    else:
        checks.append(CompatibilityCheck(rule="gpu_length", status="fail", message="그래픽카드 길이가 케이스 또는 보드 여유 공간을 초과합니다."))

    board_storage_ids_match = not board_spec.get("compatible_storage_ids") or storage_spec["id"] in board_spec["compatible_storage_ids"]
    storage_board_ids_match = not storage_spec.get("compatible_motherboard_ids") or board_spec["id"] in storage_spec["compatible_motherboard_ids"]
    storage_board_pair_match = _pair_allows(storage_spec["id"], board_spec["id"])
    if board_storage_ids_match and storage_board_ids_match and storage_board_pair_match:
        checks.append(CompatibilityCheck(rule="storage_interface", status="pass", message="저장장치 인터페이스가 메인보드와 호환됩니다."))
    else:
        checks.append(CompatibilityCheck(rule="storage_interface", status="fail", message="저장장치 인터페이스가 메인보드와 맞지 않습니다."))

    board_case_ids_match = not board_spec.get("compatible_case_ids") or case_spec["id"] in board_spec["compatible_case_ids"]
    case_board_ids_match = not case_spec.get("compatible_motherboard_ids") or board_spec["id"] in case_spec["compatible_motherboard_ids"]
    board_form_factor_match = board_spec["form_factor"] in case_spec["supported_mobo_form_factors"]
    board_case_pair_match = _pair_allows(board_spec["id"], case_spec["id"])
    if board_case_ids_match and case_board_ids_match and board_form_factor_match and board_case_pair_match:
        checks.append(CompatibilityCheck(rule="case_motherboard", status="pass", message="케이스가 메인보드 폼팩터를 지원합니다."))
    else:
        checks.append(CompatibilityCheck(rule="case_motherboard", status="fail", message="케이스가 메인보드 폼팩터를 지원하지 않습니다."))

    case_cooler_ids_match = not case_spec.get("compatible_cooler_ids") or cooler_spec["id"] in case_spec["compatible_cooler_ids"]
    air_cooler_height_ok = cooler_spec["height_mm"] == 0 or cooler_spec["height_mm"] <= case_spec["max_cpu_cooler_height"]
    radiator_ok = cooler_spec["radiator_mm"] == 0 or cooler_spec["radiator_mm"] <= case_spec["max_radiator_length"]
    cooler_case_pair_match = _pair_allows(cooler_spec["id"], case_spec["id"])
    if case_cooler_ids_match and air_cooler_height_ok and radiator_ok and cooler_case_pair_match:
        checks.append(CompatibilityCheck(rule="case_cooler", status="pass", message="쿨러가 케이스 장착 한도 안에 들어갑니다."))
    else:
        checks.append(CompatibilityCheck(rule="case_cooler", status="fail", message="쿨러 높이 또는 라디에이터 길이가 케이스 한도를 초과합니다."))

    case_psu_ids_match = not case_spec.get("compatible_psu_ids") or psu_spec["id"] in case_spec["compatible_psu_ids"]
    psu_case_ids_match = not psu_spec.get("compatible_case_ids") or case_spec["id"] in psu_spec["compatible_case_ids"]
    psu_size_ok = psu_spec["form_factor"] in case_spec["supported_psu_form_factors"] and psu_spec["length_mm"] <= case_spec["max_psu_length"]
    psu_case_pair_match = _pair_allows(psu_spec["id"], case_spec["id"])
    if case_psu_ids_match and psu_case_ids_match and psu_size_ok and psu_case_pair_match:
        checks.append(CompatibilityCheck(rule="case_psu", status="pass", message="파워 규격과 길이가 케이스에 맞습니다."))
    else:
        checks.append(CompatibilityCheck(rule="case_psu", status="fail", message="파워 규격 또는 길이가 케이스와 맞지 않습니다."))

    psu_gpu_ids_match = gpu_spec.get("integrated") or not psu_spec.get("compatible_gpu_ids") or gpu_spec["id"] in psu_spec["compatible_gpu_ids"]
    gpu_psu_ids_match = gpu_spec.get("integrated") or not gpu_spec.get("compatible_psu_ids") or psu_spec["id"] in gpu_spec["compatible_psu_ids"]
    estimated_draw = cpu_spec["tdp"] + gpu_spec["power_draw"] + 180
    recommended_watt = max(gpu_spec.get("recommended_psu_w", 0), int(estimated_draw * 1.25))
    gpu_psu_pair_match = gpu_spec.get("integrated") or _pair_allows(gpu_spec["id"], psu_spec["id"])
    if psu_spec["watt"] >= recommended_watt and psu_gpu_ids_match and gpu_psu_ids_match and gpu_psu_pair_match:
        headroom = psu_spec["watt"] - recommended_watt
        status = "pass" if headroom >= 80 else "warn"
        message = "파워 용량이 충분합니다." if status == "pass" else "파워 용량은 맞지만 업그레이드 여유가 크지 않습니다."
        checks.append(CompatibilityCheck(rule="psu_capacity", status=status, message=message))
    else:
        checks.append(CompatibilityCheck(rule="psu_capacity", status="fail", message="예상 소비전력 대비 파워 용량이 부족합니다."))

    return checks


def is_valid(checks: list[CompatibilityCheck]) -> bool:
    return all(check.status != "fail" for check in checks)
