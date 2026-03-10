from datetime import datetime

from models.enums import MatchStatus, Severity
from models.schemas import Session, ComplianceReport, FieldComparison


class ReportGenerator:
    def generate(self, session: Session) -> ComplianceReport:
        if not session.comparison_results:
            return ComplianceReport(
                session_id=session.session_id,
                lc_document=session.lc_document,
                generated_at=datetime.now(),
            )

        all_comparisons = []
        for doc_comp in session.comparison_results:
            all_comparisons.extend(doc_comp.field_comparisons)

        total_match = sum(1 for c in all_comparisons if c.match_status == MatchStatus.MATCH)
        total_evaluated = sum(
            1 for c in all_comparisons
            if c.match_status in (MatchStatus.MATCH, MatchStatus.MISMATCH, MatchStatus.MISSING)
        )
        overall_score = (total_match / total_evaluated * 100) if total_evaluated > 0 else 0

        critical = [
            c for c in all_comparisons
            if c.severity == Severity.CRITICAL and c.match_status != MatchStatus.MATCH
        ]
        warnings = [
            c for c in all_comparisons
            if c.severity == Severity.WARNING and c.match_status != MatchStatus.MATCH
        ]

        return ComplianceReport(
            session_id=session.session_id,
            lc_document=session.lc_document,
            document_comparisons=session.comparison_results,
            overall_compliance_score=round(overall_score, 1),
            critical_discrepancies=critical,
            warnings=warnings,
            generated_at=datetime.now(),
        )


report_generator = ReportGenerator()
