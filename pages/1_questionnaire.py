import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from streamlit_sortables import sort_items



st.set_page_config(page_title="Visitor Questionnaire")

st.markdown("""
    <style>
    .sortable-item {
        background-color: #ffffff !important;
        border: 1px solid #dddddd !important;
        border-radius: 8px !important;
        padding: 8px !important;
        color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

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
    
    
    preference_items = [
        "Thrill rides",
        "Family rides",
        "Water rides",
        "Live shows",
        "Food & Dining",
        "Shopping",
        "Relaxation areas"
    ]
    
    with st.container():
        st.markdown("### Please rank your preferences:")

        sorted_preferences = sort_items(preference_items, direction="vertical")

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
    as described in the Participant Information Sheet. If you did not yet download and keep a copy for your records, you may download it now (button below).
    """)

    submit = st.form_submit_button("📩 Submit")

# ✅ Download button OUTSIDE form
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
        "thrill": sorted_preferences.index("Thrill rides") + 1,
        "family": sorted_preferences.index("Family rides") + 1,
        "water": sorted_preferences.index("Water rides") + 1,
        "entertainment": sorted_preferences.index("Live shows") + 1,
        "food": sorted_preferences.index("Food & Dining") + 1,
        "shopping": sorted_preferences.index("Shopping") + 1,
        "relaxation": sorted_preferences.index("Relaxation areas") + 1,
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

    # ✅ Prepare update row: columns C-P
    update_values = [
        [age, duration, accessibility]
        + [
            sorted_preferences.index("Thrill rides") + 1,
            sorted_preferences.index("Family rides") + 1,
            sorted_preferences.index("Water rides") + 1,
            sorted_preferences.index("Live shows") + 1,
            sorted_preferences.index("Food & Dining") + 1,
            sorted_preferences.index("Shopping") + 1,
            sorted_preferences.index("Relaxation areas") + 1,
        ]
        + [", ".join(top_priorities), wait_time, walking, break_time]
    ]

    sheet.update(f"C{row_num}:P{row_num}", update_values)

    st.success("✅ Submitted! Redirecting to your personalized tour plan...")
    time.sleep(1.5)
    st.switch_page("pages/2_tour_plan.py")
