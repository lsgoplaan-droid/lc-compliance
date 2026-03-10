from typing import List

from models.enums import DocumentType, MatchStatus, Severity
from models.schemas import FieldComparison, ExtractedDocument
from utils.address_parsing import same_country


def apply_ucp600_rules(
    comparisons: List[FieldComparison],
    lc_doc: ExtractedDocument,
    supporting_doc: ExtractedDocument,
) -> List[FieldComparison]:
    results = list(comparisons)

    # Art. 14(j): Address tolerance for non-transport documents
    # Addresses on invoice, cert of origin, packing list need not match exactly
    # as long as they are in the same country
    if supporting_doc.document_type != DocumentType.BILL_OF_LADING:
        for comp in results:
            if "address" in comp.field_name and comp.match_status == MatchStatus.MISMATCH:
                if comp.lc_value and comp.doc_value and same_country(comp.lc_value, comp.doc_value):
                    comp.severity = Severity.INFO
                    comp.note = (
                        (comp.note or "")
                        + " [Art. 14(j): different address, same country - acceptable]"
                    ).strip()

    # Art. 18(c): Invoice goods description must correspond to LC description (stricter)
    if supporting_doc.document_type == DocumentType.COMMERCIAL_INVOICE:
        for comp in results:
            if (
                comp.field_name == "goods_description"
                and comp.match_status == MatchStatus.MISMATCH
                and comp.similarity_score is not None
                and comp.similarity_score < 0.80
            ):
                comp.severity = Severity.CRITICAL
                comp.note = (
                    (comp.note or "")
                    + " [Art. 18(c): Invoice goods must correspond to LC description]"
                ).strip()

    return results
