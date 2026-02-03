from __future__ import annotations

import dataclasses
from typing import Dict, Optional

import requests


@dataclasses.dataclass
class CurrencyConverter:
    base_currency: str = "USD"
    _cache: Dict[str, Dict[str, float]] = dataclasses.field(default_factory=dict)

    def convert(self, amount: float, currency: str) -> Optional[float]:
        currency = currency.upper()
        if currency == self.base_currency:
            return amount
        rates = self._get_rates(currency)
        if not rates:
            return None
        rate = rates.get(self.base_currency)
        if rate is None:
            return None
        return amount * rate

    def _get_rates(self, base: str) -> Optional[Dict[str, float]]:
        if base in self._cache:
            return self._cache[base]
        try:
            response = requests.get(
                "https://api.exchangerate.host/latest",
                params={"base": base},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return None
        rates = payload.get("rates")
        if not isinstance(rates, dict):
            return None
        self._cache[base] = {key.upper(): float(value) for key, value in rates.items()}
        return self._cache[base]
