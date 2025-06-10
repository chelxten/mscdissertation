import streamlit as st
import time

st.set_page_config(page_title="Consent Form")

st.title("📝 Participant Consent Form")

with st.expander("📄 Participant Information Sheet", expanded=True):
    st.markdown("""
    **Title of Project:** *The Search of Advanced AI-Powered Service Robots for Amusement Parks*

    **Legal Basis for the Research**  
    The University undertakes research as part of its function for the community under its legal status.  
    Data protection allows us to use personal data for research with appropriate safeguards in place under the legal basis of public tasks that are in the public interest.  

    A full statement of your rights can be found at: [Privacy Notice for Research](https://www.shu.ac.uk/about-this-website/privacy-policy/privacy-notices/privacy-notice-for-research)  

    However, all University research is reviewed to ensure that participants are treated appropriately and their rights respected. This study has been submitted for ethical review and is awaiting approval by the University’s Research Ethics Committee.  

    Further information at: [Ethics and Integrity at SHU](https://www.shu.ac.uk/research/excellence/ethics-and-integrity)

    **Invitation and Purpose**  
    You are invited to take part in a research study about the use of advanced artificial intelligence technologies to improve service robots in amusement parks. This study aims to understand how technologies like AI-driven navigation, fuzzy logic, and learning systems can help robots become more adaptable and engaging for visitors.

    **Why You Were Invited**  
    You have been invited to take part because people in your age group are typical users of amusement parks and can provide valuable insights into how technology, like service robots, could improve the visitor experience. Your feedback will help us understand what features and behaviours make these robots more useful, engaging, and enjoyable for guests.
    
    **Voluntary Participation**  
    Taking part in this study is entirely voluntary. You are free to withdraw at any time, without giving a reason, and without any negative consequences. However, once you begin the questionnaire, all questions must be answered in order to complete the survey.

    **What You Will Do**  
    If you choose to take part, you will be asked to complete a short online questionnaire. The questions will include rating scales from 1 to 10, percentage-based responses, and multiple-choice options. There are no open-ended questions, and the survey is designed to be quick and straightforward.

    **Time & Place**  
    The questionnaire will be entirely online and takes approximately 5 minutes to complete.

    **Use of Deception**  
    There is no deception involved in this study. All information about the purpose and process of the research is explained clearly to participants from the beginning.

    **Risks**  
    This is a low-risk study. The questionnaire only includes multiple-choice and rating-scale questions about amusement park experiences and ride preferences. No sensitive or personal topics are involved.

    **Benefits**  
    While there is no direct benefit to you as a participant, your responses will contribute to academic research in robotics and help improve the use of service robots in amusement parks. The findings may support future developments that enhance visitor experiences in entertainment environments. All results will be reported anonymously and used solely for educational and research purposes.

    **Opportunity for Questions**  
    If you have any questions about the study, you are welcome to contact the researcher at any time using the email provided below.

    **Confidentiality**  
    The questionnaire does not ask for your name. Only your age and gender will be required, which are collected solely for demographic analysis. Providing contact details is optional for those who wish to be contacted for a future follow-up. All data will be stored anonymously, and no one will be able to identify you from your responses.

    **Responsibility for Data**  
    The researcher is solely responsible for storing and managing the data securely in accordance with the university’s data protection policies.

    **Access to Data**  
    Only the researcher and their academic supervisor will have access to the collected data. It will not be shared with anyone else.

    **Data Retention and Future Use**  
    All data will be stored securely and retained for up to five years in line with university policy. The data will be used only for this study and will not be shared or used in any other research projects.

    **Use of Results**  
    The results of this study will be used in a postgraduate dissertation submitted as part of the researcher’s academic programme. All findings will be reported anonymously.

    **Study Duration**  
    The study will take place between June 2025 and September 2025, which includes the period of data collection and analysis.
    
    **Access to Results**  
    If you would like a summary of the study’s findings once the research is complete, you may request this by contacting the researcher using the email provided below.

    **Contact Details**  
    - **Researcher:** Cherry San – c3065323@hallam.shu.ac.uk  
    - **Supervisor:** Dr Samuele Vinanzi – s.vinanzi@shu.ac.uk  
    - **Data Concerns:** DPO@shu.ac.uk  
    - **Research Ethics Queries:** ethicssupport@shu.ac.uk  
    """)

    st.caption("Study Duration: June 2025 to September 2025")

st.header("Consent Confirmation")

with st.expander("🔍 Please confirm the following statements before continuing:", expanded=True):
    st.markdown("""
- I confirm I am 18 years or older.  
- I understand my participation is voluntary.  
- I understand the data will be anonymous and only used for academic purposes.  
- I agree my responses can be used for this study.  
- I understand I can stop at any time without giving a reason.  
    """)

agreed = st.checkbox("I have read and agree to all the above statements.")
name = st.text_input("Full Name")
signature = st.text_input("Signature")

if st.button("Submit Consent"):
    if agreed and name.strip() and signature.strip():
        st.session_state.consent_submitted = True
        st.success("✅ Consent submitted. Redirecting...")
        time.sleep(1)
        st.switch_page("pages/1_questionnaire.py")
    else:
        st.error("⚠️ Please agree to the consent statement and fill in your name and signature.")
