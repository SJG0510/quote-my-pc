import { QuoteForm } from "@/components/quote/QuoteForm";


export default function HomePage() {
  return (
    <main className="page-shell">
      <div className="page-content dashboard-grid">
        <section className="hero-grid">
          <div className="hero-copy hero-card">
            <div className="eyebrow">
              <span className="eyebrow-dot" />
              PC 견적 추천
            </div>
            <h1 className="headline">
              필요한 성능만
              <span className="accent"> 정확하게.</span>
            </h1>
            <p className="lead">
              예산과 사용 목적을 입력하면 호환성 검증을 거친 조립 PC 구성을 추천합니다.
              가격, 핵심 부품, 대안 견적을 한 화면에서 비교할 수 있습니다.
            </p>
          </div>

          <div className="hero-side-card panel">
            <div className="pc-visual" />
          </div>
        </section>

        <QuoteForm />
      </div>
    </main>
  );
}
