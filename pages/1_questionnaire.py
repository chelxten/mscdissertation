import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

st.set_page_config(page_title="Visitor Questionnaire")

# 🚫 Block access if consent not given
if "consent_submitted" not in st.session_state or not st.session_state.consent_submitted:
    st.warning("⚠️ You must submit the consent form first.")
    st.stop()

st.title("🎡 Visitor Questionnaire")

@st.cache_resource
def get_worksheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("Amusement Park Survey Responses").sheet1

# 📝 Questionnaire form
with st.form("questionnaire_form"):
    age_group = st.selectbox("What is your age group?", ["Under 18", "18–30", "31–50", "51–65", "Over 65"])
    accessibility = st.radio("Do you have any accessibility needs?", ["Yes", "No"])
    visit_group = st.selectbox("Who are you visiting with today?", [
        "Alone", "With friends", "With family (children)", "With older adults", "Mixed-age group"
    ])
    visit_duration = st.slider("How long do you plan to stay in the park today? (in hours)", 1, 12, 4)

    st.subheader("Rate your interest in the following areas (1 = Low, 10 = High):")
    preferences = {
        "thrill": st.slider("Thrill rides", 1, 10, 5),
        "family": st.slider("Family-friendly rides", 1, 10, 5),
        "water": st.slider("Water attractions", 1, 10, 5),
        "entertainment": st.slider("Live shows or performances", 1, 10, 5),
        "food": st.slider("Food & snacks", 1, 10, 5),
        "shopping": st.slider("Shops & souvenirs", 1, 10, 5),
        "relaxation": st.slider("Rest & relaxation areas", 1, 10, 5)
    }

    priorities = st.multiselect("What are your top 3 visit priorities?", [
        "Enjoying high-intensity rides",
        "Visiting family-friendly attractions together",
        "Seeing as many attractions as possible",
        "Staying comfortable throughout the visit",
        "Having regular food and rest breaks",
        "Spending time together as a group",
        "Keeping walking to a minimum"
    ], max_selections=3)

    walking_pref = st.radio("How far are you willing to walk?", [
        "Very short distances", "Moderate walking is okay", "I don’t mind long walks"
    ])

    break_pref = st.selectbox("When would you prefer to take breaks?", [
        "After every big ride", "After 1 hour", "After 2 hours", "Only when tired"
    ])

    wait_time = st.radio("How long are you willing to wait for rides?", [
        "Less than 10 minutes", "Up to 20 minutes", "Up to 30 minutes", "I don’t mind waiting"
    ])

    submit = st.form_submit_button("📩 Submit")

# ✅ Handle submission
if submit:
    st.session_state["questionnaire"] = {
        "age": age,
        "group": group,
        "duration": duration,
        "accessibility": accessibility,  # ✅ new field
        "thrill": preferences["thrill"],
        "family": preferences["family"],
        "water": preferences["water"],
        "shows": preferences["shows"],
        "food": preferences["food"],
        "shopping": preferences["shopping"],
        "relaxation": preferences["relaxation"],
        "priorities": top_priorities.copy(),
        "wait_time": wait_time,
        "walking": walking,              # ✅ must exist here
        "break": break_time,
    }

    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           age_group, accessibility, visit_group, visit_duration] + \
          list(preferences.values()) + [", ".join(priorities), walking_pref, break_pref, wait_time]

    get_worksheet().append_row(row)
    st.success("✅ Submitted! Redirecting to your personalized tour plan...")
    time.sleep(1.5)
    st.switch_page("pages/2_tour_plan.py")
