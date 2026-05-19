type Props = {
  status: "pass" | "warn" | "fail";
};


const labelMap = {
  pass: "호환 통과",
  warn: "주의 필요",
  fail: "비호환",
};


export function CompatibilityBadge({ status }: Props) {
  return <span className={`badge ${status}`}>{labelMap[status]}</span>;
}
