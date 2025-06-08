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
st.set_page_config(page_title="Amusement Park Robot Survey", layout="wide")
st.title("🎢 Research on AI-Powered Service Robots in Amusement Parks")

st.header("Participant Information Sheet")
st.download_button(
    label="📄 Download Participant Information Sheet",
    data=open("PARTICIPANT INFORMATION SHEET.pdf", "rb").read(),
    file_name="Participant_Information_Sheet.pdf",
    mime="application/pdf"
)

consent = st.checkbox("I have read the Participant Information Sheet and agree to take part in this study.")

if not consent:
    st.warning("⚠️ You must agree to the consent checkbox to proceed.")
    st.stop()

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
