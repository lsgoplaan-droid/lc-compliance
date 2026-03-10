from dataclasses import dataclass, field
from typing import Optional

from models.enums import MatchStrategy, Severity


@dataclass
class FieldMatchConfig:
    strategy: MatchStrategy
    severity: Severity
    threshold: float = 1.0          # For fuzzy/contains matching (0.0-1.0)
    tolerance_pct: float = 0.0      # For numeric matching (percentage)
    ucp_rule: Optional[str] = None


MATCH_CONFIG: dict[str, FieldMatchConfig] = {
    # Exact match fields
    "lc_number": FieldMatchConfig(
        strategy=MatchStrategy.EXACT, severity=Severity.CRITICAL
    ),
    "currency": FieldMatchConfig(
        strategy=MatchStrategy.EXACT, severity=Severity.CRITICAL
    ),
    "hs_codes": FieldMatchConfig(
        strategy=MatchStrategy.EXACT, severity=Severity.CRITICAL
    ),
    "incoterms": FieldMatchConfig(
        strategy=MatchStrategy.EXACT, severity=Severity.CRITICAL
    ),

    # Numeric match fields
    "amount": FieldMatchConfig(
        strategy=MatchStrategy.NUMERIC, severity=Severity.CRITICAL, tolerance_pct=0.0,
        ucp_rule="Art. 18(b): Invoice must not exceed LC amount",
    ),
    "quantity": FieldMatchConfig(
        strategy=MatchStrategy.NUMERIC, severity=Severity.CRITICAL, tolerance_pct=5.0,
        ucp_rule="Art. 30(a): +/-5% tolerance unless prohibited",
    ),
    "unit_price": FieldMatchConfig(
        strategy=MatchStrategy.NUMERIC, severity=Severity.WARNING, tolerance_pct=5.0,
        ucp_rule="Art. 30(a): +/-5% tolerance unless prohibited",
    ),

    # Fuzzy match fields
    "beneficiary_name": FieldMatchConfig(
        strategy=MatchStrategy.FUZZY, severity=Severity.CRITICAL, threshold=0.85
    ),
    "beneficiary_address": FieldMatchConfig(
        strategy=MatchStrategy.FUZZY, severity=Severity.WARNING, threshold=0.70,
        ucp_rule="Art. 14(j): Address need not match if same country",
    ),
    "applicant_name": FieldMatchConfig(
        strategy=MatchStrategy.FUZZY, severity=Severity.CRITICAL, threshold=0.85
    ),
    "applicant_address": FieldMatchConfig(
        strategy=MatchStrategy.FUZZY, severity=Severity.WARNING, threshold=0.70,
        ucp_rule="Art. 14(j): Address need not match if same country",
    ),

    # Contains match (goods description)
    "goods_description": FieldMatchConfig(
        strategy=MatchStrategy.CONTAINS, severity=Severity.CRITICAL, threshold=0.75,
    ),

    # Date match fields
    "expiry_date": FieldMatchConfig(
        strategy=MatchStrategy.DATE, severity=Severity.CRITICAL
    ),
    "latest_shipment_date": FieldMatchConfig(
        strategy=MatchStrategy.DATE, severity=Severity.CRITICAL,
        ucp_rule="Shipped date must not exceed latest shipment date",
    ),

    # Boolean match fields
    "partial_shipments": FieldMatchConfig(
        strategy=MatchStrategy.BOOLEAN, severity=Severity.WARNING
    ),
    "transhipment": FieldMatchConfig(
        strategy=MatchStrategy.BOOLEAN, severity=Severity.WARNING
    ),

    # Fuzzy match for ports
    "port_of_loading": FieldMatchConfig(
        strategy=MatchStrategy.FUZZY, severity=Severity.CRITICAL, threshold=0.85
    ),
    "port_of_discharge": FieldMatchConfig(
        strategy=MatchStrategy.FUZZY, severity=Severity.CRITICAL, threshold=0.85
    ),
}
