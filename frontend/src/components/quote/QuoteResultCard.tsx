import { Box, Cpu, HardDrive, MemoryStick, MonitorSmartphone, PlugZap, Snowflake } from "lucide-react";
import type { ComponentType } from "react";

import type { Purpose, QuoteItem, QuoteResponse } from "@/lib/types";

type Props = {
  result: QuoteResponse;
  onSave?: () => void;
  saving?: boolean;
};

const iconMap: Record<string, ComponentType<{ className?: string }>> = {
  cpu: Cpu,
  cooler: Snowflake,
  motherboard: Box,
  ram: MemoryStick,
  gpu: MonitorSmartphone,
  storage: HardDrive,
  psu: PlugZap,
  case: Box,
};

const categoryLabels: Record<string, string> = {
  cpu: "CPU",
  cooler: "쿨러",
  motherboard: "메인보드",
  ram: "RAM",
  gpu: "그래픽카드",
  storage: "SSD / 저장장치",
  psu: "파워",
  case: "케이스",
};

const titleMap: Record<Purpose, string> = {
  office: "사무용 안정 견적",
  gaming: "캐주얼 게이밍 견적",
  video_edit: "고사양 게이밍 / 편집 견적",
  "3d": "하이엔드 3D / 4K 견적",
  deep_learning: "딥러닝 / 렌더링 전문가 견적",
};

function getStatus(items: QuoteResponse["checks"], category: string): "pass" | "warn" | "fail" {
  if (category === "psu") {
    return items.find((check) => check.rule === "psu_capacity")?.status ?? "pass";
  }
  return "pass";
}

function QuoteComponentRow({ item, status }: { item: QuoteItem; status: "pass" | "warn" | "fail" }) {
  const Icon = iconMap[item.category] ?? Box;
  const statusLabel = status === "pass" ? "통과" : status === "warn" ? "주의" : "실패";

  return (
    <div className="component-card">
      <div className="component-icon">
        <Icon />
      </div>
      <div className="component-meta">
        <span className="component-category">{categoryLabels[item.category] ?? item.category}</span>
        <div className="component-name">
          {item.brand} {item.model}
        </div>
        <div className="component-desc">{item.reason}</div>
      </div>
      <div className="component-side">
        <span className={`status-pill ${status}`}>{statusLabel}</span>
        <strong className="price-text">₩{item.price.toLocaleString()}</strong>
      </div>
    </div>
  );
}

export function QuoteResultCard({ result, onSave, saving = false }: Props) {
  const assemblyFee: number = 0;
  const warningState = result.warnings.length > 0 ? "warn" : "pass";

  return (
    <div className="dashboard-grid">
      <section className="panel hero-summary">
        <div className="dashboard-grid" style={{ gap: 18 }}>
          <div className="eyebrow">
            <span className="eyebrow-dot" />
            {warningState === "pass" ? "호환성 검증 통과" : "호환성 주의 필요"}
          </div>
          <h1 className="section-main-title">{titleMap[result.request.purpose]}</h1>
          <p className="lead">{result.summary}</p>
          <div>
            <div className="metric-label">예상 벤치마크</div>
            <div className="metric-value">{Math.round(result.score * 220).toLocaleString()} pts</div>
          </div>
        </div>

        <div className="pc-visual small" />
      </section>

      <section className="result-layout">
        <div className="dashboard-grid">
          <h2 className="block-title">선택된 부품</h2>
          <div className="components-list">
            {result.items.map((item) => (
              <QuoteComponentRow key={`${item.category}-${item.model}`} item={item} status={getStatus(result.checks, item.category)} />
            ))}
          </div>
        </div>

        <aside className="summary-card">
          <h2 className="block-title">견적 요약</h2>
          <div className="summary-row">
            <span>부품 합계</span>
            <strong>₩{result.total_price.toLocaleString()}</strong>
          </div>
          <div className="summary-row">
            <span>조립 및 테스트</span>
            <strong>{assemblyFee === 0 ? "무료" : `₩${assemblyFee.toLocaleString()}`}</strong>
          </div>
          <div className="summary-row">
            <span>배송</span>
            <strong>무료</strong>
          </div>

          <div className="summary-total">
            <span>최종 합계</span>
            <strong>₩{(result.total_price + assemblyFee).toLocaleString()}</strong>
          </div>

          <div className="k-actions">
            <button className="button-primary" type="button" onClick={onSave} disabled={saving}>
              {saving ? "저장 중" : "견적 저장"}
            </button>
            <button className="button-ghost" type="button">
              공유하기
            </button>
          </div>

          <div className="notice-card">
            가격과 재고는 변동될 수 있습니다. 실제 주문 전 최종 호환성과 부품 수급 상태를 다시 확인하는 구성입니다.
          </div>
        </aside>
      </section>
    </div>
  );
}
