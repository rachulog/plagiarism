from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from comparative_agent.currency import CurrencyConverter
from comparative_agent.models import Document, PriceQuote
from comparative_agent.rag import RetrievalResult, Retriever, pick_backend
from comparative_agent.sources import extract_price_quotes, fetch_documents


@dataclass(frozen=True)
class ComparisonResult:
    best_quote: Optional[PriceQuote]
    converted_amount: Optional[float]
    currency: str
    top_sources: List[RetrievalResult]
    all_quotes: List[PriceQuote]


def compare_prices(
    product: str,
    urls: Iterable[str],
    base_currency: str = "USD",
    top_k: int = 5,
    prefer_sentence_transformers: bool = True,
) -> ComparisonResult:
    documents = fetch_documents(list(urls))
    retriever = Retriever(pick_backend(prefer_sentence_transformers=prefer_sentence_transformers))
    retriever.index(documents)
    top_sources = retriever.search(product, top_k=top_k)
    relevant_docs = [result.document for result in top_sources]
    quotes = extract_price_quotes(relevant_docs)
    converter = CurrencyConverter(base_currency=base_currency)
    best_quote: Optional[PriceQuote] = None
    best_converted: Optional[float] = None
    for quote in quotes:
        converted = converter.convert(quote.amount, quote.currency)
        if converted is None:
            continue
        if best_converted is None or converted < best_converted:
            best_quote = quote
            best_converted = converted
    return ComparisonResult(
        best_quote=best_quote,
        converted_amount=best_converted,
        currency=base_currency,
        top_sources=top_sources,
        all_quotes=quotes,
    )
