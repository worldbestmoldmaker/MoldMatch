import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import time

# ---------------------------
# TITLE
# ---------------------------
st.markdown("# MoldMatch - Machine Selection + Copilot Analysis")

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
st.header("Select Machine Brand")

col1, col2, col3, col4 = st.columns(4)

selected_oem = None

with col1:
    st.image("https://static.wixstatic.com/media/22a5c3_8ccee611ed11458b92d28dda93a3df86~mv2.jpeg/v1/fill/w_600,h_400,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/ENGEL%20e-mac%20180.jpeg")
    if st.button("ENGEL"):
        selected_oem = "ENGEL"

with col2:
    if st.button("ARBURG"):
        selected_oem = "ARBURG"

with col3:
    if st.button("NETSTAL"):
        selected_oem = "NETSTAL"

with col4:
    if st.button("SUMITOMO"):
        selected_oem = "SUMITOMO"

if "selected_oem" not in st.session_state:
    st.session_state.selected_oem = None

if selected_oem:
    st.session_state.selected_oem = selected_oem

if st.session_state.selected_oem:
    st.success(f"Selected OEM: {st.session_state.selected_oem}")
    df = df[df["OEM"] == st.session_state.selected_oem]

# ---------------------------
# INPUTS
# ---------------------------
st.header("Enter Mold Dimensions")

col1, col2, col3 = st.columns(3)

with col1:
    mold_length = st.number_input("Length (mm)", value=636)

with col2:
    mold_width = st.number_input("Width (mm)", value=396)

with col3:
    mold_height = st.number_input("Thickness (mm)", value=458)

# Clamp
st.subheader("Clamp Requirement")
clamp_min = st.number_input("Min Clamp (ton)", value=50)
clamp_max = st.number_input("Max Clamp (ton)", value=200)

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
    elif pd.notna(platen_y) and mold_width > platen_y:
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

    return "PASS" if not reasons else "FAIL", ", ".join(set(reasons))

# ---------------------------
# RUN BUTTON
# ---------------------------
if st.button("Run Compatibility Check"):

    results = []

    for _, m in df.iterrows():
        status, reason = check(m)
        results.append({
            "OEM": m["OEM"],
            "Model": m["Model"],
            "Clamp (ton)": m["Clamp Force (ton)"],
            "Status": status,
            "Reason": reason
        })

    results_df = pd.DataFrame(results)

    # ---------------------------
    # SHOW PASSED
    # ---------------------------
    st.subheader("✅ Passed Machines")
    passed_df = results_df[results_df["Status"] == "PASS"]
    st.dataframe(passed_df)

    # ---------------------------
    # BEST MACHINE
    # ---------------------------
    valid = passed_df
    if len(valid) > 0:
        best = valid.sort_values("Clamp (ton)").iloc[0]

        st.success(
            f"✅ Recommended Machine:\n\n"
            f"{best['OEM']} - {best['Model']} ({best['Clamp (ton)']} ton)"
        )
    else:
        st.error("❌ No compatible machines found")

    # ===========================
    # 📊 RESULTS ANALYSIS
    # ===========================
    st.header("📊 Results Analysis")

    total = len(results_df)
    passed = len(passed_df)
    failed = total - passed

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Machines", total)
    c2.metric("Passed", passed)
    c3.metric("Failed", failed)

    # Failure reasons
    st.subheader("Failure Breakdown")

