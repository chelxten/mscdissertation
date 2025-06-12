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

# ✅ Load PIS file for download
@st.cache_resource
def load_pis_file():
    with open("PISPCF.pdf", "rb") as f:
        return f.read()

pis_data = load_pis_file()

# ✅ Questionnaire form
with st.form("questionnaire_form"):
    age = st.selectbox("What is your age group?", ["Under 12", "13–17", "18–30", "31–45", "46–60", "60+"])
    accessibility = st.selectbox("Do you have any accessibility needs?", ["No", "Yes – Physical", "Yes – Sensory", "Yes – Cognitive", "Prefer not to say"])
    duration = st.selectbox("How long do you plan to stay in the park today?", ["<2 hrs", "2–4 hrs", "4–6 hrs", "All day"])
    
    st.markdown("### Please rank your preferences from 1 (most important) to 7 (least important). Each rank can only be used once.")

    # Define categories
    preference_categories = ["Thrill rides", "Family rides", "Water rides", "Live shows", "Food & Dining", "Shopping", "Relaxation areas"]

    # Build ranking inputs dynamically
    preference_ranks = {}
    used_ranks = set()

    for category in preference_categories:
        # Calculate available ranks for this field
        available_ranks = [str(i) for i in range(1, 8) if i not in used_ranks]
    
        selected_rank = st.selectbox(f"{category} rank:", options=available_ranks, key=category)
        selected_rank_int = int(selected_rank)
    
        preference_ranks[category.lower().replace(" ", "_")] = selected_rank_int
        used_ranks.add(selected_rank_int)

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

    st.markdown("""
    ---
    By clicking the **‘Submit’** button below, you are consenting to participate in this study,
    as it is described in the Participant Information Sheet. If you did not yet download and keep a copy of this document
    for your records, we recommend you do that now. You may download it at the bottom of this page.
    """)

    submit = st.form_submit_button("📩 Submit")

# ✅ Show download button (outside of form, still visually above submit)

st.download_button(
    label="📄 Download Participant Information Sheet (PDF)",
    data=pis_data,
    file_name="PISPCF.pdf",
    mime="application/pdf"
)

# ✅ Handle form submission
if submit:
    st.session_state["questionnaire"] = {
        "age": age,
        "duration": duration,
        "accessibility": accessibility,
        "thrill": preference_ranks["thrill_rides"],
        "family": preference_ranks["family_rides"],
         "water": preference_ranks["water_rides"],
        "entertainment": preference_ranks["live_shows"],
        "food": preference_ranks["food_&_dining"],
        "shopping": preference_ranks["shopping"],
        "relaxation": preference_ranks["relaxation_areas"],
        "priorities": top_priorities.copy(),
        "wait_time": wait_time,
        "walking": walking,
        "break": break_time,
    }

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unique_id = st.session_state.get("unique_id", "unknown")

    sheet = get_questionnaire_worksheet()
    cell = sheet.find(unique_id, in_column=2)
    row_num = cell.row

    update_values = [
        [age, duration, accessibility]
        + list(preferences.values())
        + [", ".join(top_priorities), wait_time, walking, break_time]
    ]

    sheet.update(f"C{row_num}:P{row_num}", update_values)

    st.success("✅ Submitted! Redirecting to your personalized tour plan...")
    time.sleep(1.5)
    st.switch_page("pages/2_tour_plan.py")
