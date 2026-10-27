import streamlit as st
from pypdf import PdfReader

st.set_page_config(
    page_title="Mold Quality Analyzer",
    page_icon="🛠️"
)

st.title("Mold Quality Analyzer")

st.success("App loaded successfully.")

st.write("pypdf loaded successfully.")