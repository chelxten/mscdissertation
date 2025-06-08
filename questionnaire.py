import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

if "consent_submitted" not in st.session_state or not st.session_state.consent_submitted:
    st.warning("⚠️ You must submit the consent form first on the Home page.")
    st.stop()

st.title("🎡 Visitor Questionnaire")

# GSheet Connect
@st.cache_resource
def get_worksheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Amusement Park Survey Responses").sheet1
    return sheet

with st.form("questionnaire"):
    age_group = st.selectbox("What is your age group?", ["Under 12", "13–17", "18–30", "31–45", "46–60", "60+"])
    gender = st.selectbox("What is your gender?", ["Male", "Female", "Non-binary", "Prefer not to say"])
    visit_group = st.selectbox("Who are you visiting with?", ["Alone", "With family", "With friends", "With young children", "With a partner"])
    duration = st.selectbox("How long do you plan to stay in the park today?", ["Less than 2 hours", "2–4 hours", "4–6 hours", "All day"])

    preferences = {
        "thrill": st.slider("Thrill rides", 1, 10, 5),
        "family": st.slider("Family rides", 1, 10, 5),
        "water": st.slider("Water rides", 1, 10, 5),
        "entertainment": st.slider("Live shows", 1, 10, 5),
        "food": st.slider("Food & dining", 1, 10, 5),
        "shopping": st.slider("Shopping", 1, 10, 5),
        "relaxation": st.slider("Relaxation zones", 1, 10, 5)
    }

    priorities = st.multiselect("Top priorities:", ["Enjoying high-intensity rides", "Visiting family-friendly attractions", "Seeing many attractions", "Staying comfortable", "Having food/rest breaks"])
    wait_time = st.selectbox("Max wait time:", ["<10 min", "10–20 min", "20–30 min", "30+ min"])
    walking = st.selectbox("Walking preference:", ["Very short", "Moderate", "I don’t mind walking"])
    crowd_sensitivity = st.selectbox("Crowd sensitivity:", ["Very uncomfortable", "Slightly uncomfortable", "Neutral", "Comfortable"])
    break_time = st.selectbox("Preferred break time:", ["After 1 hour", "After 2 hours", "After every big ride", "I decide as I go"])

    submit = st.form_submit_button("📥 Submit Questionnaire")

if submit:
    st.session_state.questionnaire = {
        "duration": duration,
        "preferences": preferences,
        "priorities": priorities,
        "walking": walking,
        "crowd": crowd_sensitivity,
        "break": break_time
    }
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [timestamp, age_group, gender, visit_group, duration] + list(preferences.values()) + [", ".join(priorities), wait_time, walking, crowd_sensitivity, break_time]
    get_worksheet().append_row(row)
    st.success("✅ Questionnaire submitted! You can now view your personalized plan.")
