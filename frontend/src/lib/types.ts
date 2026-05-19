export type Purpose = "office" | "gaming" | "video_edit" | "3d" | "deep_learning";

export type QuoteRequest = {
  budget: number;
  purpose: Purpose;
  preferred_brands: string[];
};

export type QuoteItem = {
  category: string;
  brand: string;
  model: string;
  price: number;
  reason: string;
};

export type CompatibilityCheck = {
  rule: string;
  status: "pass" | "warn" | "fail";
  message: string;
};

export type QuoteResponse = {
  quote_id: string;
  request: QuoteRequest;
  summary: string;
  total_price: number;
  score: number;
  items: QuoteItem[];
  checks: CompatibilityCheck[];
  warnings: string[];
  generated_at: string;
};

export type SavedQuote = QuoteResponse & {
  saved_at: string;
};

export type AlternativeQuote = {
  quote_id: string;
  total_price: number;
  score: number;
  summary: string;
  items: QuoteItem[];
  checks: CompatibilityCheck[];
  diff_points: string[];
};

export type FiltersResponse = {
  brands: Record<string, string[]>;
  categories: string[];
  purpose_presets: { value: Purpose; label: string }[];
};
