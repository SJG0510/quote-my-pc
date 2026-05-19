
import csv


def load_pairs(path="Compatibility_Pairs.csv"):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def find_compatible_parts(pairs, selected_part_id, target_category):
    results = []
    for p in pairs:
        if p.get("compatible") != "TRUE":
            continue
        if p.get("part_a_id") == selected_part_id and p.get("part_b_category") == target_category:
            results.append(p.get("part_b_id"))
        elif p.get("part_b_id") == selected_part_id and p.get("part_a_category") == target_category:
            results.append(p.get("part_a_id"))
    return results


def is_compatible(pairs, part_a_id, part_b_id):
    for p in pairs:
        if p.get("compatible") != "TRUE":
            continue
        if {p.get("part_a_id"), p.get("part_b_id")} == {part_a_id, part_b_id}:
            return True, p.get("reason")
    return False, "No compatible pair found"
