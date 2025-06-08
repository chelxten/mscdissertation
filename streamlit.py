# streamlit_app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Set up Google Sheets credentials using secrets
def connect_to_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

# Connect to your Google Sheet
@st.cache_resource
def get_worksheet():
    client = connect_to_gsheet()
    sheet = client.open("Amusement Park Survey Responses").sheet1
    return sheet

# ---------------------------
# PAGE 1: Info Sheet + Consent
# ---------------------------
with st.expander("📄 Click to View Participant Information Sheet"):
    st.markdown("""
    ### PARTICIPANT INFORMATION SHEET

    **Title of Project**  
    _The Search of Advanced AI-Powered Service Robots for Amusement Parks_

    **Legal Basis for the Research**  
    The University undertakes research as part of its function for the community under its legal status.  
    Data protection allows us to use personal data for research with appropriate safeguards in place under the legal basis of public tasks that are in the public interest.  
    A full statement of your rights can be found at: [Privacy Notice for Research](https://www.shu.ac.uk/about-this-website/privacy-policy/privacy-notices/privacy-notice-for-research).  
    All University research is reviewed to ensure participants are treated appropriately. This study has been submitted for ethical review and is awaiting approval.  
    Learn more: [Research Ethics](https://www.shu.ac.uk/research/excellence/ethics-and-integrity)

    **Invitation and Purpose of the Research**  
    You are invited to take part in a study on how AI technologies can enhance service robots in amusement parks.  
    The goal is to explore how systems like AI navigation and fuzzy logic can improve visitor interaction and adaptability.

    **Why You Have Been Invited**  
    You were selected because people in your age group frequently visit amusement parks and can provide helpful insights into service robot design.

    **Voluntary Participation**  
    Your participation is voluntary. You can withdraw at any time without reason. However, all survey questions must be answered to proceed.

    **What You Will Be Asked to Do**  
    You'll complete a short online questionnaire using sliders and multiple-choice options. There are no open-ended questions. It takes about 5 minutes.

    **Where the Study Will Take Place**  
    The entire questionnaire is online and can be accessed anytime on a phone or computer.

    **Time Commitment**  
    Completion time is approx. 5 minutes. Some participants may be invited for follow-up after robot deployment—this is optional.

    **Use of Deception**  
    There is no deception. All study details are transparent from the beginning.

    ---

    ### Risks and Benefits

    **Risks**  
    This is a low-risk study with only standard preference and experience questions—no personal or sensitive topics.

    **Benefits**  
    Although there is no direct benefit to you, your responses will contribute to research that could improve robotics in entertainment settings.  
    All results will be anonymous and used only for education and research.

    ---

    ### Data and Contact Information

    **Opportunity for Questions**  
    You may contact the researcher anytime with questions (see contact below).

    **Confidentiality**  
    Your name is not collected. Only age and gender are required (for demographic analysis). Contact info is optional.  
    Data is anonymous, and no identifying info will be recorded.

    **Data Management**  
    The researcher is responsible for secure data storage. Only the researcher and supervisor can access it.

    **Data Retention**  
    Data will be kept securely for up to five years and only used for this study.

    **Use of Results**  
    Results will be reported anonymously in the researcher’s postgraduate dissertation.

    **Study Timeline**  
    Research will run from June 2025 to September 2025.

    **Requesting Results**  
    If you’d like a summary after the study, email the researcher (see below).

    **Researcher Contact**  
    Name: **Cherry San**  
    Email: [c3065323@hallam.shu.ac.uk](mailto:c3065323@hallam.shu.ac.uk)  
    Course: MSc Artificial Intelligence

    **Supervisor Contact**  
    Name: **Dr. Samuele Vinanzi**  
    Email: [s.vinanzi@shu.ac.uk](mailto:s.vinanzi@shu.ac.uk)

    **Further Support**  
    - **Data Concerns**: [DPO@shu.ac.uk](mailto:DPO@shu.ac.uk)  
    - **Ethics Concerns**: [ethicssupport@shu.ac.uk](mailto:ethicssupport@shu.ac.uk)
    """, unsafe_allow_html=True)

consent = st.checkbox("I have read the Participant Information Sheet and agree to take part in this study.")

if not consent:
    st.warning("⚠️ You must agree to the consent checkbox to proceed.")
    st.stop()

st.header("📝 Participant Consent Form")

st.markdown("**Title of Project:**  \n*The Search of Advanced AI-Powered Service Robots for Amusement Parks*")

st.markdown("Please answer the following questions by ticking the response that applies:")

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
    response = st.radio(q, ["", "Yes", "No"], index=None, key=f"q{i}", format_func=lambda x: "Select an option" if x == "" else x)
    responses.append(response)

st.markdown("**Participant Information:**")
participant_name = st.text_input("Full Name")
participant_signature = st.text_input("Signature (type your name)")
participant_date = st.date_input("Date")
participant_contact = st.text_input("Contact Details (optional)")

st.markdown("---")
st.markdown("**Researcher’s Information:**")
st.markdown("**Name:** Cherry San  \n**Email:** c3065323@hallam.shu.ac.uk  \n**Course:** MSc Artificial Intelligence")

if st.button("✅ Submit Consent Form"):
    if (
        all(r in ["Yes", "No"] for r in responses)
        and all(r == "Yes" for r in responses)
        and participant_name.strip()
        and participant_signature.strip()
    ):
        st.success("✅ Consent form submitted. Thank you for participating.")
    else:
        st.error("⚠️ Please agree to all statements and fill in all required participant fields before submitting.")
        
# ---------------------------
# PAGE 2: Questionnaire Input
# ---------------------------
st.header("Visitor Questionnaire")

with st.form("questionnaire"):
    st.subheader("About You")
    age_group = st.selectbox("What is your age group?", ["Under 12", "13–17", "18–30", "31–45", "46–60", "60+"])
    gender = st.selectbox("What is your gender?", ["Male", "Female", "Non-binary", "Prefer not to say"])
    visit_group = st.selectbox("Who are you visiting with today?", ["Alone", "With family", "With friends", "With young children", "With a partner"])
    duration = st.selectbox("How long do you plan to stay in the park today?", ["Less than 2 hours", "2–4 hours", "4–6 hours", "All day"])

    st.subheader("Your Preferences (Rate from 1 to 10)")
    preferences = {
        "thrill": st.slider("Thrill rides (e.g., roller coasters)", 1, 10, 5),
        "family": st.slider("Family rides (e.g., bumper cars)", 1, 10, 5),
        "water": st.slider("Water rides", 1, 10, 5),
        "entertainment": st.slider("Live shows and performances", 1, 10, 5),
        "food": st.slider("Food and dining", 1, 10, 5),
        "shopping": st.slider("Shopping and souvenirs", 1, 10, 5),
        "relaxation": st.slider("Relaxation zones (e.g., gardens)", 1, 10, 5)
    }

    st.subheader("What is most important to you? (Choose up to 3)")
    priorities = st.multiselect(
        "Select priorities:",
        ["Enjoying high-intensity rides", "Visiting family-friendly attractions together", "Seeing as many attractions as possible", "Staying comfortable throughout the visit", "Having regular food and rest breaks"]
    )

    st.subheader("Accessibility & Comfort")
    wait_time = st.selectbox("Max time you're willing to wait in line:", ["Less than 10 minutes", "10–20 minutes", "20–30 minutes", "30+ minutes"])
    walking = st.selectbox("Walking comfort:", ["Very short distances", "Moderate walking", "I don’t mind walking a lot"])
    crowd_sensitivity = st.selectbox("Sensitivity to crowds:", ["Very uncomfortable", "Slightly uncomfortable", "Neutral", "Comfortable"])
    break_time = st.selectbox("When would you prefer to take a break?", ["After 1 hour", "After 2 hours", "After every big ride", "I decide as I go"])

    submit = st.form_submit_button("Get My Personalized Plan")

# ---------------------------
# PAGE 3: Save + Fuzzy Logic Result Placeholder
# ---------------------------
if submit:
    sheet = get_worksheet()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [
        timestamp, age_group, gender, visit_group, duration,
        preferences['thrill'], preferences['family'], preferences['water'], preferences['entertainment'],
        preferences['food'], preferences['shopping'], preferences['relaxation'],
        ", ".join(priorities), wait_time, walking, crowd_sensitivity, break_time
    ]
    sheet.append_row(row)
    st.success("✅ Your response has been saved.")

    # Optional placeholder for fuzzy plan
    st.subheader("🎯 Your Personalized Plan (Coming Soon!)")
    st.markdown("Your preferences will be used to generate a tailored tour experience. Stay tuned!")
