from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Document:
    url: str
    title: str
    text: str
    site: str


@dataclass(frozen=True)
class PriceQuote:
    amount: float
    currency: str
    raw: str
    url: str
    site: str
    product_hint: Optional[str] = None
