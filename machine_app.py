
import os
import pandas as pd
import streamlit as st

# st.title("Machine Selection Tool")
st.markdown(
    "# <span style='color:darkblue; font-style:italic;'>MoldMatch</span> - Machine Selection",
    unsafe_allow_html=True
)


# ---------------------------
# MACHINE SELECTION (TOP UI)
# ---------------------------
st.header("Select Machine Brand")

col1, col2, col3, col4 = st.columns(4)

selected_oem = None

with col1:
    st.image("https://s3-prod.plasticsnews.com/styles/width_792/s3/ENGEL%20e-mac%20180.jpg")
    if st.button("ENGEL"):
        selected_oem = "ENGEL"

with col2:
    # st.image("https://www.arburg.com/media/_processed_/b/f/csm_186074-ALLROUNDER-470H-PREMIUM_fc43cccff1.jpg")
    st.image("https://insights.globalspec.com/images/assets/776/24776/Allrounder_1000.jpg")
    if st.button("ARBURG"):
        selected_oem = "ARBURG"

with col3:
    st.image("https://www.plasticportal.eu/image/staticke/Image/2022_foto/2022_september/netstal_text1.jpg")
    if st.button("NETSTAL"):
        selected_oem = "NETSTAL"

with col4:
    st.image("https://www.tkpm.eu/wp-content/uploads/2015/11/The-New-IntElect-5-2017.jpg")
    if st.button("SUMITOMO"):
        selected_oem = "SUMITOMO"





# Store selection
if "selected_oem" not in st.session_state:
    st.session_state.selected_oem = None

if selected_oem:
    st.session_state.selected_oem = selected_oem

if st.session_state.selected_oem:
    st.success(f"Selected OEM: {st.session_state.selected_oem}")

# ---------------------------
# INPUTS (MIDDLE)
# ---------------------------
st.header("Enter Mold Dimensions")

col1, col2, col3 = st.columns(3)

with col1:
    mold_length = st.number_input("Length (mm)", value=300)

with col2:
    mold_width = st.number_input("Width (mm)", value=300)

with col3:
    mold_height = st.number_input("Height / Thickness (mm)", value=400)

# Opening calculation
safety_clearance = mold_height * 0.1 + 20
required_opening = mold_height + safety_clearance

st.info(f"Required Machine Opening: {required_opening} mm")







# Load data

@st.cache_data
def load_data():
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "machines_cleaned.xlsx")
    return pd.read_excel(file_path, engine="openpyxl")

df = load_data()

st.sidebar.header("Mold Requirements")
width = st.sidebar.number_input("Mold Width (mm)", value=500)
height = st.sidebar.number_input("Mold Height (mm)", value=500)
thickness = st.sidebar.number_input("Mold Thickness (mm)", value=300)
clamp = st.sidebar.number_input("Required Clamp Force (ton)", value=100)

# Filtering logic
results = df[
    (df["Platen X (mm)"] >= width) &
    (df["Platen Y (mm)"] >= height) &
    (df["Mold Min (mm)"].fillna(0) <= thickness) &
    (df["Mold Max (mm)"].fillna(9999) >= thickness) &
    (df["Clamp Force (ton)"] >= clamp)
]

st.subheader("Compatible Machines")

if results.empty:
    st.warning("No machines found.")
else:
    st.dataframe(results[[
        "OEM","Series","Model","Clamp Force (ton)",
        "Platen X (mm)","Platen Y (mm)","Mold Max (mm)"
    ]])






df = pd.DataFrame(machines)

# ✅ OPTIONAL: filter by selected OEM
if st.session_state.selected_oem:
    df = df[df["OEM"] == st.session_state.selected_oem]

# ---------------------------
# CHECK FUNCTION
# ---------------------------
def check(machine):
    reasons = []

    # Width
    if machine["TieBar_X"] is not None:
        if mold_width > machine["TieBar_X"]:
            reasons.append("Too wide")
    else:
        if mold_width > machine["Platen_X"]:
            reasons.append("Too wide")

    # Length
    if machine["TieBar_Y"] is not None:
        if mold_length > machine["TieBar_Y"]:
            reasons.append("Too long")
    else:
        if mold_length > machine["Platen_Y"]:
            reasons.append("Too long")

    # Height / opening
    if required_opening > machine["Daylight"]:
        reasons.append("Insufficient daylight")

    return "PASS" if not reasons else "FAIL", ", ".join(reasons)

# ---------------------------
# RUN BUTTON (BOTTOM)
# ---------------------------
if st.button("Run Compatibility Check"):

    results = []

    for _, m in df.iterrows():
        status, reason = check(m)

        results.append({
            "OEM": m["OEM"],
            "Model": m["Model"],
            "Clamp (ton)": m["Clamp"],
            "Status": status,
            "Reason": reason
        })

    results_df = pd.DataFrame(results)

    st.subheader("Results")
    st.dataframe(results_df)

    # ---------------------------
    # BEST MACHINE
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

