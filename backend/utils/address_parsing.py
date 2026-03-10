import re

ABBREVIATIONS = {
    "STREET": "ST", "ROAD": "RD", "AVENUE": "AVE", "BOULEVARD": "BLVD",
    "DRIVE": "DR", "FLOOR": "FL", "BUILDING": "BLDG", "SUITE": "STE",
    "NUMBER": "NO", "APARTMENT": "APT",
}

# Common country names and codes
COUNTRIES = {
    "CHINA": "CN", "INDIA": "IN", "UNITED STATES": "US", "USA": "US",
    "UNITED KINGDOM": "GB", "UK": "GB", "GERMANY": "DE", "FRANCE": "FR",
    "JAPAN": "JP", "SOUTH KOREA": "KR", "KOREA": "KR",
    "TAIWAN": "TW", "HONG KONG": "HK", "SINGAPORE": "SG",
    "MALAYSIA": "MY", "THAILAND": "TH", "VIETNAM": "VN",
    "INDONESIA": "ID", "PHILIPPINES": "PH", "BANGLADESH": "BD",
    "PAKISTAN": "PK", "SRI LANKA": "LK", "UAE": "AE",
    "SAUDI ARABIA": "SA", "TURKEY": "TR", "BRAZIL": "BR",
    "MEXICO": "MX", "CANADA": "CA", "AUSTRALIA": "AU",
    "NEW ZEALAND": "NZ", "SOUTH AFRICA": "ZA", "ITALY": "IT",
    "SPAIN": "ES", "NETHERLANDS": "NL", "SWITZERLAND": "CH",
    "SWEDEN": "SE", "NORWAY": "NO", "DENMARK": "DK",
    "BELGIUM": "BE", "AUSTRIA": "AT", "PORTUGAL": "PT",
    "IRELAND": "IE", "POLAND": "PL", "CZECH REPUBLIC": "CZ",
    "EGYPT": "EG", "NIGERIA": "NG", "KENYA": "KE",
}


def normalize_address(address: str) -> str:
    addr = address.upper().strip()
    addr = re.sub(r"\s+", " ", addr)
    for full, abbr in ABBREVIATIONS.items():
        addr = re.sub(rf"\b{full}\b", abbr, addr)
    return addr


def extract_country(address: str) -> str | None:
    addr_upper = address.upper()
    # Check from longest country name to shortest for best match
    for country in sorted(COUNTRIES.keys(), key=len, reverse=True):
        if country in addr_upper:
            return COUNTRIES[country]
    return None


def same_country(addr_a: str, addr_b: str) -> bool:
    country_a = extract_country(addr_a)
    country_b = extract_country(addr_b)
    if country_a and country_b:
        return country_a == country_b
    return False
