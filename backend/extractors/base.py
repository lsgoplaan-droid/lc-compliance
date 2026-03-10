import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from models.schemas import ExtractedField


class BaseFieldExtractor(ABC):
    @abstractmethod
    def extract_fields(self, raw_text: str) -> Dict[str, ExtractedField]:
        pass

    def _find_pattern(
        self, text: str, patterns: List[str], flags=re.IGNORECASE
    ) -> Optional[str]:
        for pattern in patterns:
            match = re.search(pattern, text, flags)
            if match:
                return match.group(1).strip()
        return None

    def _find_pattern_confidence(
        self, text: str, patterns: List[str], flags=re.IGNORECASE
    ) -> tuple[Optional[str], float]:
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, text, flags)
            if match:
                # Earlier patterns are more specific = higher confidence
                confidence = 1.0 - (i * 0.1)
                return match.group(1).strip(), max(confidence, 0.5)
        return None, 0.0

    def _extract_block_after_keyword(
        self, text: str, keywords: List[str], max_lines: int = 4
    ) -> Optional[str]:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            line_upper = line.upper().strip()
            for kw in keywords:
                if kw.upper() in line_upper:
                    # Check if value is on the same line after a colon/separator
                    after_kw = re.split(r"[:]\s*", line, maxsplit=1)
                    if len(after_kw) > 1 and after_kw[1].strip():
                        block_lines = [after_kw[1].strip()]
                    else:
                        block_lines = []

                    # Collect subsequent non-empty lines
                    for j in range(i + 1, min(i + 1 + max_lines, len(lines))):
                        next_line = lines[j].strip()
                        if not next_line:
                            break
                        # Stop if we hit another keyword-like line
                        if re.match(r"^[A-Z][A-Z\s]{2,}:", next_line):
                            break
                        block_lines.append(next_line)

                    if block_lines:
                        return "\n".join(block_lines)
        return None

    def _make_field(
        self, value: Optional[str], confidence: float = 0.0, source: Optional[str] = None
    ) -> ExtractedField:
        return ExtractedField(
            value=value,
            raw_source_text=source,
            confidence=confidence if value else 0.0,
        )
