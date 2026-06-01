
import os
import pandas as pd
import streamlit as st

# st.title("Machine Selection Tool")
st.markdown(
    "# <span style='color:darkblue; font-style:italic;'>MoldMatch</span> - Machine Selection",
    unsafe_allow_html=True
)




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

