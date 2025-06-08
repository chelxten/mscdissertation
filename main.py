import streamlit as st
import time

st.set_page_config(page_title="Consent Form")

st.title("📝 Participant Consent Form")

st.markdown("""
Thank you for participating in this study. Please read the information sheet carefully and confirm your consent below.
""")

questions = [
    "I confirm I am 18 years or older.",
    "I understand my participation is voluntary.",
    "I understand the data will be anonymous and only used for academic purposes.",
    "I agree my responses can be used for this study.",
    "I understand I can stop at any time without giving a reason.",
]

responses = [st.radio(q, ["No", "Yes"], key=f"q{i}") for i, q in enumerate(questions)]

name = st.text_input("Full Name")
signature = st.text_input("Signature")

if st.button("Submit Consent"):
    if all(r == "Yes" for r in responses) and name.strip() and signature.strip():
        st.session_state.consent_submitted = True
        st.success("✅ Consent submitted. Redirecting...")
        time.sleep(1)
        st.switch_page("pages/1_questionnaire.py")
    else:
        st.error("⚠️ Please agree to all questions and fill in your name and signature.")
