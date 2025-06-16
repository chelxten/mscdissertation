import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from streamlit_sortables import sort_items

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

    retries = 5
    for attempt in range(retries):
        try:
            sheet = client.open("Survey Responses").worksheet("Sheet1")
            return sheet
        except APIError as e:
            if "Visibility check was unavailable" in str(e):
                st.warning(f"Google API 503 error, retrying... ({attempt+1}/{retries})")
                time.sleep(3)
            else:
                raise e

    st.error("Failed after multiple retries.")
    st.stop()

# ✅ Load PIS file for download
@st.cache_resource
def load_pis_file():
    with open("PISPCF.pdf", "rb") as f:
        return f.read()

pis_data = load_pis_file()

# ✅ Questionnaire form
with st.form("questionnaire_form"):
    age = st.selectbox("What is your age group?", ["Under 12", "13–17", "18–30", "31–45", "46–60", "60+"])
    st.markdown("Do you have any accessibility needs? (Select all that apply)")

    # Checkbox group
    physical = st.checkbox("Physical")
    sensory = st.checkbox("Sensory")
    cognitive = st.checkbox("Cognitive")
    prefer_not = st.checkbox("Prefer not to say")
    no_accessibility = st.checkbox("No Accessibility Needs")

    # ✅ Clean logic: prevent conflicting answers
    if no_accessibility and (physical or sensory or cognitive or prefer_not):
        st.warning("You cannot select 'No Accessibility Needs' together with other options.")

    # ✅ Convert to list for storage
    accessibility_selected = []
    if physical:
        accessibility_selected.append("Physical")
    if sensory:
        accessibility_selected.append("Sensory")
    if cognitive:
        accessibility_selected.append("Cognitive")
    if prefer_not:
        accessibility_selected.append("Prefer not to say")
    if no_accessibility:
        accessibility_selected.append("No Accessibility Needs")

    # ✅ Fallback if nothing selected
    if not accessibility_selected:
        accessibility_selected = ["Not specified"]

    # ✅ Final string for database
    accessibility_cleaned = ", ".join(accessibility_selected)

    duration = st.selectbox("How long do you plan to stay in the park today?", ["<2 hrs", "2–4 hrs", "4–6 hrs", "All day"])
    
    # Instead of the previous preferences sliders
    st.markdown("### Please rank the following experiences (1 = most important, 7 = least important)")

    # Build editable ranking table
    ranking_data = {
        "Experience": [
            "Thrill rides",
            "Family rides",
            "Water rides",
            "Live shows",
            "Food & Dining",
            "Shopping",
            "Relaxation areas"
        ],
        "Rank (1-7)": [1, 2, 3, 4, 5, 6, 7]  # default starting values
    }

    ranking_df = st.data_editor(ranking_data, num_rows="fixed")

    # ✅ After form submit: Validate rankings
    # (check that values are unique and 1-7)

    if len(set(ranking_df["Rank (1-7)"])) != 7 or not all(1 <= int(r) <= 7 for r in ranking_df["Rank (1-7)"]):
        st.error("❗ Please make sure all ranks are unique and between 1 and 7.")
        st.stop()

    # ✅ Store preferences as dictionary for further processing
    preferences = {
        row["Experience"]: int(row["Rank (1-7)"])
        for idx, row in ranking_df.iterrows()
    }

    preference_mapping = {
            "Thrill rides": "thrill",
            "Family rides": "family",
            "Water rides": "water",
            "Live shows": "entertainment",
            "Food & Dining": "food",
            "Shopping": "shopping",
            "Relaxation areas": "relaxation"
        }

    preferences_mapped = {preference_mapping[k]: v for k, v in preferences.items()}


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
        "accessibility": accessibility_cleaned,
        **preferences_mapped,
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
        [age, duration, accessibility_cleaned]
        + list(preferences_mapped.values())
        + [", ".join(top_priorities), wait_time, walking, break_time]
    ]

    sheet.update(f"C{row_num}:P{row_num}", update_values)

    st.success("✅ Submitted! Redirecting to your personalized tour plan...")
    time.sleep(1.5)
    st.switch_page("pages/2_tour_plan.py")
