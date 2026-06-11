import os
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

# -----------------------------------
# PDF REPORT
# -----------------------------------

def generate_pdf(machine_name):

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(100, 750, "Mold Match Analysis Report")
    pdf.setFont("Helvetica", 14)
    pdf.drawString(
        100,
        700,
        f"Recommended Machine: {machine_name}"
    )

    pdf.save()
    buffer.seek(0)
    return buffer

log_path = os.path.join(os.getcwd(), "view_log.txt")

# Log visit once per session
if "view_logged" not in st.session_state:

    st.session_state.view_logged = True

    with open(log_path, "a") as f:
        f.write(f"{datetime.now()} | user visited\n")

# Count visits
with open(log_path, "r") as f:
    visit_count = len(f.readlines())

# Show visits
st.metric("Total Visits", visit_count)

# ---------------------------
# TITLE
# ---------------------------
#st.markdown("# MoldMatch”)
st.markdown(
    "<h1 style='color:#003366; font-style:italic;'>MoldMatch</h1><br>",
    unsafe_allow_html=True
)

# ---------------------------
# LOAD DATA
# ---------------------------
@st.cache_data
def load_data():
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "machines_clean.xlsx")
    return pd.read_excel(file_path, engine="openpyxl")

df = load_data()

# ---------------------------
# OEM SELECTION
# ---------------------------

st.subheader("Select Machine Brand")
st.markdown("""
<style>
[data-baseweb="tag"] {
    background-color: #1f77ff !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

# Multi-select dropdown (add here)
selected_oems = st.multiselect(
    "OEM",  # still required
    options=sorted(df["OEM"].dropna().unique()),
    default=[],
    label_visibility="collapsed"
)

col1, col2, col3, col4 = st.columns(4)

selected_oem = None

with col1:
    st.image("https://static.wixstatic.com/media/22a5c3_8ccee611ed11458b92d28dda93a3df86~mv2.jpeg/v1/fill/w_600,h_400,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/ENGEL%20e-mac%20180.jpeg")
    st.write("")
    if st.button("ENGEL"):        
        selected_oem = "ENGEL"

with col2:
    st.image("https://static.wixstatic.com/media/22a5c3_8da520d483c5457f9abd0adb3a1ab9ee~mv2.png/v1/fill/w_399,h_266,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/arburg2_edited_edited.png")
    st.write("")
    if st.button("ARBURG"):
        selected_oem = "ARBURG"

with col3:
    st.image("https://static.wixstatic.com/media/22a5c3_fa5afcc9c002422ea8806b087440bd00~mv2.jpeg/v1/fill/w_399,h_266,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/netstal_text1.jpeg")
    st.write("")
    if st.button("NETSTAL"):
        selected_oem = "NETSTAL"

with col4:
    st.image("https://static.wixstatic.com/media/22a5c3_a59788aa07574182af46d04aa31e7b72~mv2.jpg/v1/fill/w_399,h_266,al_c,q_80,enc_avif,quality_auto/Sumitomo.jpg")
    st.markdown(
        "<div style='height:1px;'></div>",
        unsafe_allow_html=True
    )
    #st.write("")
    if st.button("SUMITOMO"):
        selected_oem = "SUMITOMO"

# ✅ Second row
col5, col6, col7, col8 = st.columns(4)

with col5:
    st.image("https://image.made-in-china.com/2f0j00KdelktaMAzpO/Haitian-Injection-Molding-Machine-for-PVC-PPR-Pipe-Fitting-Moulding-Used-Haitian-Injection-Machine.jpg")  # replace if needed
    st.write("")
    if st.button("HAITIAN"):
        selected_oem = "HAITIAN"

# Optional: leave others empty for spacing
with col6:
    st.empty()

with col7:
    st.empty()

with col8:
    st.empty()

if "selected_oem" not in st.session_state:
    st.session_state.selected_oem = None

if selected_oem:
    st.session_state.selected_oem = selected_oem
    
# ---------------------------
# FINAL OEM FILTER LOGIC
# ---------------------------
final_oem_list = []

# Priority: button selection OR multi-select
if st.session_state.selected_oem:
    final_oem_list = [st.session_state.selected_oem]
elif selected_oems:
    final_oem_list = selected_oems

# Apply filter
if final_oem_list:
    st.success(f"Selected OEM(s): {', '.join(final_oem_list)}")
    df = df[df["OEM"].isin(final_oem_list)]

# ---------------------------
# INPUTS
# ---------------------------

st.subheader("📦 Enter Mold Dimensions")

col1, col2, col3 = st.columns(3)

with col1:
    mold_length = st.number_input("Length (mm)", value=636)

with col2:
    mold_width = st.number_input("Width (mm)", value=396)

with col3:
    mold_height = st.number_input("Thickness (mm)", value=458)

# Clamp Requirement
st.subheader("🏗️ Clamp Requirement")

c1, c2 = st.columns(2)

with c1:
    clamp_min = st.number_input("Min Clamp (ton)", value=50)

with c2:
    clamp_max = st.number_input("Max Clamp (ton)", value=200)

# Shot Weight
st.subheader("⚖️ Shot Weight (g)")

c1, c2, c3 = st.columns([1, 1, 1])

with c1:
    shot_weight = st.number_input(
        "Shot Weight (g)",
        value=15,
        label_visibility="collapsed"
    )
   
# Opening calculation
safety_clearance = mold_height * 0.1 + 20
required_opening = mold_height + safety_clearance

st.info(f"Required Machine Opening: {required_opening:.1f} mm")

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
    #elif pd.notna(platen_y) and mold_width > platen_y:
    #    reasons.append("Too wide")

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

    #Return "PASS" if not reasons else "FAIL", ", ".join(set(reasons))

    # ---------------------------
    # Shot Weight Check
    # ---------------------------
    shot_capacity = machine.get("Shot Weight (g)")  # or "Shot Size"
    
    # Recommended: use 80% max utilization
    
    if pd.notna(shot_capacity):
        utilization = shot_weight / shot_capacity
        if utilization > 0.8:
            reasons.append("Insufficient shot capacity")
        elif utilization < 0.15:
            reasons.append("Shot too small")
    else:
        reasons.append("No shot data")
    return "PASS" if not reasons else "FAIL", ", ".join(set(reasons))

# ---------------------------
# RUN BUTTON
# ---------------------------

valid = pd.DataFrame()
st.markdown(
    "<span style='font-size:24px; font-weight:bold;'>Run Compatibility Check</span>",
    unsafe_allow_html=True
)

st.markdown("""
<style>
div.stButton > button {
    background-color: #007BFF;  /* Blue */
    color: white;               /* Text color */
    font-weight: bold;
    border-radius: 8px;
    height: 50px;
    width: 150px;
}
div.stButton > button:hover {
    background-color: #0056b3;  /* Darker blue on hover */
}
</style>
""", unsafe_allow_html=True)

#st.header("Run Compatibility Check")

if st.button("Click to Run"):

    st.write("Running...")

    results = []

    for _, m in df.iterrows():
        status, reason = check(m)

        shot_capacity = m.get("Shot Weight (g)")

        if pd.notna(shot_capacity) and shot_capacity > 0:
            utilization = int((shot_weight / shot_capacity) * 100)        
        else:
            utilization = None

        results.append({
            "OEM": m["OEM"],
            "Model": m["Model"],
            "Clamp (ton)": m["Clamp Force (ton)"],
            "Platen X (mm)": m["Platen X (mm)"], 
            "Tie Bar Y (mm)": m["Tie Bar Y (mm)"],
            "Daylight Max (mm)": m["Daylight Max (mm)"], # shown
            "Shot Weight (g)": m["Shot Weight (g)"],
            "Screw Size (mm)": m["Screw Size (mm)"],
            "Status": status,   
            "Shot Utilization (%)": utilization if utilization else None,            
            "Fail Reason": reason
    })
    results_df = pd.DataFrame(results)

# ---------------------------
# DISCLAIMER
# ---------------------------

    st.warning(
        "Engineering screening tool only. "
        "Final machine approval requires OEM/application engineer validation."
    )

# ---------------------------
# SHOW PASSED
# ---------------------------

    st.subheader("✅ Passed Machines")

    passed_df = results_df[results_df["Status"] == "PASS"]
    st.dataframe(passed_df)

    # ---------------------------
    # SHOW FAILED
    # ---------------------------
    st.subheader("❌ Failed Machines")
    failed_df = results_df[results_df["Status"] == "FAIL"]
    st.dataframe(failed_df)    
       
    # ===========================
    # BEST MACHINE LOGIC — closest to 50% shot utilization
    # ===========================

    valid = passed_df.copy()

    if len(valid) > 0:
    # Compute deviation from ideal 50% utilization
        valid["Utilization Deviation"] = (valid["Shot Utilization (%)"] - 50).abs()

    # Pick machine with smallest deviation
        best = valid.sort_values("Utilization Deviation").iloc[0]

        st.success(
            f"✅ Recommended Machine :\n\n" #(Closest to 50% Shot Utilization)
            f"{best['OEM']} - {best['Model']} "
            f"({best['Clamp (ton)']} ton)"            
        )
    else:
        st.error("❌ No compatible machines found")

    # ===========================
    # 📊 RESULTS ANALYSIS
    # ===========================
    st.header("📊 Results Analysis")
    # ===========================
    # 📐 Mold Fit Analysis (guaranteed color)
    # ===========================
    if len(valid) > 0:

        machine_row = df[df["Model"] == best["Model"]].iloc[0]

        platen_x = machine_row["Platen X (mm)"]
        platen_y = machine_row["Platen Y (mm)"]
        daylight_max = machine_row["Daylight Max (mm)"]

        mold_area = mold_length * mold_width
        platen_area = platen_x * platen_y
        area_ratio = (mold_area / platen_area) * 100

    # Safety color logic        
        if 10 <= area_ratio <= 20:
            ratio_color = "🟡 WARNING"        
        elif area_ratio < 70:
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

    # Color badge ALWAYS visible
        cA.markdown(f"### {ratio_color}")
        cA.metric("Projected Area Ratio", f"{area_ratio:.1f}%")

        cB.markdown(f"### {gap_color}")
        cB.metric("Opening Gap", f"{opening_gap:.1f} mm")
        # Shot Weight Analysis

# ✅ Only run if a valid machine exists
if len(valid) > 0:

    st.subheader("⚖️ Shot Weight Analysis")

    # ✅ Use best machine directly (NO machine_row needed)
    machine_shot = best["Shot Weight (g)"]

    # User input
    actual_shot = shot_weight

    # Calculate utilization
    if machine_shot > 0:
        shot_ratio = actual_shot / machine_shot
    else:
        shot_ratio = 0

    # Status logic
    if 0.2 <= shot_ratio <= 0.8:
        shot_color = "🟢 GOOD"
    elif 0.1 <= shot_ratio < 0.2 or 0.8 < shot_ratio <= 0.9:
        shot_color = "🟡 MARGINAL"
    else:
        shot_color = "🔴 OUT OF RANGE"

    # Display
    cA, cB = st.columns(2)

    with cA:
        st.metric("Shot Utilization (%)", f"{shot_ratio*100:.1f}%")

    with cB:
        st.metric("Status", shot_color)

else:
    st.warning("No valid machine → Shot analysis skipped")

# ==========================
# 🖼️ PLATEN + MOLD FRONT VIEW
# ==========================

st.subheader("🖼️ Mold vs Platen Operator View")

# Use best machine platen dimensions

if 'valid' in locals() and len(valid) > 0:
    platen_open = daylight_max
    platen_height = platen_y

    #fig = go.Figure()
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "Front View",
            "Top View"
        )
    )

    # -------------------------
    # PLATEN RECTANGLE
    # -------------------------
    #fig.add_shape(
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
# -----------------------------------
# OPERATOR SIDE TIE BARS
# -----------------------------------

    tie_bar_x = machine_row["Tie Bar X (mm)"]
    tie_bar_y = machine_row["Tie Bar Y (mm)"]

    half_x = tie_bar_x / 2
    half_y = tie_bar_y / 2

# offset OUTSIDE platen
    tie_bar_offset = tie_bar_y
    d = 15

# BOTTOM tie bar
    
    y0_value = (platen_width - tie_bar_y) / 2 - d
    st.write("platen_width =", platen_width)
    st.write("mold_y0 =", y0_value)
    
    fig.add_shape(
        row=1,
        col=1, 
        type="line",  
        x0=0,
        y0=(platen_width - tie_bar_y) / 2 - d,
        x1=platen_height,
        y1=(platen_width - tie_bar_y) / 2 - d,
        line=dict(
            color="black",
            width=d
        )
    )

# TOP tie bar
    #fig.add_shape(
    fig.add_shape(
        row=1,
        col=1,
        type="line",
        x0=0,
        y0=(platen_width - tie_bar_y) / 2 + tie_bar_offset + d,
        x1=platen_height,
        y1=(platen_width - tie_bar_y) / 2 + tie_bar_offset + d,
        line=dict(
            color="black",
            width=d
        )
    )

    # -------------------------
    # CENTER MOLD INSIDE PLATEN
    # Rotated 90°
    # -------------------------

    mold_x0 = (platen_height - mold_height) / 2
    mold_y0 = (platen_width - mold_width) / 2

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

    # -------------------------
    # LABELS
    # -------------------------

    fig.add_annotation(
        x=platen_height / 2,
        y=platen_width + 40,
        text=f"Platen Daylight Max: {platen_width} mm",
        showarrow=False,
        font=dict(size=10, color="blue")
    )

    fig.add_annotation(
        x=platen_height + 60,
        y=platen_width / 2,
        text=f"Platen Width: {platen_height} mm",
        textangle=90,
        showarrow=False,
        font=dict(size=10, color="blue")
    )

    fig.add_annotation(
        x=(mold_x0 + mold_x1) / 2,
        y=mold_y1 + 20,
        text=f"Mold Thickness: {mold_height} mm",
        showarrow=False,
        font=dict(size=10)
    )

    fig.add_annotation(
        x=mold_x1 + 20,
        y=(mold_y0 + mold_y1) / 2,
        text=f"Mold Width: {mold_width} mm",
        textangle=90,
        showarrow=False,
        font=dict(size=10)
    )

    # -----------------------------------
    # TOP VIEW
    # -----------------------------------
    
    # platen top view
    fig.add_shape(
        type="rect",
        x0=0,
        y0=0,
        x1=platen_y,
        y1=platen_x,
        line=dict(color="blue", width=3),
        fillcolor="lightblue",
        row=1,
        col=2
    )
    
    # mold top view
    fig.add_shape(
        type="rect",
        x0=(platen_height - mold_height) / 2,
        y0=(platen_width - mold_width) / 2,
        x1=(platen_height + mold_height) / 2,
        y1=(platen_width + mold_width) / 2,
        line=dict(color="green", width=3),
        fillcolor="lightgreen",
        row=1,
        col=2
    )

    # -------------------------
    # LAYOUT
    # -------------------------

    # -----------------------------------
    # LAYOUT
    # -----------------------------------
    
    fig.update_layout(
        height=350,
        width=950,
        showlegend=False,
        margin=dict(
            l=10,
            r=10,
            t=40,
            b=10
        )
    )
    
    # -----------------------------------
    # FRONT VIEW AXES
    # -----------------------------------
    
    fig.update_xaxes(
        visible=False,
        range=[-50, platen_height + 120],
        row=1,
        col=1
    )
    
    fig.update_yaxes(
        visible=False,
        range=[-50, platen_width + 120],
        scaleanchor="x",
        scaleratio=1,
        row=1,
        col=1
    )
    
    # -----------------------------------
    # TOP VIEW AXES
    # -----------------------------------
    
    fig.update_xaxes(
        visible=False,
        range=[-50, platen_height + 120],
        row=1,
        col=2
    )
    
    fig.update_yaxes(
        visible=False,
        range=[-50, platen_width + 120],
        scaleanchor="x",
        scaleratio=1,
        row=1,
        col=2
    )
    
    # -----------------------------------
    # SHOW FIGURE
    # -----------------------------------
    
    st.plotly_chart(
        fig,
        use_container_width=False,
        key="mold_platen_views"
    )
    
    #st.plotly_chart(fig, use_container_width=False)

else:
    st.warning("No valid machine found")

# -----------------------------------
# PDF EXPORT
# -----------------------------------

machine_text = "No Recommended Machine"

try:

    machine_text = f"{best['OEM']} - {best['Model']}"

except:

    pass

pdf_file = generate_pdf(machine_text)

st.download_button(
    label="Download PDF Report",
    data=pdf_file,
    file_name="moldmatch_report.pdf",
    mime="application/pdf"
)

st.markdown("---")

st.caption(
    "Engineering screening tool only. Final machine approval "
    "requires OEM/application engineer validation."
)

    
