"""Generate sample Oil Trading LC document set as PDFs using reportlab."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "DocTitle", parent=styles["Heading1"],
    fontSize=16, alignment=TA_CENTER, spaceAfter=6, spaceBefore=0,
    textColor=colors.HexColor("#1a1a1a"),
)
subtitle_style = ParagraphStyle(
    "SubTitle", parent=styles["Normal"],
    fontSize=9, alignment=TA_CENTER, spaceAfter=12,
    textColor=colors.HexColor("#555555"),
)
heading_style = ParagraphStyle(
    "SectionHead", parent=styles["Heading3"],
    fontSize=10, spaceBefore=10, spaceAfter=4,
    textColor=colors.HexColor("#003366"), borderWidth=0,
)
normal = ParagraphStyle(
    "Body", parent=styles["Normal"], fontSize=9, leading=12, spaceAfter=2,
)
small = ParagraphStyle(
    "Small", parent=styles["Normal"], fontSize=8, leading=10, spaceAfter=1,
    textColor=colors.HexColor("#333333"),
)
bold = ParagraphStyle(
    "Bold", parent=normal, fontName="Helvetica-Bold",
)
right_style = ParagraphStyle(
    "Right", parent=normal, alignment=TA_RIGHT,
)

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=colors.grey, spaceAfter=6, spaceBefore=6)

def two_col(left_lines, right_lines, col_widths=(260, 260)):
    data = []
    maxlen = max(len(left_lines), len(right_lines))
    for i in range(maxlen):
        l = Paragraph(left_lines[i], normal) if i < len(left_lines) else ""
        r = Paragraph(right_lines[i], normal) if i < len(right_lines) else ""
        data.append([l, r])
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return t


# ===========================================================================
# 1. LC ADVICE (TEXT-BASED PDF)
# ===========================================================================
def build_lc_advice():
    doc = SimpleDocTemplate(
        os.path.join(OUT_DIR, "LC_Advice_Oil.pdf"),
        pagesize=A4, topMargin=20*mm, bottomMargin=15*mm,
        leftMargin=15*mm, rightMargin=15*mm,
    )
    story = []
    story.append(Paragraph("DOCUMENTARY CREDIT", title_style))
    story.append(Paragraph("SWIFT MT700 — Irrevocable Documentary Credit", subtitle_style))
    story.append(hr())

    fields = [
        ("27", "SEQUENCE OF TOTAL", "1/1"),
        ("40A", "FORM OF DOC CREDIT", "IRREVOCABLE"),
        ("20", "DOCUMENTARY CREDIT NO", "ADCB2025LC007891"),
        ("31C", "DATE OF ISSUE", "10MAR25"),
        ("31D", "DATE AND PLACE OF EXPIRY", "10JUN25 SINGAPORE"),
        ("50", "APPLICANT", "PETROVISTA ENERGY PTE LTD<br/>1 HARBOURFRONT PLACE #12-05<br/>HARBOURFRONT TOWER ONE<br/>SINGAPORE 098633"),
        ("59", "BENEFICIARY", "ARABIAN GULF PETROLEUM LLC<br/>AL REEM ISLAND, SKY TOWER, FLOOR 34<br/>ABU DHABI<br/>UNITED ARAB EMIRATES"),
        ("32B", "CURRENCY CODE, AMOUNT", "USD 4,680,000.00"),
        ("39A", "PERCENTAGE CREDIT AMT TOL", "5/5"),
        ("41D", "AVAILABLE WITH / BY", "ANY BANK BY NEGOTIATION"),
        ("42C", "DRAFTS AT", "SIGHT"),
        ("42D", "DRAWEE", "ABU DHABI COMMERCIAL BANK"),
        ("43P", "PARTIAL SHIPMENTS", "NOT ALLOWED"),
        ("43T", "TRANSHIPMENT", "ALLOWED"),
        ("44E", "PORT OF LOADING", "RUWAIS PORT, ABU DHABI, UAE"),
        ("44F", "PORT OF DISCHARGE", "ANY SEAPORT OF SINGAPORE"),
        ("44C", "LATEST DATE OF SHIPMENT", "25MAY25"),
        ("45A", "DESCRIPTION OF GOODS",
         "ARABIAN LIGHT CRUDE OIL (API GRAVITY 32-34 DEGREES)<br/>"
         "QUANTITY: 60,000 METRIC TONS (+/- 5 PCT)<br/>"
         "UNIT PRICE: USD 78.00 PER METRIC TON CFR SINGAPORE<br/>"
         "H.S. CODE: 2709.00.10<br/>"
         "TOTAL VALUE: USD 4,680,000.00<br/>"
         "COUNTRY OF ORIGIN: UNITED ARAB EMIRATES<br/>"
         "INCOTERMS 2020: CFR ANY SEAPORT OF SINGAPORE"),
        ("46A", "DOCUMENTS REQUIRED",
         "+SIGNED COMMERCIAL INVOICE IN 3 ORIGINALS AND 3 COPIES<br/>"
         "+FULL SET 3/3 CLEAN ON BOARD OCEAN BILLS OF LADING MADE OUT<br/>"
         "&nbsp;&nbsp;TO ORDER OF ADCB MARKED FREIGHT PREPAID NOTIFY APPLICANT<br/>"
         "+CERTIFICATE OF ORIGIN ISSUED BY ABU DHABI CHAMBER OF COMMERCE<br/>"
         "+CERTIFICATE OF QUALITY ISSUED BY SGS OR INTERTEK<br/>"
         "+CERTIFICATE OF QUANTITY ISSUED BY INDEPENDENT SURVEYOR<br/>"
         "+INSURANCE POLICY/CERTIFICATE FOR 110% CIF VALUE"),
        ("47A", "ADDITIONAL CONDITIONS",
         "+ALL DOCUMENTS MUST INDICATE LC NUMBER ADCB2025LC007891<br/>"
         "+GOODS MUST COMPLY WITH SINGAPORE MPA REGULATIONS<br/>"
         "+THIRD PARTY DOCUMENTS ACCEPTABLE EXCEPT INVOICE<br/>"
         "+DEMURRAGE FOR ACCOUNT OF APPLICANT"),
        ("71B", "CHARGES", "ALL BANKING CHARGES OUTSIDE ISSUING BANK ARE FOR BENEFICIARY ACCOUNT"),
        ("48", "PERIOD FOR PRESENTATION", "21 DAYS AFTER DATE OF SHIPMENT"),
        ("49", "CONFIRMATION INSTRUCTIONS", "MAY ADD"),
    ]

    data = []
    for tag, label, value in fields:
        data.append([
            Paragraph(f"<b>{tag}</b>", small),
            Paragraph(f"<b>{label}</b>", small),
            Paragraph(value, small),
        ])
    t = Table(data, colWidths=(30, 130, 350))
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]))
    story.append(t)
    doc.build(story)
    print("  Created LC_Advice_Oil.pdf")


# ===========================================================================
# 2. COMMERCIAL INVOICE
# ===========================================================================
def build_invoice():
    doc = SimpleDocTemplate(
        os.path.join(OUT_DIR, "Invoice_Oil.pdf"),
        pagesize=A4, topMargin=20*mm, bottomMargin=15*mm,
        leftMargin=15*mm, rightMargin=15*mm,
    )
    story = []
    story.append(Paragraph("COMMERCIAL INVOICE", title_style))
    story.append(hr())

    story.append(two_col(
        [
            "<b>ARABIAN GULF PETROLEUM LLC</b>",
            "AL REEM ISLAND, SKY TOWER, FLOOR 34",
            "ABU DHABI",
            "UNITED ARAB EMIRATES",
            "TEL: +971-2-555-8800",
        ],
        [
            "<b>INVOICE NO:</b> AGP/EXP/2025/0478",
            "<b>DATE:</b> 10 MAY 2025",
            "",
            "<b>L/C NO:</b> ADCB2025LC007891",
            "<b>L/C DATE:</b> 10 MARCH 2025",
        ]
    ))
    story.append(Spacer(1, 8))
    story.append(two_col(
        [
            "<b>BUYER:</b>",
            "PETROVISTA ENERGY PTE LTD",
            "1 HARBOURFRONT PLACE #12-05",
            "HARBOURFRONT TOWER ONE",
            "SINGAPORE 098633",
        ],
        [
            "<b>ISSUING BANK:</b>",
            "ABU DHABI COMMERCIAL BANK",
            "AL SALAM STREET",
            "ABU DHABI, UAE",
        ]
    ))
    story.append(Spacer(1, 6))

    story.append(two_col(
        [
            "<b>VESSEL:</b> MT DESERT ROSE / V.042",
            "<b>PORT OF LOADING:</b> RUWAIS PORT, ABU DHABI, UAE",
        ],
        [
            "<b>B/L NO:</b> RUWSIN2025-0478",
            "<b>PORT OF DISCHARGE:</b> ANY SEAPORT OF SINGAPORE",
        ]
    ))
    story.append(hr())

    # Goods table
    story.append(Paragraph("<b>DESCRIPTION OF GOODS</b>", heading_style))
    tdata = [
        [Paragraph("<b>Description</b>", small),
         Paragraph("<b>Quantity (MT)</b>", small),
         Paragraph("<b>Unit Price (USD)</b>", small),
         Paragraph("<b>Amount (USD)</b>", small)],
        [Paragraph("ARABIAN LIGHT CRUDE OIL<br/>(API GRAVITY 32-34 DEGREES)<br/>COUNTRY OF ORIGIN: UAE", small),
         Paragraph("60,000.000", small),
         Paragraph("78.00", small),
         Paragraph("4,680,000.00", small)],
    ]
    tdata.append([
        Paragraph("<b>TOTAL</b>", small),
        Paragraph("<b>60,000.000</b>", small),
        Paragraph("<b>78.00</b>", small),
        Paragraph("<b>4,680,000.00</b>", small),
    ])
    gt = Table(tdata, colWidths=(230, 90, 100, 100))
    gt.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f0f0")),
    ]))
    story.append(gt)
    story.append(Spacer(1, 8))

    details = [
        "H.S. CODE: 2709.00.10",
        "COUNTRY OF ORIGIN: UNITED ARAB EMIRATES",
        "TRADE TERM: CFR ANY SEAPORT OF SINGAPORE (INCOTERMS 2020)",
        "PAYMENT TERMS: AT SIGHT UNDER L/C NO. ADCB2025LC007891",
        "",
        "NET WEIGHT  : 60,000.000 MT (60,000,000 KGS)",
        "GROSS WEIGHT: 60,000.000 MT",
        "",
        "WE CERTIFY THAT THIS INVOICE SHOWS THE ACTUAL PRICE OF THE GOODS DESCRIBED,",
        "THAT ALL PARTICULARS ARE TRUE AND CORRECT.",
        "",
        "",
        "AUTHORIZED SIGNATORY",
        "FOR ARABIAN GULF PETROLEUM LLC",
    ]
    for line in details:
        story.append(Paragraph(line, normal))

    doc.build(story)
    print("  Created Invoice_Oil.pdf")


# ===========================================================================
# 3. BILL OF LADING
# ===========================================================================
def build_bill_of_lading():
    doc = SimpleDocTemplate(
        os.path.join(OUT_DIR, "Bill_of_Lading_Oil.pdf"),
        pagesize=A4, topMargin=20*mm, bottomMargin=15*mm,
        leftMargin=15*mm, rightMargin=15*mm,
    )
    story = []
    story.append(Paragraph("BILL OF LADING", title_style))
    story.append(Paragraph("(Tanker Bill of Lading — Non-Negotiable Copy)", subtitle_style))
    story.append(hr())

    story.append(two_col(
        [
            "<b>SHIPPER:</b>",
            "ARABIAN GULF PETROLEUM LLC",
            "AL REEM ISLAND, SKY TOWER, FLOOR 34",
            "ABU DHABI, UAE",
        ],
        [
            "<b>B/L NO:</b> RUWSIN2025-0478",
            "<b>DATE:</b> 14 MAY 2025",
            "",
            "<b>BOOKING NO:</b> TKR-2025-RUW-0478",
        ]
    ))
    story.append(Spacer(1, 6))
    story.append(two_col(
        [
            "<b>CONSIGNEE:</b>",
            "TO THE ORDER OF ABU DHABI COMMERCIAL BANK",
        ],
        [
            "<b>NOTIFY PARTY:</b>",
            "PETROVISTA ENERGY PTE LTD",
            "1 HARBOURFRONT PLACE #12-05",
            "SINGAPORE 098633",
        ]
    ))
    story.append(Spacer(1, 6))

    voyage_data = [
        "<b>VESSEL / VOYAGE:</b> MT DESERT ROSE / V.042",
        "<b>PORT OF LOADING:</b> RUWAIS PORT, ABU DHABI, UAE",
        "<b>PORT OF DISCHARGE:</b> ANY SEAPORT OF SINGAPORE",
        "<b>PLACE OF DELIVERY:</b> ANY SEAPORT OF SINGAPORE",
    ]
    for line in voyage_data:
        story.append(Paragraph(line, normal))
    story.append(hr())

    story.append(Paragraph("<b>DESCRIPTION OF GOODS</b>", heading_style))
    desc_lines = [
        "60,000.000 METRIC TONS OF ARABIAN LIGHT CRUDE OIL",
        "(API GRAVITY 32-34 DEGREES)",
        "COUNTRY OF ORIGIN: UNITED ARAB EMIRATES",
        "H.S. CODE: 2709.00.10",
        "L/C NO: ADCB2025LC007891",
        "",
        "LOADED IN BULK — VESSEL: MT DESERT ROSE",
        "IMO NO: 9876543",
        "",
        "GROSS WEIGHT: 60,000.000 MT",
        "NET WEIGHT: 60,000.000 MT",
        "",
        "FREIGHT: PREPAID",
        "NUMBER OF ORIGINAL B/L: THREE (3)",
        "",
        "SHIPPED ON BOARD DATE: 14 MAY 2025",
        "CLEAN ON BOARD",
        "",
        "",
        "SIGNED FOR THE CARRIER",
        "GULF NAVIGATION HOLDING PJSC",
        "AS AGENT FOR THE MASTER",
    ]
    for line in desc_lines:
        story.append(Paragraph(line, normal))

    doc.build(story)
    print("  Created Bill_of_Lading_Oil.pdf")


# ===========================================================================
# 4. CERTIFICATE OF ORIGIN
# ===========================================================================
def build_certificate_of_origin():
    doc = SimpleDocTemplate(
        os.path.join(OUT_DIR, "Certificate_of_Origin_Oil.pdf"),
        pagesize=A4, topMargin=20*mm, bottomMargin=15*mm,
        leftMargin=15*mm, rightMargin=15*mm,
    )
    story = []
    story.append(Paragraph("CERTIFICATE OF ORIGIN", title_style))
    story.append(hr())

    info = [
        "<b>CERTIFICATE NO:</b> ADCCI/CO/2025/AUH-07832",
        "<b>DATE OF ISSUE:</b> 12 MAY 2025",
        "<b>ISSUED BY:</b> ABU DHABI CHAMBER OF COMMERCE AND INDUSTRY",
    ]
    for line in info:
        story.append(Paragraph(line, normal))
    story.append(Spacer(1, 8))

    story.append(two_col(
        [
            "<b>EXPORTER:</b>",
            "ARABIAN GULF PETROLEUM LLC",
            "AL REEM ISLAND, SKY TOWER, FLOOR 34",
            "ABU DHABI, UAE",
        ],
        [
            "<b>CONSIGNEE / IMPORTER:</b>",
            "PETROVISTA ENERGY PTE LTD",
            "1 HARBOURFRONT PLACE #12-05",
            "HARBOURFRONT TOWER ONE",
            "SINGAPORE 098633",
        ]
    ))
    story.append(Spacer(1, 8))

    story.append(two_col(
        [
            "<b>COUNTRY OF ORIGIN:</b> UNITED ARAB EMIRATES",
        ],
        [
            "<b>COUNTRY OF DESTINATION:</b> SINGAPORE",
        ]
    ))
    story.append(Spacer(1, 6))

    transport = [
        "<b>TRANSPORT DETAILS:</b>",
        "VESSEL: MT DESERT ROSE / V.042",
        "PORT OF LOADING: RUWAIS PORT, ABU DHABI, UAE",
        "PORT OF DISCHARGE: ANY SEAPORT OF SINGAPORE",
    ]
    for line in transport:
        story.append(Paragraph(line, normal))
    story.append(hr())

    story.append(Paragraph("<b>DESCRIPTION OF GOODS:</b>", heading_style))
    goods = [
        "ARABIAN LIGHT CRUDE OIL (API GRAVITY 32-34 DEGREES)",
        "QUANTITY: 60,000.000 METRIC TONS",
        "H.S. CODE: 2709.00.10",
        "",
        "L/C NO: ADCB2025LC007891",
        "INVOICE NO: AGP/EXP/2025/0478",
        "",
        "",
        "THIS IS TO CERTIFY THAT THE GOODS DESCRIBED ABOVE ORIGINATE IN THE",
        "UNITED ARAB EMIRATES AND ARE PRODUCED/EXTRACTED FROM FACILITIES",
        "OPERATED UNDER THE AUTHORITY OF ADNOC (ABU DHABI NATIONAL OIL COMPANY).",
        "",
        "",
        "AUTHORIZED SIGNATORY&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;CHAMBER SEAL",
        "ABU DHABI CHAMBER OF COMMERCE",
        "AND INDUSTRY",
    ]
    for line in goods:
        story.append(Paragraph(line, normal))

    doc.build(story)
    print("  Created Certificate_of_Origin_Oil.pdf")


# ===========================================================================
# 5. PACKING LIST (for oil = cargo manifest style)
# ===========================================================================
def build_packing_list():
    doc = SimpleDocTemplate(
        os.path.join(OUT_DIR, "Packing_List_Oil.pdf"),
        pagesize=A4, topMargin=20*mm, bottomMargin=15*mm,
        leftMargin=15*mm, rightMargin=15*mm,
    )
    story = []
    story.append(Paragraph("CARGO MANIFEST / PACKING LIST", title_style))
    story.append(hr())

    story.append(two_col(
        [
            "<b>ARABIAN GULF PETROLEUM LLC</b>",
            "AL REEM ISLAND, SKY TOWER, FLOOR 34",
            "ABU DHABI, UAE",
        ],
        [
            "<b>MANIFEST NO:</b> AGP/CM/2025/0478",
            "<b>DATE:</b> 10 MAY 2025",
        ]
    ))
    story.append(Spacer(1, 6))

    story.append(two_col(
        [
            "<b>BUYER:</b>",
            "PETROVISTA ENERGY PTE LTD",
            "1 HARBOURFRONT PLACE #12-05",
            "SINGAPORE 098633",
        ],
        [
            "<b>L/C NO:</b> ADCB2025LC007891",
            "<b>INVOICE NO:</b> AGP/EXP/2025/0478",
        ]
    ))
    story.append(Spacer(1, 6))

    voyage = [
        "<b>VESSEL:</b> MT DESERT ROSE / V.042",
        "<b>PORT OF LOADING:</b> RUWAIS PORT, ABU DHABI, UAE",
        "<b>PORT OF DISCHARGE:</b> ANY SEAPORT OF SINGAPORE",
    ]
    for line in voyage:
        story.append(Paragraph(line, normal))
    story.append(hr())

    # Cargo table
    story.append(Paragraph("<b>CARGO DETAILS</b>", heading_style))
    tdata = [
        [Paragraph("<b>Tank No.</b>", small),
         Paragraph("<b>Product</b>", small),
         Paragraph("<b>Quantity (MT)</b>", small),
         Paragraph("<b>API Gravity</b>", small),
         Paragraph("<b>Temp (°C)</b>", small)],
        [Paragraph("1C / 1P / 1S", small), Paragraph("Arabian Light Crude", small),
         Paragraph("15,200.000", small), Paragraph("33.1", small), Paragraph("42.5", small)],
        [Paragraph("2C / 2P / 2S", small), Paragraph("Arabian Light Crude", small),
         Paragraph("15,000.000", small), Paragraph("32.8", small), Paragraph("42.3", small)],
        [Paragraph("3C / 3P / 3S", small), Paragraph("Arabian Light Crude", small),
         Paragraph("14,900.000", small), Paragraph("33.4", small), Paragraph("42.1", small)],
        [Paragraph("4C / 4P / 4S", small), Paragraph("Arabian Light Crude", small),
         Paragraph("14,900.000", small), Paragraph("32.9", small), Paragraph("42.4", small)],
    ]
    tdata.append([
        Paragraph("<b>TOTAL</b>", small), Paragraph("", small),
        Paragraph("<b>60,000.000</b>", small), Paragraph("", small), Paragraph("", small),
    ])
    gt = Table(tdata, colWidths=(90, 150, 100, 80, 80))
    gt.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f0f0")),
    ]))
    story.append(gt)
    story.append(Spacer(1, 10))

    details = [
        "PRODUCT: ARABIAN LIGHT CRUDE OIL (API GRAVITY 32-34 DEGREES)",
        "H.S. CODE: 2709.00.10",
        "COUNTRY OF ORIGIN: UNITED ARAB EMIRATES",
        "",
        "NET WEIGHT  : 60,000.000 METRIC TONS",
        "GROSS WEIGHT: 60,000.000 METRIC TONS",
        "LOADED IN BULK — NO SEPARATE PACKAGING",
        "",
        "SHIPPING MARKS:",
        "PETROVISTA ENERGY / SINGAPORE",
        "L/C NO: ADCB2025LC007891",
        "PRODUCT: ARABIAN LIGHT CRUDE OIL",
        "ORIGIN: UAE",
        "",
        "",
        "AUTHORIZED SIGNATORY",
        "FOR ARABIAN GULF PETROLEUM LLC",
    ]
    for line in details:
        story.append(Paragraph(line, normal))

    doc.build(story)
    print("  Created Packing_List_Oil.pdf")


if __name__ == "__main__":
    print("Generating Oil Trading LC document set...")
    build_lc_advice()
    build_invoice()
    build_bill_of_lading()
    build_certificate_of_origin()
    build_packing_list()
    print("Done! All PDFs in:", OUT_DIR)
