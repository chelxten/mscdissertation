import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import math
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from datetime import timedelta, datetime

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
        angle = idx * (2 * np.pi / len(attractions))  # even angle distribution
        radius = 80  # increase for more spacing
        offset_x = int(radius * np.cos(angle))
        offset_y = int(radius * np.sin(angle))
        zone_x, zone_y = zone_coordinates[zone]
        attraction_coordinates[attraction] = (zone_x + offset_x, zone_y + offset_y)

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


# -- Define fuzzy variables --
preference_input = ctrl.Antecedent(np.arange(0, 11, 1), 'preference')
accessibility_input = ctrl.Antecedent(np.arange(0.0, 1.1, 0.1), 'accessibility')
wait_tolerance = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'wait_tolerance')
walking_input = ctrl.Antecedent(np.arange(0.0, 1.1, 0.1), 'walking')

priority_thrill = ctrl.Antecedent(np.arange(0, 2, 1), 'priority_thrill')
priority_food = ctrl.Antecedent(np.arange(0, 2, 1), 'priority_food')
priority_comfort = ctrl.Antecedent(np.arange(0, 2, 1), 'priority_comfort')

weight_output = ctrl.Consequent(np.arange(0, 11, 1), 'weight')

# -- Membership functions --
preference_input['low'] = fuzz.trimf(preference_input.universe, [0, 0, 5])
preference_input['medium'] = fuzz.trimf(preference_input.universe, [2, 5, 8])
preference_input['high'] = fuzz.trimf(preference_input.universe, [5, 10, 10])

accessibility_input['poor'] = fuzz.trimf(accessibility_input.universe, [0.0, 0.0, 0.5])
accessibility_input['moderate'] = fuzz.trimf(accessibility_input.universe, [0.2, 0.5, 0.8])
accessibility_input['good'] = fuzz.trimf(accessibility_input.universe, [0.5, 1.0, 1.0])

wait_tolerance['low'] = fuzz.trimf(wait_tolerance.universe, [0.0, 0.0, 0.4])
wait_tolerance['medium'] = fuzz.trimf(wait_tolerance.universe, [0.2, 0.5, 0.8])
wait_tolerance['high'] = fuzz.trimf(wait_tolerance.universe, [0.6, 1.0, 1.0])

walking_input['short'] = fuzz.trimf(walking_input.universe, [0.0, 0.0, 0.4])
walking_input['medium'] = fuzz.trimf(walking_input.universe, [0.2, 0.5, 0.8])
walking_input['long'] = fuzz.trimf(walking_input.universe, [0.6, 1.0, 1.0])

for priority in [priority_thrill, priority_food, priority_comfort]:
    priority['no'] = fuzz.trimf(priority.universe, [0, 0, 1])
    priority['yes'] = fuzz.trimf(priority.universe, [0, 1, 1])

weight_output['low'] = fuzz.trimf(weight_output.universe, [0, 0, 5])
weight_output['medium'] = fuzz.trimf(weight_output.universe, [2, 5, 8])
weight_output['high'] = fuzz.trimf(weight_output.universe, [5, 10, 10])

# -- Define fuzzy rules --
rules = [
    ctrl.Rule(preference_input['high'] & accessibility_input['good'], weight_output['high']),
    ctrl.Rule(preference_input['medium'] & accessibility_input['moderate'], weight_output['medium']),
    ctrl.Rule(preference_input['low'] | accessibility_input['poor'], weight_output['low']),
    ctrl.Rule(preference_input['high'] & accessibility_input['moderate'], weight_output['high']),
    ctrl.Rule(preference_input['medium'] & accessibility_input['good'], weight_output['high']),

    ctrl.Rule(wait_tolerance['low'], weight_output['low']),
    ctrl.Rule(wait_tolerance['high'], weight_output['high']),

    ctrl.Rule(walking_input['long'], weight_output['high']),
    ctrl.Rule(walking_input['short'], weight_output['low']),

    ctrl.Rule(priority_thrill['yes'], weight_output['high']),
    ctrl.Rule(priority_food['yes'], weight_output['high']),
    ctrl.Rule(priority_comfort['yes'], weight_output['high']),

    # 1. High preference + long walking + moderate wait → High weight
    ctrl.Rule(preference_input['high'] & walking_input['long'] & wait_tolerance['medium'], weight_output['high']),

    # 2. Medium preference + short walking + good accessibility → Medium weight
    ctrl.Rule(preference_input['medium'] & walking_input['short'] & accessibility_input['good'], weight_output['medium']),

    # 3. High preference + poor accessibility → Medium weight (penalize access)
    ctrl.Rule(preference_input['high'] & accessibility_input['poor'], weight_output['medium']),
    
    # 4. Low preference + poor accessibility → Low weight
    ctrl.Rule(preference_input['low'] & accessibility_input['poor'], weight_output['low']),

    # 5. High preference + low wait tolerance → Medium weight (conflict)
    ctrl.Rule(preference_input['high'] & wait_tolerance['low'], weight_output['medium']),

    # 6. High preference + high wait tolerance + long walking → High weight
    ctrl.Rule(preference_input['high'] & wait_tolerance['high'] & walking_input['long'], weight_output['high']),

    # 7. Medium preference + moderate accessibility + short walking → Medium weight
    ctrl.Rule(preference_input['medium'] & accessibility_input['moderate'] & walking_input['short'], weight_output['medium']),

    # 8. Priority: thrill=yes + low wait tolerance → High weight
    ctrl.Rule(priority_thrill['yes'] & wait_tolerance['low'], weight_output['high']),

    # 9. Priority: food=yes + short walking → High weight (comfort focus)
    ctrl.Rule(priority_food['yes'] & walking_input['short'], weight_output['high']),

    # 10. Priority: comfort=yes + poor accessibility → Medium weight (penalize access)
    ctrl.Rule(priority_comfort['yes'] & accessibility_input['poor'], weight_output['medium']),
    ]

# Build system
weight_ctrl = ctrl.ControlSystem(rules)
weight_sim = ctrl.ControlSystemSimulation(weight_ctrl)

# Priority flags
priority_thrill_val = 1.0 if "Enjoying high-intensity rides" in priorities else 0.0
priority_food_val = 1.0 if "Having regular food and rest breaks" in priorities else 0.0
priority_comfort_val = 1.0 if "Staying comfortable throughout the visit" in priorities else 0.0

# Map walking preference to value
walking_map = {
    "Very short distances": 0.0,
    "Moderate walking": 0.5,
    "Don’t mind walking": 1.0
}
walking_val = walking_map.get(walking_pref, 0.5)

# Map wait tolerance to value
wait_map = {
    "<10 min": 0.0,
    "10–20 min": 0.3,
    "20–30 min": 0.6,
    "30+ min": 1.0
}
wait_val = wait_map.get(data["wait_time"], 0.5)

# Fuzzy weight computation
zone_weights = {}
for zone in zones:
    pref = preferences[zone]
    acc = accessibility_factors[zone]

    weight_sim.input['preference'] = pref
    weight_sim.input['accessibility'] = acc
    weight_sim.input['wait_tolerance'] = wait_val
    weight_sim.input['walking'] = walking_val
    weight_sim.input['priority_thrill'] = 1.0 if zone == "thrill" and priority_thrill_val else 0.0
    weight_sim.input['priority_food'] = 1.0 if zone == "food" and priority_food_val else 0.0
    weight_sim.input['priority_comfort'] = 1.0 if zone == "relaxation" and priority_comfort_val else 0.0

    weight_sim.compute()
    zone_weights[zone] = weight_sim.output['weight']

# Normalize weights
total_weight = sum(zone_weights.values())
normalized_weights = {z: w / total_weight for z, w in zone_weights.items()}

# Optional: Remove intense thrill rides for young children
if data["age"] == "Under 12":
    intense_rides = {"Roller Coaster", "Drop Tower", "Freefall Cannon", "Spinning Vortex"}
    for ride in intense_rides:
        for zone_list in zones.values():
            if ride in zone_list:
                zone_list.remove(ride)
                
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
    projected_time = sum(
        attraction_durations[a] + attraction_wait_times[a] for a in initial_attractions
    ) + time_needed

    # Allow up to +15 mins overflow
    if projected_time <= visit_duration + 15:
        initial_attractions.append(attraction)
    else:
        break

# ------------------------------------------
# Nearest Relaxation Spot for Break Time 
# ------------------------------------------
def nearest_relaxation_spot(from_attraction):
    last_loc = attraction_coordinates[from_attraction]
    return min(
        zones["relaxation"],
        key=lambda spot: calculate_distance(last_loc, attraction_coordinates[spot])
    )

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
    for i, stop in enumerate(route):
        updated.append(stop)
        elapsed += attraction_durations[stop] + attraction_wait_times[stop]

        needs_break = (
            (break_pref == "After 1 hour" and elapsed >= 60) or
            (break_pref == "After 2 hours" and elapsed >= 120) or
            (break_pref == "After every big ride" and stop in ["Roller Coaster", "Drop Tower", "Log Flume", "Water Slide"])
        )

        if needs_break:
            relax_spot = nearest_relaxation_spot(stop)
            updated.append(relax_spot)
            elapsed = 0  # reset counter after break

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
plan_text_lines = []
total_time_used = 0
previous_location = (0, 0)
start_time = datetime.strptime("10:00", "%H:%M")  # park opening time

with st.expander("🗺️ Your Route", expanded=True):
    for stop in final_plan:
        scheduled_time = start_time + timedelta(minutes=total_time_used)
        formatted_time = scheduled_time.strftime("%I:%M %p")

        if stop == "Break":
            added_time = 15
            plan_text_lines.append(f"• {formatted_time} — Break — 15 mins")
            st.markdown("🛑 **Break — 15 mins**")
            total_time_used += added_time
            continue

        # Calculate components
        ride_time = attraction_durations[stop]
        wait_time = attraction_wait_times[stop]
        attraction_loc = attraction_coordinates[stop]
        walk_dist = calculate_distance(previous_location, attraction_loc)
        walk_time = walk_dist / walking_speed
        display_walk = max(1, int(walk_time))
        added_time = ride_time + wait_time + walk_time

        # Check if it fits
        if total_time_used + added_time > visit_duration + 15:
            break

        # Display
        zone = next(z for z, a in zones.items() if stop in a)
        emoji = zone_emojis[zone]
        
        # 👇 Identify relaxation-based break
        is_break_spot = zone == "relaxation" and break_pref != "None"
        title_note = " — Rest Stop" if is_break_spot else ""
        
        total = int(ride_time + wait_time + display_walk)
        full_text = f"• {formatted_time} — {stop} — {ride_time}m ride + {wait_time}m wait + {display_walk}m walk = {int(ride_time + wait_time + display_walk)}m"
        plan_text_lines.append(full_text)
        st.markdown(f"{emoji} **{formatted_time} — {stop}** — {ride_time}m ride + {wait_time}m wait + {display_walk}m walk")

        previous_location = attraction_loc
        total_time_used += added_time

# Final info
leftover_time = visit_duration - total_time_used
st.info(f"Total Used: {int(total_time_used)} mins | Leftover: {int(leftover_time)} mins")


# ✅ Store clean plan into both session and Google Sheet:
final_clean_plan = "\n".join(plan_text_lines)
st.session_state.tour_plan = final_clean_plan

uid = st.session_state.get("unique_id")
sheet = get_consent_worksheet()
cell = sheet.find(uid, in_column=2)
row_num = cell.row
sheet.update_cell(row_num, 19, final_clean_plan)

sheet.update_cell(row_num, 20, str(int(total_time_used)))  # Column T
sheet.update_cell(row_num, 21, str(int(leftover_time)))  # Column U

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
