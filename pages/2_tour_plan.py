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

weight_output['low'] = fuzz.trimf(weight_output.universe, [0, 0, 5])
weight_output['medium'] = fuzz.trimf(weight_output.universe, [2, 5, 8])
weight_output['high'] = fuzz.trimf(weight_output.universe, [5, 10, 10])

food_interval = ctrl.Consequent(np.arange(60, 241, 1), 'food_interval')

food_interval['short'] = fuzz.trimf(food_interval.universe, [60, 90, 120])
food_interval['medium'] = fuzz.trimf(food_interval.universe, [100, 135, 170])
food_interval['long'] = fuzz.trimf(food_interval.universe, [160, 240, 240])

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

    ctrl.Rule(intensity_input['high'] & walking_input['long'], weight_output['medium']),
    ctrl.Rule(intensity_input['high'] & wait_tolerance['low'], weight_output['medium']),
    ctrl.Rule(intensity_input['high'] & preference_input['low'], weight_output['low']),
    ctrl.Rule(intensity_input['low'], weight_output['medium'])  # light zones get neutral boost,
    ]

food_interval_rules = [
    ctrl.Rule(preference_input['high'] & priority_food['yes'], food_interval['short']),
    ctrl.Rule(preference_input['medium'] & priority_food['yes'], food_interval['medium']),
    ctrl.Rule(preference_input['low'] | priority_food['no'], food_interval['long']),
]

food_interval_ctrl = ctrl.ControlSystem(food_interval_rules)
food_interval_sim = ctrl.ControlSystemSimulation(food_interval_ctrl)

# Special reinforcement for top preference zone
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

# Combine with main rules
rules += reinforcement_rules

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
# Sort zones by normalized fuzzy weights
sorted_zones = sorted(normalized_weights, key=lambda z: normalized_weights[z], reverse=True)

ride_zones = ["thrill", "water", "family", "entertainment"]
ride_zones_present = [z for z in preferences if z in ride_zones]

if ride_zones_present:
    top_pref_zone = max(ride_zones_present, key=lambda z: preferences[z])
else:
    top_pref_zone = "family"  # fallback to safe zone

# Guarantee its inclusion in the initial attractions
initial_attractions = []
if top_pref_zone in zones and zones[top_pref_zone]:
    initial_attractions.append(zones[top_pref_zone][0])

# Now fill remaining attractions from top-weighted zones (excluding already included one)
for zone in sorted_zones:
    if zone != top_pref_zone:
        for attraction in zones[zone]:
            if attraction not in initial_attractions:
                initial_attractions.append(attraction)
                break  # Only one from each zone
    if len(initial_attractions) >= 4:
        break

# Calculate remaining time
remaining_time = visit_duration - sum([
    attraction_durations[a] + attraction_wait_times[a] for a in initial_attractions
])

# Add more attractions if time allows (respects fuzzy ranking)
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

final_route = greedy_route(initial_attractions, start_with=first_pref_attraction)

food_pref = preferences["food"]

food_interval_sim.input['preference'] = food_pref
food_interval_sim.input['priority_food'] = priority_food_val
food_interval_sim.compute()

preferred_food_gap = int(np.clip(food_interval_sim.output['food_interval'], 60, 240))  # cap between 1h and 4h

# ------------------------------------------
# 7. Break Insertion
# ------------------------------------------

# 🧠 Automatically reorder medium-intensity zones for rhythm
def reorder_medium_intensity(route):
    medium_stops = []
    other_stops = []

    for stop in route:
        zone = next(z for z, a in zones.items() if stop in a)
        intensity = zone_intensity[zone]
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

    for i, stop in enumerate(route):
        updated.append(stop)
        zone = next(z for z, a in zones.items() if stop in a)

        duration = attraction_durations[stop]
        wait = attraction_wait_times[stop]
        time_spent = duration + wait
        walk_dist = calculate_distance(current_location, attraction_coordinates[stop])
        walk_time = max(1, int(walk_dist / walking_speed))

        total_this_stop = time_spent + walk_time
        total_elapsed_time += total_this_stop
        elapsed_since_break += total_this_stop
        elapsed_since_food += total_this_stop

        # 🔋 Energy loss
        energy_loss = zone_intensity.get(zone, 1) * energy_settings['loss_factor'] * 6
        energy_level = max(0, energy_level - energy_loss)

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
            relax = [s for s in zones["relaxation"] if s not in used_break_spots]
            if relax:
                best = min(relax, key=lambda s: calculate_distance(attraction_coordinates[stop], attraction_coordinates[s]))
                updated.append(best)
                used_break_spots.add(best)
                elapsed_since_break = 0
                energy_level = min(100, energy_level + energy_settings['rest_boost'])
                last_break_time = total_elapsed_time

        # 🍔 Food logic
        if elapsed_since_food >= preferred_food_gap:
            options = [f for f in zones["food"] if f not in used_food_spots]
            if options:
                best = min(options, key=lambda f: calculate_distance(attraction_coordinates[stop], attraction_coordinates[f]))
                updated.append(best)
                used_food_spots.add(best)
                elapsed_since_food = 0
                energy_level = min(100, energy_level + energy_settings['food_boost'])

        current_location = attraction_coordinates[stop]

    return updated

# 🚦 Final plan construction
final_route = reorder_medium_intensity(final_route)
final_plan = insert_breaks(final_route)

import matplotlib.pyplot as plt

energy = 100
energy_timeline = [energy]
time_timeline = [0]
labels = []

elapsed_time = 0
total_time_check = 0
previous_location = (0, 0)

for stop in final_plan:
    zone = next(z for z, a in zones.items() if stop in a)
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
#st.pyplot(fig)

# ------------------------------------------
# 8. Display & Time Calculation with Walks
# ------------------------------------------
zone_emojis = {
    "thrill": "🎢", "water": "💦", "family": "👨‍👩‍👧‍👦",
    "entertainment": "🎭", "food": "🍔", "shopping": "🛍️", "relaxation": "🌳"
}


plan_text_lines = []
total_time_used = 0
previous_location = (0, 0)
start_time = datetime.strptime("10:00", "%H:%M")  # park opening time

show_details = st.checkbox("Show detailed time allocation", value=False)

with st.expander("The Fun Starts Here", expanded=True):
    st.markdown("🏁 **Entrance**")
    for stop in final_plan:
        scheduled_time = start_time + timedelta(minutes=total_time_used)
        formatted_time = scheduled_time.strftime("%I:%M %p")

        ride_time = attraction_durations[stop]
        wait_time = attraction_wait_times[stop]
        attraction_loc = attraction_coordinates[stop]
        walk_dist = calculate_distance(previous_location, attraction_loc)
        walk_time = max(1, int(walk_dist / walking_speed))
        total_duration = int(ride_time + wait_time + walk_time)

        if total_time_used + total_duration > visit_duration + 15:
            break

        zone = next(z for z, a in zones.items() if stop in a)
        emoji = zone_emojis.get(zone, "📍")

        # Tagging special stops
        tag = ""
        if zone == "relaxation":
            tag = " 🌿 **[Rest Stop]**"
            st.markdown("---")
        elif zone == "food":
            tag = " 🍽️ **[Meal Break]**"
            st.markdown("---")

        # Main itinerary line
        main_line = f"{emoji} **{formatted_time} — {stop}**{tag} — **{total_duration} minutes**"
        st.markdown(main_line)

        # Detail breakdown (for all types)
        if show_details:
            st.markdown(f"• Includes: {ride_time}m ride, {wait_time}m wait, {walk_time}m walk")

        if zone in ["relaxation", "food"]:
            st.markdown("---")

        # Update state
        previous_location = attraction_loc
        total_time_used += total_duration

    st.markdown("\n🏁 **Exit**")

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
