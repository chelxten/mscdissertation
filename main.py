import streamlit as st
import time

st.set_page_config(page_title="Consent Form", layout="centered")

st.title("📝 Participant Consent Form")

# --- Participant Information Sheet ---
with st.expander("📄 Participant Information Sheet", expanded=True):
    st.markdown("""
    ### Title of Project  
    *The Search of Advanced AI-Powered Service Robots for Amusement Parks*

    ### Legal Basis for the Research  
    The University undertakes research as part of its function for the community under its legal status.  
    Data protection allows us to use personal data for research with appropriate safeguards in place under the legal basis of public tasks that are in the public interest.  

    A full statement of your rights can be found at: [Privacy Notice for Research](https://www.shu.ac.uk/about-this-website/privacy-policy/privacy-notices/privacy-notice-for-research)  
    Further information is also available at: [Ethics and Integrity at SHU](https://www.shu.ac.uk/research/excellence/ethics-and-integrity)

    ### Invitation and Purpose  
    You are invited to take part in a research study about the use of advanced artificial intelligence technologies to improve service robots in amusement parks. This study aims to understand how technologies like AI-driven navigation, fuzzy logic, and learning systems can help robots become more adaptable and engaging for visitors.

    ### Why You Were Invited  
    You have been invited to take part because people in your age group are typical users of amusement parks and can provide valuable insights into how technology, like service robots, could improve the visitor experience.

    ### Voluntary Participation  
    Taking part in this study is entirely voluntary. You are free to withdraw at any time, without giving a reason, and without any negative consequences. However, once you begin the questionnaire, all questions must be answered in order to complete the survey.

    ### What You Will Do  
    You will be asked to complete a short online questionnaire with rating scales, percentage-based responses, and multiple-choice options. The survey is quick and does not contain open-ended questions.

    ### Time & Place  
    The questionnaire is online and takes approximately 5 minutes to complete.

    ### Use of Deception  
    There is no deception involved. The study’s purpose and process are explained clearly from the beginning.

    ### Risks  
    This is a low-risk study. No sensitive or personal topics are involved.

    ### Benefits  
    While there is no direct benefit to you, your feedback contributes to research that supports the development of improved robotic systems in amusement parks. Results are anonymous and for educational use only.

    ### Opportunity for Questions  
    You may contact the researcher if you have any questions before or during the study.

    ### Confidentiality  
    The questionnaire collects only age and accessibility information for demographic analysis. No names are required. Contact information is optional. All data will be stored anonymously and securely.

    ### Responsibility for Data  
    The researcher is solely responsible for secure data handling in line with the university’s data policies.

    ### Access to Data  
    Only the researcher and their academic supervisor will access the data. It will not be shared externally.

    ### Data Retention and Future Use  
    Data will be securely stored and retained for up to five years. It will only be used for this study.

    ### Use of Results  
    The study's results will appear in a postgraduate dissertation. All reporting will be anonymous.

    ### Study Duration  
    June 2025 – September 2025 (includes data collection and analysis).

    ### Access to Results  
    To request a summary of the findings, contact the researcher via email.

    ---
    **Contact Details**  
    - **Researcher:** Cherry San – [c3065323@hallam.shu.ac.uk](mailto:c3065323@hallam.shu.ac.uk)  
    - **Supervisor:** Dr Samuele Vinanzi – [s.vinanzi@shu.ac.uk](mailto:s.vinanzi@shu.ac.uk)  
    - **Data Concerns:** [DPO@shu.ac.uk](mailto:DPO@shu.ac.uk)  
    - **Research Ethics Queries:** [ethicssupport@shu.ac.uk](mailto:ethicssupport@shu.ac.uk)
    """)

# --- Consent Confirmation Section ---
st.subheader("🔒 Consent Confirmation")

with st.expander("Please read and confirm the following statements:", expanded=True):
    st.markdown("""
    1. I have read the Information Sheet for this study and have had details of the study explained to me.  
    2. My questions about the study have been answered to my satisfaction and I understand that I may ask further questions at any point.  
    3. I understand that I am free to withdraw from the study within the time limits outlined in the Information Sheet, without giving a reason or facing any consequences.  
    4. I agree to provide information to the researchers under the conditions of confidentiality set out in the Information Sheet.  
    5. I wish to participate in the study under the conditions set out in the Information Sheet.  
    6. I consent to the information collected for the purposes of this research study, once anonymised (so that I cannot be identified), to be used for any other research purposes.  
    """)

# --- Consent Submission ---
agreed = st.checkbox("✅ I have read and agree to all the above statements.")
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Full Name")
with col2:
    signature = st.text_input("Signature")

if st.button("Submit Consent"):
    if agreed and name.strip() and signature.strip():
        st.session_state.consent_submitted = True
        st.success("✅ Consent submitted. Redirecting to the questionnaire...")
        time.sleep(1)
        st.switch_page("pages/1_questionnaire.py")
    else:
        st.error("⚠️ Please agree to the consent statement and complete all required fields.")
