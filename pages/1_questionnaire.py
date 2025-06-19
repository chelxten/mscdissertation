import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from streamlit_sortables import sort_items
import base64

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
        except Exception as e:
            st.warning(f"Google API error: retrying ({attempt+1}/5)...")
            time.sleep(3)
    st.error("Failed to connect after multiple retries.")
    st.stop()

# ✅ Load PIS file for download
@st.cache_resource
def load_pis_file():
    with open("PISPCF.pdf", "rb") as f:
        return f.read()

pis_data = load_pis_file()

# Generate base64-encoded PDF to embed as a hyperlink
b64_pdf = base64.b64encode(pis_data).decode('utf-8')
pdf_link = f'<a href="data:application/pdf;base64,{b64_pdf}" download="PISPCF.pdf">Participant Information Sheet (PDF)</a>'


# ✅ Inject Custom Styles
st.markdown("""
    <style>
    .question-label {
        font-size: 18px !important;
        font-weight: 600;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ✅ Questionnaire Form
with st.form("questionnaire_form"):

    st.markdown('<div class="question-label">1. What is your age group?</div>', unsafe_allow_html=True)
    age = st.selectbox("", ["Under 12", "13–17", "18–30", "31–45", "46–60", "60+"], key="age")

    st.markdown('<div class="question-label">2. Do you have any accessibility needs? (Select all that apply)</div><br>', unsafe_allow_html=True)
    physical = st.checkbox("Physical", key="acc_physical")
    sensory = st.checkbox("Sensory", key="acc_sensory")
    cognitive = st.checkbox("Cognitive", key="acc_cognitive")
    prefer_not = st.checkbox("Prefer not to say", key="acc_prefer")
    no_accessibility = st.checkbox("No Accessibility Needs", key="acc_none")

    if no_accessibility and (physical or sensory or cognitive or prefer_not):
        st.warning("You cannot select 'No Accessibility Needs' together with other options.")

    accessibility_selected = []
    if physical: accessibility_selected.append("Physical")
    if sensory: accessibility_selected.append("Sensory")
    if cognitive: accessibility_selected.append("Cognitive")
    if prefer_not: accessibility_selected.append("Prefer not to say")
    if no_accessibility: accessibility_selected.append("No Accessibility Needs")
    if not accessibility_selected: accessibility_selected = ["Not specified"]
    accessibility_cleaned = ", ".join(accessibility_selected)

    st.markdown('<div class="question-label">3. How long do you plan to stay in the park today?</div>', unsafe_allow_html=True)
    duration = st.selectbox(
        label="",
        options=["<2 hrs", "2–4 hrs", "4–6 hrs", "All day"],
        key="duration"
    )

    st.markdown('<div class="question-label">4. Rank your preferences (drag to reorder)</div>', unsafe_allow_html=True)
    initial_preferences = [
        "Thrill rides",
        "Family rides",
        "Water rides",
        "Live shows",
        "Food & Dining",
        "Shopping",
        "Relaxation areas"
    ]
    sorted_preferences = sort_items(initial_preferences, direction="vertical", key="preferences_sort")

    st.markdown('<div class="question-label">5. What are your top visit priorities? (Select up to 3)</div>', unsafe_allow_html=True)

    top_priorities = st.multiselect(
        label="",
        options=[
            "Enjoying high-intensity rides",
            "Visiting family-friendly attractions together",
            "Seeing as many attractions as possible",
            "Staying comfortable throughout the visit",
            "Having regular food and rest breaks"
        ],
        key="priorities"
    )

    st.markdown('<div class="question-label">6. What is the maximum wait time you are okay with?</div>', unsafe_allow_html=True)
    wait_time = st.slider(
        label="",
        min_value=0,
        max_value=40,
        step=5,
        value=15,
        format="%d min",
        key="wait_time"
    )

    st.markdown('<div class="question-label">7. How far are you willing to walk between attractions?</div>', unsafe_allow_html=True)
    walking = st.radio(
        label="",
        options=["Very short distances", "Moderate walking", "Don’t mind walking"],
        key="walking"
    )

    st.markdown('<div class="question-label">8. When do you prefer to take breaks?</div>', unsafe_allow_html=True)
    break_time = st.radio(
        label="",
        options=["After 1 hour", "After 2 hours", "After every big ride", "Flexible"],
        key="break_time"
    )
    st.markdown(f"""
    ---
    By clicking  **‘Submit’** button below, you are consenting to participate in this study,as it is described in the participant information sheet, which you can download here
    {pdf_link}. If you did not yet download and keep a copy of this document for your records, we recommend you do that now.
    """, unsafe_allow_html=True)

     # Required by Streamlit to properly process the form
    submit = st.form_submit_button("📩 Submit")

    if submit:
        if len(top_priorities) > 3:
            st.warning("Please reduce your selections to 3 or fewer before submitting.")
            st.stop()
        else:
            st.success("✅ Form submitted successfully.")
            # Continue with processing...


# ✅ Handle form submission
if submit:
    st.session_state["questionnaire"] = {
        "age": age,
        "duration": duration,
        "accessibility": accessibility_cleaned,
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

    update_values = [
        [age, duration, accessibility_cleaned]
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
