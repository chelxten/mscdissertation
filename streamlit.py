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

st.markdown("**Title of Project:**  \n*The Search of Advanced AI-Powered Service Robots for Amusement Parks*")

st.markdown("Please answer the following questions by ticking the response that applies:")

# Questions
questions = [
    "1. I have read the Information Sheet for this study and have had details of the study explained to me.",
    "2. My questions about the study have been answered to my satisfaction and I understand that I may ask further questions at any point.",
    "3. I understand that I am free to withdraw from the study within the time limits outlined in the Information Sheet, without giving a reason for my withdrawal or to decline to answer any particular questions in the study without any consequences to my future treatment by the researcher.",
    "4. I agree to provide information to the researchers under the conditions of confidentiality set out in the Information Sheet.",
    "5. I wish to participate in the study under the conditions set out in the Information Sheet.",
    "6. I consent to the information collected for the purposes of this research study, once anonymised (so that I cannot be identified), to be used for any other research purposes."
]

# Responses start empty
responses = []
for i, q in enumerate(questions):
    st.markdown(f"**{q}**")
    selected = st.radio(
        label="",
        options=["Yes", "No"],
        key=f"q{i}",
        index=None  # ✅ This removes default selection
    )
    responses.append(selected)

# Participant Fields
st.markdown("**Participant Information:**")
participant_name = st.text_input("Full Name", value="")
participant_signature = st.text_input("Signature (type your name)", value="")
participant_date = st.date_input("Date")
participant_contact = st.text_input("Contact Details (optional)", value="")

# Researcher Information
st.markdown("---")
st.markdown("**Researcher’s Information:**")
st.markdown("**Name:** Cherry San  \n**Email:** c3065323@hallam.shu.ac.uk  \n**Course:** MSc Artificial Intelligence")

# Submission Validation
if st.button("✅ Submit Consent Form"):
    if (
        all(r == "Yes" for r in responses)
        and None not in responses
        and participant_name.strip()
        and participant_signature.strip()
    ):
        st.session_state.consent_submitted = True  # ✅ Set the flag
        st.success("✅ Consent form submitted. Thank you for participating.")
        st.rerun()  # ✅ Rerun to show the questionnaire
    else:
        st.error("⚠️ Please agree to all statements and fill in all required participant fields before submitting.")
        

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

# Map visit duration text to minutes
duration_map = {
    "Less than 2 hours": 90,
    "2–4 hours": 180,
    "4–6 hours": 300,
    "All day": 480
}
duration_minutes = duration_map[duration]

# Generate personalized tour plan
final_plan, time_allocation, leftover = generate_plan_streamlit_interface(
    preferences,
    priorities,
    duration_minutes,
    walking,
    crowd_sensitivity,
    break_time
)
# 🔁 Fuzzy Logic Integration Function
def generate_plan_streamlit_interface(preferences, priorities, duration_minutes, walking, crowd_sensitivity, break_time):
    attraction_times, leftover = allocate_park_time(
        duration_minutes,
        preferences,
        priorities,
        walking,
        crowd_sensitivity
    )
    route = generate_navigation_order(attraction_times)
    final_plan = insert_breaks(route, break_time)
    return final_plan, attraction_times, leftover
    
# Show results
st.success("✅ Your response has been saved.")
st.subheader("🎯 Your Personalized Plan")
st.markdown("Your smart plan based on your preferences:")

st.write("🗺️ **Tour Route (with breaks):**", final_plan)
st.write("⏱️ **Time Allocation per Attraction:**", time_allocation)
st.write("🕒 **Leftover Time (minutes):**", leftover)
