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

st.image("Sheffield-Hallam-University.png", width=250)
st.title("🎡 Visitor Questionnaire")

# ✅ Google Sheets setup
@st.cache_resource
def get_questionnaire_worksheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Survey Responses").worksheet("Sheet1")
    return sheet
    
# 📝 Questionnaire form
with st.form("questionnaire_form"):
    age = st.selectbox("What is your age group?", ["Under 12", "13–17", "18–30", "31–45", "46–60", "60+"])
    accessibility = st.selectbox("Do you have any accessibility needs?", ["No", "Yes – Physical", "Yes – Sensory", "Yes – Cognitive", "Prefer not to say"])
    duration = st.selectbox("How long do you plan to stay in the park today?", ["<2 hrs", "2–4 hrs", "4–6 hrs", "All day"])
    
    # Preferences (1–10 scale)
    preferences = {
        "thrill": st.slider("Thrill rides", 1, 10, 5),
        "family": st.slider("Family rides", 1, 10, 5),
        "water": st.slider("Water rides", 1, 10, 5),
        "entertainment": st.slider("Live shows", 1, 10, 5),
        "food": st.slider("Food & Dining", 1, 10, 5),
        "shopping": st.slider("Shopping", 1, 10, 5),
        "relaxation": st.slider("Relaxation areas", 1, 10, 5),
    }

    # Priorities
    top_priorities = st.multiselect("What are your top visit priorities?", [
        "Enjoying high-intensity rides",
        "Visiting family-friendly attractions together",
        "Seeing as many attractions as possible",
        "Staying comfortable throughout the visit",
        "Having regular food and rest breaks"
    ])

    wait_time = st.selectbox("What is the maximum wait time you are okay with?", ["<10 min", "10–20 min", "20–30 min", "30+ min"])
    walking = st.selectbox("How far are you willing to walk?", ["Very short distances", "Moderate walking", "Don’t mind walking"])
    break_time = st.selectbox("When do you prefer to take breaks?", ["After 1 hour", "After 2 hours", "After every big ride", "Flexible"])

    submit = st.form_submit_button("📩 Submit")

# ✅ Handle form submission
if submit:
    st.session_state["questionnaire"] = {
        "age": age,
        "duration": duration,
        "accessibility": accessibility,
        "thrill": preferences["thrill"],
        "family": preferences["family"],
        "water": preferences["water"],
        "entertainment": preferences["entertainment"],
        "food": preferences["food"],
        "shopping": preferences["shopping"],
        "relaxation": preferences["relaxation"],
        "priorities": top_priorities.copy(),
        "wait_time": wait_time,
        "walking": walking,
        "break": break_time,
    }


    # Prepare row for Google Sheet (with unique ID)
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        st.session_state.get("unique_id", "unknown"),  # ✅ Insert Unique ID
        age,
        duration,
        accessibility
    ] + list(preferences.values()) + [", ".join(top_priorities), wait_time, walking, break_time]

    # Save to Google Sheet
    get_questionnaire_worksheet().append_row(row)

    st.success("✅ Submitted! Redirecting to your personalized tour plan...")
    time.sleep(1.5)
    st.switch_page("pages/2_tour_plan.py")
