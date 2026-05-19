import Link from "next/link";

import { ArchiveView } from "@/components/quote/ArchiveView";

export default function ArchivePage() {
  return (
    <main className="page-shell">
      <div className="page-content dashboard-grid">
        <div className="button-row">
          <Link className="button-ghost" href="/">
            홈으로
          </Link>
        </div>

        <section className="comparison-title">
          <h1>견적 보관함</h1>
          <p>저장한 견적 결과를 다시 열어보고, 필요 없는 구성은 바로 정리할 수 있습니다.</p>
        </section>

        <ArchiveView />
      </div>
    </main>
  );
}
