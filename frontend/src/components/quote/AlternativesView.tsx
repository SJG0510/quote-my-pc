"use client";

import { useEffect, useState } from "react";

import { AlternativeCompare } from "@/components/quote/AlternativeCompare";
import { evaluateCustomBuild, getAlternatives, getPartsCatalog, getQuoteDetail } from "@/lib/api-client";
import type { AlternativeQuote, PartOption, PartsCatalogResponse, QuoteResponse } from "@/lib/types";


type Props = {
  quoteId: string;
};


export function AlternativesView({ quoteId }: Props) {
  const [primary, setPrimary] = useState<QuoteResponse | null>(null);
  const [alternatives, setAlternatives] = useState<AlternativeQuote[]>([]);
  const [catalog, setCatalog] = useState<PartsCatalogResponse["parts"]>({});
  const [selectedPartIds, setSelectedPartIds] = useState<Record<string, string>>({});
  const [expertQuote, setExpertQuote] = useState<AlternativeQuote | null>(null);
  const [error, setError] = useState("");
  const [expertError, setExpertError] = useState("");
  const [evaluating, setEvaluating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const targetQuoteId = quoteId || window.localStorage.getItem("last_quote_id") || "";

    if (!targetQuoteId) {
      setError("비교할 견적이 없습니다. 먼저 견적을 생성한 뒤 대안 비교를 열어 주세요.");
      setLoading(false);
      return;
    }

    Promise.all([getQuoteDetail(targetQuoteId), getAlternatives(targetQuoteId), getPartsCatalog()])
      .then(([quoteDetail, alternativeData, catalogData]) => {
        setPrimary(quoteDetail);
        setAlternatives(alternativeData.alternatives);
        setCatalog(catalogData.parts);
        setSelectedPartIds((current) => {
          if (Object.keys(current).length > 0) {
            return current;
          }
          return Object.fromEntries(
            categoryOrder.map((category) => [category, catalogData.parts[category]?.[0]?.id ?? ""]),
          );
        });
        setError("");
      })
      .catch((err: Error) => {
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, [quoteId]);

  if (loading) {
    return <div className="loading-state">대안 견적을 불러오는 중입니다.</div>;
  }

  if (error) {
    return (
      <section className="panel empty-state">
        <h2 className="block-title">대안 비교를 시작할 수 없습니다</h2>
        <p>{error}</p>
        <a className="button-primary" href="/">
          새 견적 만들기
        </a>
      </section>
    );
  }

  if (alternatives.length === 0) {
    return (
      <section className="panel empty-state">
        <h2 className="block-title">대안 견적이 없습니다</h2>
        <p>현재 조건에서는 비교 가능한 대안 조합을 찾지 못했습니다.</p>
      </section>
    );
  }

  const comparableQuotes: AlternativeQuote[] = [
    ...(primary ? [toAlternativeQuote(primary)] : []),
    ...(expertQuote ? [expertQuote] : []),
    ...alternatives,
  ];

  const onSelectPart = (category: string, partId: string) => {
    setSelectedPartIds((current) => ({ ...current, [category]: partId }));
    setExpertQuote(null);
    setExpertError("");
  };

  const onEvaluateExpertBuild = () => {
    if (!primary) {
      return;
    }
    setEvaluating(true);
    evaluateCustomBuild({
      budget: primary.request.budget,
      purpose: primary.request.purpose,
      selected_part_ids: selectedPartIds,
    })
      .then((data) => {
        setExpertQuote(data);
        setExpertError("");
      })
      .catch((err: Error) => {
        setExpertError(err.message);
      })
      .finally(() => setEvaluating(false));
  };

  return (
    <div className="dashboard-grid">
      <ExpertBuildPanel
        catalog={catalog}
        selectedPartIds={selectedPartIds}
        expertQuote={expertQuote}
        expertError={expertError}
        evaluating={evaluating}
        onSelectPart={onSelectPart}
        onEvaluate={onEvaluateExpertBuild}
      />
      <AlternativeCompare quotes={comparableQuotes} />
    </div>
  );
}

const categoryOrder = ["cpu", "cooler", "motherboard", "ram", "gpu", "storage", "psu", "case"];

const categoryLabels: Record<string, string> = {
  cpu: "CPU",
  cooler: "쿨러",
  motherboard: "메인보드",
  ram: "RAM",
  gpu: "그래픽카드",
  storage: "저장장치",
  psu: "파워",
  case: "케이스",
};

function toAlternativeQuote(quote: QuoteResponse): AlternativeQuote {
  return {
    quote_id: quote.quote_id,
    total_price: quote.total_price,
    score: quote.score,
    summary: quote.summary,
    items: quote.items,
    checks: quote.checks,
    diff_points: ["추천 엔진이 생성한 기준 견적"],
  };
}

function partLabel(part: PartOption) {
  const benchmark = part.benchmark_score ? ` · ${Math.round(part.benchmark_score)}점` : "";
  return `${part.brand} ${part.model} · ₩${part.price.toLocaleString()}${benchmark}`;
}

function ExpertBuildPanel({
  catalog,
  selectedPartIds,
  expertQuote,
  expertError,
  evaluating,
  onSelectPart,
  onEvaluate,
}: {
  catalog: Record<string, PartOption[]>;
  selectedPartIds: Record<string, string>;
  expertQuote: AlternativeQuote | null;
  expertError: string;
  evaluating: boolean;
  onSelectPart: (category: string, partId: string) => void;
  onEvaluate: () => void;
}) {
  const selectedParts = categoryOrder
    .map((category) => catalog[category]?.find((part) => part.id === selectedPartIds[category]))
    .filter(Boolean) as PartOption[];
  const selectedTotal = selectedParts.reduce((sum, part) => sum + part.price, 0);
  const selectedCount = selectedParts.length;

  return (
    <section className="panel expert-builder">
      <div className="expert-builder-head">
        <div>
          <div className="eyebrow">
            <span className="eyebrow-dot" />
            전문가 견적 비교
          </div>
          <h2 className="block-title">직접 부품을 지정하고 AI 추천 견적과 비교하세요</h2>
        </div>
        <div className="expert-builder-summary">
          <span>선택 부품 {selectedCount}/8</span>
          <strong>₩{selectedTotal.toLocaleString()}</strong>
        </div>
      </div>

      <div className="expert-select-grid">
        {categoryOrder.map((category) => (
          <label key={category} className="expert-select-field">
            <span>{categoryLabels[category]}</span>
            <select value={selectedPartIds[category] ?? ""} onChange={(event) => onSelectPart(category, event.target.value)}>
              {(catalog[category] ?? []).map((part) => (
                <option key={part.id} value={part.id}>
                  {partLabel(part)}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>

      <div className="expert-actions">
        <button className="button-primary" type="button" onClick={onEvaluate} disabled={evaluating || selectedCount < categoryOrder.length}>
          {evaluating ? "비교 중" : "전문가 견적 벤치마크 비교"}
        </button>
        {expertQuote ? <span className="success-box compact">전문가 견적 평가가 완료되었습니다.</span> : null}
        {expertError ? <span className="error-box compact">{expertError}</span> : null}
      </div>
    </section>
  );
}
