"use client";

import { useEffect, useMemo, useState } from "react";
import type { ComponentType, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { BrainCircuit, BriefcaseBusiness, Clapperboard, Gamepad2, Rocket } from "lucide-react";

import { getFilters } from "@/lib/api-client";
import type { FiltersResponse, Purpose } from "@/lib/types";

const initialFilters: FiltersResponse = {
  brands: {},
  categories: [],
  purpose_presets: [],
};

const budgetPresets: Array<{ label: string; value: number; caption: string }> = [
  { label: "90만", value: 900000, caption: "입문 구성" },
  { label: "130만", value: 1300000, caption: "표준 구성" },
  { label: "200만", value: 2000000, caption: "상급 구성" },
  { label: "350만", value: 3500000, caption: "고성능 구성" },
  { label: "700만", value: 7000000, caption: "전문가 구성" },
];

const purposeMeta: Record<Purpose, { label: string; description: string; icon: ComponentType<{ className?: string }> }> = {
  office: { label: "사무 / 학습", description: "인강, 문서 작업, 단순 웹서핑", icon: BriefcaseBusiness },
  gaming: { label: "캐주얼 게이밍", description: "온라인 게임과 FHD 게이밍", icon: Gamepad2 },
  video_edit: { label: "고사양 게이밍 / 편집", description: "QHD 게임, 영상 편집, 방송", icon: Clapperboard },
  "3d": { label: "하이엔드 3D", description: "3D 작업과 4K 게이밍", icon: Rocket },
  deep_learning: { label: "딥러닝 / 렌더링", description: "AI 학습, VRAM 중심 워크스테이션", icon: BrainCircuit },
};

const MAX_BRAND_SELECTIONS = 6;

function normalizeBrand(brand: string) {
  return brand.trim().toLowerCase();
}

export function QuoteForm() {
  const router = useRouter();
  const [filters, setFilters] = useState<FiltersResponse>(initialFilters);
  const [budget, setBudget] = useState("90");
  const [purpose, setPurpose] = useState<Purpose>("office");
  const [selectedBrands, setSelectedBrands] = useState<string[]>(["AMD", "NVIDIA"]);
  const [ignoreBrands, setIgnoreBrands] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getFilters()
      .then(setFilters)
      .catch(() => {
        setError("필터 정보를 불러오지 못했습니다. 백엔드가 실행 중인지 확인해 주세요.");
      });
  }, []);

  const chipBrands = useMemo(
    () => Array.from(new Set([...(filters.brands.cpu ?? []), ...(filters.brands.gpu ?? [])])),
    [filters.brands],
  );

  const toggleBrand = (brand: string) => {
    const normalizedBrand = normalizeBrand(brand);
    setSelectedBrands((current) => {
      const exists = current.some((item) => normalizeBrand(item) === normalizedBrand);
      if (exists) {
        return current.filter((item) => normalizeBrand(item) !== normalizedBrand);
      }
      return current.length < MAX_BRAND_SELECTIONS ? [...current, brand] : current;
    });
  };

  const applyBudgetPreset = (preset: (typeof budgetPresets)[number]) => {
    setBudget(String(Math.floor(preset.value / 10000)));
    setError("");
  };

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const budgetInWon = Number(budget) * 10000;

    if (!Number.isInteger(budgetInWon) || budgetInWon < 300000 || budgetInWon > 10000000) {
      setError("예산은 30만 원 이상 1,000만 원 이하로 입력해 주세요.");
      return;
    }

    const params = new URLSearchParams({
      budget: String(budgetInWon),
      purpose,
      brands: ignoreBrands ? "" : selectedBrands.join(","),
    });

    router.push(`/quote/result?${params.toString()}`);
  };

  return (
    <form className="form-layout" onSubmit={onSubmit}>
      <div className="form-stack">
        <section className="form-card">
          <div className="step-title-row">
            <div className="step-badge">1</div>
            <div>
              <h2 className="step-title">예산 설정</h2>
            </div>
          </div>

          <div className="preset-grid">
            {budgetPresets.map((preset) => (
              <button
                key={preset.label}
                className={`choice-card${Number(budget) * 10000 === preset.value ? " active" : ""}`}
                type="button"
                onClick={() => applyBudgetPreset(preset)}
              >
                <strong>{preset.label}</strong>
                <span>{preset.caption}</span>
              </button>
            ))}
          </div>

          <div className="budget-input-shell">
            <span className="subtle">직접 입력 (단위: 만 원)</span>
            <input value={budget} onChange={(event) => setBudget(event.target.value.replace(/[^\d]/g, ""))} inputMode="numeric" />
            <strong>만 원</strong>
          </div>
        </section>

        <section className="form-card">
          <div className="step-title-row">
            <div className="step-badge">2</div>
            <div>
              <h2 className="step-title">사용 목적</h2>
            </div>
          </div>

          <div className="purpose-grid">
            {(Object.keys(purposeMeta) as Purpose[]).map((key) => {
              const item = purposeMeta[key];
              const Icon = item.icon;
              return (
                <button
                  key={key}
                  type="button"
                  className={`purpose-card${purpose === key ? " active" : ""}`}
                  onClick={() => setPurpose(key)}
                >
                  <Icon />
                  <div>
                    <strong>{item.label}</strong>
                    <span>{item.description}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        <section className="form-card">
          <div className="step-title-row">
            <div className="step-badge">3</div>
            <div>
              <h2 className="step-title">선호 브랜드</h2>
            </div>
          </div>

          <div className="hint-row">
            <span>최대 {MAX_BRAND_SELECTIONS}개까지 선택할 수 있습니다.</span>
            <label className="toggle-chip">
              <input type="checkbox" checked={ignoreBrands} onChange={(event) => setIgnoreBrands(event.target.checked)} />
              <span>관계없음 (가성비 최우선)</span>
            </label>
          </div>

          <div className="brand-grid" style={{ marginTop: 16 }}>
            {chipBrands.map((brand) => {
              const normalized = brand.toLowerCase();
              const klass = normalized.includes("intel") ? "intel" : normalized.includes("nvidia") ? "nvidia" : "amd";
              const selected = selectedBrands.some((item) => normalizeBrand(item) === normalizeBrand(brand));
              return (
                <button
                  key={brand}
                  type="button"
                  disabled={ignoreBrands}
                  className={`brand-card ${klass}${selected && !ignoreBrands ? " active" : ""}`}
                  onClick={() => toggleBrand(brand)}
                >
                  <strong>{brand}</strong>
                  <span>{brand === "Intel" ? "CPU" : brand === "NVIDIA" ? "GPU" : "CPU / GPU"}</span>
                </button>
              );
            })}
          </div>
        </section>
      </div>

      <aside className="summary-card">
        <h3 className="block-title">입력 요약</h3>
        <div className="summary-row">
          <span>예산</span>
          <strong>{Number(budget || "0").toLocaleString()}만 원</strong>
        </div>
        <div className="summary-row">
          <span>목적</span>
          <strong>{purposeMeta[purpose].label}</strong>
        </div>
        <div className="summary-row">
          <span>브랜드</span>
          <strong>{ignoreBrands ? "관계없음" : selectedBrands.join(", ") || "미선택"}</strong>
        </div>

        <div className="notice-card">
          예산과 목적은 서로 독립적으로 반영됩니다. 먼저 사용할 금액을 정하고, 다음 단계에서 실제 용도를 선택하세요.
        </div>

        {error ? <div className="error-box">{error}</div> : null}

        <div className="cta-section">
          <p className="cta-note">
            선택한 {Number(budget || "0").toLocaleString()}만 원 예산과 {purposeMeta[purpose].label} 목적에 맞는 부품 조합을 분석합니다.
          </p>
          <button className="cta-button" type="submit">
            견적 요청하기
          </button>
        </div>
      </aside>
    </form>
  );
}
