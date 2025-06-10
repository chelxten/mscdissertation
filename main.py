import streamlit as st
import time

st.set_page_config(page_title="Consent Form")

st.title("📝 Participant Consent Form")

with st.expander("📄 Participant Information Sheet", expanded=True):
    st.markdown("""
    **Title of Project:** *The Search of Advanced AI-Powered Service Robots for Amusement Parks*

    **Legal Basis for the Research**  
    Sheffield Hallam University conducts research under its legal duty to serve the public. Your data will be used for research purposes with appropriate safeguards. Full privacy notice: [Privacy Notice for Research](https://www.shu.ac.uk/about-this-website/privacy-policy/privacy-notices/privacy-notice-for-research)

    **Invitation and Purpose**  
    You are invited to participate in a study on AI-enhanced service robots in amusement parks, focusing on technologies such as fuzzy logic and adaptive navigation. Your feedback will help improve how these robots support visitors.

    **Why You Were Invited**  
    Your demographic is typical of amusement park visitors, and your experience will help identify what robot behaviours are most effective and enjoyable.

    **Voluntary Participation**  
    Your participation is voluntary. You can withdraw at any time. Once the survey begins, all questions must be completed to finish.

    **What You Will Do**  
    You’ll complete a short online questionnaire with rating scales and multiple-choice questions. There are no open-ended responses.

    **Time & Place**  
    The survey is online and takes approximately 5 minutes to complete.

    **Risks & Benefits**  
    There are no risks or sensitive questions. While there is no direct benefit to you, your answers will contribute to academic research and development in robotics.

    **Confidentiality & Data Use**  
    No names are collected. Age and gender are collected only for analysis. All data is anonymized and stored securely by the researcher. Only the researcher and their supervisor will access it.

    **Contact Details**  
    - **Researcher:** Cherry San – c3065323@hallam.shu.ac.uk  
    - **Supervisor:** Dr Samuele Vinanzi – s.vinanzi@shu.ac.uk  
    - **Data Concerns:** DPO@shu.ac.uk  
    - **Research Ethics Queries:** ethicssupport@shu.ac.uk  
    """)

    st.caption("Study Duration: June to September 2025")

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
