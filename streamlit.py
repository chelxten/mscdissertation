import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. GSheet Connection
def connect_to_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

@st.cache_resource
def get_worksheet():
    client = connect_to_gsheet()
    sheet = client.open("Amusement Park Survey Responses").sheet1
    return sheet

# 2. Session flag
if "consent_submitted" not in st.session_state:
    st.session_state.consent_submitted = False

# 3. Info Sheet
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

# 4. Consent Checkbox
consent = st.checkbox("I have read the Participant Information Sheet and agree to take part in this study.")
if not consent:
    st.warning("⚠️ You must agree to the consent checkbox to proceed.")
    st.stop()

# 5. Consent Form
st.header("📝 Participant Consent Form")
st.markdown("*Please answer the following by selecting Yes or No:*")

questions = [
    "1. I have read the Information Sheet for this study.",
    "2. My questions have been answered and I can ask more anytime.",
    "3. I can withdraw at any time without reason.",
    "4. I agree to share information under the confidentiality terms.",
    "5. I wish to participate under the described conditions.",
    "6. I consent to the anonymous use of my data for future research."
]

responses = []
for i, q in enumerate(questions):
    st.markdown(f"**{q}**")
    response = st.radio("", ["Yes", "No"], key=f"q{i}")
    responses.append(response)

# 6. Participant Details
st.markdown("**Participant Information:**")
participant_name = st.text_input("Full Name")
participant_signature = st.text_input("Signature (type your name)")
participant_date = st.date_input("Date")
participant_contact = st.text_input("Contact Details (optional)")

# 7. Researcher Details
st.markdown("---")
st.markdown("**Researcher’s Information:**  \n**Name:** Cherry San  \n**Email:** c3065323@hallam.shu.ac.uk  \n**Course:** MSc Artificial Intelligence")

# 8. Submit Button
if st.button("✅ Submit Consent Form"):
    if all(r == "Yes" for r in responses) and participant_name.strip() and participant_signature.strip():
        st.session_state.consent_submitted = True
        st.success("✅ Consent form submitted. Thank you for participating.")
    else:
        st.error("⚠️ Please agree to all statements and fill in all required fields.")

# 9. Questionnaire - only shown if consent submitted
if st.session_state.consent_submitted:
    st.header("🎡 Visitor Questionnaire")

    with st.form("questionnaire"):
        st.subheader("About You")
        age_group = st.selectbox("What is your age group?", ["Under 12", "13–17", "18–30", "31–45", "46–60", "60+"])
        gender = st.selectbox("What is your gender?", ["Male", "Female", "Non-binary", "Prefer not to say"])
        visit_group = st.selectbox("Who are you visiting with?", ["Alone", "With family", "With friends", "With young children", "With a partner"])
        duration = st.selectbox("How long do you plan to stay in the park today?", ["Less than 2 hours", "2–4 hours", "4–6 hours", "All day"])

        st.subheader("Your Preferences (1 to 10)")
        preferences = {
            "thrill": st.slider("Thrill rides", 1, 10, 5),
            "family": st.slider("Family rides", 1, 10, 5),
            "water": st.slider("Water rides", 1, 10, 5),
            "entertainment": st.slider("Live shows", 1, 10, 5),
            "food": st.slider("Food & dining", 1, 10, 5),
            "shopping": st.slider("Shopping", 1, 10, 5),
            "relaxation": st.slider("Relaxation zones", 1, 10, 5)
        }

        st.subheader("Most Important to You (Choose up to 3)")
        priorities = st.multiselect(
            "Select priorities:",
            ["Enjoying high-intensity rides", "Visiting family-friendly attractions", "Seeing many attractions", "Staying comfortable", "Having food/rest breaks"]
        )

        st.subheader("Accessibility & Comfort")
        wait_time = st.selectbox("Max time you're willing to wait in line:", ["<10 min", "10–20 min", "20–30 min", "30+ min"])
        walking = st.selectbox("Walking comfort:", ["Very short", "Moderate", "I don’t mind walking"])
        crowd_sensitivity = st.selectbox("Crowd sensitivity:", ["Very uncomfortable", "Slightly uncomfortable", "Neutral", "Comfortable"])
        break_time = st.selectbox("Preferred break time:", ["After 1 hour", "After 2 hours", "After every big ride", "I decide as I go"])

        submit = st.form_submit_button("Get My Personalized Plan")

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
        st.subheader("🎯 Your Personalized Plan (Coming Soon!)")
        st.markdown("Thanks! Your preferences will be used to generate a smart tour plan.")
