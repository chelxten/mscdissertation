import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time  # make sure this is imported at the top

st.set_page_config(page_title="Visitor Questionnaire")

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
    sheet = client.open("Amusement Park Survey Responses").sheet1
    return sheet

with st.form("questionnaire"):
    age = st.selectbox("Age group:", ["Under 12", "13–17", "18–30", "31–45", "46–60", "60+"])
    gender = st.selectbox("Gender:", ["Male", "Female", "Non-binary", "Prefer not to say"])
    group = st.selectbox("Who are you visiting with?", ["Alone", "Family", "Friends", "Partner", "Children"])
    duration = st.selectbox("Visit duration:", ["<2 hrs", "2–4 hrs", "4–6 hrs", "All day"])

    preferences = {
        "thrill": st.slider("Thrill rides", 1, 10, 5),
        "family": st.slider("Family rides", 1, 10, 5),
        "water": st.slider("Water rides", 1, 10, 5),
        "shows": st.slider("Live shows", 1, 10, 5),
        "food": st.slider("Food", 1, 10, 5),
        "shopping": st.slider("Shopping", 1, 10, 5),
        "relaxation": st.slider("Relaxation", 1, 10, 5),
    }

    top_priorities = st.multiselect("Top priorities:", [
        "High-intensity rides", "Family activities", "See many attractions", "Comfort", "Frequent breaks"
    ])

    wait_time = st.selectbox("Max wait time:", ["<10 min", "10–20 min", "20–30 min", "30+ min"])
    walking = st.selectbox("Walking preference:", ["Short", "Moderate", "Don’t mind walking"])
    crowd = st.selectbox("Crowd comfort:", ["Very uncomfortable", "Slightly uncomfortable", "Neutral", "Comfortable"])
    break_time = st.selectbox("Preferred break time:", ["1 hr", "2 hrs", "After big rides", "Flexible"])

    submit = st.form_submit_button("📩 Submit")

if submit:
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
        "priorities": top_priorities.copy(),
        "wait_time": wait_time,
        "walking": walking,
        "crowd": crowd,
        "break": break_time,
    }

    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), age, gender, group, duration] + \
          list(preferences.values()) + [", ".join(top_priorities), wait_time, walking, crowd, break_time]

    get_worksheet().append_row(row)

    st.success("✅ Submitted! Redirecting to your plan...")
    time.sleep(1)  # optional pause
    st.switch_page("2_tour_plan")
