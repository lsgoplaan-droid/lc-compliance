"""Generate matching supporting documents from LC advice fields.

Given extracted LC fields, produces text content for:
  - Commercial Invoice
  - Bill of Lading
  - Certificate of Origin
  - Packing List

The generated documents are designed to be compliant with the LC terms,
so when run through the comparison engine they should score high.
"""

import re
from datetime import datetime, timedelta
from typing import Dict

from models.schemas import ExtractedField


def _val(fields: Dict[str, ExtractedField], key: str) -> str:
    """Get field value or empty string."""
    f = fields.get(key)
    return (f.value or "") if f else ""


def _parse_quantity_unit(qty_str: str) -> tuple[str, str]:
    """Parse '600 METRIC TONS (+/- 5 PCT)' -> ('600.000', 'METRIC TONS')."""
    if not qty_str:
        return "0", ""
    m = re.match(r"([\d,]+\.?\d*)\s*(.*?)(?:\s*\(\+/-.*)?$", qty_str.strip())
    if not m:
        return qty_str.strip(), ""
    num = m.group(1)
    unit = m.group(2).strip()
    # Normalize number to 3 decimal places for weight units
    try:
        n = float(num.replace(",", ""))
        if unit.upper() in ("MT", "MTS", "METRIC TONS", "METRIC TON"):
            num = f"{n:,.3f}"
        elif unit.upper() in ("KGS", "KG"):
            num = f"{n:,.2f}"
        else:
            num = f"{n:,.0f}".replace(",", "") if n == int(n) else f"{n:,.3f}"
    except ValueError:
        pass
    return num, unit


def _qty_in_kgs(qty_str: str) -> str:
    """Convert MT quantity to KGS string."""
    num, unit = _parse_quantity_unit(qty_str)
    try:
        n = float(num.replace(",", ""))
    except ValueError:
        return num
    if unit.upper() in ("MT", "MTS", "METRIC TONS", "METRIC TON"):
        kgs = n * 1000
        return f"{kgs:,.2f} KGS"
    return f"{num} {unit}".strip()


def _gross_weight(qty_str: str) -> str:
    """Estimate gross weight (net + ~0.5-1% packaging)."""
    num, unit = _parse_quantity_unit(qty_str)
    try:
        n = float(num.replace(",", ""))
    except ValueError:
        return num
    if unit.upper() in ("MT", "MTS", "METRIC TONS", "METRIC TON"):
        gross_kgs = n * 1000 * 1.006  # ~0.6% tare
        return f"{gross_kgs:,.2f} KGS"
    elif unit.upper() in ("KGS", "KG"):
        gross = n * 1.006
        return f"{gross:,.2f} KGS"
    elif unit.upper() in ("PCS", "PIECES"):
        # Estimate 0.3 kg per piece for garments, 0.5 kg for general
        return f"{n * 0.3:,.2f} KGS"
    return f"{num} {unit}".strip()


def _ship_date_from_latest(latest_str: str) -> str:
    """Generate a shipped date a few days before latest shipment date."""
    if not latest_str:
        return datetime.now().strftime("%d %B %Y").upper()
    # Try DDMMMYY format
    from dateutil import parser as dateparser
    try:
        dt = dateparser.parse(latest_str, dayfirst=True)
        ship = dt - timedelta(days=8)
        return ship.strftime("%d %B %Y").upper()
    except Exception:
        return latest_str


def _invoice_date_from_latest(latest_str: str) -> str:
    """Generate invoice date ~15 days before latest shipment."""
    if not latest_str:
        return datetime.now().strftime("%d %B %Y").upper()
    from dateutil import parser as dateparser
    try:
        dt = dateparser.parse(latest_str, dayfirst=True)
        inv_dt = dt - timedelta(days=15)
        return inv_dt.strftime("%d %B %Y").upper()
    except Exception:
        return latest_str


def _extract_port_country(port_str: str) -> str:
    """Extract country from port string like 'CHITTAGONG, BANGLADESH' -> 'BANGLADESH'."""
    if not port_str:
        return ""
    # Handle "ANY SEAPORT OF CHINA"
    m = re.search(r"(?:SEAPORT|PORT)\s+OF\s+(\w[\w\s]*)", port_str, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    parts = port_str.split(",")
    if len(parts) >= 2:
        return parts[-1].strip()
    return port_str.strip()


def _extract_loading_port(port_str: str) -> str:
    """Resolve 'ANY SEAPORT OF CHINA' to a specific port for supporting docs."""
    upper = (port_str or "").upper()
    if "ANY" in upper and "CHINA" in upper:
        return "SHANGHAI, CHINA"
    if "ANY" in upper and "SINGAPORE" in upper:
        return "PORT OF SINGAPORE, SINGAPORE"
    if "ANY" in upper and "BANGLADESH" in upper:
        return "CHITTAGONG, BANGLADESH"
    if "ANY" in upper and "INDIA" in upper:
        return "NHAVA SHEVA, INDIA"
    if "ANY" in upper and "UAE" in upper or "ARAB EMIRATES" in upper:
        return "JEBEL ALI, UAE"
    return port_str or ""


def generate_invoice(lc_fields: Dict[str, ExtractedField]) -> str:
    """Generate Commercial Invoice text from LC fields."""
    beneficiary = _val(lc_fields, "beneficiary_name")
    beneficiary_addr = _val(lc_fields, "beneficiary_address")
    applicant = _val(lc_fields, "applicant_name")
    applicant_addr = _val(lc_fields, "applicant_address")
    lc_num = _val(lc_fields, "lc_number")
    currency = _val(lc_fields, "currency") or "USD"
    amount = _val(lc_fields, "amount")
    goods = _val(lc_fields, "goods_description")
    hs = _val(lc_fields, "hs_codes")
    qty = _val(lc_fields, "quantity")
    unit_price = _val(lc_fields, "unit_price")
    incoterms = _val(lc_fields, "incoterms")
    pol = _extract_loading_port(_val(lc_fields, "port_of_loading"))
    pod = _val(lc_fields, "port_of_discharge")
    latest = _val(lc_fields, "latest_shipment_date")
    origin = _val(lc_fields, "country_of_origin") or _extract_port_country(pol)

    inv_date = _invoice_date_from_latest(latest)
    inv_no = f"INV/{datetime.now().strftime('%Y')}/001"
    qty_kgs = _qty_in_kgs(qty)
    gross = _gross_weight(qty)
    num_qty, unit_qty = _parse_quantity_unit(qty)

    return f"""COMMERCIAL INVOICE

SELLER:
{beneficiary}
{beneficiary_addr}

INVOICE NO: {inv_no}
DATE: {inv_date}
L/C NO: {lc_num}

BUYER:
{applicant}
{applicant_addr}

PORT OF LOADING: {pol}
PORT OF DISCHARGE: {pod}

DESCRIPTION OF GOODS:
{goods}

QUANTITY: {num_qty} {unit_qty}
PRICE {currency} {unit_price}
TOTAL AMOUNT: {currency} {amount}

H.S. CODE: {hs}
COUNTRY OF ORIGIN: {origin}
TRADE TERM: {incoterms}

NET WEIGHT  : {qty_kgs}
GROSS WEIGHT: {gross}

WE CERTIFY THAT THIS INVOICE SHOWS THE ACTUAL PRICE OF THE GOODS DESCRIBED,
THAT ALL PARTICULARS ARE TRUE AND CORRECT.

AUTHORIZED SIGNATORY
FOR {beneficiary}
"""


def generate_bill_of_lading(lc_fields: Dict[str, ExtractedField]) -> str:
    """Generate Bill of Lading text from LC fields."""
    beneficiary = _val(lc_fields, "beneficiary_name")
    beneficiary_addr = _val(lc_fields, "beneficiary_address")
    applicant = _val(lc_fields, "applicant_name")
    applicant_addr = _val(lc_fields, "applicant_address")
    lc_num = _val(lc_fields, "lc_number")
    goods = _val(lc_fields, "goods_description")
    hs = _val(lc_fields, "hs_codes")
    qty = _val(lc_fields, "quantity")
    pol = _extract_loading_port(_val(lc_fields, "port_of_loading"))
    pod = _val(lc_fields, "port_of_discharge")
    latest = _val(lc_fields, "latest_shipment_date")

    ship_date = _ship_date_from_latest(latest)
    bl_no = f"BL/{datetime.now().strftime('%Y')}/001"
    num_qty, unit_qty = _parse_quantity_unit(qty)
    gross = _gross_weight(qty)

    return f"""BILL OF LADING

SHIPPER:
{beneficiary}
{beneficiary_addr}

B/L NO: {bl_no}
DATE: {ship_date}

CONSIGNEE:
TO THE ORDER OF ISSUING BANK

NOTIFY PARTY:
{applicant}
{applicant_addr}

VESSEL / VOYAGE: TBN / V.001
PORT OF LOADING: {pol}
PORT OF DISCHARGE: {pod}

DESCRIPTION OF GOODS:
{num_qty} {unit_qty} OF {goods}
H.S. CODE: {hs}
L/C NO: {lc_num}

GROSS WEIGHT: {gross}

FREIGHT: PREPAID
NUMBER OF ORIGINAL B/L: THREE (3)

SHIPPED ON BOARD DATE: {ship_date}
CLEAN ON BOARD

SIGNED FOR THE CARRIER
"""


def generate_certificate_of_origin(lc_fields: Dict[str, ExtractedField]) -> str:
    """Generate Certificate of Origin text from LC fields."""
    beneficiary = _val(lc_fields, "beneficiary_name")
    beneficiary_addr = _val(lc_fields, "beneficiary_address")
    applicant = _val(lc_fields, "applicant_name")
    applicant_addr = _val(lc_fields, "applicant_address")
    goods = _val(lc_fields, "goods_description")
    hs = _val(lc_fields, "hs_codes")
    qty = _val(lc_fields, "quantity")
    pol = _extract_loading_port(_val(lc_fields, "port_of_loading"))
    pod = _val(lc_fields, "port_of_discharge")
    origin = _val(lc_fields, "country_of_origin") or _extract_port_country(pol)
    dest = _extract_port_country(pod)
    lc_num = _val(lc_fields, "lc_number")

    num_qty, unit_qty = _parse_quantity_unit(qty)
    cert_no = f"CO/{datetime.now().strftime('%Y')}/001"

    return f"""CERTIFICATE OF ORIGIN

CERTIFICATE NO: {cert_no}
DATE OF ISSUE: {_invoice_date_from_latest(_val(lc_fields, 'latest_shipment_date'))}

EXPORTER:
{beneficiary}
{beneficiary_addr}

CONSIGNEE / IMPORTER:
{applicant}
{applicant_addr}

COUNTRY OF ORIGIN: {origin}
COUNTRY OF DESTINATION: {dest}

PORT OF LOADING: {pol}
PORT OF DISCHARGE: {pod}

DESCRIPTION OF GOODS:
{goods}
QUANTITY: {num_qty} {unit_qty}
H.S. CODE: {hs}

L/C NO: {lc_num}

THIS IS TO CERTIFY THAT THE GOODS DESCRIBED ABOVE ORIGINATE IN {origin}.

AUTHORIZED SIGNATORY
CHAMBER OF COMMERCE
"""


def generate_packing_list(lc_fields: Dict[str, ExtractedField]) -> str:
    """Generate Packing List text from LC fields."""
    beneficiary = _val(lc_fields, "beneficiary_name")
    beneficiary_addr = _val(lc_fields, "beneficiary_address")
    applicant = _val(lc_fields, "applicant_name")
    applicant_addr = _val(lc_fields, "applicant_address")
    lc_num = _val(lc_fields, "lc_number")
    goods = _val(lc_fields, "goods_description")
    hs = _val(lc_fields, "hs_codes")
    qty = _val(lc_fields, "quantity")
    pol = _extract_loading_port(_val(lc_fields, "port_of_loading"))
    pod = _val(lc_fields, "port_of_discharge")
    origin = _val(lc_fields, "country_of_origin") or _extract_port_country(pol)

    num_qty, unit_qty = _parse_quantity_unit(qty)
    qty_kgs = _qty_in_kgs(qty)
    gross = _gross_weight(qty)

    return f"""PACKING LIST

SHIPPER:
{beneficiary}
{beneficiary_addr}

BUYER:
{applicant}
{applicant_addr}

L/C NO: {lc_num}

PORT OF LOADING: {pol}
PORT OF DISCHARGE: {pod}

PRODUCT: {goods}
H.S. CODE: {hs}
COUNTRY OF ORIGIN: {origin}

QUANTITY: {num_qty} {unit_qty}

NET WEIGHT  : {qty_kgs}
GROSS WEIGHT: {gross}

SHIPPING MARKS:
{applicant.split()[0] if applicant else 'BUYER'} / {_extract_port_country(pod)}
L/C NO: {lc_num}

AUTHORIZED SIGNATORY
FOR {beneficiary}
"""


def generate_all_documents(lc_fields: Dict[str, ExtractedField]) -> Dict[str, str]:
    """Generate all 4 supporting documents from LC fields.

    Returns dict mapping document type to generated text content.
    """
    return {
        "commercial_invoice": generate_invoice(lc_fields),
        "bill_of_lading": generate_bill_of_lading(lc_fields),
        "certificate_of_origin": generate_certificate_of_origin(lc_fields),
        "packing_list": generate_packing_list(lc_fields),
    }
