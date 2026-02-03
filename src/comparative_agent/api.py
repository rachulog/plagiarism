from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from comparative_agent.agent import compare_prices

app = FastAPI(title="Comparative Pricing Agent")


class CompareRequest(BaseModel):
    product: str = Field(..., description="Product name or query")
    urls: List[str] = Field(..., min_items=1, description="Product page URLs to compare")
    base_currency: str = Field("USD", description="Normalize prices to this currency")
    top_k: int = Field(5, ge=1, le=20, description="Number of sources to retrieve")


class QuoteResponse(BaseModel):
    amount: float
    currency: str
    raw: str
    url: str
    site: str
    product_hint: str | None = None


class SourceResponse(BaseModel):
    url: str
    site: str
    score: float


class CompareResponse(BaseModel):
    best_quote: QuoteResponse | None
    converted_amount: float | None
    currency: str
    sources: List[SourceResponse]
    quotes: List[QuoteResponse]


@app.post("/compare", response_model=CompareResponse)
def compare(payload: CompareRequest) -> CompareResponse:
    if not payload.urls:
        raise HTTPException(status_code=400, detail="At least one URL is required.")
    result = compare_prices(
        product=payload.product,
        urls=payload.urls,
        base_currency=payload.base_currency,
        top_k=payload.top_k,
    )
    best_quote = None
    if result.best_quote is not None:
        best_quote = QuoteResponse(
            amount=result.best_quote.amount,
            currency=result.best_quote.currency,
            raw=result.best_quote.raw,
            url=result.best_quote.url,
            site=result.best_quote.site,
            product_hint=result.best_quote.product_hint,
        )
    sources = [
        SourceResponse(url=item.document.url, site=item.document.site, score=item.score)
        for item in result.top_sources
    ]
    quotes = [
        QuoteResponse(
            amount=quote.amount,
            currency=quote.currency,
            raw=quote.raw,
            url=quote.url,
            site=quote.site,
            product_hint=quote.product_hint,
        )
        for quote in result.all_quotes
    ]
    return CompareResponse(
        best_quote=best_quote,
        converted_amount=result.converted_amount,
        currency=result.currency,
        sources=sources,
        quotes=quotes,
    )
