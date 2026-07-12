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

def generate_pdf(machine_data):

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    # Title
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(100, 750, "Mold Match Analysis Report")

    pdf.setFont("Helvetica", 12)

    pdf.drawString(
        100, 700,
        f"Machine: {machine_data['oem']} - {machine_data['model']}"
    )

    pdf.drawString(
        100, 670,
        f"Platen: {machine_data['platen_x']} × {machine_data['platen_y']} mm"
    )

    pdf.drawString(
        100, 650,
        f"Tie Bars: {machine_data['tie_bar_x']} × {machine_data['tie_bar_y']} mm"
    )

    shot = machine_data["shot_utilization"]
    if isinstance(shot, (int, float)):
        shot = f"{shot:.1f}%"

    pdf.drawString(
        100, 630,
        f"Shot Utilization: {shot}"
    )

    pdf.save()
    buffer.seek(0)

    return buffer

# -----------------------------------
# VISITOR LOG (continuous)
# -----------------------------------

log_path = os.path.join(os.getcwd(), "view_log.txt")

# Log EVERY visit (continuous total)
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

st.markdown(
    "<h1 style='color:#003366; font-style:italic;'>MoldMatch</h1><br>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style='text-align:center;'>
        <h2>Please send comments to:</h2>        
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="text-align:center; font-size:18px; padding:10px;">
        Please let us know if you like to add a machine in our database.<br><br>
        📧 <a href="mailto:info@moldmatchapp.com">
        info@moldmatchapp.com
        </a>
    </div>
    """,
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

selected_oems = st.multiselect(
    "OEM",
    options=sorted(df["OEM"].dropna().unique()),
    default=[],
    label_visibility="collapsed"
)

col1, col2, col3, col4 = st.columns(4)

selected_oem = None

with col1:
    st.image("https://static.wixstatic.com/media/22a5c3_8ccee611ed11458b92d28dda93a3df86~mv2.jpeg")
    st.write("")
    if st.button("ENGEL"):        
        selected_oem = "ENGEL"

with col2:
    st.image("https://static.wixstatic.com/media/22a5c3_8da520d483c545