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
st.title("Your Personalized Tour Plan")

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

# 🧼 Changing Room (Utility location)
change_location = "Shower & Changing Room"
change_coordinates = (450, 250)  # or wherever it should be on the map

# Add it to attraction_coordinates
attraction_coordinates[change_location] = change_coordinates

# ------------------------------------------
# 3. Accessibility, Duration & Wait Times
# ------------------------------------------
accessibility_factors = {
    "thrill": 0.7, "water": 0.8, "family": 1.0,
    "entertainment": 0.9, "food": 1.0, "shopping": 1.0, "relaxation": 1.0
}

attraction_durations = {
    # Thrill (longer ride time)
    "Roller Coaster": 5, "Drop Tower": 3, "Haunted Mine Train": 4, "Spinning Vortex": 4, "Freefall Cannon": 3,

    # Water (medium–long experience)
    "Water Slide": 4, "Lazy River": 10, "Log Flume": 6, "Splash Battle": 5, "Wave Pool": 10,

    # Family (shorter ride time)
    "Bumper Cars": 3, "Mini Ferris Wheel": 4, "Animal Safari Ride": 6, "Ball Pit Dome": 6, "Train Adventure": 8,

    # Entertainment (long shows)
    "Live Stage": 20, "Street Parade": 15, "Magic Show": 25, "Circus Tent": 25, "Musical Fountain": 15,

    # Food (time to eat)
    "Food Court": 25, "Snack Bar": 15, "Ice Cream Kiosk": 10, "Pizza Plaza": 20, "Smoothie Station": 10,

    # Shopping (quick)
    "Souvenir Shop": 10, "Candy Store": 8, "Photo Booth": 5, "Gift Emporium": 10, "Toy World": 10,

    # Relaxation (fixed)
    "Relaxation Garden": 15, "Shaded Benches": 10, "Quiet Lake View": 10, "Zen Courtyard": 10, "Sky Deck": 10
}

attraction_wait_times = {
    # Thrill (very popular)
    "Roller Coaster": 30, "Drop Tower": 25, "Haunted Mine Train": 20, "Spinning Vortex": 18, "Freefall Cannon": 20,

    # Water (popular on hot days)
    "Water Slide": 15, "Lazy River": 10, "Log Flume": 20, "Splash Battle": 12, "Wave Pool": 15,

    # Family (shorter queues)
    "Bumper Cars": 5, "Mini Ferris Wheel": 5, "Animal Safari Ride": 8, "Ball Pit Dome": 6, "Train Adventure": 8,

    # Entertainment (seating based, fixed wait)
    "Live Stage": 10, "Street Parade": 5, "Magic Show": 10, "Circus Tent": 10, "Musical Fountain": 5,

    # Food (variable)
    "Food Court": 10, "Snack Bar": 5, "Ice Cream Kiosk": 4, "Pizza Plaza": 8, "Smoothie Station": 4,

    # Shopping (minimal)
    "Souvenir Shop": 3, "Candy Store": 2, "Photo Booth": 1, "Gift Emporium": 3, "Toy World": 3,

    # Relaxation (no wait)
    "Relaxation Garden": 0, "Shaded Benches": 0, "Quiet Lake View": 0, "Zen Courtyard": 0, "Sky Deck": 0
}

zone_intensity = {
    "thrill": 0.95,         # High energy demand (e.g. roller coasters)
    "water": 0.75,          # Swimming or flume-based attractions
    "family": 0.55,         # Interactive but moderate exertion
    "entertainment": 0.35,  # Low exertion, seated shows
    "food": 0.15,           # Resting and eating
    "shopping": 0.25,       # Low walking activity
    "relaxation": 0.1       # Passive resting (benches, gardens)
}

wet_ride_names = {"Water Slide", "Wave Pool", "Splash Battle"}

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

intensity_input = ctrl.Antecedent(np.arange(0.0, 1.1, 0.1), 'intensity')

intensity_input['low'] = fuzz.trimf(intensity_input.universe, [0.0, 0.0, 0.4])
intensity_input['medium'] = fuzz.trimf(intensity_input.universe, [0.3, 0.5, 0.7])
intensity_input['high'] = fuzz.trimf(intensity_input.universe, [0.6, 1.0, 1.0])
weight_output = ctrl.Consequent(np.arange(0, 11, 1), 'weight')

# -- Membership functions --
preference_input['low'] = fuzz.trimf(preference_input.universe, [0, 0, 5])
preference_input['medium'] = fuzz.trimf(preference_input.universe, [2, 5, 8])
preference_input['high'] = fuzz.trimf(preference_input.universe, [5, 10, 10])

# Detect top preference zone
top_zone = max(preferences, key=preferences.get)

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

weight_output['low'] = fuzz.trimf(weight_output.universe, [0, 0, 4])
weight_output['medium'] = fuzz.trimf(weight_output.universe, [3, 5, 7])
weight_output['high'] = fuzz.trimf(weight_output.universe, [6, 10, 10])

food_interval = ctrl.Consequent(np.arange(60, 241, 1), 'food_interval')

food_interval['short'] = fuzz.trimf(food_interval.universe, [60, 90, 120])
food_interval['medium'] = fuzz.trimf(food_interval.universe, [100, 135, 170])
food_interval['long'] = fuzz.trimf(food_interval.universe, [160, 240, 240])


# -------------------------------
# Fuzzy System Definition Starts
# -------------------------------

# -- Define fuzzy rules --
rules = []

# -------------------------------
# A. Core: Preference × Accessibility
# -------------------------------
rules += [
    ctrl.Rule(preference_input['high'] & accessibility_input['good'], weight_output['high']),
    ctrl.Rule(preference_input['high'] & accessibility_input['moderate'], weight_output['medium']),
    ctrl.Rule(preference_input['high'] & accessibility_input['poor'], weight_output['medium']),

    ctrl.Rule(preference_input['medium'] & accessibility_input['good'], weight_output['medium']),
    ctrl.Rule(preference_input['medium'] & accessibility_input['moderate'], weight_output['medium']),
    ctrl.Rule(preference_input['medium'] & accessibility_input['poor'], weight_output['low']),

    ctrl.Rule(preference_input['low'], weight_output['low']),
]

# -------------------------------
# B. User Attributes: Walk & Wait
# -------------------------------
rules += [
    ctrl.Rule(wait_tolerance['low'], weight_output['low']),
    ctrl.Rule(wait_tolerance['high'], weight_output['high']),
    ctrl.Rule(walking_input['short'], weight_output['low']),
    ctrl.Rule(walking_input['long'], weight_output['high']),
]

# -------------------------------
# C. User Priorities
# -------------------------------
rules += [
    ctrl.Rule(priority_thrill['yes'], weight_output['high']),
    ctrl.Rule(priority_food['yes'], weight_output['medium']),
    ctrl.Rule(priority_comfort['yes'], weight_output['medium']),
]

# -------------------------------
# D. Zone Intensity Adjustment
# -------------------------------
rules += [
    ctrl.Rule(intensity_input['high'] & preference_input['high'], weight_output['medium']),
    ctrl.Rule(intensity_input['high'] & preference_input['low'], weight_output['low']),
    ctrl.Rule(intensity_input['low'], weight_output['medium']),
]

# -------------------------------
# E. Top-Zone Reinforcement
# -------------------------------
reinforcement_rules = []
if top_zone == "thrill":
    reinforcement_rules += [
        ctrl.Rule(preference_input['high'] & priority_thrill['yes'], weight_output['high']),
        ctrl.Rule(preference_input['high'] & wait_tolerance['medium'], weight_output['high']),
        ctrl.Rule(preference_input['high'] & walking_input['medium'], weight_output['high'])
    ]
elif top_zone == "family":
    reinforcement_rules += [
        ctrl.Rule(preference_input['high'] & walking_input['short'], weight_output['high']),
        ctrl.Rule(preference_input['high'] & accessibility_input['good'], weight_output['high'])
    ]
elif top_zone == "water":
    reinforcement_rules += [
        ctrl.Rule(preference_input['high'] & wait_tolerance['high'], weight_output['high']),
        ctrl.Rule(preference_input['high'] & walking_input['medium'], weight_output['high'])
    ]
elif top_zone == "entertainment":
    reinforcement_rules += [
        ctrl.Rule(preference_input['high'] & wait_tolerance['medium'], weight_output['high']),
        ctrl.Rule(preference_input['high'] & accessibility_input['good'], weight_output['high'])
    ]
elif top_zone == "shopping":
    reinforcement_rules += [
        ctrl.Rule(preference_input['high'] & walking_input['short'], weight_output['high']),
        ctrl.Rule(preference_input['high'] & accessibility_input['good'], weight_output['high'])
    ]

rules += reinforcement_rules

food_interval_rules = [
    ctrl.Rule(preference_input['high'] & priority_food['yes'], food_interval['short']),
    ctrl.Rule(preference_input['medium'] & priority_food['yes'], food_interval['medium']),
    ctrl.Rule(preference_input['low'] | priority_food['no'], food_interval['long']),
]

food_interval_ctrl = ctrl.ControlSystem(food_interval_rules)
food_interval_sim = ctrl.ControlSystemSimulation(food_interval_ctrl)

# -------------------------------
# Fuzzy Energy Loss Estimation
# -------------------------------
intensity_input_energy = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'intensity')
walk_time_input = ctrl.Antecedent(np.arange(0, 16, 1), 'walk_time')  # up to 15 minutes walk
age_sensitivity_input = ctrl.Antecedent(np.arange(0.8, 1.4, 0.1), 'age_sensitivity')

energy_loss_output = ctrl.Consequent(np.arange(0, 21, 1), 'energy_loss')  # 0–20 points per stop

# Intensity
intensity_input_energy['low'] = fuzz.trimf(intensity_input_energy.universe, [0.0, 0.0, 0.4])
intensity_input_energy['medium'] = fuzz.trimf(intensity_input_energy.universe, [0.3, 0.5, 0.7])
intensity_input_energy['high'] = fuzz.trimf(intensity_input_energy.universe, [0.6, 1.0, 1.0])

# Walk time
walk_time_input['short'] = fuzz.trimf(walk_time_input.universe, [0, 0, 5])
walk_time_input['medium'] = fuzz.trimf(walk_time_input.universe, [3, 7, 11])
walk_time_input['long'] = fuzz.trimf(walk_time_input.universe, [10, 15, 15])

# Age sensitivity
age_sensitivity_input['low'] = fuzz.trimf(age_sensitivity_input.universe, [0.8, 0.8, 1.0])
age_sensitivity_input['medium'] = fuzz.trimf(age_sensitivity_input.universe, [0.9, 1.1, 1.2])
age_sensitivity_input['high'] = fuzz.trimf(age_sensitivity_input.universe, [1.1, 1.3, 1.4])


# Energy loss
energy_loss_output['low'] = fuzz.trimf(energy_loss_output.universe, [0, 0, 8])
energy_loss_output['medium'] = fuzz.trimf(energy_loss_output.universe, [5, 10, 15])
energy_loss_output['high'] = fuzz.trimf(energy_loss_output.universe, [12, 20, 20])

energy_loss_rules = [
    ctrl.Rule(intensity_input_energy['high'] & walk_time_input['long'] & age_sensitivity_input['high'], energy_loss_output['high']),
    ctrl.Rule(intensity_input_energy['high'] & walk_time_input['medium'], energy_loss_output['medium']),
    ctrl.Rule(intensity_input_energy['medium'] & walk_time_input['medium'], energy_loss_output['medium']),
    ctrl.Rule(intensity_input_energy['low'] & walk_time_input['short'], energy_loss_output['low']),
    ctrl.Rule(age_sensitivity_input['low'] & intensity_input_energy['low'], energy_loss_output['low']),
    ctrl.Rule(intensity_input_energy['medium'] & walk_time_input['long'], energy_loss_output['high']),
    ctrl.Rule(walk_time_input['long'] & age_sensitivity_input['high'], energy_loss_output['high']),
    ctrl.Rule(intensity_input_energy['high'] & age_sensitivity_input['low'], energy_loss_output['medium']),
]

energy_loss_ctrl = ctrl.ControlSystem(energy_loss_rules)
energy_loss_sim = ctrl.ControlSystemSimulation(energy_loss_ctrl)


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

age_energy_scaling = {
    "Child":        {"loss_factor": 0.8, "rest_boost": 35, "food_boost": 20},
    "Teen":         {"loss_factor": 1.0, "rest_boost": 30, "food_boost": 18},
    "Young Adult":  {"loss_factor": 1.2, "rest_boost": 25, "food_boost": 15},
    "Middle-aged":  {"loss_factor": 1.0, "rest_boost": 30, "food_boost": 18},
    "Older Adult":  {"loss_factor": 1.3, "rest_boost": 40, "food_boost": 25},
    "Adult":        {"loss_factor": 1.1, "rest_boost": 30, "food_boost": 18},  # fallback
}

raw_age = data.get("age", "Adult")

age_group_map = {
    "Under 12": "Child",
    "13–17": "Teen",
    "18–30": "Young Adult",
    "31–45": "Middle-aged",
    "46–60": "Middle-aged",
    "60+":    "Older Adult"
}

user_age_group = age_group_map.get(raw_age, "Adult")
energy_settings = age_energy_scaling[user_age_group]



# Fuzzy weight computation
zone_weights = {}
for zone in zones:
    pref = preferences[zone]
    acc = accessibility_factors[zone]
    intensity = zone_intensity[zone]

    weight_sim.input['preference'] = pref
    weight_sim.input['accessibility'] = acc
    weight_sim.input['wait_tolerance'] = wait_val
    weight_sim.input['walking'] = walking_val
    weight_sim.input['priority_thrill'] = 1.0 if zone == "thrill" and priority_thrill_val else 0.0
    weight_sim.input['priority_food'] = 1.0 if zone == "food" and priority_food_val else 0.0
    weight_sim.input['priority_comfort'] = 1.0 if zone == "relaxation" and priority_comfort_val else 0.0
    weight_sim.input['intensity'] = intensity

    weight_sim.compute()
    zone_weights[zone] = weight_sim.output['weight']

# Cap weight of food and relaxation zones to prevent domination
for zone in ["food", "relaxation"]:
    if zone in zone_weights:
        zone_weights[zone] = min(zone_weights[zone], 4.5)  # limit to moderate level

# Normalize weights
total_weight = sum(zone_weights.values())
if total_weight > 0:
    normalized_weights = {z: w / total_weight for z, w in zone_weights.items()}
else:
    normalized_weights = {z: 1 / len(zone_weights) for z in zone_weights}  # equal weighting

# Optional: Remove intense thrill rides for young children
if data["age"] == "Under 12":
    intense_rides = {"Roller Coaster", "Drop Tower", "Freefall Cannon", "Spinning Vortex"}
    for ride in intense_rides:
        for zone_list in zones.values():
            if ride in zone_list:
                zone_list.remove(ride)
                
# ------------------------------------------
# 5. Attraction Scoring Based on Fuzzy Output
# ------------------------------------------

# Parameters for scoring (you can tune these)
WAIT_PENALTY_FACTOR = 0.02     # reduces score if wait is high
INTENSITY_COMFORT_FACTOR = 0.2 # bonus for low intensity zones

attraction_scores = {}

for zone, attractions in zones.items():
    zone_weight = normalized_weights.get(zone, 0)
    user_pref = preferences.get(zone, 5) / 10.0  # Normalize to 0–1
    intensity = zone_intensity.get(zone, 0.5)

    for attraction in attractions:
        wait_time = attraction_wait_times.get(attraction, 0)
        duration = attraction_durations.get(attraction, 5)

        is_wet = attraction in wet_ride_names
        comfort_penalty = 1.0
        if is_wet and priority_comfort_val and wet_time_pct < 35:
            comfort_penalty = 0.7  # reduce score by 30%

        score = (
            zone_weight
            * user_pref
            * (1 - WAIT_PENALTY_FACTOR * wait_time)
            * (1 + INTENSITY_COMFORT_FACTOR * (1 - intensity))
            * comfort_penalty
        )

        attraction_scores[attraction] = score
        

# Sort all attractions based on score (high to low)
sorted_attractions = sorted(attraction_scores, key=lambda a: attraction_scores[a], reverse=True)

# ------------------------------------------
# 6. Balanced Initial Attractions Selection
# ------------------------------------------

initial_attractions = []
time_budget = visit_duration + 15
current_time_used = 0

# Categorize rides by intensity
high_rides = []
medium_rides = []
low_rides = []

for attraction in sorted_attractions:
    zone = next((z for z, a_list in zones.items() if attraction in a_list), None)
    if not zone:
        continue

    ride_time = attraction_durations.get(attraction, 0)
    wait_time = attraction_wait_times.get(attraction, 0)
    time_required = ride_time + wait_time

    if current_time_used + time_required > time_budget:
        continue

    intensity = zone_intensity.get(zone, 0.5)

    if intensity >= 0.7:
        high_rides.append(attraction)
    elif 0.3 <= intensity < 0.7:
        medium_rides.append(attraction)
    else:
        low_rides.append(attraction)

    current_time_used += time_required

# Interleave rides for balanced pacing
h, m, l = 0, 0, 0
while h < len(high_rides) or m < len(medium_rides) or l < len(low_rides):
    if h < len(high_rides):
        initial_attractions.append(high_rides[h])
        h += 1
    if m < len(medium_rides):
        initial_attractions.append(medium_rides[m])
        m += 1
    if l < len(low_rides) and (len(initial_attractions) % 3 == 0):
        initial_attractions.append(low_rides[l])
        l += 1


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
    if isinstance(point_a, str):
        point_a = attraction_coordinates[point_a]
    if isinstance(point_b, str):
        point_b = attraction_coordinates[point_b]
    x1, y1 = point_a
    x2, y2 = point_b
    return math.hypot(x2 - x1, y2 - y1)

def reorder_by_distance(route, start_location=(0, 0)):
    reordered = []
    current = start_location
    remaining = [r for r in route if r in attraction_coordinates]

    while remaining:
        next_stop = min(remaining, key=lambda r: calculate_distance(current, attraction_coordinates[r]))
        reordered.append(next_stop)
        current = attraction_coordinates[next_stop]
        remaining.remove(next_stop)

    return reordered

def greedy_route(attractions, start_with=None):
    route = []
    pool = attractions.copy()

    # Optional forced first attraction
    if start_with and start_with in pool:
        route.append(start_with)
        current = attraction_coordinates[start_with]
        pool.remove(start_with)
    else:
        current = (0, 0)  # Default: Entrance

    # Greedy selection of remaining attractions
    while pool:
        next_attraction = min(pool, key=lambda a: calculate_distance(current, attraction_coordinates[a]))
        route.append(next_attraction)
        current = attraction_coordinates[next_attraction]
        pool.remove(next_attraction)

    return route
    
first_preference_zone = max(preferences, key=preferences.get)
first_pref_attraction = None

# Choose one attraction from top preference zone
for a in zones[first_preference_zone]:
    if a in initial_attractions:
        first_pref_attraction = a
        break


wet_ride_pref = ctrl.Antecedent(np.arange(0, 11, 1), 'wet_ride_pref')  # from preference score
comfort_priority = ctrl.Antecedent(np.arange(0, 2, 1), 'comfort_priority')  # binary yes/no

wet_time_position = ctrl.Consequent(np.arange(0, 101, 1), 'wet_time_position')  # % of tour duration

wet_ride_pref['low'] = fuzz.trimf(wet_ride_pref.universe, [0, 0, 5])
wet_ride_pref['medium'] = fuzz.trimf(wet_ride_pref.universe, [3, 5, 7])
wet_ride_pref['high'] = fuzz.trimf(wet_ride_pref.universe, [5, 10, 10])

comfort_priority['no'] = fuzz.trimf(comfort_priority.universe, [0, 0, 1])
comfort_priority['yes'] = fuzz.trimf(comfort_priority.universe, [0, 1, 1])

wet_time_position['early'] = fuzz.trimf(wet_time_position.universe, [0, 0, 30])
wet_time_position['mid'] = fuzz.trimf(wet_time_position.universe, [25, 50, 75])
wet_time_position['late'] = fuzz.trimf(wet_time_position.universe, [70, 100, 100])

wet_ride_rules = [
    ctrl.Rule(wet_ride_pref['high'] & comfort_priority['no'], wet_time_position['early']),
    ctrl.Rule(wet_ride_pref['medium'], wet_time_position['mid']),
    ctrl.Rule(comfort_priority['yes'], wet_time_position['late']),
]

wet_time_ctrl = ctrl.ControlSystem(wet_ride_rules)
wet_time_sim = ctrl.ControlSystemSimulation(wet_time_ctrl)

# Inputs
wet_pref_val = preferences.get("water", 5)
wet_time_sim.input['wet_ride_pref'] = wet_pref_val
wet_time_sim.input['comfort_priority'] = 1.0 if priority_comfort_val else 0.0
wet_time_sim.compute()

wet_time_pct = wet_time_sim.output['wet_time_position']  # e.g., 52%


# ------------------------------------------
# Nearest Relaxation Spot for Break Time 
# ------------------------------------------
def schedule_wet_rides_midday(route, wet_rides, zones):
    """
    Moves all wet rides to the middle of the route, followed by [Clothing Change],
    and injects 1–2 medium-intensity fillers between wet rides and food/rest zones.
    """
    wet_block = [a for a in route if a in wet_rides]
    dry_block = [a for a in route if a not in wet_rides and not a.startswith("[Clothing Change]")]

    if not wet_block:
        return route

    # Insert clothing change after wet rides
    change_stop = "[Clothing Change] Shower & Changing Room"
    if change_stop not in wet_block and change_stop not in dry_block:
        wet_block.append(change_stop)

    # Insert wet block into middle of dry block
    insert_pos = int((wet_time_pct / 100) * len(dry_block))
    insert_pos = min(max(1, insert_pos), len(dry_block)-1)
    merged = dry_block[:insert_pos] + wet_block + dry_block[insert_pos:]

    # ➕ Insert relaxing fillers after wet rides to help dry off before next food/rest zone
    last_wet_idx = merged.index(wet_block[-1])
    after_wet = merged[last_wet_idx + 1:]

    fillers = [a for a in after_wet if any(a in zones[z] for z in ["family", "entertainment"])]
    filler_count = 2 if len(fillers) >= 2 else 1 if fillers else 0
    selected_fillers = fillers[:filler_count]

    # Remove fillers from original location
    merged = [a for a in merged if a not in selected_fillers]

    # Re-insert fillers right after wet block
    insert_pos = merged.index(wet_block[-1]) + 1
    merged = merged[:insert_pos] + selected_fillers + merged[insert_pos:]

    return merged
    

food_pref = preferences["food"]

food_interval_sim.input['preference'] = food_pref
food_interval_sim.input['priority_food'] = priority_food_val
food_interval_sim.compute()

preferred_food_gap = int(np.clip(food_interval_sim.output['food_interval'], 60, 240))  # cap between 1h and 4h



# ------------------------------------------
# 7. No Consecutive Break
# ------------------------------------------

def no_consecutive_food_or_break(attractions, zones):
    final = []
    prev_soft = False

    for item in attractions:
        zone = next((z for z, a in zones.items() if item in a), None)
        is_soft = zone in {"food", "relaxation"}

        if item.startswith("[Clothing Change]"):
            final.append(item)
            prev_soft = False
            continue

        # Skip if previous was food/rest and current is also soft
        if is_soft and prev_soft:
            continue

        final.append(item)
        prev_soft = is_soft

    return final
    
# ------------------------------------------
# 7. Break Insertion
# ------------------------------------------

# 🧠 Automatically reorder medium-intensity zones for rhythm
def reorder_medium_intensity(route):
    medium_stops = []
    other_stops = []

    for stop in route:
        zone = next((z for z, a in zones.items() if stop in a), None)
        if zone is None:
            other_stops.append(stop)
            continue

        intensity = zone_intensity.get(zone, 0)
        if 0.3 <= intensity <= 0.7:
            medium_stops.append(stop)
        else:
            other_stops.append(stop)

    # Alternate medium with others
    reordered = []
    m_idx = 0
    for i, stop in enumerate(other_stops):
        reordered.append(stop)
        if i % 2 == 1 and m_idx < len(medium_stops):
            reordered.append(medium_stops[m_idx])
            m_idx += 1
    reordered += medium_stops[m_idx:]
    return reordered



walking_speed = 67  # meters/min
def insert_breaks(route):
    updated = []
    elapsed_since_break = 0
    elapsed_since_food = 0
    last_break_time = -999
    used_break_spots = set()
    used_food_spots = set()
    energy_level = 100
    current_location = (0, 0)
    total_elapsed_time = 0
    meal_break_count = 0
    max_meals = 3

    # 🔒 Detect wet ride block range
    wet_start = None
    wet_end = None
    for i, stop in enumerate(route):
        if stop in wet_ride_names or stop.startswith("[Clothing Change]"):
            if wet_start is None:
                wet_start = i
            wet_end = i

    for i, stop in enumerate(route):
        in_wet_block = wet_start is not None and wet_start <= i <= wet_end
        updated.append(stop)

        zone = next((z for z, a in zones.items() if stop in a), None)
        if zone is None:
            continue

        duration = attraction_durations[stop]
        wait = attraction_wait_times[stop]
        time_spent = duration + wait
        walk_dist = calculate_distance(current_location, attraction_coordinates[stop])
        walk_time = max(1, int(walk_dist / walking_speed))

        total_this_stop = time_spent + walk_time
        total_elapsed_time += total_this_stop
        elapsed_since_break += total_this_stop
        elapsed_since_food += total_this_stop

        intensity_val = zone_intensity.get(zone, 1.0)
        age_sens = energy_settings['loss_factor']

        try:
            energy_loss_sim.input['intensity'] = intensity_val
            energy_loss_sim.input['walk_time'] = walk_time
            energy_loss_sim.input['age_sensitivity'] = age_sens
            energy_loss_sim.compute()
            energy_loss = energy_loss_sim.output['energy_loss']
        except Exception as e:
            print("⚠️ Fuzzy energy_loss fallback:", e)
            energy_loss = 8

        energy_level = max(0, energy_level - energy_loss)

        # 🚫 Skip any inserts if we're in the wet block
        if in_wet_block:
            current_location = attraction_coordinates[stop]
            continue

        # 🌳 Dynamic rest
        if energy_level < 40 and elapsed_since_break > 10:
            relax = [s for s in zones["relaxation"] if s not in used_break_spots]
            if relax:
                best = min(relax, key=lambda s: calculate_distance(attraction_coordinates[stop], attraction_coordinates[s]))
                updated.append(best)
                used_break_spots.add(best)
                elapsed_since_break = 0
                energy_level = min(100, energy_level + energy_settings['rest_boost'])
                last_break_time = total_elapsed_time

        # 😴 Scheduled rest
        needs_break = (
            (break_pref == "After 1 hour" and elapsed_since_break >= 60) or
            (break_pref == "After 2 hours" and elapsed_since_break >= 120) or
            (break_pref == "After every big ride" and stop in {"Roller Coaster", "Drop Tower", "Log Flume", "Water Slide"})
        )
        if needs_break and energy_level >= 40 and (total_elapsed_time - last_break_time) > 10:
            relax = [s for s in zones["relaxation"] if s not in used_break_spots and s not in updated]
            if relax:
                last_zone = next((z for z, a in zones.items() if updated[-1] in a), None) if updated else None
            if last_zone not in {"relaxation", "food"}:
                best = min(relax, key=lambda s: calculate_distance(attraction_coordinates[stop], attraction_coordinates[s]))
                updated.append(best)
                used_break_spots.add(best)
                elapsed_since_break = 0
                energy_level = min(100, energy_level + energy_settings['rest_boost'])
                last_break_time = total_elapsed_time

        # 🍔 Food logic (avoid back-to-back with rest or food)
        if (
            elapsed_since_food >= preferred_food_gap
            and meal_break_count < max_meals
            and not (updated and next((z for z, a in zones.items() if updated[-1] in a), None) in ["food", "relaxation"])
        ):
            options = [f for f in zones["food"] if f not in used_food_spots]
            if options:
                best = min(options, key=lambda f: calculate_distance(attraction_coordinates[stop], attraction_coordinates[f]))
                updated.append(best)
                used_food_spots.add(best)
                elapsed_since_food = 0
                meal_break_count += 1
                energy_level = min(100, energy_level + energy_settings['food_boost'])

        # ⛔ Prevent inserting break right after wet ride
        if stop in wet_ride_names and i+1 < len(route):
            next_stop = route[i+1]
            next_zone = next((z for z, a in zones.items() if next_stop in a), None)
            if next_zone in ["relaxation", "food"]:
                continue

        current_location = attraction_coordinates[stop]

    return updated

# Optional: start with top zone attraction
first_preference_zone = max(preferences, key=preferences.get)
first_pref_attraction = next(
    (a for a in zones[first_preference_zone] if a in initial_attractions),
    None
)

# Apply distance optimization
optimized_initial = reorder_by_distance(
    initial_attractions,
    start_location=attraction_coordinates[first_pref_attraction] if first_pref_attraction else (0, 0)
)

# Schedule wet rides mid-tour if needed
wet_scheduled = schedule_wet_rides_midday(optimized_initial, wet_ride_names, zones)

# Insert breaks and food stops
final_route = insert_breaks(wet_scheduled)
final_route = no_consecutive_food_or_break(final_route, zones)


final_plan = final_route

import matplotlib.pyplot as plt

energy = 100
energy_timeline = [energy]
time_timeline = [0]
labels = []

elapsed_time = 0
total_time_check = 0
previous_location = (0, 0)

for stop in final_plan:
    zone = next((z for z, a in zones.items() if stop in a), None)
    if zone is None:
        continue 
    duration = attraction_durations[stop]
    wait = attraction_wait_times[stop]
    time_spent = duration + wait

    # Walk distance
    current_location = attraction_coordinates[stop]
    walk_dist = calculate_distance(previous_location, current_location)
    walk_time = max(1, int(walk_dist / walking_speed))
    total_this_stop = time_spent + walk_time

    # Check time cutoff
    if total_time_check + total_this_stop > visit_duration + 15:
        break

    # Apply energy logic
    if zone == "relaxation":
        energy += energy_settings["rest_boost"]
    elif zone == "food":
        energy += energy_settings["food_boost"]
    else:
        energy -= zone_intensity.get(zone, 1) * energy_settings["loss_factor"] * 6

    energy = max(0, min(100, energy))  # clamp
    elapsed_time += total_this_stop
    total_time_check += total_this_stop

    energy_timeline.append(energy)
    time_timeline.append(elapsed_time)
    labels.append(f"{stop}\n{int(energy)}%")

    previous_location = current_location

# 📊 Plot with annotated labels
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(time_timeline, energy_timeline, marker='o')

for i in range(1, len(time_timeline)):
    ax.annotate(
        labels[i - 1],
        (time_timeline[i], energy_timeline[i]),
        textcoords="offset points",
        xytext=(0, 8),
        ha='center',
        fontsize=8,
        rotation=30
    )

ax.set_title("🧠 Energy Over Time")
ax.set_xlabel("Minutes Since Start")
ax.set_ylabel("Energy Level (%)")
ax.grid(True)
st.pyplot(fig)

# ------------------------------------------
# 8. Display & Time Calculation with Walks
# ------------------------------------------
# ------------------------------------------
# 8. Display & Time Calculation with Walks
# ------------------------------------------
CLOTHING_CHANGE_DURATION = 10  # minutes

zone_emojis = {
    "thrill": "🎢", "water": "💦", "family": "👨‍👩‍👧‍👦",
    "entertainment": "🎭", "food": "🍔", "shopping": "🛍️",
    "relaxation": "🌳", "change": "👕"
}

plan_text_lines = []
total_time_used = 0
entrance_location = (250, 250)
previous_location = entrance_location
start_time = datetime.strptime("10:00", "%H:%M")
walking_speed = 67  # meters/min

show_details_block = st.checkbox("Show detailed time breakdown", value=False)

with st.expander("The Fun Starts Here", expanded=True):
    st.markdown("🏁 **Entrance**")
    plan_text_lines.append("Entrance")

    for stop in final_plan:
        if stop.startswith("[Clothing Change]"):
            display_name = "👕 [Clothing Change] Shower & Changing Room"
            save_name = stop
            formatted_time = (start_time + timedelta(minutes=total_time_used)).strftime("%I:%M %p")
            st.markdown(f"**{formatted_time} — {display_name} — {CLOTHING_CHANGE_DURATION} minutes**")
            if show_details_block:
                st.markdown("• Includes: 10m clothing change time")
            plan_text_lines.append(f"{formatted_time} — {save_name} — {CLOTHING_CHANGE_DURATION} minutes")
            plan_text_lines.append("Includes: 10m clothing change time")
            total_time_used += CLOTHING_CHANGE_DURATION
            st.markdown("---")
            continue

        zone = next((z for z, a in zones.items() if stop in a), None)
        if zone is None:
            continue  # skip unknowns

        ride_time = attraction_durations[stop]
        wait_time = attraction_wait_times[stop]
        attraction_loc = attraction_coordinates[stop]
        walk_dist = calculate_distance(previous_location, attraction_loc)
        walk_time = max(1, int(walk_dist / walking_speed))
        total_duration = ride_time + wait_time + walk_time

        if total_time_used + total_duration > visit_duration + 15:
            break

        scheduled_time = start_time + timedelta(minutes=total_time_used)
        formatted_time = scheduled_time.strftime("%I:%M %p")
        emoji = zone_emojis.get(zone, "")

        # Special formatting
        if zone == "relaxation":
            display_name = f"🌿 [Rest Stop] {stop}"
            save_name = f"[Rest Stop] {stop}"
            st.markdown("---")
        elif zone == "food":
            display_name = f"🍽️ [Meal Break] {stop}"
            save_name = f"[Meal Break] {stop}"
            st.markdown("---")
        else:
            display_name = f"{emoji} {stop}"
            save_name = stop

        display_line = f"**{formatted_time} — {display_name} — {total_duration} minutes**"
        st.markdown(display_line)

        if show_details_block:
            detail_line = f"• Includes: {ride_time}m ride, {wait_time}m wait, {walk_time}m walk"
            st.markdown(detail_line)

        if zone in ["relaxation", "food"]:
            st.markdown("---")

        plan_text_lines.append(f"{formatted_time} — {save_name} — {total_duration} minutes")
        plan_text_lines.append(f"Includes: {ride_time}m ride, {wait_time}m wait, {walk_time}m walk")

        total_time_used += total_duration
        previous_location = attraction_loc

    st.markdown("🏁 **Exit**")
    plan_text_lines.append("Exit")

# ⏱ Final time info
leftover_time = visit_duration - total_time_used
st.info(f"Total Used: {int(total_time_used)} mins | Leftover: {int(leftover_time)} mins")

# 🗂 Save Plan
final_clean_plan = "\n".join(plan_text_lines)
st.session_state.tour_plan = final_clean_plan

# 🧾 Save to Sheet
uid = st.session_state.get("unique_id")
sheet = get_consent_worksheet()
cell = sheet.find(uid, in_column=2)
if cell:
    row_num = cell.row
    sheet.update_cell(row_num, 19, final_clean_plan)
    sheet.update_cell(row_num, 20, str(int(total_time_used)))
    sheet.update_cell(row_num, 21, str(int(leftover_time)))
else:
    st.warning("⚠️ Could not save tour plan. User ID not found in the sheet.")

# ------------------------------------------
# 9. Feedback & Rating
# ------------------------------------------
st.subheader("⭐ Plan Feedback")
rating = st.slider("How would you rate your personalized tour plan?", 1, 10, 8)
feedback = st.text_area("Do you have any comments or suggestions?")

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
