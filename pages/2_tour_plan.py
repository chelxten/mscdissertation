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

# ------------------------------------------
# 1. Setup attraction data 
# ------------------------------------------
zones = {
    "thrill": ["Roller Coaster", "Drop Tower", "Haunted Mine Train", "Spinning Vortex", "Freefall Cannon"],
    "water": ["Water Slide", "Lazy River", "Log Flume", "Splash Battle", "Wave Pool"],
    "family": ["Bumper Cars", "Mini Ferris Wheel", "Animal Safari Ride", "Ball Pit Dome", "Train Adventure"],
    "entertainment": ["Live Stage", "Street Parade", "Magic Show", "Circus Tent", "Musical Fountain"],
    "food": ["Food Court", "Snack Bar", "Ice Cream Kiosk", "Pizza Plaza", "Smoothie Station"],
    "shopping": ["Souvenir Shop", "Candy Store", "Photo Booth", "Gift Emporium", "Toy World"],
    "relaxation": ["Relaxation Garden", "Shaded Benches", "Quiet Lake View", "Zen Courtyard", "Sky Deck"]
}

attraction_durations = { # keep as your original
    "Roller Coaster": 25, "Drop Tower": 20, "Haunted Mine Train": 20, "Spinning Vortex": 15, "Freefall Cannon": 20,
    "Water Slide": 20, "Lazy River": 25, "Log Flume": 20, "Splash Battle": 15, "Wave Pool": 30,
    "Bumper Cars": 10, "Mini Ferris Wheel": 10, "Animal Safari Ride": 15, "Ball Pit Dome": 15, "Train Adventure": 20,
    "Live Stage": 30, "Street Parade": 25, "Magic Show": 30, "Circus Tent": 30, "Musical Fountain": 20,
    "Food Court": 30, "Snack Bar": 15, "Ice Cream Kiosk": 10, "Pizza Plaza": 25, "Smoothie Station": 10,
    "Souvenir Shop": 10, "Candy Store": 10, "Photo Booth": 10, "Gift Emporium": 15, "Toy World": 15,
    "Relaxation Garden": 20, "Shaded Benches": 10, "Quiet Lake View": 15, "Zen Courtyard": 15, "Sky Deck": 20
}

# ------------------------------------------
# 2. Get Data & Convert Rankings to Weights
# ------------------------------------------
if "questionnaire" not in st.session_state:
    st.warning("❗ Please complete the questionnaire first.")
    st.stop()

data = st.session_state["questionnaire"]

# ✅ Ranks (from questionnaire stored data)
preference_ranks = {
    "thrill": data["thrill"],
    "family": data["family"],
    "water": data["water"],
    "entertainment": data["entertainment"],
    "food": data["food"],
    "shopping": data["shopping"],
    "relaxation": data["relaxation"]
}

# ✅ Convert ranks to weights → Rank 1 = weight 7; Rank 7 = weight 1
preferences = {k: 8 - v for k, v in preference_ranks.items()}

priorities = data["priorities"]
walking_pref = data["walking"]
break_pref = data["break"]

duration_map = {
    "<2 hrs": 90, "2–4 hrs": 180, "4–6 hrs": 300, "All day": 420
}
visit_duration = duration_map.get(data["duration"], 180)

# ------------------------------------------
# 3. Allocate Time (Main Algorithm)
# ------------------------------------------
def allocate_park_time(total_time, preferences, priorities, walking_pref):
    attraction_times, remaining_time = {}, total_time

    zone_penalty = {}
    if walking_pref == "Very short distances":
        zone_penalty = {"water": 0.6, "relaxation": 0.8}
    elif walking_pref == "Moderate walking":
        zone_penalty = {"water": 0.8}

    total_weight = sum(preferences.values())
    weights = {
        zone: preferences[zone] / total_weight * zone_penalty.get(zone, 1)
        for zone in zones
    }

    # ✅ Apply fuzzy modifiers based on user priorities
    if "Enjoying high-intensity rides" in priorities: weights["thrill"] *= 1.2
    if "Visiting family-friendly attractions together" in priorities: weights["family"] *= 1.2
    if "Staying comfortable throughout the visit" in priorities: weights["relaxation"] *= 1.3; weights["entertainment"] *= 1.1
    if "Having regular food and rest breaks" in priorities: weights["food"] *= 1.2; weights["relaxation"] *= 1.1

    # Normalize again
    total_weight = sum(weights.values())
    weights = {k: v / total_weight for k, v in weights.items()}

    # Time allocation loop
    for zone, attractions in zones.items():
        zone_time = weights[zone] * total_time
        for attraction in attractions:
            duration = attraction_durations[attraction]
            if remaining_time >= duration:
                attraction_times[attraction] = duration
                remaining_time -= duration

    return attraction_times, remaining_time

# ------------------------------------------
# 4. Generate Tour Plan
# ------------------------------------------
attraction_times, leftover = allocate_park_time(visit_duration, preferences, priorities, walking_pref)

def generate_navigation_order(attraction_times):
    return ["Entrance"] + list(attraction_times.keys())

def insert_breaks(route, break_pref):
    updated, counter = [], 0
    for stop in route:
        updated.append(stop)
        counter += attraction_durations.get(stop, 10)
        if break_pref == "After every big ride" and stop in ["Roller Coaster", "Drop Tower", "Log Flume", "Water Slide"]:
            updated.append("Break")
        elif break_pref in ["After 1 hour", "After 2 hours"]:
            limit = 60 if break_pref == "After 1 hour" else 120
            if counter >= limit:
                updated.append("Break")
                counter = 0
    return updated

route = generate_navigation_order(attraction_times)
final_plan = insert_breaks(route, break_pref)

# ------------------------------------------
# 5. Display Output
# ------------------------------------------
zone_emojis = {
    "thrill": "🎢", "water": "💦", "family": "👨‍👩‍👧‍👦",
    "entertainment": "🎭", "food": "🍔", "shopping": "🛍️", "relaxation": "🌳"
}

st.success(f"""
👤 **Age**: {data['age']}  
⏳ **Visit Duration**: {visit_duration} minutes  
🚶‍♂️ **Walking Preference**: {walking_pref}  
🛑 **Break Preference**: {break_pref}  
""")

with st.expander("🗺️ Route Plan", expanded=True):
    st.subheader("Your Personalized Route")
    cumulative_time = 0
    for stop in final_plan:
        if stop == "Break":
            st.markdown("🛑 **Break** – Recharge!")
        elif stop == "Entrance":
            st.markdown("🏁 **Entrance** – Start your adventure")
        else:
            zone = next(z for z, a in zones.items() if stop in a)
            emoji = zone_emojis[zone]
            duration = attraction_durations[stop]
            cumulative_time += duration
            st.markdown(f"{emoji} **{stop}** — {duration} mins (Total: {cumulative_time} mins)")

with st.expander("🕒 Leftover Time"):
    st.info(f"Leftover Time: **{leftover} minutes** to revisit or relax.")

# ✅ Save plan for download
plan_text = "Your Personalized Amusement Park Tour Plan\n\n"
plan_text += f"Visit Duration: {visit_duration} minutes\nWalking Preference: {walking_pref}\nBreak Preference: {break_pref}\n\n"
plan_text += "Planned Route:\n"
for stop in final_plan:
    if stop == "Break": plan_text += "- Break\n"
    elif stop == "Entrance": plan_text += "- Entrance\n"
    else: plan_text += f"- {stop} ({attraction_durations[stop]} mins)\n"
plan_text += f"\nEstimated Time Used: {sum(attraction_times.values())} minutes\nLeftover Time: {leftover} minutes\n"
st.session_state.tour_plan = plan_text
