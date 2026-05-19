
export type CompatibilityPair = {
  part_a_id: string;
  part_a_category: string;
  part_b_id: string;
  part_b_category: string;
  relation: string;
  compatible: string;
  reason: string;
};

export function findCompatibleParts(
  pairs: CompatibilityPair[],
  selectedPartId: string,
  targetCategory: string
): string[] {
  return pairs
    .filter((p) => p.compatible === "TRUE")
    .filter((p) =>
      (p.part_a_id === selectedPartId && p.part_b_category === targetCategory) ||
      (p.part_b_id === selectedPartId && p.part_a_category === targetCategory)
    )
    .map((p) => p.part_a_id === selectedPartId ? p.part_b_id : p.part_a_id);
}

export function isCompatible(pairs: CompatibilityPair[], partAId: string, partBId: string): boolean {
  return pairs.some((p) =>
    p.compatible === "TRUE" &&
    ((p.part_a_id === partAId && p.part_b_id === partBId) ||
     (p.part_a_id === partBId && p.part_b_id === partAId))
  );
}
