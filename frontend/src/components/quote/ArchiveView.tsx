"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";

import { deleteSavedQuote, getSavedQuotes } from "@/lib/api-client";
import type { SavedQuote } from "@/lib/types";

const purposeLabels: Record<SavedQuote["request"]["purpose"], string> = {
  office: "사무 / 학습",
  gaming: "캐주얼 게이밍",
  video_edit: "고사양 게이밍 / 편집",
  "3d": "하이엔드 3D / 4K",
  deep_learning: "딥러닝 / 렌더링",
};

export function ArchiveView() {
  const [items, setItems] = useState<SavedQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    getSavedQuotes()
      .then((data) => {
        setItems(data.items);
        setError("");
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const onDelete = (quoteId: string) => {
    deleteSavedQuote(quoteId)
      .then(() => {
        setItems((current) => current.filter((item) => item.quote_id !== quoteId));
      })
      .catch((err: Error) => setError(err.message));
  };

  if (loading) {
    return <div className="loading-state">보관함을 불러오는 중입니다.</div>;
  }

  if (error) {
    return <div className="error-box">{error}</div>;
  }

  if (items.length === 0) {
    return (
      <section className="panel empty-state">
        <h2 className="block-title">저장한 견적이 없습니다</h2>
        <p>견적 결과 화면에서 “견적 저장”을 누르면 이곳에 모입니다.</p>
        <Link className="button-primary" href="/">
          새 견적 만들기
        </Link>
      </section>
    );
  }

  return (
    <div className="archive-list">
      {items.map((item) => {
        const cpu = item.items.find((part) => part.category === "cpu");
        const gpu = item.items.find((part) => part.category === "gpu");
        const savedAt = new Date(item.saved_at).toLocaleString("ko-KR");

        return (
          <article key={item.quote_id} className="panel archive-card">
            <div className="archive-main">
              <div>
                <span className="tier-pill">{purposeLabels[item.request.purpose]}</span>
                <h2 className="block-title">{item.summary}</h2>
                <p className="archive-spec">
                  {cpu ? `${cpu.brand} ${cpu.model}` : "CPU 미정"} / {gpu ? `${gpu.brand} ${gpu.model}` : "GPU 미정"}
                </p>
              </div>

              <div className="archive-price">
                <span>저장일 {savedAt}</span>
                <strong>₩{item.total_price.toLocaleString()}</strong>
              </div>
            </div>

            <div className="archive-actions">
              <Link className="button-primary" href={`/quote/result?quote_id=${item.quote_id}`}>
                결과 보기
              </Link>
              <button className="button-ghost icon-action" type="button" onClick={() => onDelete(item.quote_id)} aria-label="저장한 견적 삭제">
                <Trash2 />
              </button>
            </div>
          </article>
        );
      })}
    </div>
  );
}
