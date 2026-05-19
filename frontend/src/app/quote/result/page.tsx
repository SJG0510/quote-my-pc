import { QuoteResultView } from "@/components/quote/QuoteResultView";
import type { QuoteRequest } from "@/lib/types";


type Props = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};


export default async function QuoteResultPage({ searchParams }: Props) {
  const params = await searchParams;
  const quoteId = typeof params.quote_id === "string" ? params.quote_id : "";
  const request: QuoteRequest = {
    budget: Number(typeof params.budget === "string" ? params.budget : 0),
    purpose: (typeof params.purpose === "string" ? params.purpose : "gaming") as QuoteRequest["purpose"],
    preferred_brands:
      typeof params.brands === "string"
        ? params.brands
            .split(",")
            .map((brand) => brand.trim())
            .filter(Boolean)
        : [],
  };

  return (
    <main className="page-shell">
      <div className="page-content">
        <QuoteResultView quoteId={quoteId} request={request} />
      </div>
    </main>
  );
}
