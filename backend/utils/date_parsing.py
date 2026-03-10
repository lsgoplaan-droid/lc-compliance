import re
from datetime import date
from typing import Optional

from dateutil import parser as dateutil_parser


def parse_date(text: str) -> Optional[date]:
    if not text:
        return None

    text = text.strip()

    # Try common trade document formats explicitly
    formats = [
        r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})",  # DD/MM/YYYY or MM/DD/YYYY
        r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{4})",
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{1,2}),?\s+(\d{4})",
        r"(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})",  # YYYY-MM-DD
    ]

    for pattern in formats:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            break

    # Use dateutil as fallback with dayfirst=True (international trade standard)
    try:
        parsed = dateutil_parser.parse(text, dayfirst=True, fuzzy=True)
        return parsed.date()
    except (ValueError, OverflowError):
        return None
