import streamlit as st
import time
from fpdf import FPDF
from datetime import datetime
import base64
import os
from constants import INFO_SHEET, CONSENT_TEXT
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("YOUR_CREDENTIALS_FILE.json", scope)
client = gspread.authorize(credentials)
sheet = client.open("Amusement Park Survey Responses").worksheet("Consent & Feedback")

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
        # Store in session state
        st.session_state.consent_submitted = True
        st.session_state.participant_name = name.strip()
        st.session_state.participant_signature = signature.strip()

        # ✅ Save to Google Sheet
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, name.strip(), signature.strip(), "", "", ""])  # Tour, rating, feedback to be filled later

        st.success("✅ Consent submitted. Redirecting to your personalized tour plan...")
        st.switch_page("pages/1_questionnaire.py")
    else:
        st.warning("⚠️ Please agree to the terms and fill in both name and signature.")
