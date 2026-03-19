import re
from typing import List, Optional

from models.enums import DocumentType, MatchStatus, MatchStrategy, Severity
from models.schemas import (
    ExtractedDocument, FieldComparison, DocumentComparison, ComparisonSummary,
)
from rules.field_mappings import FIELD_MAPPINGS, FIELD_CATEGORIES
from rules.match_config import MATCH_CONFIG
from rules.ucp600 import apply_ucp600_rules
from services.fuzzy_matcher import fuzzy_matcher
from utils.amount_parsing import parse_amount
from utils.date_parsing import parse_date


class ComparisonEngine:
    def compare_document(
        self, lc_doc: ExtractedDocument, supporting_doc: ExtractedDocument
    ) -> DocumentComparison:
        doc_type = supporting_doc.document_type
        mapping = FIELD_MAPPINGS.get(doc_type, {})
        comparisons: List[FieldComparison] = []

        for lc_field_name, doc_field_name in mapping.items():
            config = MATCH_CONFIG.get(lc_field_name)
            if not config:
                continue

            lc_field = lc_doc.fields.get(lc_field_name)
            doc_field = supporting_doc.fields.get(doc_field_name)

            lc_value = lc_field.value if lc_field else None
            doc_value = doc_field.value if doc_field else None

            comparison = self._compare_field(
                field_name=lc_field_name,
                lc_value=lc_value,
                doc_value=doc_value,
                config=config,
            )
            comparisons.append(comparison)

        # Apply UCP 600 cross-field rules
        comparisons = apply_ucp600_rules(comparisons, lc_doc, supporting_doc)

        summary = self._compute_summary(comparisons)
        return DocumentComparison(
            doc_id=supporting_doc.doc_id,
            document_type=doc_type,
            original_filename=supporting_doc.original_filename,
            field_comparisons=comparisons,
            summary=summary,
        )

    def _compare_field(self, field_name, lc_value, doc_value, config):
        category = FIELD_CATEGORIES.get(field_name, "core")

        # Both missing
        if not lc_value and not doc_value:
            return FieldComparison(
                field_name=field_name, field_category=category,
                lc_value=lc_value, doc_value=doc_value,
                match_status=MatchStatus.NOT_APPLICABLE,
                match_strategy=config.strategy, severity=Severity.INFO,
            )

        # LC has value but doc missing
        if lc_value and not doc_value:
            return FieldComparison(
                field_name=field_name, field_category=category,
                lc_value=lc_value, doc_value=doc_value,
                match_status=MatchStatus.MISSING,
                match_strategy=config.strategy, severity=config.severity,
                note=f"Field present in LC but not found in document",
            )

        # Doc has value but not in LC
        if not lc_value and doc_value:
            return FieldComparison(
                field_name=field_name, field_category=category,
                lc_value=lc_value, doc_value=doc_value,
                match_status=MatchStatus.NOT_APPLICABLE,
                match_strategy=config.strategy, severity=Severity.INFO,
                note="Field not found in LC",
            )

        # Both have values - compare
        match config.strategy:
            case MatchStrategy.EXACT:
                return self._exact_match(field_name, category, lc_value, doc_value, config)
            case MatchStrategy.FUZZY:
                return self._fuzzy_match(field_name, category, lc_value, doc_value, config)
            case MatchStrategy.NUMERIC:
                return self._numeric_match(field_name, category, lc_value, doc_value, config)
            case MatchStrategy.DATE:
                return self._date_match(field_name, category, lc_value, doc_value, config)
            case MatchStrategy.BOOLEAN:
                return self._boolean_match(field_name, category, lc_value, doc_value, config)
            case MatchStrategy.CONTAINS:
                return self._contains_match(field_name, category, lc_value, doc_value, config)
            case _:
                return self._exact_match(field_name, category, lc_value, doc_value, config)

    def _exact_match(self, field_name, category, lc_value, doc_value, config):
        norm_lc = self._normalize_exact(lc_value)
        norm_doc = self._normalize_exact(doc_value)
        is_match = norm_lc == norm_doc
        return FieldComparison(
            field_name=field_name, field_category=category,
            lc_value=lc_value, doc_value=doc_value,
            match_status=MatchStatus.MATCH if is_match else MatchStatus.MISMATCH,
            match_strategy=config.strategy,
            similarity_score=1.0 if is_match else 0.0,
            severity=Severity.INFO if is_match else config.severity,
            ucp_rule=config.ucp_rule,
        )

    def _fuzzy_match(self, field_name, category, lc_value, doc_value, config):
        # Special port matching: "ANY SEAPORT OF <COUNTRY>" means any port in that country
        if field_name in ("port_of_loading", "port_of_discharge"):
            port_result = self._match_port(field_name, category, lc_value, doc_value, config)
            if port_result:
                return port_result

        if "name" in field_name:
            score = fuzzy_matcher.match_names(lc_value, doc_value)
        elif "address" in field_name:
            score = fuzzy_matcher.match_addresses(lc_value, doc_value)
        else:
            score = fuzzy_matcher.match(lc_value, doc_value)

        is_match = score >= config.threshold
        return FieldComparison(
            field_name=field_name, field_category=category,
            lc_value=lc_value, doc_value=doc_value,
            match_status=MatchStatus.MATCH if is_match else MatchStatus.MISMATCH,
            match_strategy=config.strategy,
            similarity_score=round(score, 3),
            severity=Severity.INFO if is_match else config.severity,
            ucp_rule=config.ucp_rule,
        )

    def _numeric_match(self, field_name, category, lc_value, doc_value, config):
        # For quantity fields, normalize weight units (MT vs KGS) before comparison
        if field_name == "quantity":
            lc_num = self._parse_quantity_normalized(lc_value)
            doc_num = self._parse_quantity_normalized(doc_value)
        else:
            lc_num = parse_amount(lc_value)
            doc_num = parse_amount(doc_value)

        if lc_num is None or doc_num is None:
            return FieldComparison(
                field_name=field_name, field_category=category,
                lc_value=lc_value, doc_value=doc_value,
                match_status=MatchStatus.MISMATCH,
                match_strategy=config.strategy, severity=config.severity,
                note="Could not parse numeric value",
                ucp_rule=config.ucp_rule,
            )

        # Special rule: invoice amount must not exceed LC amount
        if field_name == "amount" and doc_num > lc_num:
            return FieldComparison(
                field_name=field_name, field_category=category,
                lc_value=lc_value, doc_value=doc_value,
                match_status=MatchStatus.MISMATCH,
                match_strategy=config.strategy,
                similarity_score=round(min(lc_num, doc_num) / max(lc_num, doc_num), 3) if max(lc_num, doc_num) > 0 else 0,
                severity=Severity.CRITICAL,
                note=f"Document amount ({doc_num:,.2f}) exceeds LC amount ({lc_num:,.2f})",
                ucp_rule="Art. 18(b): Invoice must not exceed LC amount",
            )

        # For amount, doc can be less (partial drawing)
        if field_name == "amount" and doc_num <= lc_num:
            ratio = doc_num / lc_num if lc_num > 0 else 0
            note = None
            if ratio < 0.95:
                note = f"Invoice is {ratio*100:.1f}% of LC amount (partial drawing?)"
            return FieldComparison(
                field_name=field_name, field_category=category,
                lc_value=lc_value, doc_value=doc_value,
                match_status=MatchStatus.MATCH,
                match_strategy=config.strategy,
                similarity_score=round(ratio, 3),
                severity=Severity.INFO if ratio >= 0.95 else Severity.WARNING,
                note=note, ucp_rule=config.ucp_rule,
            )

        # Quantity/unit price with tolerance
        if lc_num == 0:
            is_match = doc_num == 0
            pct_diff = 0.0
        else:
            pct_diff = abs(doc_num - lc_num) / lc_num * 100
            is_match = pct_diff <= config.tolerance_pct

        return FieldComparison(
            field_name=field_name, field_category=category,
            lc_value=lc_value, doc_value=doc_value,
            match_status=MatchStatus.MATCH if is_match else MatchStatus.MISMATCH,
            match_strategy=config.strategy,
            similarity_score=round(1.0 - (pct_diff / 100), 3) if lc_num > 0 else (1.0 if is_match else 0.0),
            severity=Severity.INFO if is_match else config.severity,
            note=f"Difference: {pct_diff:.1f}%" if pct_diff > 0 else None,
            ucp_rule=config.ucp_rule,
        )

    def _date_match(self, field_name, category, lc_value, doc_value, config):
        lc_date = parse_date(lc_value)
        doc_date = parse_date(doc_value)

        if not lc_date or not doc_date:
            return FieldComparison(
                field_name=field_name, field_category=category,
                lc_value=lc_value, doc_value=doc_value,
                match_status=MatchStatus.MISMATCH,
                match_strategy=config.strategy, severity=config.severity,
                note="Could not parse date",
                ucp_rule=config.ucp_rule,
            )

        # For latest_shipment_date: shipped date must be on or before LC date
        if field_name == "latest_shipment_date":
            if doc_date <= lc_date:
                return FieldComparison(
                    field_name=field_name, field_category=category,
                    lc_value=lc_value, doc_value=doc_value,
                    match_status=MatchStatus.MATCH,
                    match_strategy=config.strategy, similarity_score=1.0,
                    severity=Severity.INFO,
                    note=f"Shipped {doc_date} (on or before {lc_date})",
                    ucp_rule=config.ucp_rule,
                )
            else:
                return FieldComparison(
                    field_name=field_name, field_category=category,
                    lc_value=lc_value, doc_value=doc_value,
                    match_status=MatchStatus.MISMATCH,
                    match_strategy=config.strategy, similarity_score=0.0,
                    severity=Severity.CRITICAL,
                    note=f"Shipped {doc_date} AFTER latest allowed {lc_date}",
                    ucp_rule=config.ucp_rule,
                )

        is_match = lc_date == doc_date
        return FieldComparison(
            field_name=field_name, field_category=category,
            lc_value=lc_value, doc_value=doc_value,
            match_status=MatchStatus.MATCH if is_match else MatchStatus.MISMATCH,
            match_strategy=config.strategy,
            similarity_score=1.0 if is_match else 0.0,
            severity=Severity.INFO if is_match else config.severity,
            ucp_rule=config.ucp_rule,
        )

    def _boolean_match(self, field_name, category, lc_value, doc_value, config):
        lc_bool = self._parse_boolean(lc_value)
        doc_bool = self._parse_boolean(doc_value)

        if lc_bool is None or doc_bool is None:
            return FieldComparison(
                field_name=field_name, field_category=category,
                lc_value=lc_value, doc_value=doc_value,
                match_status=MatchStatus.MISSING,
                match_strategy=config.strategy, severity=config.severity,
                note="Could not determine boolean value",
            )

        is_match = lc_bool == doc_bool
        return FieldComparison(
            field_name=field_name, field_category=category,
            lc_value=lc_value, doc_value=doc_value,
            match_status=MatchStatus.MATCH if is_match else MatchStatus.MISMATCH,
            match_strategy=config.strategy,
            similarity_score=1.0 if is_match else 0.0,
            severity=Severity.INFO if is_match else config.severity,
        )

    def _contains_match(self, field_name, category, lc_value, doc_value, config):
        lc_tokens = self._tokenize_goods(lc_value)
        doc_tokens = self._tokenize_goods(doc_value)

        if not lc_tokens or not doc_tokens:
            return FieldComparison(
                field_name=field_name, field_category=category,
                lc_value=lc_value, doc_value=doc_value,
                match_status=MatchStatus.MATCH if not lc_tokens else MatchStatus.MISMATCH,
                match_strategy=config.strategy, similarity_score=1.0 if not lc_tokens else 0.0,
                severity=Severity.INFO if not lc_tokens else config.severity,
            )

        # Check both directions: LC tokens found in doc, and doc tokens found in LC
        # Use the better score (handles cases where doc is a subset of LC or vice versa)
        def token_coverage(source_tokens, target_tokens):
            matched = 0
            for token in source_tokens:
                best = max(
                    (fuzzy_matcher.match(token, dt) for dt in target_tokens),
                    default=0.0,
                )
                if best >= 0.85:
                    matched += 1
            return matched / len(source_tokens) if source_tokens else 0.0

        lc_in_doc = token_coverage(lc_tokens, doc_tokens)
        doc_in_lc = token_coverage(doc_tokens, lc_tokens)
        coverage = max(lc_in_doc, doc_in_lc)

        is_match = coverage >= config.threshold
        note = None
        if not is_match:
            note = f"Only {coverage*100:.0f}% of description keywords matched"

        return FieldComparison(
            field_name=field_name, field_category=category,
            lc_value=lc_value, doc_value=doc_value,
            match_status=MatchStatus.MATCH if is_match else MatchStatus.MISMATCH,
            match_strategy=config.strategy,
            similarity_score=round(coverage, 3),
            severity=Severity.INFO if is_match else config.severity,
            note=note,
        )

    def _match_port(self, field_name, category, lc_value, doc_value, config):
        """Handle 'ANY SEAPORT/PORT OF <COUNTRY>' LC specifications."""
        lc_upper = lc_value.upper()
        doc_upper = doc_value.upper()
        m = re.match(r"ANY\s+(?:SEA)?PORT\s+(?:OF|IN)\s+(.+)", lc_upper)
        if m:
            country = m.group(1).strip()
            # If doc port is in that country, it's a match
            if country in doc_upper:
                return FieldComparison(
                    field_name=field_name, field_category=category,
                    lc_value=lc_value, doc_value=doc_value,
                    match_status=MatchStatus.MATCH,
                    match_strategy=config.strategy, similarity_score=1.0,
                    severity=Severity.INFO,
                    note=f"LC allows any port in {country}",
                    ucp_rule=config.ucp_rule,
                )
        return None

    @staticmethod
    def _parse_quantity_normalized(text: str) -> Optional[float]:
        """Parse a quantity value, normalizing weight units to MT (metric tons)."""
        if not text:
            return None
        upper = text.upper()
        # Extract just the numeric part (before unit text like "METRIC TONS")
        m = re.match(r"^[\s]*([0-9,]+\.?\d*)", text.strip())
        if not m:
            return None
        num_str = m.group(1).replace(",", "")
        try:
            raw_num = float(num_str)
        except ValueError:
            return None
        # Detect unit and normalize to MT
        if re.search(r"\bKGS?\b", upper):
            return raw_num / 1000.0  # KGS -> MT
        if re.search(r"\bLBS?\b", upper):
            return raw_num / 2204.62  # LBS -> MT
        # MT, MTS, METRIC TONS, or no unit — assume already in MT-compatible value
        return raw_num

    @staticmethod
    def _normalize_exact(val: str) -> str:
        return re.sub(r"[\s\-/.,]", "", val.upper().strip())

    @staticmethod
    def _parse_boolean(val: str) -> Optional[bool]:
        v = val.upper().strip()
        if v in ("ALLOWED", "PERMITTED", "YES", "Y"):
            return True
        if v in ("NOT ALLOWED", "PROHIBITED", "NO", "N"):
            return False
        return None

    @staticmethod
    def _tokenize_goods(text: str) -> list[str]:
        text = text.upper()
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = text.split()
        # Filter out common stopwords
        stopwords = {"THE", "OF", "AND", "OR", "A", "AN", "IN", "ON", "FOR", "TO", "AT", "AS", "PER", "WITH"}
        return [t for t in tokens if t not in stopwords and len(t) > 1]

    @staticmethod
    def _compute_summary(comparisons: List[FieldComparison]) -> ComparisonSummary:
        match_count = sum(1 for c in comparisons if c.match_status == MatchStatus.MATCH)
        mismatch_count = sum(1 for c in comparisons if c.match_status == MatchStatus.MISMATCH)
        missing_count = sum(1 for c in comparisons if c.match_status == MatchStatus.MISSING)
        total = match_count + mismatch_count + missing_count
        score = (match_count / total * 100) if total > 0 else 0

        return ComparisonSummary(
            match_count=match_count,
            mismatch_count=mismatch_count,
            missing_count=missing_count,
            total_fields=total,
            compliance_score=round(score, 1),
        )


comparison_engine = ComparisonEngine()
