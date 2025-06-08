# 1. Home.py (Consent Page)
import streamlit as st

st.set_page_config(page_title="Consent Form", page_icon="📝")
st.title("📝 Participant Consent Form")

with st.expander("📄 Participant Information Sheet"):
    st.markdown("""
    ### PARTICIPANT INFORMATION SHEET
    Title: _The Search of Advanced AI-Powered Service Robots for Amusement Parks_
    ...
    Researcher: **Cherry San** – c3065323@hallam.shu.ac.uk  
    Supervisor: **Dr. Samuele Vinanzi** – s.vinanzi@shu.ac.uk
    """, unsafe_allow_html=True)

consent = st.checkbox("I have read the information sheet and agree to participate.")

questions = [
    "I have read the Information Sheet.",
    "I understand I may withdraw at any time.",
    "I understand my data will be anonymised.",
    "I consent to participate."
]

responses = []
for i, q in enumerate(questions):
    st.markdown(f"**{q}**")
    selected = st.radio("", ["Yes", "No"], key=f"q{i}", index=None)
    responses.append(selected)

name = st.text_input("Full Name")
signature = st.text_input("Signature")

if st.button("Submit Consent"):
    if all(r == "Yes" for r in responses) and consent and name and signature:
        st.session_state.consent_given = True
        st.success("Consent submitted. Proceed to the questionnaire via the sidebar.")
    else:
        st.error("Please complete all consent items.")
