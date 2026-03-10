import re

from rapidfuzz import fuzz


class FuzzyMatcher:
    def match(self, str_a: str, str_b: str) -> float:
        if not str_a or not str_b:
            return 0.0
        a = self._normalize(str_a)
        b = self._normalize(str_b)
        return fuzz.token_sort_ratio(a, b) / 100.0

    def match_names(self, name_a: str, name_b: str) -> float:
        if not name_a or not name_b:
            return 0.0
        a = self._normalize_name(name_a)
        b = self._normalize_name(name_b)
        return fuzz.token_sort_ratio(a, b) / 100.0

    def match_addresses(self, addr_a: str, addr_b: str) -> float:
        if not addr_a or not addr_b:
            return 0.0
        a = self._normalize_address(addr_a)
        b = self._normalize_address(addr_b)
        # token_set_ratio handles addresses where one has extra details
        return fuzz.token_set_ratio(a, b) / 100.0

    def _normalize(self, text: str) -> str:
        text = text.upper().strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s]", "", text)
        return text

    def _normalize_name(self, name: str) -> str:
        name = self._normalize(name)
        replacements = {
            "LIMITED": "LTD", "CORPORATION": "CORP", "INCORPORATED": "INC",
            "COMPANY": "CO", "INTERNATIONAL": "INTL", "MANUFACTURING": "MFG",
            "INDUSTRIES": "IND", "ENTERPRISE": "ENT", "PRIVATE": "PVT",
        }
        for full, abbr in replacements.items():
            name = name.replace(full, abbr)
        return name

    def _normalize_address(self, addr: str) -> str:
        addr = self._normalize(addr)
        replacements = {
            "STREET": "ST", "ROAD": "RD", "AVENUE": "AVE", "BOULEVARD": "BLVD",
            "DRIVE": "DR", "FLOOR": "FL", "BUILDING": "BLDG", "SUITE": "STE",
            "NUMBER": "NO", "APARTMENT": "APT",
        }
        for full, abbr in replacements.items():
            addr = addr.replace(full, abbr)
        return addr


fuzzy_matcher = FuzzyMatcher()
