import streamlit as st
import re
from io import BytesIO

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
# RULES
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
        ["guided ejection", "ejection guide",
         "ejector guide"],
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
         "mold masters", "synventive", "husky",
         "yudo"],
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
        ["spare parts", "wear parts",
         "replacement parts"],
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
        ["medical tooling", "medical mold",
         "medical device"],
        12,
        "Medical tooling experience stated"
    ),
    (
        ["in-house design", "in house design",
         "design department"],
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
        ["lead time", "delivery weeks",
         "delivery date"],
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
        ["drawing", "3d data", "cad",
         "documentation"],
        10,
        "Engineering documentation included"
    ),
    (
        ["inspection report", "dimensional report",
         "cmm report"],
        15,
        "Dimensional inspection report included"
    ),
    (
        ["maintenance", "preventive maintenance",
         "pm schedule"],
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
# CLARIFICATION QUESTIONS
# ============================================================

CLARIFICATION_RULES = [
    (
        ["cavity steel", "core steel",
         "h13", "s136", "p20",
         "1.2344", "1.2083"],
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
        "Please provide the purchased-component BOM including "
        "manufacturer and component part numbers."
    ),
    (
        ["mold base"],
        "Please identify the mold-base manufacturer, plate "
        "materials and plate hardness."
    ),
    (
        ["hot runner", "cold runner", "valve gate"],
        "Please confirm the runner/gating system and identify "
        "the manufacturer and model."
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
        "format and measurement equipment."
    ),
    (
        ["acceptance criteria", "mold acceptance", "fat", "sat"],
        "Please define mold acceptance criteria, trial material, "
        "trial duration, cycle-time target and approval responsibilities."
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
        "standard and expected flow requirements."
    ),
    (
        ["venting", "vent depth"],
        "Please define mold vent locations and recommended vent "
        "depth for the specified resin."
    ),
    (
        ["maintenance", "preventive maintenance", "pm schedule"],
        "Please provide the preventive-maintenance schedule and "
        "recommended service intervals."
    ),
    (
        ["moldflow", "mold flow", "simulation"],
        "Please confirm whether filling, packing, cooling and "
        "warpage simulation are included."
    ),
]

# ============================================================
# FUNCTIONS
# ============================================================

def contains_any(text, keywords):
    text = text.lower()
    return any(keyword.lower() in text for keyword in keywords)


def evaluate_rules(text, rules):
    score = 0
    detected = []

    for keywords, points, description in rules:
        if contains_any(text, keywords):
            score += points
            detected.append(description)

    return min(score, 100), detected


def generate_clarifications(text):
    questions = []

    for keywords, question in CLARIFICATION_RULES:
        if not contains_any(text, keywords):
            questions.append(question)

    return questions


def calculate_quality(
    text,
    required_cycles,
    tolerance,
    application
):

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
    # Mold Construction
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
    # ENGINEERING PENALTIES
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

    if not contains_any(
        text,
        ["mold life", "tool life", "cycles warranty"]
    ):
        risks.append(
            "No mold-life commitment was detected."
        )

    if not contains_any(
        text,
        ["steel certificate", "material certificate",
         "mill certificate"]
    ):
        risks.append(
            "No steel certification/traceability commitment detected."
        )

    if not contains_any(
        text,
        ["spare parts", "wear parts"]
    ):
        risks.append(
            "No spare or wear-parts package detected."
        )

    mold_construction = max(0, min(mold_construction, 100))
    maker_score = max(0, min(maker_score, 100))
    quote_score = max(0, min(quote_score, 100))

    # --------------------------------------------------------
    # Overall MoldMatch Score
    # --------------------------------------------------------

    overall = round(
        mold_construction * 0.45
        + maker_score * 0.25
        + quote_score * 0.30
    )

    strengths = (
        material_hits
        + component_hits
        + construction_hits
        + maker_hits
        + quote_hits
    )

    questions = generate_clarifications(text)

    return {
        "overall": overall,
        "construction": mold_construction,
        "maker": maker_score,
        "quote": quote_score,
        "strengths": strengths,
        "risks": risks,
        "questions": questions,
    }


def score_status(score):

    if score >= 85:
        return "🟢 Preferred"

    elif score >= 70:
        return "🟡 Accept with Clarification"

    elif score >= 55:
        return "🟠 Conditional / Engineering Review"

    else:
        return "🔴 High Risk"


# ============================================================
# USER INTERFACE
# ============================================================

st.title("🛠️ Mold Quality Analyzer")

st.caption(
    "MoldMatch | Supplier Quote Technical Assessment"
)

st.info(
    "Upload or paste a supplier quotation. "
    "The analyzer reviews mold construction, mold-maker "
    "capability and quotation completeness."
)

# ============================================================
# INPUT
# ============================================================

left, right = st.columns([1.3, 1])

with left:

    st.subheader("Supplier Quotation")

    uploaded_file = st.file_uploader(
        "Upload quotation",
        type=["txt"]
    )

    quote_text = ""

    if uploaded_file:

        try:

            quote_text = uploaded_file.read().decode(
                "utf-8",
                errors="ignore"
            )

        except Exception:
            st.error("Unable to read quotation.")

    quote_text = st.text_area(
        "Quotation text",
        value=quote_text,
        height=350,
        placeholder=(
            "Paste quotation, mold specification, "
            "steel list, standard components, "
            "hot runner details, warranty, etc."
        )
    )


with right:

    st.subheader("Application Requirements")

    supplier_name = st.text_input(
        "Mold Maker"
    )

    application = st.selectbox(
        "Application",
        [
            "Medical / Precision",
            "Automotive",
            "Consumer",
            "Packaging",
            "Industrial"
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
            "Other"
        ]
    )

    cavities = st.number_input(
        "Number of Cavities",
        min_value=1,
        max_value=512,
        value=4
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
# ANALYSIS
# ============================================================

st.divider()

if st.button(
    "🔍 Analyze Mold Quote",
    type="primary",
    use_container_width=True
):

    if len(quote_text.strip()) < 40:

        st.error(
            "Please upload or paste the supplier quotation."
        )

    else:

        result = calculate_quality(
            quote_text.lower(),
            required_cycles,
            tolerance,
            application
        )

        # ====================================================
        # OVERALL RESULT
        # ====================================================

        st.header("Mold Quality Assessment")

        st.metric(
            "Overall MoldMatch Score",
            f"{result['overall']} / 100"
        )

        st.markdown(
            f"### {score_status(result['overall'])}"
        )

        st.progress(
            result["overall"] / 100
        )

        # ====================================================
        # THREE CORE SCORES
        # ====================================================

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "🛠️ Mold Construction",
                f"{result['construction']} / 100"
            )

            st.progress(
                result["construction"] / 100
            )

        with c2:

            st.metric(
                "🏭 Mold Maker Confidence",
                f"{result['maker']} / 100"
            )

            st.progress(
                result["maker"] / 100
            )

        with c3:

            st.metric(
                "📄 Quote Confidence",
                f"{result['quote']} / 100"
            )

            st.progress(
                result["quote"] / 100
            )

        # ====================================================
        # STRENGTHS
        # ====================================================

        st.subheader("✅ Detected Strengths")

        if result["strengths"]:

            for item in result["strengths"][:12]:
                st.write(f"✓ {item}")

        else:

            st.warning(
                "No significant technical strengths "
                "were detected in the quotation."
            )

        # ====================================================
        # RISKS
        # ====================================================

        st.subheader("⚠️ Technical Risks")

        if result["risks"]:

            for risk in result["risks"]:
                st.warning(risk)

        else:

            st.success(
                "No major rule-based technical risks detected."
            )

        # ====================================================
        # CLARIFICATION LIST
        # ====================================================

        st.header("📋 Supplier Clarification List")

        st.caption(
            "Generated automatically from missing information "
            "in the quotation."
        )

        questions = result["questions"]

        if questions:

            clarification_text = ""

            for number, question in enumerate(
                questions,
                start=1
            ):

                st.write(
                    f"**{number}.** {question}"
                )

                clarification_text += (
                    f"{number}. {question}\n\n"
                )

            st.download_button(
                "⬇️ Download Clarification List",
                clarification_text,
                file_name="supplier_clarification_list.txt",
                mime="text/plain"
            )

        else:

            st.success(
                "No standard clarification gaps detected."
            )

        # ====================================================
        # FINAL RECOMMENDATION
        # ====================================================

        st.header("Recommendation")

        score = result["overall"]

        if score >= 85:

            st.success(
                "PREFERRED: The quotation provides strong evidence "
                "of a production-ready mold. Close remaining "
                "clarification items before PO release."
            )

        elif score >= 70:

            st.warning(
                "ACCEPT WITH CLARIFICATION: The proposal appears "
                "technically promising, but clarification items "
                "should be closed in writing before PO release."
            )

        elif score >= 55:

            st.warning(
                "CONDITIONAL: Require a revised technical "
                "specification and engineering design review "
                "before supplier selection."
            )

        else:

            st.error(
                "HIGH RISK: Significant technical or documentation "
                "gaps exist. Do not release the PO based on the "
                "current quotation alone."
            )

# ============================================================
# DISCLAIMER
# ============================================================

st.divider()

st.caption(
    "MoldMatch Mold Quality Analyzer is a screening and "
    "decision-support tool. Final mold approval should include "
    "engineering review of the mold design, materials, mold-flow "
    "analysis, tolerances, validation requirements and application."
)
