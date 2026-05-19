"use client";

import { useEffect, useState } from "react";

import { AlternativeCompare } from "@/components/quote/AlternativeCompare";
import { getAlternatives } from "@/lib/api-client";
import type { AlternativeQuote } from "@/lib/types";


type Props = {
  quoteId: string;
};


export function AlternativesView({ quoteId }: Props) {
  const [alternatives, setAlternatives] = useState<AlternativeQuote[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const targetQuoteId = quoteId || window.localStorage.getItem("last_quote_id") || "";

    if (!targetQuoteId) {
      setError("비교할 견적이 없습니다. 먼저 견적을 생성한 뒤 대안 비교를 열어 주세요.");
      setLoading(false);
      return;
    }

    getAlternatives(targetQuoteId)
      .then((data) => {
        setAlternatives(data.alternatives);
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

  return <AlternativeCompare alternatives={alternatives} />;
}
