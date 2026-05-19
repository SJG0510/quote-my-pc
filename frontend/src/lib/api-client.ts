import type { AlternativeQuote, FiltersResponse, QuoteRequest, QuoteResponse, SavedQuote } from "./types";


const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";


async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  const data = await response.json();

  if (!response.ok) {
    const detail = typeof data.detail === "object" ? data.detail.message : data.detail;
    throw new Error(detail ?? "요청 처리에 실패했습니다.");
  }

  return data.data as T;
}


export function getFilters(): Promise<FiltersResponse> {
  return fetchJson<FiltersResponse>("/parts/filters");
}


export function createQuote(payload: QuoteRequest): Promise<QuoteResponse> {
  return fetchJson<QuoteResponse>("/quotes/recommend", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}


export function getQuoteDetail(quoteId: string): Promise<QuoteResponse> {
  return fetchJson<QuoteResponse>(`/quotes/${quoteId}`);
}


export function getAlternatives(quoteId: string): Promise<{ quote_id: string; alternatives: AlternativeQuote[] }> {
  return fetchJson<{ quote_id: string; alternatives: AlternativeQuote[] }>(`/quotes/${quoteId}/alternatives`);
}

export function saveQuote(quoteId: string): Promise<SavedQuote> {
  return fetchJson<SavedQuote>(`/quotes/${quoteId}/save`, {
    method: "POST",
  });
}

export function getSavedQuotes(): Promise<{ items: SavedQuote[] }> {
  return fetchJson<{ items: SavedQuote[] }>("/quotes/saved");
}

export function deleteSavedQuote(quoteId: string): Promise<{ quote_id: string }> {
  return fetchJson<{ quote_id: string }>(`/quotes/saved/${quoteId}`, {
    method: "DELETE",
  });
}
