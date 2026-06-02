import os
import pandas as pd
import streamlit as st


import time


# ---------------------------
# TITLE
# ---------------------------
# st.markdown("# MoldMatch - Machine Selection")
st.markdown(
    "# <span style='color:darkblue; font-style:italic;'>MoldMatch</span> - Machine Selection",
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
st.header("Select Machine Brand")

col1, col2, col3, col4 = st.columns(4)

selected_oem = None

with col1:
    st.image("https://static.wixstatic.com/media/22a5c3_8ccee611ed11458b92d28dda93a3df86~mv2.jpeg/v1/fill/w_600,h_400,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/ENGEL%20e-mac%20180.jpeg")
    if st.button("ENGEL"):
        selected_oem = "ENGEL"

with col2:
    st.image("https://static.wixstatic.com/media/22a5c3_a5d69d06e7fe43a8a1bdccbfdff0c5f4~mv2.webp/v1/fill/w_525,h_266,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/arburg2.webp")
    if st.button("ARBURG"):
        selected_oem = "ARBURG"

with col3:
    st.image("https://static.wixstatic.com/media/22a5c3_fa5afcc9c002422ea8806b087440bd00~mv2.jpeg/v1/fill/w_399,h_266,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/netstal_text1.jpeg")
    if st.button("NETSTAL"):
        selected_oem = "NETSTAL"

with col4:
    st.image("https://static.wixstatic.com/media/22a5c3_7bf8a568d3b84008ba793e09c1a1b409~mv2.jpeg/v1/fill/w_376,h_266,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/22a5c3_7bf8a568d3b84008ba793e09c1a1b409~mv2.jpeg")
    if st.button("SUMITOMO"):
        selected_oem = "SUMITOMO"

# Session state
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


# ---------------------------
# OPTIONAL CLAMP INPUT
# ---------------------------
st.subheader("Clamp Requirement")

# use_clamp = st.checkbox("Apply Clamp Requirement", value=True)

# if use_clamp:
#    clamp_required = st.number_input("Required Clamp Force (ton)", value=80)
# else:
#    clamp_required = None

st.subheader("Clamp Requirement")

clamp_min = st.number_input("Min Clamp (ton)", value=50)
clamp_max = st.number_input("Max Clamp (ton)", value=200)


# Clamp input
# clamp_required = st.number_input("Required Clamp Force (ton)", value=80)

# Opening calculation
safety_clearance = mold_height * 0.1 + 20
required_opening = mold_height + safety_clearance

st.info(f"Required Machine Opening: {required_opening:.1f} mm")
#st.info(f"mold_length: {mold_length:.1f} mm")
#st.info(f"mold_height: {mold_height:.1f} mm")

# ---------------------------
# CHECK FUNCTION (FIXED)
# ---------------------------
def check(machine):
    reasons = []
   
    # Length check
    tie_x = machine.get("Tie Bar X (mm)")
    #410
    platen_x = machine.get("Platen X (mm)")
    #650
    #st.info(f"platen_x: {platen_x:.1f} mm")

    if pd.notna(platen_x):
        if mold_length > platen_x:
            reasons.append("Too long")
    elif pd.notna(platen_x):
        if mold_length > platen_x:
            reasons.append("Too long")

    # Width check
    tie_y = machine.get("Tie Bar Y (mm)")
    #410
    platen_y = machine.get("Platen Y (mm)")
    #621

    if pd.notna(tie_y):
        if mold_width > tie_y:
            reasons.append("Too wide")
    elif pd.notna(platen_y):
        if mold_width > platen_y:
            reasons.append("Too wide")

    # Thickness (mold height)
    mold_min = machine.get("Mold Min (mm)", 0)
    mold_max = machine.get("Mold Max (mm)", 9999)
    daylight_max = machine.get("Daylight Max (mm)", 9999)

    if pd.notna(mold_min) and mold_height < mold_min:
        reasons.append("Too thin")

    # if pd.notna(mold_max) and mold_height > mold_max:
    if pd.notna(daylight_max) and required_opening > daylight_max:
        reasons.append("Too thick")


# ✅ Optional clamp check
    #if clamp_required is not None:
    #    if machine.get("Clamp Force (ton)", 0) < clamp_required:
    #        reasons.append("Insufficient clamp")
    
    clamp_force = machine.get("Clamp Force (ton)", 0)
    if not (clamp_min <= clamp_force <= clamp_max):
        reasons.append("Clamp force out of range")

    # Clamp check
    #if machine.get("Clamp Force (ton)", 0) < clamp_required:
    #    reasons.append("Insufficient clamp")

    # Daylight check
    daylight = machine.get("Daylight Max (mm)", 0)
    if pd.notna(daylight) and required_opening > daylight:
        reasons.append("Insufficient daylight")

    return "PASS" if not reasons else "FAIL", ", ".join(reasons)


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

    st.subheader("Results")
    st.dataframe(results_df)

    # ---------------------------
    # BEST MACHINE LOGIC
    # ---------------------------
    valid = results_df[results_df["Status"] == "PASS"]

    if len(valid) > 0:
        best = valid.sort_values("Clamp (ton)").iloc[0]

        st.success(
            f"✅ Recommended Machine:\n\n"
            f"{best['OEM']} - {best['Model']} ({best['Clamp (ton)']} ton)"
        )
    else:
        st.error("❌ No compatible machines found")


