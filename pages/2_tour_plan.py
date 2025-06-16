import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import random

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
preferences = {k: 8 - v for k, v in preference_ranks.items()}  # Convert ranks to weights
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
        offset = idx * 5  # slight offset per attraction
        zone_x, zone_y = zone_coordinates[zone]
        attraction_coordinates[attraction] = (zone_x + offset, zone_y + offset)

# ------------------------------------------
# 3. Accessibility Constraints
# ------------------------------------------

accessibility_factors = {
    "thrill": 0.7, "water": 0.8, "family": 1.0,
    "entertainment": 0.9, "food": 1.0, "shopping": 1.0, "relaxation": 1.0
}

# ------------------------------------------
# 4. Ride Durations & Wait Times
# ------------------------------------------

attraction_durations = {   # minutes per ride
    "Roller Coaster": 25, "Drop Tower": 20, "Haunted Mine Train": 20, "Spinning Vortex": 15, "Freefall Cannon": 20,
    "Water Slide": 20, "Lazy River": 25, "Log Flume": 20, "Splash Battle": 15, "Wave Pool": 30,
    "Bumper Cars": 10, "Mini Ferris Wheel": 10, "Animal Safari Ride": 15, "Ball Pit Dome": 15, "Train Adventure": 20,
    "Live Stage": 30, "Street Parade": 25, "Magic Show": 30, "Circus Tent": 30, "Musical Fountain": 20,
    "Food Court": 30, "Snack Bar": 15, "Ice Cream Kiosk": 10, "Pizza Plaza": 25, "Smoothie Station": 10,
    "Souvenir Shop": 10, "Candy Store": 10, "Photo Booth": 10, "Gift Emporium": 15, "Toy World": 15,
    "Relaxation Garden": 20, "Shaded Benches": 10, "Quiet Lake View": 15, "Zen Courtyard": 15, "Sky Deck": 20
}

attraction_wait_times = {  # minutes of wait
    "Roller Coaster": 20, "Drop Tower": 15, "Water Slide": 10, "Lazy River": 12, "Log Flume": 18,
    "Haunted Mine Train": 14, "Spinning Vortex": 8, "Freefall Cannon": 10, "Splash Battle": 7, "Wave Pool": 12,
    "Bumper Cars": 5, "Mini Ferris Wheel": 3, "Animal Safari Ride": 6, "Ball Pit Dome": 5, "Train Adventure": 8,
    "Live Stage": 10, "Street Parade": 8, "Magic Show": 12, "Circus Tent": 10, "Musical Fountain": 8,
    "Food Court": 5, "Snack Bar": 3, "Ice Cream Kiosk": 3, "Pizza Plaza": 4, "Smoothie Station": 3,
    "Souvenir Shop": 3, "Candy Store": 3, "Photo Booth": 2, "Gift Emporium": 3, "Toy World": 3,
    "Relaxation Garden": 0, "Shaded Benches": 0, "Quiet Lake View": 0, "Zen Courtyard": 0, "Sky Deck": 0
}

# ------------------------------------------
# 5. Distance Calculator
# ------------------------------------------

def calculate_distance(a, b):
    if isinstance(a, str): a = attraction_coordinates[a]
    if isinstance(b, str): b = attraction_coordinates[b]
    return ((a[0] - b[0])**2 + (a[1] - b[1])**2) ** 0.5

# ------------------------------------------
# 6. Fuzzy Allocation Engine (Master Formula)
# ------------------------------------------

def fuzzy_zone_weight(zone):
    base = preferences[zone]
    base *= accessibility_factors[zone]
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
# 7. Allocation Logic: Start from top zones
# ------------------------------------------

# Allocate attractions: Start by assigning one attraction from top 4 zones
sorted_zones = sorted(normalized_weights, key=lambda z: normalized_weights[z], reverse=True)

# Build initial list:
initial_attractions = []
for zone in sorted_zones[:4]:
    initial_attractions.append(zones[zone][0])  # always take first ride as placeholder

remaining_time = visit_duration - sum([
    attraction_durations[a] + attraction_wait_times[a] for a in initial_attractions
])

# Fill additional attractions based on remaining time:
all_candidates = [a for zone in sorted_zones for a in zones[zone] if a not in initial_attractions]

for attraction in all_candidates:
    time_needed = attraction_durations[attraction] + attraction_wait_times[attraction]
    if remaining_time >= time_needed:
        initial_attractions.append(attraction)
        remaining_time -= time_needed

# ------------------------------------------
# 8. Break Planner (simplified, smart version)
# ------------------------------------------

# 8. Smarter Break Planner
def insert_breaks(route):
    updated = []
    elapsed_time = 0
    walked_distance = 0
    prev = (0, 0)

    for stop in route:
        updated.append(stop)

        attraction_coord = attraction_coordinates[stop]
        walk_distance = calculate_distance(prev, attraction_coord)
        walked_distance += walk_distance

        ride_time = attraction_durations[stop]
        wait_time = attraction_wait_times[stop]
        total_time = ride_time + wait_time
        elapsed_time += total_time

        # Insert breaks (time-based + distance-based fatigue)
        if break_pref == "After 1 hour" and elapsed_time >= 60:
            updated.append("Break")
            elapsed_time = 0
            walked_distance = 0
        elif break_pref == "After 2 hours" and elapsed_time >= 120:
            updated.append("Break")
            elapsed_time = 0
            walked_distance = 0
        elif walked_distance >= 700:
            updated.append("Break")
            elapsed_time = 0
            walked_distance = 0

        prev = attraction_coord

    return updated

# ------------------------------------------
# 9. Weighted A* Route (simple zone approximation for now)
# ------------------------------------------

def greedy_route(attractions):
    route = []
    current = (0, 0)  # Entrance at (0,0)
    pool = attractions.copy()

    while pool:
        next_attraction = min(pool, key=lambda a: calculate_distance(current, attraction_coordinates[a]))
        route.append(next_attraction)
        current = attraction_coordinates[next_attraction]
        pool.remove(next_attraction)
    return route

final_route = greedy_route(initial_attractions)

final_plan = insert_breaks(final_route)

# ------------------------------------------
# 10. Display Plan (Rewritten with total time calculation)
# ------------------------------------------

zone_emojis = {
    "thrill": "🎢", "water": "💦", "family": "👨‍👩‍👧‍👦",
    "entertainment": "🎭", "food": "🍔", "shopping": "🛍️", "relaxation": "🌳"
}

def calculate_distance(coord1, coord2):
    dx = coord1[0] - coord2[0]
    dy = coord1[1] - coord2[1]
    return (dx**2 + dy**2) ** 0.5

# Walking speed constant (meters per minute)
walking_speed = 67  # ~4 km/h

st.success(f"""
👤 **Age**: {data['age']}  
⏳ **Visit Duration**: {visit_duration} minutes  
🚶‍♂️ **Walking Preference**: {walking_pref}  
🛑 **Break Preference**: {break_pref}  
""")

with st.expander("🗺️ Your Route", expanded=True):
    total_time_used = 0
    cumulative_time = 0
    previous_location = (0, 0)  # Entrance assumed to be (0,0)

    for stop in final_plan:
        if stop == "Break":
            st.markdown("🛑 **Break — 15 mins rest**")
            total_time_used += 15
            cumulative_time += 15
            previous_location = previous_location  # Stay at same place
            continue

        # Lookup info
        zone = next((z for z, a in zones.items() if stop in a), "")
        emoji = zone_emojis[zone]
        ride_duration = attraction_durations[stop]
        wait_time = attraction_wait_times[stop]
        attraction_coord = attraction_coordinates[stop]

        # Calculate walking time
        walk_distance = calculate_distance(previous_location, attraction_coord)
        walk_time = walk_distance / walking_speed

        # Total time for this stop
        total_attraction_time = ride_duration + wait_time + walk_time
        total_time_used += total_attraction_time
        cumulative_time += total_attraction_time

        st.markdown(f"{emoji} **{stop}** — Total: {int(total_attraction_time)} mins (incl. ride, wait & walk)")

        previous_location = attraction_coord

st.info(f"Total Time Used: {int(total_time_used)} mins | Leftover: {int(visit_duration - total_time_used)} mins")

# ------------------------------------------

# ------------------------------------------

# ✅ Final plan text generation (same as before)
plan_text = "\n".join([f"{stop}" for stop in final_plan])
st.session_state.tour_plan = plan_text

# ✅ Clean version for storage
def clean_tour_plan_for_storage(plan_text):
    cleaned_lines = []
    for line in plan_text.split('\n'):
        clean_line = ''.join(c for c in line if ord(c) < 128)
        if clean_line.strip().startswith("- "):
            clean_line = clean_line.strip()[2:]
        cleaned_lines.append(clean_line.strip())
    return "\n".join(cleaned_lines)

formatted_plan_for_storage = clean_tour_plan_for_storage(plan_text)

# ✅ Save both plan & get worksheet only once here
uid = st.session_state.get("unique_id")
sheet = get_consent_worksheet()
cell = sheet.find(uid, in_column=2)
row_num = cell.row

sheet.update_cell(row_num, 19, formatted_plan_for_storage)

# ------------------------------------------
# 11. Feedback & Rating (Unified, Cleaned)
# ------------------------------------------

st.subheader("⭐ Feedback")
rating = st.slider("Rate your plan:", 1, 10, 8)
feedback = st.text_area("Comments?")

if st.button("Submit Feedback"):
    try:
        sheet.update_cell(row_num, 17, str(rating))
        sheet.update_cell(row_num, 18, feedback)

        # ✅ Store in session state
        st.session_state.tour_rating = rating
        st.session_state.tour_feedback = feedback

        st.success("✅ Feedback saved successfully!")

        # ✅ Switch directly to final download page
        time.sleep(1)
        st.switch_page("pages/3_final_download.py")

    except Exception as e:
        st.error(f"Error saving feedback: {e}")
