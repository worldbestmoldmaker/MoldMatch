import streamlit as st
from pypdf import PdfReader


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Mold Quality Analyzer",
    page_icon="🛠️",
    layout="wide"
)


# ============================================================
# APP TITLE
# ============================================================

st.title("🛠️ Mold Quality Analyzer")
st.caption("MoldMatch | Supplier Mold Quotation Assessment")

st.write(
    "Upload a supplier mold quotation and evaluate the proposed "
    "mold construction, mold-maker confidence, quotation completeness, "
    "technical risks, and missing information."
)


# ============================================================
# SCORING DATA
# ============================================================

MATERIAL_RULES = [
    (
        ["h13", "1.2344"],
        18,
        "H13 / 1.2344 tool steel identified"
    ),
    (
        ["s136"],
        18,
        "S136 stainless mold steel identified"
    ),
    (
        ["420 stainless", "420ss", "1.2083"],
        18,
        "420 / 1.2083 stainless mold steel identified"
    ),
    (
        ["elmax", "stavamax"],
        18,
        "Premium stainless mold steel identified"
    ),
    (
        ["p20", "1.2311", "1.2738"],
        10,
        "P20-type mold steel identified"
    ),
    (
        ["nak80"],
        12,
        "NAK80 mold steel identified"
    ),
    (
        ["hrc", "rockwell", "hardness", "hardened to"],
        15,
        "Steel hardness specified"
    ),
    (
        ["heat treatment", "heat treated"],
        8,
        "Heat treatment requirement specified"
    ),
    (
        [
            "steel certificate",
            "material certificate",
            "mill certificate",
        ],
        12,
        "Steel certification specified"
    ),
    (
        ["traceability", "material traceability"],
        8,
        "Material traceability specified"
    ),
    (
        [
            "mold base steel",
            "dme mold base",
            "hasco mold base",
            "meusburger mold base",
        ],
        10,
        "Mold-base specification identified"
    ),
]


COMPONENT_RULES = [
    (
        ["dme"],
        20,
        "DME components identified"
    ),
    (
        ["hasco"],
        20,
        "HASCO components identified"
    ),
    (
        ["meusburger"],
        20,
        "Meusburger components identified"
    ),
    (
        ["misumi"],
        18,
        "MISUMI components identified"
    ),
    (
        ["progressive components"],
        18,
        "Progressive Components identified"
    ),
    (
        ["strack"],
        15,
        "STRACK components identified"
    ),
    (
        ["standard component", "standard components"],
        10,
        "Standard mold components specified"
    ),
    (
        ["leader pin", "guide pin", "guide pillar"],
        8,
        "Guide components identified"
    ),
    (
        ["guide bushing", "leader bushing"],
        8,
        "Guide bushings identified"
    ),
    (
        ["ejector pin", "ejection pin"],
        8,
        "Ejector components identified"
    ),
    (
        ["cycle counter", "mold counter"],
        8,
        "Mold cycle counter specified"
    ),
]


CONSTRUCTION_RULES = [
    (
        ["guided ejection", "ejector guide", "ejection guide"],
        12,
        "Guided ejection specified"
    ),
    (
        [
            "taper lock",
            "interlock",
            "side lock",
            "precision interlock",
        ],
        12,
        "Precision mold alignment specified"
    ),
    (
        ["wear plate", "wear plates", "replaceable wear"],
        8,
        "Replaceable wear surfaces specified"
    ),
    (
        [
            "cooling circuit",
            "cooling channel",
            "water line",
            "water circuit",
        ],
        12,
        "Mold cooling system described"
    ),
    (
        ["baffle", "bubbler"],
        5,
        "Localized cooling components specified"
    ),
    (
        ["conformal cooling"],
        8,
        "Conformal cooling specified"
    ),
    (
        ["venting", "vent depth", "vacuum vent"],
        10,
        "Mold venting described"
    ),
    (
        [
            "hot runner",
            "valve gate",
            "mold-masters",
            "mold masters",
            "synventive",
            "husky",
            "yudo",
        ],
        12,
        "Runner/gating system identified"
    ),
    (
        [
            "moldflow",
            "mold flow",
            "filling analysis",
            "warpage analysis",
            "cooling analysis",
        ],
        10,
        "Molding simulation specified"
    ),
    (
        ["spare parts", "wear parts", "replacement parts"],
        8,
        "Spare/wear-parts package specified"
    ),
]


MAKER_RULES = [
    (
        ["iso 9001", "iso9001"],
        15,
        "ISO 9001 referenced"
    ),
    (
        ["iso 13485", "iso13485"],
        20,
        "ISO 13485 referenced"
    ),
    (
        [
            "medical tooling",
            "medical mold",
            "medical mould",
            "medical device tooling",
        ],
        14,
        "Medical tooling experience stated"
    ),
    (
        ["in-house design", "in house design"],
        10,
        "In-house mold design stated"
    ),
    (
        ["mold design department", "tool design department"],
        8,
        "Dedicated mold-design capability stated"
    ),
    (
        ["wire edm", "wire-edm"],
        8,
        "Wire EDM capability stated"
    ),
    (
        ["sinker edm", "die sink edm"],
        8,
        "Sinker EDM capability stated"
    ),
    (
        [
            "high speed machining",
            "high-speed machining",
            "5-axis",
            "five-axis",
        ],
        10,
        "Advanced machining capability stated"
    ),
    (
        [
            "validation",
            "qualification",
            "iq/oq/pq",
            "iq oq pq",
            "fat",
            "sat",
        ],
        12,
        "Validation/qualification capability stated"
    ),
    (
        [
            "years in business",
            "years of experience",
            "customer reference",
            "industry award",
        ],
        8,
        "Supplier experience/reputation evidence stated"
    ),
]


QUOTE_RULES = [
    (
        [
            "mold life",
            "mould life",
            "tool life",
            "cycles warranty",
            "shots warranty",
        ],
        15,
        "Mold-life commitment stated"
    ),
    (
        ["lead time", "delivery date", "delivery weeks"],
        10,
        "Lead time stated"
    ),
    (
        [
            "acceptance criteria",
            "mold acceptance",
            "mould acceptance",
        ],
        15,
        "Acceptance criteria stated"
    ),
    (
        ["t1", "t2", "mold trial", "mould trial"],
        10,
        "Mold trial process identified"
    ),
    (
        ["drawing", "3d data", "cad data", "documentation"],
        8,
        "Engineering documentation identified"
    ),
    (
        [
            "inspection report",
            "dimensional report",
            "cmm report",
        ],
        15,
        "Dimensional inspection report specified"
    ),
    (
        [
            "preventive maintenance",
            "maintenance schedule",
            "pm schedule",
        ],
        10,
        "Preventive-maintenance requirement specified"
    ),
    (
        [
            "steel certificate",
            "material certificate",
            "mill certificate",
        ],
        10,
        "Material certification specified"
    ),
]


# ============================================================
# CLARIFICATION RULES
# ============================================================

CLARIFICATION_RULES = [
    (
        [
            "cavity steel",
            "core steel",
            "h13",
            "s136",
            "420 stainless",
            "p20",
            "nak80",
            "1.2344",
            "1.2083",
        ],
        "Please identify the exact cavity and core steel grades, "
        "steel manufacturer, and country of origin."
    ),

    (
        ["hrc", "rockwell", "hardness", "hardened to"],
        "Please specify the required hardness for the cavity, core, "
        "slides, lifters, and critical wear components."
    ),

    (
        [
            "steel certificate",
            "material certificate",
            "mill certificate",
        ],
        "Please confirm that steel/material certificates will be "
        "provided with the completed mold."
    ),

    (
        [
            "dme",
            "hasco",
            "misumi",
            "meusburger",
            "progressive components",
        ],
        "Please provide the standard purchased-component BOM, "
        "including manufacturer names and part numbers."
    ),

    (
        ["mold base", "mould base"],
        "Please identify the mold-base manufacturer, plate materials, "
        "and hardness specifications."
    ),

    (
        [
            "hot runner",
            "cold runner",
            "valve gate",
            "hot-runner",
        ],
        "Please confirm the runner and gating system. If a hot runner "
        "is used, identify the manufacturer, model, controller "
        "requirements, and spare heater/thermocouple recommendation."
    ),

    (
        [
            "mold life",
            "mould life",
            "tool life",
            "cycles warranty",
        ],
        "Please state the warranted mold life in cycles and define "
        "the conditions of the mold-life warranty."
    ),

    (
        [
            "inspection report",
            "dimensional report",
            "cmm report",
        ],
        "Please define the dimensional inspection plan, measurement "
        "equipment, report format, and sampling requirements."
    ),

    (
        [
            "acceptance criteria",
            "mold acceptance",
            "mould acceptance",
            "fat",
            "sat",
        ],
        "Please define the mold acceptance criteria, trial duration, "
        "approved molding material, cycle-time target, and approval "
        "responsibilities."
    ),

    (
        ["spare parts", "wear parts"],
        "Please provide the recommended spare-parts and wear-parts "
        "list, including part numbers, quantities, pricing, and "
        "replacement lead times."
    ),

    (
        [
            "cooling circuit",
            "cooling channel",
            "water line",
            "water circuit",
        ],
        "Please provide the cooling-circuit layout, connection "
        "standard, recommended flow rate, and pressure requirements."
    ),

    (
        ["venting", "vent depth"],
        "Please define the mold vent locations and recommended vent "
        "depth based on the specified molding material."
    ),

    (
        [
            "preventive maintenance",
            "maintenance schedule",
            "pm schedule",
        ],
        "Please provide the recommended preventive-maintenance "
        "schedule and service intervals."
    ),

    (
        [
            "moldflow",
            "mold flow",
            "filling analysis",
            "warpage analysis",
        ],
        "Please confirm whether filling, packing, cooling, and "
        "warpage simulation are included and whether the final "
        "analysis report will be provided."
    ),
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def contains_any(text, keywords):
    """Check whether any keyword occurs in text."""
    clean_text = str(text).lower()

    return any(
        keyword.lower() in clean_text
        for keyword in keywords
    )


def evaluate_rules(text, rules):
    """Evaluate one group of scoring rules."""

    score = 0
    detected = []

    for keywords, points, description in rules:

        if contains_any(text, keywords):
            score += points
            detected.append(description)

    score = min(score, 100)

    return score, detected


def generate_clarification_questions(text):
    """Create questions when required information is missing."""

    questions = []

    for keywords, question in CLARIFICATION_RULES:

        if not contains_any(text, keywords):
            questions.append(question)

    return questions


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_pdf_text(pdf_file):
    """
    Extract selectable text from a PDF.

    Returns:
        text
        page_count
        pages_with_text
        error
    """

    try:

        reader = PdfReader(pdf_file)

        extracted_pages = []
        pages_with_text = 0

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            try:

                text = page.extract_text()

                if text and text.strip():

                    pages_with_text += 1

                    extracted_pages.append(
                        f"\n--- PAGE {page_number} ---\n{text}"
                    )

            except Exception:
                # One bad page should not crash the entire app.
                continue

        full_text = "\n".join(extracted_pages)

        return (
            full_text,
            len(reader.pages),
            pages_with_text,
            None
        )

    except Exception as error:

        return "", 0, 0, str(error)


# ============================================================
# TXT EXTRACTION
# ============================================================

def extract_txt_text(txt_file):

    try:

        raw_data = txt_file.read()

        if isinstance(raw_data, bytes):

            text = raw_data.decode(
                "utf-8",
                errors="ignore"
            )

        else:
            text = str(raw_data)

        return text, None

    except Exception as error:

        return "", str(error)


# ============================================================
# MAIN QUALITY CALCULATION
# ============================================================

def calculate_quality(
    quote_text,
    required_cycles,
    tolerance,
    application
):

    text = quote_text.lower()

    # --------------------------------------------------------
    # Raw category scores
    # --------------------------------------------------------

    material_score, material_hits = evaluate_rules(
        text,
        MATERIAL_RULES
    )

    component_score, component_hits = evaluate_rules(
        text,
        COMPONENT_RULES
    )

    design_score, design_hits = evaluate_rules(
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
    # Construction score
    #
    # Materials          40%
    # Mold design        40%
    # Components         20%
    # --------------------------------------------------------

    mold_construction_score = round(
        material_score * 0.40
        + design_score * 0.40
        + component_score * 0.20
    )

    risks = []

    # ========================================================
    # HIGH-LIFE MOLD CHECK
    # ========================================================

    if required_cycles >= 1_000_000:

        if not contains_any(
            text,
            [
                "hardened",
                "hrc",
                "rockwell",
                "h13",
                "s136",
                "420 stainless",
                "1.2344",
                "1.2083",
            ]
        ):

            mold_construction_score -= 12

            risks.append(
                "High mold-life requirement entered, but strong "
                "evidence of hardened cavity/core tooling material "
                "was not detected."
            )

    # ========================================================
    # HIGH-PRECISION CHECK
    # ========================================================

    if tolerance <= 0.020:

        if not contains_any(
            text,
            [
                "cmm",
                "inspection report",
                "dimensional report",
            ]
        ):

            quote_score -= 8

            risks.append(
                "The entered tolerance is 0.020 mm or tighter, but "
                "no dimensional inspection or CMM report requirement "
                "was detected."
            )

    # ========================================================
    # MEDICAL / PRECISION CHECK
    # ========================================================

    if application == "Medical / Precision":

        if not contains_any(
            text,
            [
                "iso 13485",
                "validation",
                "qualification",
                "traceability",
                "inspection report",
            ]
        ):

            maker_score -= 10

            risks.append(
                "Medical/precision application selected, but limited "
                "quality-system, validation, or traceability evidence "
                "was detected."
            )

    # ========================================================
    # GENERAL RISKS
    # ========================================================

    if not contains_any(
        text,
        [
            "mold life",
            "mould life",
            "tool life",
            "cycles warranty",
        ]
    ):

        risks.append(
            "No mold-life commitment or warranty was detected."
        )

    if not contains_any(
        text,
        [
            "steel certificate",
            "material certificate",
            "mill certificate",
        ]
    ):

        risks.append(
            "No steel/material certification requirement "
            "was detected."
        )

    if not contains_any(
        text,
        ["spare parts", "wear parts"]
    ):

        risks.append(
            "No spare-parts or wear-parts package was detected."
        )

    if not contains_any(
        text,
        [
            "dme",
            "hasco",
            "meusburger",
            "misumi",
            "progressive components",
        ]
    ):

        risks.append(
            "No recognized standard mold-component supplier "
            "was clearly identified."
        )

    if not contains_any(
        text,
        [
            "cooling circuit",
            "cooling channel",
            "water line",
            "water circuit",
        ]
    ):

        risks.append(
            "Cooling-circuit requirements were not clearly detected."
        )

    if not contains_any(
        text,
        ["venting", "vent depth"]
    ):

        risks.append(
            "Mold venting requirements were not clearly detected."
        )

    # --------------------------------------------------------
    # Clamp values between 0 and 100
    # --------------------------------------------------------

    mold_construction_score = max(
        0,
        min(100, mold_construction_score)
    )

    maker_score = max(
        0,
        min(100, maker_score)
    )

    quote_score = max(
        0,
        min(100, quote_score)
    )

    # ========================================================
    # OVERALL MOLDMATCH SCORE
    #
    # Construction       45%
    # Mold maker         25%
    # Quote confidence   30%
    # ========================================================

    overall_score = round(
        mold_construction_score * 0.45
        + maker_score * 0.25
        + quote_score * 0.30
    )

    strengths = (
        material_hits
        + component_hits
        + design_hits
        + maker_hits
        + quote_hits
    )

    # Remove duplicates while preserving order

    strengths = list(
        dict.fromkeys(strengths)
    )

    # Clarifications

    questions = generate_clarification_questions(
        text
    )

    return {
        "overall": overall_score,
        "construction": mold_construction_score,
        "maker": maker_score,
        "quote": quote_score,
        "materials": material_score,
        "components": component_score,
        "design": design_score,
        "strengths": strengths,
        "risks": risks,
        "questions": questions,
    }


# ============================================================
# SCORE LABEL
# ============================================================

def get_score_label(score):

    if score >= 85:
        return "Preferred", "green"

    elif score >= 70:
        return "Accept with Clarification", "orange"

    elif score >= 55:
        return "Conditional / Engineering Review", "orange"

    else:
        return "High Risk", "red"


# ============================================================
# SESSION STATE
# ============================================================

if "quote_text" not in st.session_state:
    st.session_state.quote_text = ""

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None


# ============================================================
# INPUT SECTION
# ============================================================

st.divider()

left_column, right_column = st.columns(
    [1.35, 1]
)


# ============================================================
# LEFT COLUMN
# ============================================================

with left_column:

    st.subheader("1. Supplier Quotation")

    uploaded_file = st.file_uploader(
        "Upload Supplier Quotation",
        type=["pdf", "txt"],
        help="Supported files: PDF and TXT"
    )

    # --------------------------------------------------------
    # Process upload
    # --------------------------------------------------------

    if uploaded_file is not None:

        current_file = (
            uploaded_file.name,
            uploaded_file.size
        )

        previous_file = st.session_state.get(
            "processed_file"
        )

        if current_file != previous_file:

            st.session_state.processed_file = current_file

            # =================================================
            # PDF
            # =================================================

            if uploaded_file.name.lower().endswith(".pdf"):

                (
                    pdf_text,
                    page_count,
                    pages_with_text,
                    pdf_error,
                ) = extract_pdf_text(uploaded_file)

                if pdf_error:

                    st.error(
                        "The PDF could not be read."
                    )

                    st.caption(pdf_error)

                elif pdf_text.strip():

                    st.session_state.quote_text = pdf_text

                    st.success(
                        f"PDF loaded: {page_count} page(s), "
                        f"text detected on {pages_with_text} page(s)."
                    )

                else:

                    st.warning(
                        "The PDF opened successfully, but no selectable "
                        "text was detected. It may be a scanned/image-only "
                        "quotation. Paste the quotation text below or use "
                        "an OCR-converted PDF."
                    )

            # =================================================
            # TXT
            # =================================================

            elif uploaded_file.name.lower().endswith(".txt"):

                txt_text, txt_error = extract_txt_text(
                    uploaded_file
                )

                if txt_error:

                    st.error(
                        "The TXT file could not be read."
                    )

                else:

                    st.session_state.quote_text = txt_text

                    st.success(
                        "TXT quotation loaded successfully."
                    )

    # --------------------------------------------------------
    # Editable quotation text
    # --------------------------------------------------------

    quote_text = st.text_area(
        "Quotation Text",
        value=st.session_state.quote_text,
        height=430,
        placeholder=(
            "Upload a PDF/TXT quotation or paste quotation text here.\n\n"
            "Examples of useful information:\n"
            "- Cavity and core material\n"
            "- Steel hardness\n"
            "- Mold base\n"
            "- Standard components\n"
            "- Hot runner\n"
            "- Cooling\n"
            "- Venting\n"
            "- Mold life\n"
            "- Validation\n"
            "- Inspection reports\n"
            "- Warranty\n"
        )
    )

    st.session_state.quote_text = quote_text

    # --------------------------------------------------------
    # PDF/text check
    # --------------------------------------------------------

    if quote_text.strip():

        with st.expander(
            "🔎 Quotation Extraction Check"
        ):

            st.write(
                f"Extracted text length: "
                f"**{len(quote_text):,} characters**"
            )

            preview_length = min(
                len(quote_text),
                5000
            )

            st.text_area(
                "Extracted Content Preview",
                value=quote_text[:preview_length],
                height=250,
                disabled=True
            )


# ============================================================
# RIGHT COLUMN
# ============================================================

with right_column:

    st.subheader("2. Application Requirements")

    supplier_name = st.text_input(
        "Mold Maker",
        placeholder="Example: ABC Tool & Mold"
    )

    application = st.selectbox(
        "Application",
        [
            "Medical / Precision",
            "Automotive",
            "Consumer",
            "Packaging",
            "Industrial",
        ]
    )

    resin = st.selectbox(
        "Molded Material",
        [
            "PP",
            "PE",
            "ABS",
            "PC",
            "PA / Nylon",
            "POM",
            "PEEK",
            "Optical / Medical Resin",
            "Other",
        ]
    )

    cavities = st.number_input(
        "Number of Cavities",
        min_value=1,
        max_value=512,
        value=4,
        step=1
    )

    annual_volume = st.number_input(
        "Estimated Annual Volume",
        min_value=1,
        max_value=1_000_000_000,
        value=1_000_000,
        step=100_000
    )

    required_cycles = st.number_input(
        "Required Mold Life (cycles)",
        min_value=1,
        max_value=100_000_000,
        value=1_000_000,
        step=100_000
    )

    tolerance = st.number_input(
        "Tightest Part Tolerance (mm)",
        min_value=0.001,
        max_value=5.000,
        value=0.020,
        step=0.001,
        format="%.3f"
    )


# ============================================================
# ANALYZE
# ============================================================

st.divider()

if st.button(
    "🔍 Analyze Mold Quote",
    type="primary",
    use_container_width=True
):

    clean_quote = st.session_state.quote_text.strip()

    if len(clean_quote) < 40:

        st.error(
            "Not enough quotation text was detected. "
            "Upload a readable PDF/TXT file or paste the quotation "
            "text into the quotation box."
        )

        st.session_state.analysis_result = None

    else:

        try:

            result = calculate_quality(
                clean_quote,
                required_cycles,
                tolerance,
                application
            )

            st.session_state.analysis_result = result

        except Exception as error:

            st.session_state.analysis_result = None

            st.error(
                "The quotation could not be analyzed."
            )

            st.exception(error)


# ============================================================
# RESULTS
# ============================================================

result = st.session_state.analysis_result

if result is not None:

    st.divider()

    st.header("Mold Quality Assessment")

    # --------------------------------------------------------
    # Basic project information
    # --------------------------------------------------------

    info1, info2, info3, info4 = st.columns(4)

    with info1:
        st.write("**Mold Maker**")
        st.write(
            supplier_name if supplier_name else "Not entered"
        )

    with info2:
        st.write("**Material**")
        st.write(resin)

    with info3:
        st.write("**Cavities**")
        st.write(cavities)

    with info4:
        st.write("**Required Life**")
        st.write(
            f"{required_cycles:,} cycles"
        )

    # ========================================================
    # OVERALL SCORE
    # ========================================================

    st.subheader("Overall MoldMatch Score")

    status, status_color = get_score_label(
        result["overall"]
    )

    score_column, recommendation_column = st.columns(
        [1, 2]
    )

    with score_column:

        st.metric(
            "Overall Score",
            f"{result['overall']} / 100"
        )

        st.progress(
            result["overall"] / 100
        )

    with recommendation_column:

        if status_color == "green":

            st.success(
                f"🟢 {status}"
            )

        elif status_color == "orange":

            st.warning(
                f"🟡 {status}"
            )

        else:

            st.error(
                f"🔴 {status}"
            )


    # ========================================================
    # THREE MAIN SCORES
    # ========================================================

    st.subheader("Core Quality Scores")

    score1, score2, score3 = st.columns(3)

    with score1:

        st.metric(
            "🛠️ Mold Construction",
            f"{result['construction']} / 100"
        )

        st.progress(
            result["construction"] / 100
        )

        st.caption(
            "Materials + design + standard components"
        )

    with score2:

        st.metric(
            "🏭 Mold Maker Confidence",
            f"{result['maker']} / 100"
        )

        st.progress(
            result["maker"] / 100
        )

        st.caption(
            "Quality systems + capabilities + experience"
        )

    with score3:

        st.metric(
            "📄 Quote Confidence",
            f"{result['quote']} / 100"
        )

        st.progress(
            result["quote"] / 100
        )

        st.caption(
            "Completeness + commitments + documentation"
        )


    # ========================================================
    # CONSTRUCTION DETAILS
    # ========================================================

    st.subheader("Mold Construction Detail")

    sub1, sub2, sub3 = st.columns(3)

    with sub1:

        st.metric(
            "Materials",
            f"{result['materials']} / 100"
        )

        st.progress(
            result["materials"] / 100
        )

    with sub2:

        st.metric(
            "Standard Components",
            f"{result['components']} / 100"
        )

        st.progress(
            result["components"] / 100
        )

    with sub3:

        st.metric(
            "Design / Construction",
            f"{result['design']} / 100"
        )

        st.progress(
            result["design"] / 100
        )


    # ========================================================
    # STRENGTHS AND RISKS
    # ========================================================

    strengths_column, risks_column = st.columns(2)

    with strengths_column:

        st.subheader("✅ Detected Strengths")

        if result["strengths"]:

            for strength in result["strengths"]:
                st.success(strength)

        else:

            st.info(
                "No significant technical strengths were "
                "automatically detected."
            )

    with risks_column:

        st.subheader("⚠️ Technical Risks")

        if result["risks"]:

            for risk in result["risks"]:
                st.warning(risk)

        else:

            st.success(
                "No significant rule-based risks detected."
            )


    # ========================================================
    # SUPPLIER CLARIFICATION LIST
    # ========================================================

    st.divider()

    st.header("📋 Supplier Clarification List")

    st.write(
        "The following questions were generated because the "
        "required information was not clearly detected in the quote."
    )

    questions = result["questions"]

    if questions:

        clarification_lines = []

        for number, question in enumerate(
            questions,
            start=1
        ):

            st.write(
                f"**{number}.** {question}"
            )

            clarification_lines.append(
                f"{number}. {question}"
            )

        # ----------------------------------------------------
        # Downloadable clarification report
        # ----------------------------------------------------

        supplier_display = (
            supplier_name
            if supplier_name
            else "Not entered"
        )

        clarification_report = (
            "MOLDMATCH\n"
            "MOLD QUALITY ANALYZER\n"
            "SUPPLIER CLARIFICATION LIST\n"
            "========================================\n\n"
            f"Mold Maker: {supplier_display}\n"
            f"Application: {application}\n"
            f"Molded Material: {resin}\n"
            f"Number of Cavities: {cavities}\n"
            f"Estimated Annual Volume: "
            f"{annual_volume:,}\n"
            f"Required Mold Life: "
            f"{required_cycles:,} cycles\n"
            f"Tightest Tolerance: "
            f"{tolerance:.3f} mm\n\n"
            f"Mold Construction Score: "
            f"{result['construction']}/100\n"
            f"Mold Maker Confidence: "
            f"{result['maker']}/100\n"
            f"Quote Confidence: "
            f"{result['quote']}/100\n"
            f"Overall MoldMatch Score: "
            f"{result['overall']}/100\n\n"
            "SUPPLIER QUESTIONS\n"
            "========================================\n\n"
            + "\n\n".join(clarification_lines)
        )

        st.download_button(
            "⬇️ Download Supplier Clarification List",
            data=clarification_report,
            file_name="MoldMatch_Supplier_Clarification.txt",
            mime="text/plain",
            use_container_width=True
        )

    else:

        st.success(
            "No standard clarification gaps were detected."
        )


    # ========================================================
    # RECOMMENDATION
    # ========================================================

    st.divider()

    st.header("Recommendation")

    score = result["overall"]

    if score >= 85:

        st.success(
            "PREFERRED\n\n"
            "The quotation provides strong evidence of a "
            "production-ready mold. Complete normal engineering "
            "review and close any remaining clarification items "
            "before purchase-order release."
        )

    elif score >= 70:

        st.warning(
            "ACCEPT WITH CLARIFICATION\n\n"
            "The proposed mold appears technically promising. "
            "Require the supplier to answer the clarification "
            "questions and incorporate the agreed requirements "
            "into the final technical specification before PO release."
        )

    elif score >= 55:

        st.warning(
            "CONDITIONAL / ENGINEERING REVIEW REQUIRED\n\n"
            "Important technical information is missing. Request "
            "a revised mold specification and conduct a detailed "
            "engineering review before supplier selection."
        )

    else:

        st.error(
            "HIGH RISK\n\n"
            "The quotation does not currently provide enough "
            "technical evidence to support mold-quality approval. "
            "Resolve the identified construction, documentation, "
            "and supplier-capability gaps before PO release."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "MoldMatch Mold Quality Analyzer is a supplier-screening "
    "and engineering decision-support tool. The score does not "
    "replace review of mold drawings, steel specifications, "
    "tolerances, Moldflow results, validation requirements, "
    "supplier capability, mold trials, and formal mold acceptance."
)