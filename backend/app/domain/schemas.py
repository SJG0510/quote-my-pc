from typing import Literal

from pydantic import BaseModel, Field, field_validator


Purpose = Literal["office", "gaming", "video_edit", "3d", "deep_learning"]


class QuoteRequestPayload(BaseModel):
    budget: int = Field(..., ge=300_000, le=10_000_000)
    purpose: Purpose
    preferred_brands: list[str] = Field(default_factory=list, max_length=6)

    @field_validator("preferred_brands")
    @classmethod
    def normalize_brands(cls, value: list[str]) -> list[str]:
        return [brand.strip() for brand in value if brand.strip()]


class CustomBuildPayload(BaseModel):
    budget: int = Field(..., ge=300_000, le=10_000_000)
    purpose: Purpose
    selected_part_ids: dict[str, str]


class QuoteItem(BaseModel):
    category: str
    brand: str
    model: str
    price: int
    reason: str


class CompatibilityCheck(BaseModel):
    rule: str
    status: Literal["pass", "warn", "fail"]
    message: str


class QuoteResult(BaseModel):
    quote_id: str
    total_price: int
    score: float
    summary: str
    items: list[QuoteItem]
    checks: list[CompatibilityCheck]
    diff_points: list[str] = Field(default_factory=list)
