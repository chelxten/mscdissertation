import streamlit as st
from datetime import datetime
import time 

# Set session state defaults
if "consent_submitted" not in st.session_state:
    st.session_state.consent_submitted = False

st.title("🧾 Participant Information & Consent")

# Info Sheet
with st.expander("📄 Click to View Participant Information Sheet"):
    st.markdown("""
    ### PARTICIPANT INFORMATION SHEET
    **Title:** _The Search of Advanced AI-Powered Service Robots for Amusement Parks_

    **Legal Basis:** This study is under SHU’s ethical research framework. [Research Ethics](https://www.shu.ac.uk/research/excellence/ethics-and-integrity)

    **Invitation & Purpose:** You are invited to explore how AI can enhance service robots in amusement parks.

    **Voluntary Participation:** You may withdraw at any time. All questions must be completed to proceed.

    **Time Commitment:** ~5 minutes.

    **Risks & Benefits:** Low risk. No direct benefit, but responses will improve robotics research. Anonymous data only.

    **Data Use:** Stored securely for up to 5 years, used for MSc dissertation. No personal IDs collected.

    **Contact Info:**  
    Researcher: **Cherry San** – c3065323@hallam.shu.ac.uk  
    Supervisor: **Dr. Samuele Vinanzi** – s.vinanzi@shu.ac.uk
    """, unsafe_allow_html=True)

# Consent Form
st.subheader("📝 Participant Consent Form")

st.markdown("**Title of Project:**  \
*The Search of Advanced AI-Powered Service Robots for Amusement Parks*")

questions = [
    "1. I have read the Information Sheet for this study and have had details of the study explained to me.",
    "2. My questions about the study have been answered to my satisfaction and I understand that I may ask further questions at any point.",
    "3. I understand that I am free to withdraw from the study within the time limits outlined in the Information Sheet, without giving a reason for my withdrawal or to decline to answer any particular questions in the study without any consequences to my future treatment by the researcher.",
    "4. I agree to provide information to the researchers under the conditions of confidentiality set out in the Information Sheet.",
    "5. I wish to participate in the study under the conditions set out in the Information Sheet.",
    "6. I consent to the information collected for the purposes of this research study, once anonymised (so that I cannot be identified), to be used for any other research purposes."
]

responses = []
for i, q in enumerate(questions):
    st.markdown(f"**{q}**")
    selected = st.radio("", ["Yes", "No"], key=f"q{i}", index=None)
    responses.append(selected)

st.markdown("**Participant Information:**")
name = st.text_input("Full Name")
signature = st.text_input("Signature (type your name)")
date = st.date_input("Date")
contact = st.text_input("Contact Details (optional)")

# Researcher Info
st.markdown("---")
st.markdown("**Researcher:** Cherry San")
st.markdown("**Email:** c3065323@hallam.shu.ac.uk")
st.markdown("**Course:** MSc Artificial Intelligence")

# Submission
if st.button("✅ Submit Consent Form", type="primary"):
    if all(r == "Yes" for r in responses) and name.strip() and signature.strip():
        st.session_state.consent_submitted = True
        st.success("✅ Consent form submitted. Redirecting to questionnaire...")

        # Add delay before redirect
        time.sleep(1)

        # 👇 This redirects to the Questionnaire page
        st.switch_page("pages/1_questionnaire.py")
    else:
        st.error("⚠️ Please agree to all questions and fill in required fields.")
