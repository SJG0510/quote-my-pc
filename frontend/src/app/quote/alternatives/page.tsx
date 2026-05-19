import Link from "next/link";

import { AlternativesView } from "@/components/quote/AlternativesView";


type Props = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};


export default async function AlternativesPage({ searchParams }: Props) {
  const params = await searchParams;
  const quoteId = typeof params.quote_id === "string" ? params.quote_id : "";

  return (
    <main className="page-shell">
      <div className="page-content dashboard-grid">
        <div className="button-row">
          <Link className="button-ghost" href="/">
            홈으로
          </Link>
          {quoteId ? (
            <Link className="button-secondary" href={`/quote/result?quote_id=${quoteId}`}>
              결과 화면으로
            </Link>
          ) : null}
        </div>

        <section className="comparison-title">
          <h1>대안 견적 비교</h1>
          <p>선택한 빌드 후보들의 성능 밸런스, 핵심 부품 구성, 가격 효율을 비교해서 가장 적합한 조합을 빠르게 고를 수 있게 정리했습니다.</p>
        </section>

        <AlternativesView quoteId={quoteId} />
      </div>
    </main>
  );
}
