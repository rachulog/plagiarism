from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List


def _load_urls(args: argparse.Namespace) -> List[str]:
    urls: List[str] = []
    if args.urls:
        urls.extend(args.urls)
    if args.urls_file:
        urls.extend([line.strip() for line in Path(args.urls_file).read_text().splitlines() if line.strip()])
    if args.urls_json:
        payload = json.loads(Path(args.urls_json).read_text())
        urls.extend(payload.get("urls", []))
    return urls


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare product pricing across sources with RAG retrieval.")
    parser.add_argument("product", help="Product name or query to compare")
    parser.add_argument("--urls", nargs="*", help="List of URLs to compare")
    parser.add_argument("--urls-file", help="Path to a newline-delimited file of URLs")
    parser.add_argument("--urls-json", help="Path to JSON file with {\"urls\": [...]} format")
    parser.add_argument("--base-currency", default="USD", help="Currency to normalize prices into")
    parser.add_argument("--top-k", type=int, default=5, help="Number of retrieved sources to consider")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    urls = _load_urls(args)
    if not urls:
        raise SystemExit("Provide --urls, --urls-file, or --urls-json with at least one URL.")
    from comparative_agent.agent import compare_prices

    result = compare_prices(
        product=args.product,
        urls=urls,
        base_currency=args.base_currency,
        top_k=args.top_k,
    )
    if result.best_quote is None:
        print("No comparable prices found.")
        return
    quote = result.best_quote
    print(f"Best price: {quote.raw} ({quote.currency}) at {quote.site}")
    if result.converted_amount is not None:
        print(f"Normalized: {result.converted_amount:.2f} {result.currency}")
    print("\nTop sources:")
    for item in result.top_sources:
        print(f"- {item.document.site} ({item.score:.3f}) -> {item.document.url}")


if __name__ == "__main__":
    main()
