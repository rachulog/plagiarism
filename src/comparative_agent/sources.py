from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Iterable, List, Sequence
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from comparative_agent.models import Document, PriceQuote

PRICE_PATTERN = re.compile(
    r"(?P<currency>USD|EUR|GBP|JPY|INR|KRW|AUD|CAD|CHF|CNY|SEK|NOK|MXN|BRL|ZAR|TRY|RUB|VND|PHP|IDR|SGD|HKD|NZD|AED|SAR|PLN|CZK|DKK|HUF|ILS|THB|MYR|KWD|QAR|CLP|COP|PEN|ARS|\\$|€|£|¥|₹|₩|₺|₽|₫)\\s?(?P<amount>[0-9][0-9,\\.]+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SourceConfig:
    timeout_s: int = 15
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    sleep_s: float = 0.5


def _clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "img", "video", "audio"]):
        tag.decompose()
    text = " ".join(soup.stripped_strings)
    return re.sub(r"\s+", " ", text)


def _get_site(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or parsed.path


def fetch_documents(urls: Sequence[str], config: SourceConfig | None = None) -> List[Document]:
    config = config or SourceConfig()
    headers = {"User-Agent": config.user_agent}
    documents: List[Document] = []
    for url in urls:
        response = requests.get(url, headers=headers, timeout=config.timeout_s)
        response.raise_for_status()
        text = _clean_text(response.text)
        title_match = re.search(r"<title>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else url
        documents.append(Document(url=url, title=title, text=text, site=_get_site(url)))
        time.sleep(config.sleep_s)
    return documents


def extract_price_quotes(documents: Iterable[Document]) -> List[PriceQuote]:
    quotes: List[PriceQuote] = []
    for doc in documents:
        for match in PRICE_PATTERN.finditer(doc.text):
            currency = match.group("currency")
            amount = match.group("amount")
            raw = match.group(0)
            normalized = _parse_amount(amount)
            if normalized is None:
                continue
            quotes.append(
                PriceQuote(
                    amount=normalized,
                    currency=currency.upper(),
                    raw=raw,
                    url=doc.url,
                    site=doc.site,
                    product_hint=doc.title,
                )
            )
    return quotes


def _parse_amount(value: str) -> float | None:
    cleaned = value.replace(" ", "")
    if cleaned.count(",") > 1 and "." not in cleaned:
        cleaned = cleaned.replace(",", "")
    if cleaned.count(".") > 1 and "," not in cleaned:
        cleaned = cleaned.replace(".", "")
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    else:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None
