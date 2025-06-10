import streamlit as st
import time
from fpdf import FPDF
from datetime import datetime
import base64
import os
from constants import info_sheet, consent_text

st.set_page_config(page_title="Consent Form")

st.image("Sheffield-Hallam-University.png", width=250)


st.title("📝 Participant Consent Form")



with st.expander("📄 Participant Information Sheet", expanded=True):
    st.markdown(info_sheet)

st.header("Consent Confirmation")

with st.expander("🔍 Please confirm the following statements before continuing:", expanded=True):
    st.markdown("""
1.	I have read the Information Sheet for this study and have had details of the study explained to me.
2.	My questions about the study have been answered to my satisfaction and I understand that I may ask further questions at any point. 
3.	I understand that I am free to withdraw from the study within the time limits outlined in the Information Sheet, without giving a reason for my withdrawal or to decline to answer any particular questions in the study without any consequences to my future treatment by the researcher.          
4.	I agree to provide information to the researchers under the conditions of confidentiality set out in the Information Sheet.
5.	I wish to participate in the study under the conditions set out in the Information Sheet.
6.	I consent to the information collected for the purposes of this research study, once anonymised (so that I cannot be identified), to be used for any other research purposes.
    """)

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
