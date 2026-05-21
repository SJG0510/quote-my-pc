import { Cpu, HardDrive, MemoryStick, MonitorSmartphone, PlugZap } from "lucide-react";
import type { ComponentType } from "react";
import Link from "next/link";

import type { AlternativeQuote, QuoteItem } from "@/lib/types";


type Props = {
  quotes: AlternativeQuote[];
};

const tierLabels = ["AI 추천", "전문가 견적", "대안 1", "대안 2", "대안 3", "대안 4"];
const titles = ["추천 엔진 견적", "직접 지정 견적", "가격 우선 견적", "균형형 견적", "성능 우선 견적", "저장공간 우선 견적"];

const specRows: Array<{
  category: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
}> = [
  { category: "cpu", label: "프로세서", icon: Cpu },
  { category: "gpu", label: "그래픽", icon: MonitorSmartphone },
  { category: "ram", label: "메모리", icon: MemoryStick },
  { category: "psu", label: "파워", icon: PlugZap },
  { category: "storage", label: "저장장치", icon: HardDrive },
];

function findPart(items: QuoteItem[], category: string) {
  return items.find((item) => item.category === category);
}

function formatPart(part?: QuoteItem) {
  return part ? `${part.brand} ${part.model}` : "미정";
}

export function AlternativeCompare({ quotes }: Props) {
  return (
    <div className="compare-grid">
      {quotes.map((alternative, index) => {
        const scoreValue = Math.max(12, Math.min(100, Math.round((alternative.score / 100) * 100)));
        const hasFailures = alternative.checks.some((check) => check.status === "fail");

        return (
          <article key={alternative.quote_id} className="compare-card panel">
            <div className="compare-top">
              <span className="tier-pill">{tierLabels[index] ?? `ALT ${index + 1}`}</span>
            </div>

            <div className="compare-visual">
              <div className="pc-visual small" />
            </div>

            <div className="compare-body">
              <h2 className="block-title" style={{ marginBottom: 8 }}>
                {titles[index] ?? `대안 견적 ${index + 1}`}
              </h2>
              <div className="metric-value">
                ₩{alternative.total_price.toLocaleString()}
              </div>
              <div className={`status-pill ${hasFailures ? "fail" : "pass"}`}>{hasFailures ? "호환성 실패" : "호환성 통과"}</div>

              <div className="feature-stack">
                {specRows.map(({ category, label, icon: Icon }) => {
                  const part = findPart(alternative.items, category);
                  return (
                    <div key={category} className="feature-row">
                      <div className="component-category">
                        <Icon className="feature-icon" />
                        {label}
                      </div>
                      <div className="component-name">{formatPart(part)}</div>
                      {part ? <div className="component-price">₩{part.price.toLocaleString()}</div> : null}
                    </div>
                  );
                })}
              </div>

              {alternative.diff_points.length > 0 ? (
                <div className="diff-list">
                  {alternative.diff_points.map((point) => (
                    <span key={point}>{point}</span>
                  ))}
                </div>
              ) : null}

              <div className="compare-footer">
                <div className="summary-row">
                  <span>성능 점수</span>
                  <strong>{Math.round(alternative.score * 135).toLocaleString()} pts</strong>
                </div>
                <div className="score-bar">
                  <div className="score-fill" style={{ width: `${scoreValue}%` }} />
                </div>
                {alternative.quote_id === "expert_custom" ? null : (
                  <Link className={index === 0 ? "button-primary" : "button-ghost"} href={`/quote/result?quote_id=${alternative.quote_id}`}>
                    선택하기
                  </Link>
                )}
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
