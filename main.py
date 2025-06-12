import streamlit as st
import time
from fpdf import FPDF
from datetime import datetime
import base64
import os
from constants import INFO_SHEET, CONSENT_TEXT
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_consent_worksheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]

    # Small improvement: force nested dict to dict()
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)

    client = gspread.authorize(creds)
    sheet = client.open("Amusement Park Survey Responses").worksheet("Sheet2")
    return sheet

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

# ✅ Submit button
if st.button("Submit Consent"):
    if agreed and name.strip() and signature.strip():
        # ✅ Create unique ID using first and last letter
        clean_name = name.strip().replace(" ", "")
        if len(clean_name) >= 2:
            name_code = f"{clean_name[0]}{clean_name[-1]}"
        elif len(clean_name) == 1:
            name_code = f"{clean_name[0]}_"
        else:
            name_code = "NA"

        unique_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{name_code}"

        # ✅ Store in session state for later use
        st.session_state.unique_id = unique_id
        st.session_state.participant_name = name.strip()
        st.session_state.participant_signature = signature.strip()
        st.session_state.consent_submitted = True
        st.session_state.consent_agreed = agreed 

        # ✅ Write to Google Sheet (Sheet2)
        sheet = get_consent_worksheet()
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            unique_id,
            name.strip(),
            signature.strip(),
            "", "", ""  # placeholders for Tour Plan, Rating, Feedback
        ]
        sheet.append_row(row)

        st.success("✅ Consent submitted. Redirecting to your personalized tour plan...")
        
        st.switch_page("pages/1_questionnaire.py")

    else:
        st.warning("⚠️ Please agree to the terms and fill in both name and signature.")
