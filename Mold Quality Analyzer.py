import streamlit as st
from pypdf import PdfReader

# ============================================================
# MOLD QUALITY ANALYZER
# MoldMatch
# ============================================================

st.set_page_config(
    page_title="Mold Quality Analyzer",
    page_icon="🛠️",
    layout="wide"
)

# ============================================================
# SCORING RULES
# ============================================================

MATERIAL_RULES = [
    (
        ["h13", "1.2344", "420 stainless", "s136",
         "1.2083", "elmax", "stavamax"],
        22,
        "Premium cavity/core steel identified"
    ),
    (
        ["p20", "1.2311", "1.2738", "nak80"],
        14,
        "Recognized mold steel identified"
    ),
    (
        ["hrc", "rockwell", "heat treatment",
         "hardened to", "steel hardness"],
        16,
        "Steel hardness or heat treatment specified"
    ),
    (
        ["steel certificate", "material certificate",
         "mill certificate", "traceability"],
        10,
        "Steel certification or traceability included"
    ),
    (
        ["mold base steel", "dme mold base",
         "hasco mold base", "meusburger mold base"],
        10,
        "Mold-base material or supplier specified"
    ),
]

COMPONENT_RULES = [
    (
        ["dme", "hasco", "misumi", "meusburger",
         "progressive components", "pcs company", "strack"],
        30,
        "Recognized standard-component supplier identified"
    ),
    (
        ["standard components", "standardized components",
         "interchangeable"],
        15,
        "Standardized components specified"
    ),
    (
        ["guide pin", "leader pin", "guide bushing",
         "ejector pin", "return pin"],
        15,
        "Guidance/ejection components described"
    ),
    (
        ["cycle counter", "mold counter", "date stamp"],
        10,
        "Cycle/traceability component included"
    ),
]

CONSTRUCTION_RULES = [
    (
        ["guided ejection", "ejection guide", "ejector guide"],
        12,
        "Guided ejection specified"
    ),
    (
        ["taper lock", "interlock", "side lock",
         "precision interlock"],
        12,
        "Precision mold alignment specified"
    ),
    (
        ["wear plate", "replaceable wear", "gib"],
        8,
        "Replaceable wear components specified"
    ),
    (
        ["cooling circuit", "water line",
         "baffle", "bubbler", "conformal cooling"],
        12,
        "Cooling design described"
    ),
    (
        ["venting", "vent depth", "vacuum vent"],
        10,
        "Venting strategy described"
    ),
    (
        ["hot runner", "valve gate", "mold-master",
         "mold masters", "synventive", "husky", "yudo"],
        12,
        "Runner/gating system identified"
    ),
    (
        ["moldflow", "mold flow", "simulation",
         "warpage analysis", "cooling analysis"],
        8,
        "Molding simulation included"
    ),
    (
        ["spare parts", "wear parts", "replacement parts"],
        6,
        "Spare/wear-parts package included"
    ),
]

MAKER_RULES = [
    (
        ["iso 9001", "iso9001"],
        12,
        "ISO 9001 quality system referenced"
    ),
    (
        ["iso 13485", "iso13485"],
        16,
        "ISO 13485 medical quality system referenced"
    ),
    (
        ["medical tooling", "medical mold", "medical device"],
        12,
        "Medical tooling experience stated"
    ),
    (
        ["in-house design", "in house design", "design department"],
        10,
        "In-house mold design capability stated"
    ),
    (
        ["wire edm", "sinker edm",
         "high speed machining", "5-axis", "five-axis"],
        12,
        "Advanced manufacturing capability stated"
    ),
    (
        ["qualification", "validation",
         "iq oq pq", "fat", "sat"],
        12,
        "Qualification/validation capability stated"
    ),
    (
        ["years in business", "years experience",
         "award", "customer reference"],
        10,
        "Experience/reputation evidence stated"
    ),
]

QUOTE_RULES = [
    (
        ["mold life", "tool life",
         "cycles warranty", "shots warranty"],
        15,
        "Mold life/warranty stated"
    ),
    (
        ["lead time", "delivery weeks", "delivery date"],
        10,
        "Lead time stated"
    ),
    (
        ["acceptance criteria", "mold acceptance",
         "t1", "t2", "trial"],
        15,
        "Trial/acceptance process included"
    ),
    (
        ["drawing", "3d data", "cad", "documentation"],
        10,
        "Engineering documentation included"
    ),
    (
        ["inspection report", "dimensional report", "cmm report"],
        15,
        "Dimensional inspection report included"
    ),
    (
        ["maintenance", "preventive maintenance", "pm schedule"],
        10,
        "Maintenance requirements included"
    ),
    (
        ["steel certificate", "material certificate",
         "mill certificate"],
        10,
        "Material certification included"
    ),
]

# ============================================================
# SUPPLIER CLARIFICATION RULES
# ============================================================

CLARIFICATION_RULES = [
    (
        ["cavity steel", "core steel", "h13", "s136",
         "p20", "1.2344", "1.2083"],
        "Please identify the exact cavity and core steel grades, "
        "steel manufacturer, and country of origin."
    ),
    (
        ["hrc", "rockwell", "hardness", "heat treatment"],
        "Please specify the cavity, core, slide and wear-component "
        "hardness after heat treatment."
    ),
    (
        ["steel certificate", "material certificate",
         "mill certificate"],
        "Please confirm that steel mill certificates and material "
        "traceability records will be supplied."
    ),
    (
        ["dme", "hasco", "misumi", "meusburger",
         "progressive components"],
        "Please provide the purchased-component BOM, including "
        "manufacturer and component part numbers."
    ),
    (
        ["mold base"],
        "Please identify the mold-base manufacturer, plate "
        "materials, and plate hardness."
    ),
    (
        ["hot runner", "cold runner", "valve gate"],
        "Please confirm the runner/gating system, including the "
        "hot-runner manufacturer and model where applicable."
    ),
    (
        ["mold life", "tool life",
         "cycles warranty", "shots warranty"],
        "Please state the warranted mold life in cycles and "
        "define the warranty conditions."
    ),
    (
        ["inspection report", "dimensional report", "cmm"],
        "Please define the dimensional inspection plan, report "
        "format, sampling requirements, and measurement equipment."
    ),
    (
        ["acceptance criteria", "mold acceptance", "fat", "sat"],
        "Please define mold acceptance criteria, trial material, "
        "trial duration, cycle-time target, and approval responsibilities."
    ),
    (
        ["spare parts", "wear parts"],
        "Please provide the recommended spare-parts and wear-parts "
        "list with pricing and delivery lead times."
    ),
    (
        ["cooling circuit", "water line",
         "conformal cooling", "baffle", "bubbler"],
        "Please provide the cooling-circuit layout, connection "
        "standard, flow target, and pressure-drop information."
    ),
    (
        ["venting", "vent depth"],
        "Please define the vent locations and recommended vent "
        "depth for the specified resin."
    ),
    (
        ["maintenance", "preventive maintenance", "pm schedule"],
        "Please provide the preventive-maintenance schedule and "
        "recommended service intervals."
    ),
    (
        ["moldflow", "mold flow", "simulation"],
        "Please confirm whether filling, packing, cooling, and "
        "warpage simulation are included and provide the final report."
    ),
]

# ============================================================
# FUNCTIONS
# ============================================================

def contains_any(text, keywords):
    """Return True when any keyword is present."""
    text = text.lower()
    return any(keyword.lower() in text for keyword in keywords)


def evaluate_rules(text, rules):
    """Calculate score and return detected strengths."""

    score = 0
    detected = []

    for keywords, points, description in rules:
        if contains_any(text, keywords):
            score += points
            detected.append(description)

    return min(score, 100), detected


def generate_clarifications(text):
    """Generate clarification questions from missing quote info."""

    questions = []

    for keywords, question in CLARIFICATION_RULES:

        if not contains_any(text, keywords):
            questions.append(question)

    return questions


def extract_pdf_text(uploaded_file):
    """Extract selectable text from a PDF quotation."""

    reader = PdfReader(uploaded_file)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):

        try:
            page_text = page.extract_text()

            if page_text:
                pages.append(
                    f"\n--- PAGE {page_number} ---\n"
                    f"{page_text}"
                )

        except Exception:
            continue

    return "\n".join(pages)


def calculate_quality(
    text,
    required_cycles,
    tolerance,
    application
):

    # --------------------------------------------------------
    # Individual evaluations
    # --------------------------------------------------------

    material_score, material_hits = evaluate_rules(
        text,
        MATERIAL_RULES
    )

    component_score, component_hits = evaluate_rules(
        text,
        COMPONENT_RULES
    )

    construction_score, construction_hits = evaluate_rules(
        text,
        CONSTRUCTION_RULES
    )

    maker_score, maker_hits = evaluate_rules(
        text,
        MAKER_RULES
    )

    quote_score, quote_hits = evaluate_rules(
        text,
        QUOTE_RULES
    )

    # --------------------------------------------------------
    # Mold Construction Score
    #
    # Materials     40%
    # Construction  40%
    # Components    20%
    # --------------------------------------------------------

    mold_construction = round(
        material_score * 0.40
        + construction_score * 0.40
        + component_score * 0.20
    )

    risks = []

    # ========================================================
    # HIGH MOLD-LIFE CHECK
    # ========================================================

    if (
        required_cycles >= 1_000_000
        and not contains_any(
            text,
            [
                "hardened",
                "hrc",
                "rockwell",
                "h13",
                "s136",
                "1.2344",
                "1.2083"
            ]
        )
    ):

        mold_construction -= 12

        risks.append(
            "High mold-life requirement entered, but adequate "
            "evidence of hardened tooling steel was not detected."
        )

    # ========================================================
    # TIGHT TOLERANCE CHECK
    # ========================================================

    if (
        tolerance <= 0.020
        and not contains_any(
            text,
            [
                "cmm",
                "dimensional report",
                "inspection report"
            ]
        )
    ):

        mold_construction -= 8

        risks.append(
            "Tight part tolerance entered, but no dimensional "
            "inspection plan was detected."
        )

    # ========================================================
    # MEDICAL / PRECISION APPLICATION CHECK
    # ========================================================

    if (
        application == "Medical / Precision"
        and not contains_any(
            text,
            [
                "iso 13485",
                "validation",
                "traceability",
                "inspection report"
            ]
        )
    ):

        maker_score -= 10

        risks.append(
            "Medical/precision application selected, but limited "
            "validation or traceability evidence was detected."
        )

    # ========================================================
    # GENERAL RISK CHECKS
    # ========================================================

    if not contains_any(
        text,
        [
            "mold life",
            "tool life",
            "cycles warranty",
            "shots warranty"
        ]
    ):

        risks.append(
            "No mold-life commitment was detected."
        )

    if not contains_any(
        text,
        [
            "steel certificate",
            "material certificate",
            "mill certificate"
        ]
    ):

        risks.append(
            "No steel certification or traceability "
            "commitment was detected."
        )

    if not contains_any(
        text,
        [
            "spare parts",
            "wear parts"
        ]
    ):

        risks.append(
            "No spare or wear-parts package was detected."
        )

    # --------------------------------------------------------
    # Keep scores between 0 and 100
    # --------------------------------------------------------

    mold_construction = max(
        0,
        min(mold_construction, 100)
    )

    maker_score = max(
        0,
        min(maker_score, 100)
    )

    quote_score = max(
        0,
        min(quote_score, 100)
    )

    # ===