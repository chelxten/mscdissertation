import streamlit as st
import time
from fpdf import FPDF
from datetime import datetime
import base64
import os
from constants import INFO_SHEET, CONSENT_TEXT

st.set_page_config(page_title="Consent Form")

st.image("Sheffield-Hallam-University.png", width=250)


st.title("📝 Participant Consent Form")


with st.expander("📄 Participant Information Sheet", expanded=True):
    st.markdown(INFO_SHEET)

st.header("Consent Confirmation")

with st.expander("🔍 Please confirm the following statements before continuing:", expanded=True):
    st.markdown(CONSENT_TEXT)

agreed = st.checkbox("I have read and agree to all the above statements.")
name = st.text_input("Full Name")
signature = st.text_input("Signature")

if st.button("Submit Consent"):
    if agreed and name.strip() and signature.strip():
        st.session_state.consent_submitted = True
        st.session_state.participant_name = name.strip()
        st.session_state.participant_signature = signature.strip()
        st.success("✅ Consent submitted. Redirecting to your personalized tour plan...")
        st.switch_page("pages/1_questionnaire.py")
