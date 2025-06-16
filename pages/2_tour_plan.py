import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import math

# ✅ Google Sheets function for feedback update
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
# 1. Load Data from Session
# ------------------------------------------
if "questionnaire" not in st.session_state:
    st.warning("❗ Please complete the questionnaire first.")
    st.stop()

data = st.session_state["questionnaire"]

# Extract user answers
preference_ranks = {
    "thrill": data["thrill"], "family": data["family"], "water": data["water"],
    "entertainment": data["entertainment"], "food": data["food"],
    "shopping": data["shopping"], "relaxation": data["relaxation"]
}
preferences = {k: 8 - v for k, v in preference_ranks.items()}
priorities = data["priorities"]
walking_pref = data["walking"]
break_pref = data["break"]

duration_map = {"<2 hrs": 90, "2–4 hrs": 180, "4–6 hrs": 300, "All day": 420}
visit_duration = duration_map.get(data["duration"], 180)

# ------------------------------------------
# 2. Zones, Attractions & Coordinates Setup
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

zone_coordinates = {
    "thrill": (100, 400), "water": (400, 400), "family": (100, 100),
    "entertainment": (400, 100), "food": (250, 250), "shopping": (300, 300), "relaxation": (200, 200)
}

attraction_coordinates = {}
for zone, attractions in zones.items():
    for idx, attraction in enumerate(attractions):
        offset = idx * 5
        zone_x, zone_y = zone_coordinates[zone]
        attraction_coordinates[attraction] = (zone_x + offset, zone_y + offset)

# ------------------------------------------
# 3. Accessibility, Duration & Wait Times
# ------------------------------------------
accessibility_factors = {
    "thrill": 0.7, "water": 0.8, "family": 1.0,
    "entertainment": 0.9, "food": 1.0, "shopping": 1.0, "relaxation": 1.0
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

attraction_wait_times = {
    "Roller Coaster": 20, "Drop Tower": 15, "Water Slide": 10, "Lazy River": 12, "Log Flume": 18,
    "Haunted Mine Train": 14, "Spinning Vortex": 8, "Freefall Cannon": 10, "Splash Battle": 7, "Wave Pool": 12,
    "Bumper Cars": 5, "Mini Ferris Wheel": 3, "Animal Safari Ride": 6, "Ball Pit Dome": 5, "Train Adventure": 8,
    "Live Stage": 10, "Street Parade": 8, "Magic Show": 12, "Circus Tent": 10, "Musical Fountain": 8,
    "Food Court": 5, "Snack Bar": 3, "Ice Cream Kiosk": 3, "Pizza Plaza": 4, "Smoothie Station": 3,
    "Souvenir Shop": 3, "Candy Store": 3, "Photo Booth": 2, "Gift Emporium": 3, "Toy World": 3,
    "Relaxation Garden": 0, "Shaded Benches": 0, "Quiet Lake View": 0, "Zen Courtyard": 0, "Sky Deck": 0
}

# ------------------------------------------
# 4. Weighted Allocation System (Fuzzy Logic)
# ------------------------------------------
def fuzzy_zone_weight(zone):
    base = preferences[zone] * accessibility_factors[zone]
    if "Visiting family-friendly attractions together" in priorities and zone == "family":
        base *= 1.2
    if "Staying comfortable throughout the visit" in priorities and zone == "relaxation":
        base *= 1.3
    if "Having regular food and rest breaks" in priorities and zone == "food":
        base *= 1.2
    return base

zone_weights = {zone: fuzzy_zone_weight(zone) for zone in zones}
total_weight = sum(zone_weights.values())
normalized_weights = {z: w / total_weight for z, w in zone_weights.items()}

# ------------------------------------------
# 5. Initial Attraction Allocation
# ------------------------------------------
sorted_zones = sorted(normalized_weights, key=lambda z: normalized_weights[z], reverse=True)
initial_attractions = []

for zone in sorted_zones[:4]:
    initial_attractions.append(zones[zone][0])

remaining_time = visit_duration - sum([
    attraction_durations[a] + attraction_wait_times[a] for a in initial_attractions
])

all_candidates = [a for zone in sorted_zones for a in zones[zone] if a not in initial_attractions]

for attraction in all_candidates:
    time_needed = attraction_durations[attraction] + attraction_wait_times[attraction]
    if remaining_time >= time_needed:
        initial_attractions.append(attraction)
        remaining_time -= time_needed

# ------------------------------------------
# 6. Greedy Route Optimization
# ------------------------------------------
def calculate_distance(point_a, point_b):
    # point_a or point_b can be either attraction name or coordinates
    if isinstance(point_a, str):
        point_a = attraction_coordinates[point_a]
    if isinstance(point_b, str):
        point_b = attraction_coordinates[point_b]

    x1, y1 = point_a
    x2, y2 = point_b
    return math.hypot(x2 - x1, y2 - y1)

def greedy_route(attractions):
    route = []
    current = (0, 0)  # Entrance
    pool = attractions.copy()
    while pool:
        next_attraction = min(pool, key=lambda a: calculate_distance(current, attraction_coordinates[a]))
        route.append(next_attraction)
        current = attraction_coordinates[next_attraction]
        pool.remove(next_attraction)
    return route

final_route = greedy_route(initial_attractions)

# ------------------------------------------
# 7. Break Insertion
# ------------------------------------------
def insert_breaks(route):
    updated = []
    elapsed = 0
    for stop in route:
        updated.append(stop)
        elapsed += attraction_durations[stop] + attraction_wait_times[stop]

        if break_pref == "After 1 hour" and elapsed >= 60:
            updated.append("Break")
            elapsed = 0
        elif break_pref == "After 2 hours" and elapsed >= 120:
            updated.append("Break")
            elapsed = 0
        elif break_pref == "After every big ride" and stop in ["Roller Coaster", "Drop Tower", "Log Flume", "Water Slide"]:
            updated.append("Break")
    return updated

final_plan = insert_breaks(final_route)

# ------------------------------------------
# 8. Display & Time Calculation with Walks
# ------------------------------------------
zone_emojis = {
    "thrill": "🎢", "water": "💦", "family": "👨‍👩‍👧‍👦",
    "entertainment": "🎭", "food": "🍔", "shopping": "🛍️", "relaxation": "🌳"
}

walking_speed = 67  # meters/min
total_time_used = 0
previous_location = (0, 0)

plan_text_lines = []
with st.expander("🗺️ Your Route", expanded=True):
    for stop in final_plan:
        if stop == "Break":
            total_time_used += 15
            plan_text_lines.append("Break — 15 mins")
            st.markdown("🛑 **Break — 15 mins**")
            continue

        zone = next(z for z, a in zones.items() if stop in a)
        emoji = zone_emojis[zone]
        ride_time = attraction_durations[stop]
        wait_time = attraction_wait_times[stop]
        attraction_loc = attraction_coordinates[stop]
        walk_dist = calculate_distance(previous_location, attraction_loc)
        walk_time = walk_dist / walking_speed

        total = ride_time + wait_time + walk_time
        total_time_used += total

        display_text = f"{emoji} **{stop}** — {int(total)} mins total"
        full_text = f"{stop} — {ride_time}m ride + {wait_time}m wait + {int(walk_time)}m walk = {int(total)}m"
        plan_text_lines.append(full_text)
        st.markdown(display_text)

        previous_location = attraction_loc

leftover_time = visit_duration - total_time_used
st.info(f"Total Used: {int(total_time_used)} mins | Leftover: {int(leftover_time)} mins")

sheet.update_cell(row_num, 20, str(int(total_time_used)))  # Column T
sheet.update_cell(row_num, 21, str(int(visit_duration - total_time_used)))  # Column U

# ✅ Store clean plan into both session and Google Sheet:
final_clean_plan = "\n".join(plan_text_lines)
st.session_state.tour_plan = final_clean_plan

uid = st.session_state.get("unique_id")
sheet = get_consent_worksheet()
cell = sheet.find(uid, in_column=2)
row_num = cell.row
sheet.update_cell(row_num, 19, final_clean_plan)

# ------------------------------------------
# 9. Feedback & Rating
# ------------------------------------------
st.subheader("⭐ Feedback")
rating = st.slider("Rate your plan:", 1, 10, 8)
feedback = st.text_area("Comments?")

if st.button("Submit Feedback"):
    try:
        sheet.update_cell(row_num, 17, str(rating))
        sheet.update_cell(row_num, 18, feedback)
        st.session_state.tour_rating = rating
        st.session_state.tour_feedback = feedback
        st.success("✅ Feedback saved!")
        time.sleep(1)
        st.switch_page("pages/3_final_download.py")
    except Exception as e:
        st.error(f"Error saving feedback: {e}")
