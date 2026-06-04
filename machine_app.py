import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import time

# ---------------------------
# TITLE
# ---------------------------
#st.markdown("# MoldMatch”)
st.markdown(
    "<h1 style='color:#003366; font-style:italic;'>MoldMatch</h1>",
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
#st.write(df.columns.tolist())
#st.write("COLUMNS:", df.columns.tolist())
# ---------------------------
# OEM SELECTION
# ---------------------------
#st.header("Select Machine Brand")
st.subheader("Select Machine Brand")

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
#st.subheader("Shot Weight")
#shot_weight = st.number_input("Shot Weight (g)", value=5)

# Shot Weight
st.subheader("⚖️ Shot Weight (g)")

c1, c2, c3 = st.columns([1, 1, 1])

with c1:
    shot_weight = st.number_input(
        "Shot Weight (g)",
        value=5,
        label_visibility="collapsed"
    )
    #shot_weight = st.number_input("", value=5)

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
#if st.button("Run Compatibility Check"):
#st.markdown("**Run Compatibility Check**")

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

#if st.button("Run Compatibility Check"):
    st.write("Running...")

    results = []

    for _, m in df.iterrows():
        status, reason = check(m)
        results.append({
            "OEM": m["OEM"],
            "Model": m["Model"],
            "Clamp (ton)": m["Clamp Force (ton)"],
            "Platen X (mm)": m["Platen X (mm)"], 
            "Platen Y (mm)": m["Platen Y (mm)"], 
            "Tie Bar Y (mm)": m["Tie Bar Y (mm)"],
            "Daylight Max (mm)": m["Daylight Max (mm)"], # shown
            "Shot Weight (g)": m["Shot Weight (g)"],
             "Screw Size (mm)": m["Screw Size (mm)"],
            "Status": status   
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
        #if area_ratio < 40:
        if 20 <= area_ratio <= 40:
            ratio_color = "🟡 WARNING"        
        elif area_ratio < 65:
            ratio_color = "🟢 SAFE"
        elif area_ratio < 80:
            ratio_color = "🟡 WARNING"
        else:
            ratio_color = "🔴 RISK"

        opening_gap = daylight_max - mold_height

        if opening_gap >= 0:
            gap_color = "🟢 SAFE"
        elif opening_gap > -20:
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
# Shot Weight Analysis
    st.subheader("⚖️ Shot Weight Analysis")

# Machine data (from your dataset)
    machine_shot = machine_row["Shot Weight (g)"]

# User input
    actual_shot = shot_weight
#st.number_input("Actual Shot Weight (g)", value=50)

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

st.header("🧊 3D Machine + Mold Visualization")

if len(valid) > 0:

    machine_row = df[df["Model"] == best["Model"]].iloc[0]

    platen_x = machine_row["Platen X (mm)"]
    platen_y = machine_row["Platen Y (mm)"]
    daylight_max = machine_row["Daylight Max (mm)"]

    # Mold centered on platen
    mold_x0 = (platen_x - mold_length) / 2
    mold_x1 = mold_x0 + mold_length

    mold_y0 = (platen_y - mold_width) / 2
    mold_y1 = mold_y0 + mold_width

    # Mold positioned between platens
    mold_z0 = (daylight_max - mold_height) / 2
    mold_z1 = mold_z0 + mold_height

    fig = go.Figure()

    # --- Fixed Platen (bottom) ---
    fig.add_trace(go.Mesh3d(
        x=[0, platen_x, platen_x, 0, 0, platen_x, platen_x, 0],
        y=[0, 0, platen_y, platen_y, 0, 0, platen_y, platen_y],
        z=[0, 0, 0, 0, -40, -40, -40, -40],
        opacity=0.35,
        color='gray',
        name="Fixed Platen"
    ))

    # --- Movable Platen (top) ---
    fig.add_trace(go.Mesh3d(
        x=[0, platen_x, platen_x, 0, 0, platen_x, platen_x, 0],
        y=[0, 0, platen_y, platen_y, 0, 0, platen_y, platen_y],
        z=[daylight_max, daylight_max, daylight_max, daylight_max,
           daylight_max + 40, daylight_max + 40, daylight_max + 40, daylight_max + 40],
        opacity=0.35,
        color='darkgray',
        name="Movable Platen"
    ))

    # --- Mold Block ---
    fig.add_trace(go.Mesh3d(
        x=[mold_x0, mold_x1, mold_x1, mold_x0, mold_x0, mold_x1, mold_x1, mold_x0],
        y=[mold_y0, mold_y0, mold_y1, mold_y1, mold_y0, mold_y0, mold_y1, mold_y1],
        z=[mold_z0, mold_z0, mold_z0, mold_z0,
           mold_z1, mold_z1, mold_z1, mold_z1],
        opacity=0.7,
        color='steelblue',
        name="Mold"
    ))

    fig.update_layout(
        scene=dict(
            xaxis_title="X (mm)",
            yaxis_title="Y (mm)",
            zaxis_title="Z (mm)",
            aspectmode="data"
        ),
        width=800,
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Run compatibility check to visualize machine + mold.")
