from enum import Enum


class DocumentType(str, Enum):
    LC_ADVICE = "lc_advice"
    COMMERCIAL_INVOICE = "commercial_invoice"
    CERTIFICATE_OF_ORIGIN = "certificate_of_origin"
    BILL_OF_LADING = "bill_of_lading"
    PACKING_LIST = "packing_list"


class MatchStatus(str, Enum):
    MATCH = "match"
    MISMATCH = "mismatch"
    MISSING = "missing"
    NOT_APPLICABLE = "n/a"


class MatchStrategy(str, Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"
    NUMERIC = "numeric"
    DATE = "date"
    BOOLEAN = "boolean"
    CONTAINS = "contains"


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
