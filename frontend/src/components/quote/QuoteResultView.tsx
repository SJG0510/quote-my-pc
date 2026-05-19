"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { createQuote, getQuoteDetail, saveQuote } from "@/lib/api-client";
import { QuoteResultCard } from "@/components/quote/QuoteResultCard";
import type { QuoteRequest, QuoteResponse } from "@/lib/types";


type Props = {
  quoteId?: string;
  request: QuoteRequest;
};


export function QuoteResultView({ quoteId = "", request }: Props) {
  const [result, setResult] = useState<QuoteResponse | null>(null);
  const [error, setError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const loader = quoteId ? getQuoteDetail(quoteId) : createQuote(request);

    loader
      .then((data) => {
        setResult(data);
        window.localStorage.setItem("last_quote_id", data.quote_id);
        setError("");
        setSaveMessage("");
      })
      .catch((err: Error) => {
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, [quoteId, request]);

  const onSave = () => {
    if (!result) {
      return;
    }
    setSaving(true);
    saveQuote(result.quote_id)
      .then(() => {
        setSaveMessage("보관함에 저장했습니다.");
        setError("");
      })
      .catch((err: Error) => {
        setError(err.message);
      })
      .finally(() => setSaving(false));
  };

  return (
    <div className="dashboard-grid">
      <div className="button-row">
        <Link className="button-ghost" href="/">
          홈으로
        </Link>
        {result ? (
          <Link className="button-primary" href={`/quote/alternatives?quote_id=${result.quote_id}`}>
            대안 비교 보기
          </Link>
        ) : null}
        <Link className="button-secondary" href="/quote/archive">
          보관함
        </Link>
      </div>

      {loading ? <div className="loading-state">추천 견적을 계산하는 중입니다.</div> : null}
      {!loading && error ? <div className="error-box">{error}</div> : null}
      {!loading && saveMessage ? <div className="success-box">{saveMessage}</div> : null}
      {!loading && result ? <QuoteResultCard result={result} onSave={onSave} saving={saving} /> : null}
    </div>
  );
}
