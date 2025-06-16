import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials


@st.cache_resource
def get_consent_worksheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Survey Responses").worksheet("Sheet1")
    return sheet
    
st.set_page_config(page_title="Personalized Tour Plan")

st.image("Sheffield-Hallam-University.png", width=250)
st.title("🎢 Your Personalized Tour Plan")

# --------------------------
# 1. SETUP: Zones, Durations, Popularity
# --------------------------

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

# --------------------------
# 2. GET DATA + RANKING-BASED PREFERENCES (This is updated)
# --------------------------

if "questionnaire" not in st.session_state:
    st.warning("❗ Please complete the questionnaire first.")
    st.stop()

data = st.session_state["questionnaire"]

st.write("Thanks for your input! Here’s a preview of how we’ll personalize your visit:")

# ✅ REBUILD preferences based on ranking position (Rank 1 → Weight 7, Rank 7 → Weight 1)
preference_ranks = {
    "thrill": data["thrill"],
    "family": data["family"],
    "water": data["water"],
    "entertainment": data["entertainment"],
    "food": data["food"],
    "shopping": data["shopping"],
    "relaxation": data["relaxation"]
}

preferences = {k: 8 - v for k, v in preference_ranks.items()}

priorities = data["priorities"]
walking_pref = data["walking"]
break_pref = data["break"]

duration_map = {
    "<2 hrs": 90, "2–4 hrs": 180, "4–6 hrs": 300, "All day": 420
}
visit_duration = duration_map.get(data["duration"], 180)


# --------------------------
# 3. TIME ALLOCATION FUNCTION
# --------------------------

def allocate_park_time(total_time, preferences, walking_pref):
    attraction_times = {}
    remaining_time = total_time

    # Apply walking penalties if needed
    zone_penalty = {}
    if walking_pref == "Very short distances":
        zone_penalty = {"water": 0.6, "relaxation": 0.8}
    elif walking_pref == "Moderate walking":
        zone_penalty = {"water": 0.8}

    # Apply base weights from preferences (sortable ranking)
    total_weight = sum(preferences.values())
    weights = {
        zone: (preferences[zone] / total_weight) * zone_penalty.get(zone, 1)
        for zone in zones
    }

    # Normalize weights again
    total_weight = sum(weights.values())
    weights = {k: v / total_weight for k, v in weights.items()}

    # Allocate time across zones based on weights
    for zone, attractions in zones.items():
        zone_time = weights[zone] * total_time
        for attraction in attractions:
            duration = attraction_durations[attraction]
            if remaining_time >= duration:
                attraction_times[attraction] = duration
                remaining_time -= duration

    # Use leftover time to top-up
    while remaining_time >= 5:
        for attraction in attraction_times:
            addition = min(5, remaining_time)
            attraction_times[attraction] += addition
            remaining_time -= addition
            if remaining_time < 5:
                break

    return attraction_times, remaining_time

# --------------------------
# 4. GENERATE ROUTE + BREAKS
# --------------------------

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

        elif break_preference in ["After 1 hour", "After 2 hours"]:
            limit = 60 if break_preference == "After 1 hour" else 120
            if time_counter >= limit:
                updated_route.append("Break")
                time_counter = 0

    return updated_route


preferences = {
    "thrill": data["thrill"],
    "family": data["family"],
    "water": data["water"],
    "entertainment": data["entertainment"],
    "food": data["food"],
    "shopping": data["shopping"],
    "relaxation": data["relaxation"]
}

priorities = data["priorities"]
walking_pref = data["walking"]
break_pref = data["break"]

duration_map = {
    "<2 hrs": 90,
    "2–4 hrs": 180,
    "4–6 hrs": 300,
    "All day": 420
}
visit_duration = duration_map.get(data["duration"], 180)

attraction_times, leftover = allocate_park_time(
    visit_duration, preferences, walking_pref
)
route = generate_navigation_order(attraction_times)
final_plan = insert_breaks(route, break_pref)

zone_emojis = {
    "thrill": "🎢",
    "water": "💦",
    "family": "👨‍👩‍👧‍👦",
    "entertainment": "🎭",
    "food": "🍔",
    "shopping": "🛍️",
    "relaxation": "🌳"
}

with st.container():
    st.success(f"""
    👤 **Age**: {data['age']}  
    ⏳ **Visit Duration**: {visit_duration} minutes  
    🚶‍♂️ **Walking Preference**: {walking_pref}  
    🛑 **Break Preference**: {break_pref}  
    """)

with st.expander("🗺️ Route with Breaks", expanded=True):
    st.subheader("Your Route Timeline")
    cumulative_time = 0
    for stop in final_plan:
        if stop == "Break":
            st.markdown("🛑 **Break** – Recharge and relax!")
        elif stop == "Entrance":
            st.markdown("🏁 **Entrance** – Start your adventure")
        else:
            zone = next((z for z, a in zones.items() if stop in a), "")
            emoji = zone_emojis.get(zone, "🎡")
            duration = attraction_durations.get(stop, 10)
            cumulative_time += duration
            st.markdown(f"{emoji} **{stop}** – Approx. {duration} mins (⏱️ ~{cumulative_time} mins in)")

with st.expander("⏱️ Time Allocation", expanded=False):
    total_time = sum(attraction_times.values())
    for attraction, time in attraction_times.items():
        zone = next((z for z, a in zones.items() if attraction in a), "")
        icon = zone_emojis.get(zone, "🎡")
        pct = time / total_time
        st.markdown(f"{icon} **{attraction}**: {time} min ({round(pct*100)}%)")
        st.progress(pct)

with st.expander("🕒 Leftover Time"):
    st.info(f"You have **{leftover} minutes** remaining. You can revisit your favorite attractions or relax.")

# Save final plan to session_state for download in 3_final_download
plan_text = "Your Personalized Amusement Park Tour Plan\n\n"
plan_text += f"Visitor Age Group: {data['age']}\n"
plan_text += f"Visit Duration: {visit_duration} minutes\n"
plan_text += f"Walking Preference: {walking_pref}\n"
plan_text += f"Break Preference: {break_pref}\n\n"
plan_text += "Planned Route:\n"
for stop in final_plan:
    if stop == "Break":
        plan_text += "- 🛑 Break\n"
    elif stop == "Entrance":
        plan_text += "- 🏁 Entrance\n"
    else:
        zone = next((z for z, a in zones.items() if stop in a), "")
        emoji = zone_emojis.get(zone, "🎡")
        duration = attraction_durations.get(stop, 10)
        plan_text += f"- {emoji} {stop} ({duration} mins)\n"

plan_text += f"\nEstimated Time Used: {sum(attraction_times.values())} minutes\n"
plan_text += f"Leftover Time: {leftover} minutes\n"

# ✅ Store in session_state for download
st.session_state.tour_plan = plan_text

def update_rating_feedback_sheet(uid, rating, feedback):
    sheet = get_consent_worksheet()  # ✅ Correct function

    try:
        cell = sheet.find(uid, in_column=2)  # UID in column B
        row_num = cell.row

        sheet.update_cell(row_num, 17, str(rating))  # Column Q
        sheet.update_cell(row_num, 18, feedback)     # Column R
        st.success("✅ Feedback saved to Google Sheet!")
    except Exception as e:
        st.error(f"❌ Error updating feedback: {e}")
    
# --------------------------
# 4. FEEDBACK SECTION (Updated)
# --------------------------
st.subheader("⭐ Rate and Feedback")

st.markdown("Please rate your personalized tour plan and share your thoughts:")

rating = st.slider("How satisfied are you with the plan?", min_value=1, max_value=10, value=8, format="%d ⭐")

feedback = st.text_area("Any comments, suggestions, or things you liked/disliked?", placeholder="Your feedback here...")

if st.button("Submit Feedback"):
    st.success("✅ Thank you! Redirecting you to the download page...")

    st.session_state.tour_rating = rating
    st.session_state.tour_feedback = feedback

    uid = st.session_state.get("unique_id")
    if uid:
        update_rating_feedback_sheet(uid, rating, feedback)

    st.switch_page("pages/3_final_download.py")
