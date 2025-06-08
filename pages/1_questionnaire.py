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

# ✅ Google Sheets setup
@st.cache_resource
def get_worksheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Amusement Park Survey Responses").sheet1
    return sheet

# 📝 Questionnaire form
with st.form("questionnaire_form"):
    age = st.selectbox("What is your age group?", ["Under 12", "13–17", "18–30", "31–45", "46–60", "60+"])
    gender = st.selectbox("What is your gender?", ["Male", "Female", "Non-binary", "Prefer not to say"])
    group = st.selectbox("Who are you visiting with?", ["Alone", "Family", "Friends", "Partner", "Children"])
    duration = st.selectbox("How long do you plan to stay in the park today?", ["<2 hrs", "2–4 hrs", "4–6 hrs", "All day"])

    preferences = {
        "thrill": st.slider("Thrill rides", 1, 10, 5),
        "family": st.slider("Family rides", 1, 10, 5),
        "water": st.slider("Water rides", 1, 10, 5),
        "shows": st.slider("Live shows", 1, 10, 5),
        "food": st.slider("Food & Dining", 1, 10, 5),
        "shopping": st.slider("Shopping", 1, 10, 5),
        "relaxation": st.slider("Relaxation areas", 1, 10, 5),
    }

    top_priorities = st.multiselect("What are your top visit priorities?", [
        "High-intensity rides",
        "Family activities",
        "See many attractions",
        "Comfort",
        "Frequent breaks"
    ])

    wait_time = st.selectbox("Maximum acceptable wait time:", ["<10 min", "10–20 min", "20–30 min", "30+ min"])
    walking = st.selectbox("How far are you willing to walk?", ["Short", "Moderate", "Don’t mind walking"])
    crowd = st.selectbox("How comfortable are you with crowds?", ["Very uncomfortable", "Slightly uncomfortable", "Neutral", "Comfortable"])
    break_time = st.selectbox("When do you prefer to take breaks?", ["1 hr", "2 hrs", "After big rides", "Flexible"])

    submit = st.form_submit_button("📩 Submit")

# ✅ Handle form submission
if submit:
    # Store in session
    st.session_state["questionnaire"] = {
        "age": age,
        "gender": gender,
        "group": group,
        "duration": duration,
        "thrill": preferences["thrill"],
        "family": preferences["family"],
        "water": preferences["water"],
        "shows": preferences["shows"],
        "food": preferences["food"],
        "shopping": preferences["shopping"],
        "relaxation": preferences["relaxation"],
        "priorities": top_priorities.copy(),  # Avoid Streamlit mutability errors
        "wait_time": wait_time,
        "walking": walking,
        "crowd": crowd,
        "break": break_time,
    }

    # Prepare row for Google Sheet
    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), age, gender, group, duration] + \
          list(preferences.values()) + [", ".join(top_priorities), wait_time, walking, crowd, break_time]

    # Save to Google Sheet
    get_worksheet().append_row(row)

    # Success message + redirect
    st.success("✅ Submitted! Redirecting to your personalized tour plan...")
    time.sleep(1.5)
    st.switch_page("2_tour_plan")
