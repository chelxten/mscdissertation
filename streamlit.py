import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. GSheet Connection
def connect_to_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

@st.cache_resource
def get_worksheet():
    client = connect_to_gsheet()
    sheet = client.open("Amusement Park Survey Responses").sheet1
    return sheet

# 2. Session flags
if "consent_submitted" not in st.session_state:
    st.session_state.consent_submitted = False
if "questionnaire_submitted" not in st.session_state:
    st.session_state.questionnaire_submitted = False

# 3. Info Sheet
with st.expander("📄 Click to View Participant Information Sheet"):
    st.markdown("""
    ### PARTICIPANT INFORMATION SHEET
    **Title:** _The Search of Advanced AI-Powered Service Robots for Amusement Parks_

    **Legal Basis:** This study is under SHU’s ethical research framework. [Research Ethics](https://www.shu.ac.uk/research/excellence/ethics-and-integrity)

    **Invitation & Purpose:** You are invited to explore how AI can enhance service robots in amusement parks.

    **Voluntary Participation:** You may withdraw at any time. All questions must be completed to proceed.

    **Time Commitment:** ~5 minutes.

    **Risks & Benefits:** Low risk. No direct benefit, but responses will improve robotics research. Anonymous data only.

    **Data Use:** Stored securely for up to 5 years, used for MSc dissertation. No personal IDs collected.

    **Contact Info:**  
    Researcher: **Cherry San** – c3065323@hallam.shu.ac.uk  
    Supervisor: **Dr. Samuele Vinanzi** – s.vinanzi@shu.ac.uk
    """, unsafe_allow_html=True)

# 4. Consent Checkbox
consent = st.checkbox("I have read the Participant Information Sheet and agree to take part in this study.")
if not consent:
    st.warning("⚠️ You must agree to the consent checkbox to proceed.")
    st.stop()

# 5. Consent Form
st.header("📝 Participant Consent Form")

st.markdown("**Title of Project:**  \n*The Search of Advanced AI-Powered Service Robots for Amusement Parks*")

questions = [
    "1. I have read the Information Sheet for this study and have had details of the study explained to me.",
    "2. My questions about the study have been answered to my satisfaction and I understand that I may ask further questions at any point.",
    "3. I understand that I am free to withdraw from the study within the time limits outlined in the Information Sheet, without giving a reason for my withdrawal or to decline to answer any particular questions in the study without any consequences to my future treatment by the researcher.",
    "4. I agree to provide information to the researchers under the conditions of confidentiality set out in the Information Sheet.",
    "5. I wish to participate in the study under the conditions set out in the Information Sheet.",
    "6. I consent to the information collected for the purposes of this research study, once anonymised (so that I cannot be identified), to be used for any other research purposes."
]

responses = []
for i, q in enumerate(questions):
    st.markdown(f"**{q}**")
    selected = st.radio("", ["Yes", "No"], key=f"q{i}", index=None)
    responses.append(selected)

st.markdown("**Participant Information:**")
participant_name = st.text_input("Full Name", value="")
participant_signature = st.text_input("Signature (type your name)", value="")
participant_date = st.date_input("Date")
participant_contact = st.text_input("Contact Details (optional)", value="")

st.markdown("---")
st.markdown("**Researcher’s Information:**")
st.markdown("**Name:** Cherry San  \n**Email:** c3065323@hallam.shu.ac.uk  \n**Course:** MSc Artificial Intelligence")

if st.button("✅ Submit Consent Form"):
    if all(r == "Yes" for r in responses) and None not in responses and participant_name.strip() and participant_signature.strip():
        st.session_state.consent_submitted = True
        st.success("✅ Consent form submitted. Thank you for participating.")
        st.rerun()
    else:
        st.error("⚠️ Please agree to all statements and fill in all required participant fields before submitting.")

# 9. Questionnaire - only shown if consent submitted
if st.session_state.consent_submitted:
    st.header("🎡 Visitor Questionnaire")

    with st.form("questionnaire"):
        st.subheader("About You")
        age_group = st.selectbox("What is your age group?", ["Under 12", "13–17", "18–30", "31–45", "46–60", "60+"])
        gender = st.selectbox("What is your gender?", ["Male", "Female", "Non-binary", "Prefer not to say"])
        visit_group = st.selectbox("Who are you visiting with?", ["Alone", "With family", "With friends", "With young children", "With a partner"])
        duration = st.selectbox("How long do you plan to stay in the park today?", ["Less than 2 hours", "2–4 hours", "4–6 hours", "All day"])

        st.subheader("Your Preferences (1 to 10)")
        preferences = {
            "thrill": st.slider("Thrill rides", 1, 10, 5),
            "family": st.slider("Family rides", 1, 10, 5),
            "water": st.slider("Water rides", 1, 10, 5),
            "entertainment": st.slider("Live shows", 1, 10, 5),
            "food": st.slider("Food & dining", 1, 10, 5),
            "shopping": st.slider("Shopping", 1, 10, 5),
            "relaxation": st.slider("Relaxation zones", 1, 10, 5)
        }

        st.subheader("Most Important to You (Choose up to 3)")
        priorities = st.multiselect(
            "Select priorities:",
            ["Enjoying high-intensity rides", "Visiting family-friendly attractions", "Seeing many attractions", "Staying comfortable", "Having food/rest breaks"]
        )

        st.subheader("Accessibility & Comfort")
        wait_time = st.selectbox("Max time you're willing to wait in line:", ["<10 min", "10–20 min", "20–30 min", "30+ min"])
        walking = st.selectbox("Walking comfort:", ["Very short", "Moderate", "I don’t mind walking"])
        crowd_sensitivity = st.selectbox("Crowd sensitivity:", ["Very uncomfortable", "Slightly uncomfortable", "Neutral", "Comfortable"])
        break_time = st.selectbox("Preferred break time:", ["After 1 hour", "After 2 hours", "After every big ride", "I decide as I go"])

        submit = st.form_submit_button("Get My Personalized Plan")

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


    
# --------------------------
# 🎢 FUZZY LOGIC TOUR PLANNER
# --------------------------

# 1. Attraction Setup
zones = {
    "thrill": ["Roller Coaster", "Drop Tower", "Haunted Mine Train", "Spinning Vortex", "Freefall Cannon"],
    "water": ["Water Slide", "Lazy River", "Log Flume", "Splash Battle", "Wave Pool"],
    "family": ["Bumper Cars", "Mini Ferris Wheel", "Animal Safari Ride", "Ball Pit Dome", "Train Adventure"],
    "entertainment": ["Live Stage", "Street Parade", "Magic Show", "Circus Tent", "Musical Fountain"],
    "food": ["Food Court", "Snack Bar", "Ice Cream Kiosk", "Pizza Plaza", "Smoothie Station"],
    "shopping": ["Souvenir Shop", "Candy Store", "Photo Booth", "Gift Emporium", "Toy World"],
    "relaxation": ["Relaxation Garden", "Shaded Benches", "Quiet Lake View", "Zen Courtyard", "Sky Deck"]
}

attraction_durations = {
    "Roller Coaster": 25, "Drop Tower": 20, "Haunted Mine Train": 20, "Spinning Vortex": 15, "Freefall Cannon": 20,
    "Water Slide": 20, "Lazy River": 25, "Log Flume": 20, "Splash Battle": 15, "Wave Pool": 30,
    "Bumper Cars": 10, "Mini Ferris Wheel": 10, "Animal Safari Ride": 15, "Ball Pit Dome": 15, "Train Adventure": 20,
    "Live Stage": 30, "Street Parade": 25, "Magic Show": 30, "Circus Tent": 30, "Musical Fountain": 20,
    "Food Court": 30, "Snack Bar": 15, "Ice Cream Kiosk": 10, "Pizza Plaza": 25, "Smoothie Station": 10,
    "Souvenir Shop": 10, "Candy Store": 10, "Photo Booth": 10, "Gift Emporium": 15, "Toy World": 15,
    "Relaxation Garden": 20, "Shaded Benches": 10, "Quiet Lake View": 15, "Zen Courtyard": 15, "Sky Deck": 20
}

popularity_scores = {
    "Roller Coaster": 9, "Drop Tower": 8, "Haunted Mine Train": 7, "Spinning Vortex": 6, "Freefall Cannon": 8,
    "Water Slide": 9, "Lazy River": 7, "Log Flume": 8, "Splash Battle": 6, "Wave Pool": 8,
    "Bumper Cars": 6, "Mini Ferris Wheel": 4, "Animal Safari Ride": 5, "Ball Pit Dome": 5, "Train Adventure": 6,
    "Live Stage": 6, "Street Parade": 7, "Magic Show": 8, "Circus Tent": 7, "Musical Fountain": 6,
    "Food Court": 9, "Snack Bar": 6, "Ice Cream Kiosk": 7, "Pizza Plaza": 8, "Smoothie Station": 6,
    "Souvenir Shop": 7, "Candy Store": 6, "Photo Booth": 5, "Gift Emporium": 6, "Toy World": 7,
    "Relaxation Garden": 4, "Shaded Benches": 3, "Quiet Lake View": 2, "Zen Courtyard": 3, "Sky Deck": 5
}

# 2. Allocation Function
def allocate_park_time(total_time, preferences, priorities, walking_pref, crowd_sensitivity):
    attraction_times = {}
    remaining_time = total_time

    zone_penalty = {}
    if walking_pref == "Very short":
        zone_penalty = {"water": 0.6, "relaxation": 0.8}
    elif walking_pref == "Moderate":
        zone_penalty = {"water": 0.8}

    total_weight = sum(preferences.values())
    weights = {
        zone: preferences[zone] / total_weight * zone_penalty.get(zone, 1)
        for zone in zones
    }

    if "Enjoying high-intensity rides" in priorities:
        weights["thrill"] *= 1.2
    if "Visiting family-friendly attractions" in priorities:
        weights["family"] *= 1.2
    if "Staying comfortable" in priorities:
        weights["relaxation"] *= 1.3
        weights["entertainment"] *= 1.1
    if "Having food/rest breaks" in priorities:
        weights["food"] *= 1.2
        weights["relaxation"] *= 1.1

    QUICK_MODE = "Seeing many attractions" in priorities
    weights = {k: v / sum(weights.values()) for k, v in weights.items()}

    for zone, attractions in zones.items():
        zone_time = weights[zone] * total_time
        for attraction in attractions:
            pop = popularity_scores.get(attraction, 5)
            if crowd_sensitivity == "Very uncomfortable" and pop >= 7:
                continue
            if crowd_sensitivity == "Slightly uncomfortable" and pop >= 8 and preferences[zone] < 8:
                continue

            duration = attraction_durations[attraction]
            time_spent = min(duration, 15) if QUICK_MODE else duration

            if remaining_time >= time_spent:
                attraction_times[attraction] = time_spent
                remaining_time -= time_spent

    while remaining_time >= 5:
        for attraction in attraction_times:
            addition = min(5, remaining_time)
            attraction_times[attraction] += addition
            remaining_time -= addition
            if remaining_time < 5:
                break

    return attraction_times, remaining_time

# 3. Routing
def generate_navigation_order(attraction_times):
    return ["Entrance"] + list(attraction_times.keys())

def insert_breaks(route, break_preference):
    updated_route = []
    time_counter = 0

    for stop in route:
        updated_route.append(stop)
        time_counter += attraction_durations.get(stop, 10)

        if break_preference == "After every big ride" and stop in ["Roller Coaster", "Drop Tower", "Log Flume", "Water Slide"]:
            updated_route.append("Break")
        elif break_preference == "After 1 hour" and time_counter >= 60:
            updated_route.append("Break")
            time_counter = 0
        elif break_preference == "After 2 hours" and time_counter >= 120:
            updated_route.append("Break")
            time_counter = 0

    return updated_route

# 4. Generate and Show the Plan
if duration == "All day":
    visit_time = 240
elif "Less than" in duration:
    visit_time = 90  # Default estimate for short visits
else:
    try:
        visit_time = 60 * int(duration.split("-")[0].strip())
    except Exception:
        visit_time = 180  # Default fallback
attraction_times, leftover_time = allocate_park_time(
    total_time=visit_time,
    preferences=preferences,
    priorities=priorities,
    walking_pref=walking,
    crowd_sensitivity=crowd_sensitivity
)
route = generate_navigation_order(attraction_times)
final_plan = insert_breaks(route, break_time)

st.subheader("🎯 Your Personalized Plan")
st.markdown("Here is your customized route including breaks:")

for step in final_plan:
    if step == "Break":
        st.markdown("☕ **Break Time**")
    else:
        st.markdown(f"🎡 **{step}** – {attraction_times.get(step, 'N/A')} min")

st.markdown(f"🕒 Estimated Total Duration: **{visit_time - leftover_time} minutes**")
