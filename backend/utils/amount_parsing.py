import re
from typing import Optional, Tuple

# Common currency codes
CURRENCY_CODES = {
    "USD", "EUR", "GBP", "JPY", "CNY", "CHF", "AUD", "CAD", "HKD", "SGD",
    "INR", "AED", "SAR", "KRW", "THB", "MYR", "IDR", "PHP", "VND", "BDT",
    "PKR", "LKR", "TWD", "NZD", "ZAR", "BRL", "MXN", "TRY",
}

CURRENCY_SYMBOLS = {
    "$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR",
}


def parse_currency(text: str) -> Optional[str]:
    if not text:
        return None
    text = text.strip().upper()

    # Check for currency code
    for code in CURRENCY_CODES:
        if code in text:
            return code

    # Check for symbol
    for symbol, code in CURRENCY_SYMBOLS.items():
        if symbol in text:
            return code

    return None


def parse_amount(text: str) -> Optional[float]:
    if not text:
        return None
    text = text.strip()

    # Remove currency codes and symbols
    text = re.sub(r"[A-Z]{3}", "", text)
    for symbol in CURRENCY_SYMBOLS:
        text = text.replace(symbol, "")
    text = text.strip()

    # Detect European format (1.234.567,89) vs US format (1,234,567.89)
    # If last separator is a comma, it's European
    last_dot = text.rfind(".")
    last_comma = text.rfind(",")

    if last_comma > last_dot:
        # European format: dots are thousands, comma is decimal
        text = text.replace(".", "").replace(",", ".")
    else:
        # US format: commas are thousands, dot is decimal
        text = text.replace(",", "")

    # Remove any remaining non-numeric chars except dot
    text = re.sub(r"[^\d.]", "", text)

    try:
        return float(text)
    except ValueError:
        return None


def parse_currency_and_amount(text: str) -> Tuple[Optional[str], Optional[float]]:
    return parse_currency(text), parse_amount(text)
