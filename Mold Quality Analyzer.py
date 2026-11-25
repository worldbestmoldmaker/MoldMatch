import os
import re
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
import time
import numpy as np

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import letter
from io import BytesIO
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(
    page_title="MoldMatch | RICO Mold Machine Matching",
    page_icon="⚙️",
    layout="wide",
)

# -----------------------------------
# BASE PATH & ASSETS CONFIGURATION
# -----------------------------------
base_path = os.path.dirname(__file__)
logo_file = os.path.join(base_path, "MoldMatchLogo.PNG")
rico_hero_file = os.path.join(base_path, "RICO.jpg")
qr_file = os.path.join(base_path, "moldmatch_qr.png")
haitian_img = os.path.join(base_path, "Haitian.jpg")
krauss_img = os.path.join(base_path, "KraussM.jpg")
arburg_img = os.path.join(base_path, "Arburg.jpg")
sodick_img = os.path.join(base_path, "RICO.jpg")
engel_img = os.path.join(base_path, "Engel.jpg")
netstal_img = os.path.join(base_path, "Netstal.jpg")
sumitomo_img = os.path.join(base_path, "Sumitomo.jpg")
babyplast_img = os.path.join(base_path, "Babyplast.jpg")



excel_file = os.path.join(base_path, "machines_clean.xlsx")
log_path = os.path.join(base_path, "view_log.txt")

# -----------------------------------
# PDF REPORT GENERATORS
# -----------------------------------

def _parse_dimensions(value):
    """Return the first three numeric dimensions found in an L x W x H value."""
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    numbers = re.findall(r"\d+(?:\.\d+)?", str(value).replace(",", ""))
    if len(numbers) < 3:
        return None
    dims = tuple(float(number) for number in numbers[:3])
    return dims if all(dimension > 0 for dimension in dims) else None


def _draw_proportional_block_view(pdf, machine_data):
    machine_dims = _parse_dimensions(machine_data.get("machine_dimensions"))
    mold_dims = (
        float(machine_data.get("mold_length", 0) or 0),
        float(machine_data.get("mold_width", 0) or 0),
        float(machine_data.get("mold_thickness", 0) or 0),
    )
    if not machine_dims or not all(dimension > 0 for dimension in mold_dims):
        return

    machine_l, machine_w, machine_h = machine_dims
    mold_l, mold_w, mold_t = mold_dims
    pdf.showPage()
    if os.path.exists(logo_file):
        try:
            pdf.drawImage(
                logo_file, 50, 720, width=55, height=40,
                preserveAspectRatio=True, mask="auto"
            )
            header_x = 120
        except Exception:
            header_x = 50
    else:
        header_x = 50

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(header_x, 750, "MoldMatch Machine and Mold Size Comparison")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(header_x, 733, "Relative blocks based on actual dimensions (mm)")

    def draw_view(title, x, y, box_w, box_h, outer_a, outer_b, inner_a, inner_b, outer_label, inner_label):
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x, y + box_h + 18, title)
        scale = min(box_w / outer_a, box_h / outer_b)
        drawn_w, drawn_h = outer_a * scale, outer_b * scale
        outer_x = x + (box_w - drawn_w) / 2
        outer_y = y + (box_h - drawn_h) / 2
        pdf.setFillColorRGB(0.16, 0.55, 0.42, alpha=0.28)
        pdf.setStrokeColorRGB(0.08, 0.31, 0.25)
        pdf.rect(outer_x, outer_y, drawn_w, drawn_h, fill=1, stroke=1)
        inner_w, inner_h = inner_a * scale, inner_b * scale
        inner_x = outer_x + (drawn_w - inner_w) / 2
        inner_y = outer_y + (drawn_h - inner_h) / 2
        pdf.setFillColorRGB(0.25, 0.55, 0.90, alpha=0.65)
        pdf.setStrokeColorRGB(0.10, 0.29, 0.58)
        pdf.rect(inner_x, inner_y, inner_w, inner_h, fill=1, stroke=1)
        pdf.setFillColorRGB(0, 0, 0)
        pdf.setFont("Helvetica", 8)
        pdf.drawString(x, y - 13, outer_label)
        pdf.drawString(x, y - 26, inner_label)

    # Side view: machine L x H; mold thickness x mold width.
    draw_view(
        "Side View", 50, 415, 512, 230,
        machine_l, machine_h, mold_t, mold_width_for_view := min(mold_w, machine_h),
        f"Machine envelope: {machine_l:g} L x {machine_h:g} H",
        f"Mold block: {mold_t:g} thickness x {mold_width_for_view:g} height",
    )
    # Top view: machine L x W; mold thickness x mold length.
    draw_view(
        "Top View", 50, 105, 512, 230,
        machine_l, machine_w, mold_t, min(mold_l, machine_w),
        f"Machine envelope: {machine_l:g} L x {machine_w:g} W",
        f"Mold block: {mold_t:g} thickness x {mold_l:g} length",
    )
    pdf.setFont("Helvetica-Oblique", 8)
    pdf.drawString(50, 55, "Visualization compares external envelopes only; it does not represent platen position or installation clearances.")


def generate_pdf(machine_data):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    if os.path.exists(logo_file):
        try:
            pdf.drawImage(logo_file, 50, 720, width=40, height=40, preserveAspectRatio=True, mask='auto')
            title_x = 100
        except Exception:
            title_x = 50
    else:
        title_x = 50

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(title_x, 735, "Mold Match Analysis Report")

    pdf.setFont("Helvetica", 12)

    pdf.drawString(50, 680, f"Machine: {machine_data['oem']} - {machine_data['model']}")
    pdf.drawString(50, 655, f"Platen: {machine_data['platen_x']} × {machine_data['platen_y']} mm")
    pdf.drawString(50, 630, f"Tie Bars: {machine_data['tie_bar_x']} × {machine_data['tie_bar_y']} mm")
    machine_dimensions = machine_data.get("machine_dimensions", "N/A")
    if pd.isna(machine_dimensions) or str(machine_dimensions).strip() == "":
        machine_dimensions = "N/A"
    pdf.drawString(50, 605, f"Machine Dimensions L X W X H: {machine_dimensions} mm")
    pdf.drawString(50, 580, f"Screw Size: {machine_data['screw_size']} mm")

    shot = machine_data.get("shot_utilization", "N/A")
    shot_text = str(shot).strip()
    if shot_text and shot_text.lower() != "nan" and not shot_text.endswith("%"):
        try:
            shot_text = f"{round(float(shot))}%"
        except (TypeError, ValueError):
            pass
    shot = shot_text or "N/A"

    pdf.drawString(50, 555, f"Shot Utilization: {shot}")

    # Include Injection Unit 2 in the Mold Match Analysis Report for Two Shots.
    if machine_data.get("machine_type") == "Two Shots":
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, 520, "2nd Injection Unit")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, 495, f"OEM: {machine_data.get('shot_2_unit_oem') or 'N/A'}")
        pdf.drawString(50, 470, f"Series: {machine_data.get('shot_2_unit_series') or 'N/A'}")
        pdf.drawString(50, 445, f"Model: {machine_data.get('shot_2_unit_model') or 'N/A'}")
        pdf.drawString(50, 420, f"Shot Capacity: {machine_data.get('shot_2_capacity', 'N/A')} g")
        pdf.drawString(50, 395, f"Screw Size: {machine_data.get('shot_2_screw_size', 'N/A')} mm")
        shot2 = machine_data.get("shot_2_utilization", "N/A")
        try:
            shot2 = f"{round(float(shot2))}%"
        except (TypeError, ValueError):
            shot2 = str(shot2) if shot2 not in (None, "") else "N/A"
        pdf.drawString(50, 370, f"Shot Utilization: {shot2}")
        pdf.drawString(50, 345, f"Required Shot 2: {machine_data.get('shot_2_required_weight', 'N/A')} g")
        pdf.drawString(50, 320, f"Material: {machine_data.get('shot_2_material') or 'N/A'}")

    _draw_proportional_block_view(pdf, machine_data)
    pdf.save()
    buffer.seek(0)
    return buffer


def generate_process_sheet_pdf(machine_data, process_inputs):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    if os.path.exists(logo_file):
        try:
            pdf.drawImage(logo_file, 50, 720, width=40, height=40, preserveAspectRatio=True, mask='auto')
            title_x = 100
        except Exception:
            title_x = 50
    else:
        title_x = 50

    # Title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(title_x, 735, "Process Sheet Report")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 690, "1. Recommended Machine Specifications")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(60, 675, f"OEM & Model: {machine_data['oem']} - {machine_data['model']}")
    pdf.drawString(60, 660, f"Platen Size: {machine_data['platen_x']} × {machine_data['platen_y']} mm")
    pdf.drawString(60, 645, f"Tie Bar Spacing: {machine_data['tie_bar_x']} × {machine_data['tie_bar_y']} mm")
    pdf.drawString(60, 630, f"Screw Diameter: {machine_data['screw_size']} mm")
    shot = machine_data.get("shot_utilization", "N/A")
    shot_text = str(shot).strip()
    if shot_text and shot_text.lower() != "nan" and not shot_text.endswith("%"):
        try:
            shot_text = f"{round(float(shot))}%"
        except (TypeError, ValueError):
            pass
    shot = shot_text or "N/A"
    pdf.drawString(60, 615, f"Shot Utilization: {shot}")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 585, "2. Material & Tooling Parameters")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(60, 570, f"Resin Material: {process_inputs['material']}")
    pdf.drawString(60, 555, f"Number of Cavities: {process_inputs['cavity_num']}")
    pdf.drawString(60, 540, f"Wall Thickness: {process_inputs['wall_thickness']} mm")
    pdf.drawString(60, 525, f"Gate Size: {process_inputs['gate_size']} mm")
    pdf.drawString(60, 510, f"Runner System: {process_inputs['runner_type']}")
    
    if process_inputs['runner_type'] == "Cold Runner":
        runner_str = f"- Cold Runner Weight: {process_inputs['cold_runner_weight']} g"
        pdf.drawString(60, 495, f"Cold Runner Weight: {process_inputs['cold_runner_weight']} g")
        prompt_y = 465
    else:
        runner_str = ""
        prompt_y = 480

    # AI instructions are embedded invisibly below and are not rendered on the page.
    # Keep the original thermoplastic prompt, but automatically use an LSR-specific
    # prompt when the LSR database/material/machine is selected.
    is_lsr = (
        str(process_inputs.get("material", "")).strip().upper() == "LSR"
        or str(machine_data.get("model", "")).strip().upper().endswith("-LSR")
    )

    thermoplastic_prompt = (
        f"Act as a Senior Injection Molding Process Engineer. Create a detailed baseline processing sheet\n "
        f"for an injection molding setup using the following parameters:\n"
        f"- Machine: {machine_data['oem']} {machine_data['model']} (Screw Size: {machine_data['screw_size']} mm)\n"
        f"- Material: {process_inputs['material']}\n"
        f"- Tooling: {process_inputs['cavity_num']}-cavity mold with {process_inputs['runner_type']} system\n"
        f"- Nominal Wall Thickness: {process_inputs['wall_thickness']} mm\n"
        f"- Gate Size: {process_inputs['gate_size']} mm\n"
        f"- Part Weight / Shot Weight: {process_inputs['shot_weight']} g\n"
        f"{runner_str}\n\n"
        f"Please calculate and recommend:\n"
        f"1. Melt Temperature Profile (Rear, Center, Front, Nozzle zones)\n"
        f"2. Mold Temperature & Drying Guidelines (Temp & Hours)\n"
        f"3. Injection Speed, Packing Pressure, and Hold Time\n"
        f"4. Cooling Time & Total Cycle Time Estimation\n"
        f"5. Estimate Clamp Force based on part weight, wall thickness, and material and\n"
        f"multiply by a factor of 1.2. Also recommend the Back Pressure.\n"
        f"6. Estimate the Start of Screw Position in mm using the {machine_data['screw_size']} mm\n"
        f"screw diameter and {process_inputs['shot_weight']} g shot weight,\n"
        f"and {process_inputs['material']} material. State the assumptions used for melt density,\n"
        f"available screw stroke, and required cushion. Report both the estimated start position\n"
        f"and recommended cushion, and\n"
        f"note that the value must be verified during machine setup.\n\n"
        f"Generate downloadable process setup sheet based on this report."
    )

    if is_lsr:
        prompt_text = (
            f"Act as a Senior Liquid Silicone Rubber (LSR) Injection Molding Process Engineer. "
            f"Create a detailed baseline processing sheet for an LSR injection molding setup using the following parameters:\n"
            f"- Machine: {machine_data['oem']} {machine_data['model']} (Injection/Screw Size: {machine_data['screw_size']} mm)\n"
            f"- Material: {process_inputs['material']}\n"
            f"- Tooling: {process_inputs['cavity_num']}-cavity mold with {process_inputs['runner_type']} system\n"
            f"- Nominal Wall Thickness: {process_inputs['wall_thickness']} mm\n"
            f"- Gate Size: {process_inputs['gate_size']} mm\n"
            f"- Part Weight / Shot Weight: {process_inputs['shot_weight']} g\n"
            f"{runner_str}\n\n"
            f"Please calculate and recommend an LSR-specific baseline process:\n"
            f"1. Material preparation: recommended A:B ratio, pigment/additive assumptions, dosing/mixing checks, and air-entry prevention. "
            f"Do not recommend thermoplastic resin drying unless the specific LSR supplier requires it.\n"
            f"2. Injection-unit temperature control: recommend feed, barrel/injection unit, and nozzle/cold-runner temperature targets or limits "
            f"needed to prevent premature curing. Clearly distinguish these from mold temperature.\n"
            f"3. Mold temperature: recommend a starting hot-mold curing temperature range and temperature-balance guidance.\n"
            f"4. Filling: recommend injection speed/profile, injection pressure limit, and V/P transfer strategy suitable for low-viscosity LSR.\n"
            f"5. Hold/pack: recommend hold pressure and hold time, and explain that excessive pressure can create flash on LSR tooling.\n"
            f"6. Cure: estimate cure/vulcanization time and total cycle time from wall thickness and assumed LSR cure behavior. "
            f"Do not calculate thermoplastic cooling time.\n"
            f"7. Runner/gating: recommend cold-runner and valve-gate settings/strategy when applicable, including gate timing and shutoff considerations; otherwise state N/A.\n"
            f"8. Clamp force: estimate required clamp force based on part weight, wall thickness, and material, then multiply by a 1.2 safety factor. "
            f"Show the assumptions and calculation.\n"
            f"9. Metering/back pressure: recommend LSR-appropriate metering/back-pressure guidance. If the selected machine uses a plunger or V-LINE-style separate plasticization/injection system, "
            f"do not assume conventional reciprocating-screw behavior; explain the machine-specific limitation.\n"
            f"10. Start position / shot position: estimate the starting injection or metering position in mm using the {machine_data['screw_size']} mm injection diameter and {process_inputs['shot_weight']} g shot weight. "
            f"State the assumed mixed-LSR density, usable injection stroke, volumetric efficiency, and required cushion. Report both the estimated start position and recommended cushion. "
            f"If the available machine data is insufficient for a reliable conversion, explicitly state what additional machine parameter is required rather than inventing it.\n"
            f"11. Startup/validation: provide a short setup sequence and checks for A:B ratio, dosing/mixing, air entrapment, short shot, flash, cure state, sticking/demolding, and dimensional stability.\n"
            f"12. Process window: provide practical low/nominal/high starting values for the critical settings where enough information exists.\n\n"
            f"Separate calculated values from engineering assumptions. Flag all values that require verification against the LSR supplier datasheet, mold design, dosing system, and {machine_data['oem']} machine documentation. "
            f"Generate a downloadable LSR process setup sheet based on this report."
        )
    else:
        prompt_text = thermoplastic_prompt

    # PDF text rendering mode 3 stores text in the PDF text layer but does not
    # paint it on screen or on paper. This is stronger than white/off-page text.
    pdf.saveState()
    text_obj = pdf.beginText(20, 20)
    text_obj.setFont("Helvetica", 1)
    text_obj.setLeading(1)
    text_obj.setTextRenderMode(3)
    for raw_line in prompt_text.split("\n"):
        line = raw_line.strip()
        while len(line) > 140:
            split_at = line.rfind(" ", 0, 140)
            if split_at < 1:
                split_at = 140
            text_obj.textLine(line[:split_at])
            line = line[split_at:].lstrip()
        text_obj.textLine(line)
    pdf.drawText(text_obj)
    pdf.restoreState()

    pdf.save()
    buffer.seek(0)
    return buffer


# -----------------------------------
# NPE / RICO MOLD BOOTH EXPERIENCE
# -----------------------------------
st.markdown(
    """
    <style>
    .stApp { background-color: #f6f8fb; }
    .block-container { padding-top: 3.75rem !important; padding-bottom: 3rem; max-width: 1200px; }
    .npe-hero {
        background: linear-gradient(135deg, #003b71 0%, #005b9f 100%);
        padding: 34px 40px 32px; border-radius: 18px; color: white;
        margin-bottom: 24px; box-shadow: 0 5px 18px rgba(0,0,0,0.12);
    }
    .npe-brand { font-size: 52px; font-weight: 900; letter-spacing: 1px; color: #58D6FF; line-height: 1.05; text-shadow: 0 2px 8px rgba(0,0,0,.18); }
    .npe-title { font-size: 40px; font-weight: 800; line-height: 1.1; margin: 16px 0 10px; }
    .npe-subtitle { font-size: 20px; font-weight: 500; opacity: .96; }
    .npe-description { font-size: 15px; margin-top: 13px; opacity: .87; max-width: 760px; }

    .rico-mold-caption {
        text-align: center; color: #52606d; font-size: 14px; font-weight: 600;
        margin-top: -4px; margin-bottom: 8px; letter-spacing: .2px;
    }
    div[data-testid="stImage"] img { border-radius: 18px; }
    .step-header {
        background: white; border-left: 6px solid #0072CE; padding: 14px 18px;
        border-radius: 8px; margin: 20px 0 16px; box-shadow: 0 2px 8px rgba(0,0,0,.06);
    }
    .step-number { color: #0072CE; font-size: 13px; font-weight: 800; letter-spacing: 1px; }
    .step-title { color: #1f2937; font-size: 25px; font-weight: 700; }
    .result-card {
        background: linear-gradient(135deg, #eaf7ef, #fff); border: 2px solid #28a745;
        padding: 24px; border-radius: 15px; margin: 18px 0;
        box-shadow: 0 4px 14px rgba(0,0,0,.09);
    }
    .result-label { color: #188038; font-size: 15px; font-weight: 800; letter-spacing: 1px; }
    .result-machine { color: #003b71; font-size: 32px; font-weight: 800; }
    div.stButton > button {
        background: linear-gradient(90deg, #0072CE, #005b9f); color: white;
        border: none; font-size: 21px; font-weight: 800; height: 62px;
        border-radius: 12px; width: 100%; box-shadow: 0 4px 12px rgba(0,91,159,.25);
    }
    div.stButton > button:hover { background: linear-gradient(90deg, #005b9f, #003b71); color: white; border: none; }
    div[data-testid="stMetric"] { background: white; border: 1px solid #e3e8ef; padding: 12px; border-radius: 10px; }
    .booth-disclaimer {
        margin-top: 35px; padding: 15px 20px; background: #eef2f6;
        border-radius: 9px; color: #59636e; font-size: 12px; text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Hero area
logo_col, hero_col = st.columns([1, 7])
with logo_col:
    if os.path.exists(logo_file):
        st.image(logo_file, width=105)
    if os.path.exists(qr_file):
        st.image(qr_file, width=105)
        st.markdown(
            '<div style="text-align:center;font-size:12px;font-weight:700;color:#005b9f;line-height:1.2;">SCAN<br>moldmatchapp.com</div>',
            unsafe_allow_html=True,
        )
with hero_col:
    st.markdown(
        """
        <div class="npe-hero">
            <div class="npe-brand">MoldMatch × RICO MOLD</div>
            <div class="npe-title">Match Your Mold.<br>With the Right Machine.</div>
            <div class="npe-subtitle">Independent mold-to-machine compatibility screening</div>
            <div class="npe-description">
                Enter the RICO mold and process requirements. MoldMatch evaluates the machine
                database and identifies compatible injection molding machines.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Optional RICO mold visual
if os.path.exists(rico_hero_file):
    st.image(rico_hero_file, use_container_width=True)
    st.markdown(
        '<div class="rico-mold-caption">RICO Mold Engineering and Manufacturing</div>',
        unsafe_allow_html=True,
    )
else:
    st.info("Optional: add RicoMold.jpg beside this Python file to display a large RICO mold image.")

# ---------------------------
# LOAD DATA
# ---------------------------
@st.cache_data
def get_excel_sheet_names():
    return pd.ExcelFile(excel_file, engine="openpyxl").sheet_names

@st.cache_data
def load_data(sheet_name="Plastic"):
    """Load a worksheet with case/space-insensitive sheet-name matching."""
    sheet_names = get_excel_sheet_names()
    normalized = {str(name).strip().casefold(): name for name in sheet_names}
    requested = str(sheet_name).strip().casefold()
    if requested not in normalized:
        available = ", ".join(str(name) for name in sheet_names)
        raise ValueError(f"Worksheet '{sheet_name}' not found. Available worksheets: {available}")
    return pd.read_excel(excel_file, sheet_name=normalized[requested], engine="openpyxl")

# STEP 1
st.markdown(
    '<div class="step-header"><div class="step-number">STEP 1</div>'
    '<div class="step-title">Select Molding Technology</div></div>',
    unsafe_allow_html=True,
)
machine_type = st.selectbox(
    "Molding Technology",
    options=["Thermoplastic", "LSR", "Two Shots"],
    index=0,
    label_visibility="collapsed",
)

if machine_type == "LSR":
    data_sheet = "LSR"
elif machine_type == "Two Shots":
    data_sheet = "Two Shot"
else:
    data_sheet = "Plastic"

try:
    df = load_data(data_sheet).copy()
except ValueError as exc:
    st.error(f"Unable to load worksheet '{data_sheet}' from machines_clean.xlsx.")
    st.caption(str(exc))
    st.stop()

if machine_type == "Two Shots":
    required_two_shot_cols = [
        "OEM", "Series", "1st Unit Model", "Shot Weight (g)", "Screw Size (mm)",
        "2nd Unit Model", "2nd Shot Weight (g)", "2nd Screw Size (mm)",
    ]
    missing_two_shot_cols = [c for c in required_two_shot_cols if c not in df.columns]
    if missing_two_shot_cols:
        st.error("The 'Two Shot' tab is missing required columns: " + ", ".join(missing_two_shot_cols))
        st.stop()
    df["Model"] = df["1st Unit Model"]

# Evaluate all machine OEMs by default so the RICO mold can be matched independently.
available_oems = sorted(df["OEM"].dropna().astype(str).str.strip().unique().tolist())
oem_scope = st.selectbox(
    "Machine brand scope",
    options=["All machine brands"] + available_oems,
    index=0,
    help="Use all brands for an independent match, or select one OEM for a focused review.",
)
selected_oem = oem_scope
if oem_scope != "All machine brands":
    df = df[df["OEM"].astype(str).str.strip() == oem_scope].copy()
if df.empty:
    st.error(f"No machines were found for the selected scope in the '{data_sheet}' worksheet.")
    st.stop()

# STEP 2
st.markdown(
    '<div class="step-header"><div class="step-number">STEP 2</div>'
    '<div class="step-title">Enter Your Mold Requirements</div></div>',
    unsafe_allow_html=True,
)

rico_mold_reference = st.text_input(
    "RICO Mold Reference / Project",
    value="RICO Mold Project",
    help="Enter the RICO mold number, quotation number, or project name.",
)

st.markdown("### 📐 Mold Dimensions")
col1, col2, col3 = st.columns(3)
with col1:
    mold_length = st.number_input("Length (mm)", min_value=1, value=636)
with col2:
    mold_width = st.number_input("Width (mm)", min_value=1, value=396)
with col3:
    mold_height = st.number_input("Thickness (mm)", min_value=1, value=458)

st.markdown("### 🏗️ Clamp Requirement")
c1, c2 = st.columns(2)
with c1:
    clamp_min = st.number_input("Minimum Clamp Force (ton)", min_value=0, value=50)
with c2:
    clamp_max = st.number_input("Maximum Clamp Force (ton)", min_value=1, value=200)

st.markdown("### ⚖️ Shot Requirement")
if machine_type == "Two Shots":
    s1, s2 = st.columns(2)
    with s1:
        shot_weight = st.number_input("Shot 1 Weight (g)", min_value=0.01, value=15.0, step=0.5)
    with s2:
        shot_2_weight = st.number_input("Shot 2 Weight (g)", min_value=0.01, value=5.0, step=0.5)
else:
    shot_weight = st.number_input("Shot Weight (g)", min_value=0.01, value=15.0, step=0.5)
    shot_2_weight = 0.0

st.markdown("### 🧪 Material & Tooling")
mcol1, mcol2 = st.columns(2)
with mcol1:
    material_input = st.text_input("Material / Resin", value="LSR" if machine_type == "LSR" else "ABS")
    cavity_num_input = st.number_input("Number of Cavities", min_value=1, value=4, step=1)
    if machine_type == "LSR":
        runner_system = st.selectbox("Runner System", ["Cold Runner"], index=0, disabled=True)
    else:
        runner_system = st.selectbox("Runner System", ["Hot Runner", "Cold Runner"], index=0)
with mcol2:
    wall_thickness_input = st.number_input("Nominal Wall Thickness (mm)", min_value=0.01, value=2.0, step=0.1)
    gate_size_input = st.number_input("Gate Size (mm)", min_value=0.01, value=1.2, step=0.1)

cold_runner_weight_input = 0.0
if runner_system == "Cold Runner":
    cold_runner_weight_input = st.number_input("Cold Runner Weight (g)", min_value=0.0, value=5.0, step=0.5)

shot_2_material = ""
if machine_type == "Two Shots":
    shot_2_material = st.text_input("Shot 2 Material", value="TPE")

safety_clearance = mold_height * 0.1 + 20
required_opening = mold_height + safety_clearance
r1, r2 = st.columns(2)
with r1:
    st.metric("Mold Thickness", f"{mold_height:.0f} mm")
with r2:
    st.metric("Required Machine Opening", f"{required_opening:.0f} mm")

# ---------------------------
# TWO-SHOT SAME-ROW MATCHING
# ---------------------------
def same_row_second_shot(machine):
    if machine_type != "Two Shots":
        return None
    cap = pd.to_numeric(pd.Series([machine.get("2nd Shot Weight (g)")]), errors="coerce").iloc[0]
    if pd.isna(cap) or cap <= 0:
        return None
    util = shot_2_weight / cap * 100
    if util < 15 or util > 80:
        return None
    return {
        "OEM": machine.get("OEM"),
        "Series": machine.get("Series"),
        "Model": machine.get("2nd Unit Model"),
        "2nd Shot Weight (g)": cap,
        "2nd Screw Size (mm)": machine.get("2nd Screw Size (mm)"),
        "Shot 2 Utilization (%)": util,
    }

# ---------------------------
# CHECK FUNCTION
# ---------------------------
def check(machine):
    reasons = []

    platen_x = machine.get("Platen X (mm)")
    if pd.notna(platen_x) and mold_length > platen_x:
        reasons.append("Too long")

    tie_y = machine.get("Tie Bar Y (mm)")
    platen_y = machine.get("Platen Y (mm)")

    if pd.notna(tie_y) and mold_width > tie_y:
        reasons.append("Too wide")

    mold_min = machine.get("Mold Min (mm)", 0)
    daylight_max = machine.get("Daylight Max (mm)", 9999)

    if pd.notna(mold_min) and mold_height < mold_min:
        reasons.append("Too thin")

    if pd.notna(daylight_max) and required_opening > daylight_max:
        reasons.append("Too thick")

    clamp_force = machine.get("Clamp Force (ton)", 0)
    if not (clamp_min <= clamp_force <= clamp_max):
        reasons.append("Clamp out of range")

    if pd.notna(daylight_max) and required_opening > daylight_max:
        reasons.append("Insufficient daylight")

    shot_capacity = machine.get("Shot Weight (g)")
    
    if pd.notna(shot_capacity):
        utilization = shot_weight / shot_capacity
        if utilization > 0.8:
            reasons.append("Insufficient shot capacity")
        elif utilization < 0.15:
            reasons.append("Shot too small")
    else:
        reasons.append("No shot data")
    if machine_type == "Two Shots" and same_row_second_shot(machine) is None:
        reasons.append("No compatible Injection Unit 2")
    return "PASS" if not reasons else "FAIL", ", ".join(set(reasons))

# ---------------------------
# STEP 3 - RUN ANALYSIS
# ---------------------------
st.markdown(
    '<div class="step-header"><div class="step-number">STEP 3</div>'
    '<div class="step-title">Match the RICO Mold with Your Machine</div></div>',
    unsafe_allow_html=True,
)
st.caption(
    "MoldMatch evaluates mold fit, clamp range, shot capacity, tie-bar clearance, "
    "and machine opening against the available machine database."
)

valid = pd.DataFrame()
best = None
run_analysis = st.button("🔎 MATCH THIS RICO MOLD", use_container_width=True)

if run_analysis:
    with st.spinner("Evaluating machine compatibility for the RICO mold..."):
        results = []
        for _, m in df.iterrows():
            status, reason = check(m)
            shot_capacity = m.get("Shot Weight (g)")
            utilization = int((shot_weight / shot_capacity) * 100) if pd.notna(shot_capacity) and shot_capacity > 0 else None
            unit_2 = same_row_second_shot(m) if machine_type == "Two Shots" else None
            results.append({
                "OEM": m["OEM"],
                "Model": m["Model"],
                "Clamp (ton)": m["Clamp Force (ton)"],
                "Platen X (mm)": m["Platen X (mm)"],
                "Platen Y (mm)": m["Platen Y (mm)"],
                "Tie Bar X (mm)": m["Tie Bar X (mm)"],
                "Tie Bar Y (mm)": m["Tie Bar Y (mm)"],
                "Daylight Max (mm)": m["Daylight Max (mm)"],
                "Shot Weight (g)": m["Shot Weight (g)"],
                "Screw Size (mm)": m["Screw Size (mm)"],
                "Machine Dimensions L X W X H (mm)": m.get("Machine Dimensions L X W X H (mm)", "N/A"),
                "2nd Unit OEM": unit_2["OEM"] if unit_2 else None,
                "2nd Unit Series": unit_2["Series"] if unit_2 else None,
                "2nd Unit Model": unit_2["Model"] if unit_2 else None,
                "2nd Shot Weight (g)": unit_2["2nd Shot Weight (g)"] if unit_2 else None,
                "2nd Screw Size (mm)": unit_2["2nd Screw Size (mm)"] if unit_2 else None,
                "Shot 2 Utilization (%)": unit_2["Shot 2 Utilization (%)"] if unit_2 else None,
                "Status": status,
                "Shot Utilization (%)": utilization,
                "Fail Reason": reason,
            })

    results_df = pd.DataFrame(results)
    passed_df = results_df[results_df["Status"] == "PASS"].copy()
    failed_df = results_df[results_df["Status"] == "FAIL"].copy()
    valid = passed_df.copy()

    st.warning(
        "Engineering screening tool only. Final machine approval requires "
        "machine OEM/application engineer and RICO Mold validation."
    )

    if not valid.empty:
        valid["Utilization Deviation"] = (valid["Shot Utilization (%)"] - 50).abs()
        if machine_type == "Two Shots":
            valid["Unit 2 Utilization Deviation"] = (valid["Shot 2 Utilization (%)"] - 50).abs()
            valid["Combined Utilization Deviation"] = valid["Utilization Deviation"] + valid["Unit 2 Utilization Deviation"]
            best = valid.sort_values("Combined Utilization Deviation").iloc[0]
        else:
            best = valid.sort_values("Utilization Deviation").iloc[0]

        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-label">RECOMMENDED MACHINE FOR {rico_mold_reference}</div>
                <div class="result-machine">{best['Model']}</div>
                <div style="font-size:18px;margin-top:10px;color:#333;">
                    Clamp Force: <b>{best['Clamp (ton)']} ton</b>
                    &nbsp;&nbsp;|&nbsp;&nbsp;
                    Shot Utilization: <b>{round(float(best['Shot Utilization (%)']))}%</b>
                </div>
                <div style="margin-top:18px;font-size:17px;line-height:1.8;">
                    ✅ Mold dimensions compatible<br>
                    ✅ Tie-bar clearance compatible<br>
                    ✅ Machine opening compatible<br>
                    ✅ Clamp range compatible<br>
                    ✅ Shot capacity compatible
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if machine_type == "Two Shots":
            st.markdown("#### Recommended Injection Units")
            u1, u2 = st.columns(2)
            with u1:
                st.markdown("**Injection Unit 1**")
                st.write(f"Machine: {best['OEM']} - {best['Model']}")
                st.write(f"Shot capacity: {best['Shot Weight (g)']} g PS")
                st.write(f"Screw size: {best['Screw Size (mm)']} mm")
                st.write(f"Required Shot 1: {shot_weight:.1f} g")
                st.write(f"Shot utilization: {round(float(best['Shot Utilization (%)']))}%")
                st.write(f"Material: {material_input}")
            with u2:
                st.markdown("**Injection Unit 2**")
                st.write(f"OEM: {best['2nd Unit OEM']}")
                st.write(f"Series: {best['2nd Unit Series']}")
                st.write(f"Model: {best['2nd Unit Model']}")
                st.write(f"Shot capacity: {best['2nd Shot Weight (g)']} g")
                st.write(f"Screw size: {best['2nd Screw Size (mm)']} mm")
                st.write(f"Required Shot 2: {shot_2_weight:.1f} g")
                st.write(f"Shot utilization: {best['Shot 2 Utilization (%)']:.1f}%")
                st.write(f"Material: {shot_2_material}")

        with st.expander("View Engineering Analysis"):
            st.markdown("### Compatible Machines")
            st.dataframe(passed_df.head(10), use_container_width=True)
            st.markdown("### Other Evaluated Machines")
            st.dataframe(failed_df.head(10), use_container_width=True)

        st.header("📊 Results Analysis")
        machine_row = df[df["Model"] == best["Model"]].iloc[0]
        platen_x = machine_row["Platen X (mm)"]
        platen_y = machine_row["Platen Y (mm)"]
        daylight_max = machine_row["Daylight Max (mm)"]
        mold_area = mold_length * mold_width
        platen_area = platen_x * platen_y
        area_ratio = (mold_area / platen_area) * 100
        if area_ratio < 70:
            ratio_color = "🟢 SAFE"
        elif area_ratio < 85:
            ratio_color = "🟡 WARNING"
        else:
            ratio_color = "🔴 RISK"
        opening_gap = daylight_max - mold_height
        if opening_gap >= safety_clearance:
            gap_color = "🟢 SAFE"
        elif opening_gap > 0:
            gap_color = "🟡 TIGHT"
        else:
            gap_color = "🔴 TOO TALL"
        st.subheader("📐 Mold Fit Analysis")
        cA, cB = st.columns(2)
        cA.markdown(f"### {ratio_color}")
        cA.metric("Projected Area Ratio", f"{area_ratio:.1f}%")
        cB.markdown(f"### {gap_color}")
        cB.metric("Opening Gap", f"{opening_gap:.1f} mm")
    else:
        st.error("No compatible machine was found for the entered RICO mold requirements.")

if len(valid) > 0:

    st.subheader("⚖️ Shot Weight Analysis")

    machine_shot = best["Shot Weight (g)"]
    actual_shot = shot_weight

    if machine_shot > 0:
        shot_ratio = actual_shot / machine_shot
    else:
        shot_ratio = 0

    if 0.2 <= shot_ratio <= 0.8:
        shot_color = "🟢 GOOD"
    elif 0.1 <= shot_ratio < 0.2 or 0.8 < shot_ratio <= 0.9:
        shot_color = "🟡 MARGINAL"
    else:
        shot_color = "🔴 OUT OF RANGE"

    cA, cB = st.columns(2)

    with cA:
        st.metric("Shot 1 Utilization (%)" if machine_type == "Two Shots" else "Shot Utilization (%)", f"{round(shot_ratio*100)}%")

    with cB:
        st.metric("Shot 1 Status" if machine_type == "Two Shots" else "Status", shot_color)

    if machine_type == "Two Shots":
        shot_2_ratio = best["Shot 2 Utilization (%)"] / 100
        if 0.20 <= shot_2_ratio <= 0.80:
            shot_2_color = "🟢 GOOD"
        elif 0.15 <= shot_2_ratio < 0.20:
            shot_2_color = "🟡 MARGINAL"
        else:
            shot_2_color = "🔴 OUT OF RANGE"
        s2a, s2b = st.columns(2)
        with s2a:
            st.metric("Shot 2 Utilization (%)", f"{best['Shot 2 Utilization (%)']:.1f}%")
        with s2b:
            st.metric("Shot 2 Status", shot_2_color)

else:
    st.warning("No valid machine → Shot analysis skipped")

st.subheader("🖼️ Visual RICO Mold Fit on Recommended Machine")

if 'valid' in locals() and len(valid) > 0:
    platen_open = daylight_max
    platen_height = platen_y

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "Front View",
            "Top View"
        )
    )

    fig.add_shape(
        row=1,
        col=1,
        type="rect",
        x0=0,
        y0=0,
        y1=platen_height,
        x1=platen_open,
        line=dict(color="blue", width=2),
        fillcolor="rgba(173,216,230,0.2)"
    )

    tie_bar_x = machine_row["Tie Bar X (mm)"]
    tie_bar_y = machine_row["Tie Bar Y (mm)"]

    tie_bar_offset = tie_bar_y
    d = 15

    y0_value = (platen_height - tie_bar_y) / 2
    
    fig.add_shape(
        row=1,
        col=1, 
        type="line",  
        x0=0,
        y0=y0_value - d,        
        x1=platen_open,
        y1=y0_value - d,
        line=dict(color="black", width=d)
    )

    fig.add_shape(
        row=1,
        col=1,
        type="line",
        x0=0,
        y0=y0_value + tie_bar_offset + d,
        x1=platen_open,
        y1=y0_value + tie_bar_offset + d,
        line=dict(color="black", width=d)
    )

    mold_x0 = platen_open - mold_height      
    mold_y0 = (platen_height - mold_width) / 2
    mold_x1 = mold_x0 + mold_height    
    mold_y1 = mold_y0 + mold_width

    fig.add_shape(
        row=1,
        col=1,
        type="rect",
        x0=mold_x0,
        y0=mold_y0,
        x1=mold_x1,
        y1=mold_y1,
        line=dict(color="black", width=2),
        fillcolor="rgba(128,128,128,0.5)"
    )

    fig.add_annotation(
        x=platen_height / 2,
        y=platen_open + 40,
        text=f"Platen Daylight Max: {platen_open} mm",
        showarrow=False,
        font=dict(size=10, color="blue")
    )

    fig.add_annotation(
        x=platen_open + 60,
        y=platen_height / 2,
        text=f"Platen Width: {platen_height} mm",
        textangle=90,
        showarrow=False,
        font=dict(size=10, color="blue")
    )

    fig.add_annotation(
        x=mold_x0 - 40,
        y=(mold_y0 + mold_y1) / 2,
        text=f"Mold Width: {mold_width} mm",
        textangle=90,
        showarrow=False,
        font=dict(size=10)
    )

    fig.add_shape(
        type="rect",
        x0=0,
        y0=0,
        x1=platen_x,
        y1=platen_open,
        line=dict(color="blue", width=2),
        fillcolor="rgba(173,216,230,0.2)",
        row=1,
        col=2
    )

    fig.add_shape(
        type="rect",
        x0=(platen_x - mold_length) / 2,
        y0=0,
        x1=(platen_x + mold_length) / 2,
        y1=mold_height,
        line=dict(color="black", width=3),
        fillcolor="rgba(128,128,128,0.5)",
        row=1,
        col=2
    )

    fig.add_shape(
        type="line",
        x0=(platen_x - tie_bar_x) / 2 - d,
        y0=0,
        x1=(platen_x - tie_bar_x) / 2 - d,
        y1=platen_open,
        line=dict(color="black", width=d),
        row=1,
        col=2
    )

    fig.add_shape(
        type="line",
        x0=(platen_x + tie_bar_x) / 2 + d,
        y0=0,
        x1=(platen_x + tie_bar_x) / 2 + d,
        y1=platen_open,
        line=dict(color="black", width=d),
        row=1,
        col=2
    )      

    fig.update_layout(
        height=350,
        width=950,
        showlegend=False,
        margin=dict(l=10, r=10, t=40, b=10)
    )

    fig.update_xaxes(visible=False, range=[-50, platen_height + 120], row=1, col=1)
    fig.update_yaxes(visible=False, range=[-50, platen_open + 120], scaleanchor="x", scaleratio=1, row=1, col=1)
    fig.update_xaxes(visible=False, range=[-50, platen_height + 120], row=1, col=2)
    fig.update_yaxes(visible=False, range=[-50, platen_open + 120], scaleanchor="x", scaleratio=1, row=1, col=2)

    st.plotly_chart(fig, use_container_width=False, key="mold_platen_views")

else:
    st.warning("No valid machine found")

# -----------------------------------
# PDF EXPORT SETUP
# -----------------------------------
pdf_file = None
process_pdf_file = None

machine_data = {
    "oem": "N/A",
    "model": "N/A",
    "platen_x": "N/A",
    "platen_y": "N/A",
    "tie_bar_x": "N/A",
    "tie_bar_y": "N/A",
    "screw_size": "N/A",
    "machine_dimensions": "N/A",
    "mold_length": mold_length,
    "mold_width": mold_width,
    "mold_thickness": mold_height,
    "shot_utilization": "N/A"
}

if 'best' in locals() and best is not None:
    try:
        machine_data = {
            "oem": best.get("OEM", "Unknown OEM"),
            "model": best.get("Model", "Unknown Model"),
            "platen_x": best.get("Platen X (mm)", "N/A"),
            "platen_y": best.get("Platen Y (mm)") or "N/A",
            "tie_bar_x": best.get("Tie Bar X (mm)") or "N/A",
            "tie_bar_y": best.get("Tie Bar Y (mm)", "N/A"),
            "screw_size": best.get("Screw Size (mm)", "N/A"),
            "machine_dimensions": best.get("Machine Dimensions L X W X H (mm)", "N/A"),
            "mold_length": mold_length,
            "mold_width": mold_width,
            "mold_thickness": mold_height,
            "shot_utilization": best.get("Shot Utilization (%)", "N/A"),
            "machine_type": machine_type,
            "shot_2_unit_oem": best.get("2nd Unit OEM") if machine_type == "Two Shots" else None,
            "shot_2_unit_series": best.get("2nd Unit Series") if machine_type == "Two Shots" else None,
            "shot_2_unit_model": best.get("2nd Unit Model") if machine_type == "Two Shots" else None,
            "shot_2_capacity": best.get("2nd Shot Weight (g)") if machine_type == "Two Shots" else None,
            "shot_2_screw_size": best.get("2nd Screw Size (mm)") if machine_type == "Two Shots" else None,
            "shot_2_utilization": best.get("Shot 2 Utilization (%)") if machine_type == "Two Shots" else None,
            "shot_2_required_weight": shot_2_weight if machine_type == "Two Shots" else None,
            "shot_2_material": shot_2_material if machine_type == "Two Shots" else None
        }

        process_inputs = {
            "material": material_input,
            "cavity_num": cavity_num_input,
            "wall_thickness": wall_thickness_input,
            "gate_size": gate_size_input,
            "runner_type": runner_system,
            "cold_runner_weight": cold_runner_weight_input,
            "shot_weight": shot_weight,
            "machine_type": machine_type,
            "shot_2_material": shot_2_material,
            "shot_2_weight": shot_2_weight,
            "shot_2_unit_oem": best.get("2nd Unit OEM") if machine_type == "Two Shots" else None,
            "shot_2_unit_series": best.get("2nd Unit Series") if machine_type == "Two Shots" else None,
            "shot_2_unit_model": best.get("2nd Unit Model") if machine_type == "Two Shots" else None,
            "shot_2_capacity": best.get("2nd Shot Weight (g)") if machine_type == "Two Shots" else None,
            "shot_2_screw_size": best.get("2nd Screw Size (mm)") if machine_type == "Two Shots" else None,
            "shot_2_utilization": best.get("Shot 2 Utilization (%)") if machine_type == "Two Shots" else None
        }

        st.subheader("📄 Recommended Machine & Process Details")

        st.write(f"Machine: {machine_data['oem']} - {machine_data['model']}")
        st.write(
            f"Platen: {machine_data['platen_x']} × "
            f"{machine_data['platen_y']} mm"
        )
        st.write(
            f"Tie Bars: {machine_data['tie_bar_x']} × "
            f"{machine_data['tie_bar_y']} mm"
        )
        st.write(f"Screw Size: {machine_data['screw_size']} mm")

        shot_util = machine_data.get("shot_utilization", "N/A")

        if shot_util != "N/A":
            shot_text = str(shot_util).strip()

            if not shot_text.endswith("%"):
                try:
                    shot_text = f"{float(shot_util):g}%"
                except (TypeError, ValueError):
                    pass

            shot_util = shot_text

        st.write(f"Shot Utilization: {shot_util}")

        if machine_type == "Two Shots":
            st.markdown("#### 2nd Injection Unit")
            st.write(f"OEM: {best.get('2nd Unit OEM', 'N/A')}")
            st.write(f"Series: {best.get('2nd Unit Series', 'N/A')}")
            st.write(f"Model: {best.get('2nd Unit Model', 'N/A')}")
            st.write(f"Shot Capacity: {best.get('2nd Shot Weight (g)', 'N/A')} g")
            st.write(f"Screw Size: {best.get('2nd Screw Size (mm)', 'N/A')} mm")
            shot2_util = best.get("Shot 2 Utilization (%)", "N/A")
            if pd.notna(shot2_util) and shot2_util != "N/A":
                st.write(f"Shot Utilization: {round(float(shot2_util))}%")
            else:
                st.write("Shot Utilization: N/A")
            st.write(f"Required Shot 2: {shot_2_weight:.1f} g")
            st.write(f"Material: {shot_2_material}")





        pdf_file = generate_pdf(machine_data)
        process_pdf_file = generate_process_sheet_pdf(machine_data, process_inputs)
        
    except Exception as e:
        st.warning(f"PDF generation error: {e}")

col_pdf1, col_pdf2 = st.columns(2)

with col_pdf1:
    if pdf_file is not None:
        st.download_button(
            label="⬇️ Download RICO Mold Machine-Match Analysis",
            data=pdf_file,
            file_name="rico_mold_machine_match_analysis.pdf",
            mime="application/pdf"
        )
    else:
        st.info("Run analysis to enable Machine PDF export")

with col_pdf2:
    if process_pdf_file is not None:
        st.download_button(
            label="⬇️ Download Process Sheet PDF",
            data=process_pdf_file,
            file_name="process_sheet_prompt_report.pdf",
            mime="application/pdf"
        )
    else:
        st.info("Run analysis to enable Process Sheet PDF export.")

st.markdown("---")
st.caption(
    "Engineering screening tool only. Final machine approval "
    "requires machine OEM/application engineer and RICO Mold validation."
)
