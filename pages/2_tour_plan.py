# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. Imports and Setup
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import math
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from datetime import timedelta, datetime

from functools import lru_cache

@lru_cache(maxsize=None)
def get_fuzzy_weight(preference, accessibility, wait_tol, walking, priority_thrill, priority_food, priority_comfort, intensity, repeat_count):
    weight_sim.input['preference'] = preference
    weight_sim.input['accessibility'] = accessibility
    weight_sim.input['wait_tolerance'] = wait_tol
    weight_sim.input['walking'] = walking
    weight_sim.input['priority_thrill'] = priority_thrill
    weight_sim.input['priority_food'] = priority_food
    weight_sim.input['priority_comfort'] = priority_comfort
    weight_sim.input['intensity'] = intensity
    weight_sim.input['zone_repeat_count'] = repeat_count
    weight_sim.compute()
    return weight_sim.output['weight']

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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Load questionnaire data from session
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if "questionnaire" not in st.session_state:
    st.warning("❗ Please complete the questionnaire first.")
    st.stop()

data = st.session_state["questionnaire"]

# Extract answers
preference_ranks = {
    "thrill": data["thrill"], "family": data["family"], "water": data["water"],
    "entertainment": data["entertainment"], "food": data["food"],
    "shopping": data["shopping"], "relaxation": data["relaxation"]
}
preferences = {k: 8 - v for k, v in preference_ranks.items()}
priorities = data["priorities"]
walking_pref = data["walking"]
break_pref = data["break"]

# Visit duration
duration_map = {"<2 hrs": 90, "2–4 hrs": 180, "4–6 hrs": 300, "All day": 420}
visit_duration = duration_map.get(data["duration"], 180)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Define zones and coordinates
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCALE_FACTOR_METERS_PER_UNIT = 2.0  # Each grid unit is 2 meters

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

# Calculate coordinates for each attraction
attraction_coordinates = {}
for zone, attractions in zones.items():
    for idx, attraction in enumerate(attractions):
        angle = idx * (2 * np.pi / len(attractions))  # even angle distribution
        radius = 80  # increase for more spacing
        offset_x = int(radius * np.cos(angle))
        offset_y = int(radius * np.sin(angle))
        zone_x, zone_y = zone_coordinates[zone]
        attraction_coordinates[attraction] = (zone_x + offset_x, zone_y + offset_y)

# Utility location
change_location = "Shower & Changing Room"
change_coordinates = (450, 250)  
attraction_coordinates[change_location] = change_coordinates

# ------------------------------------------
# 4. Ride durations, wait times, and accessibility levels
# ------------------------------------------
accessibility_factors = {
    "thrill": 0.7, "water": 0.8, "family": 1.0,
    "entertainment": 0.9, "food": 1.0, "shopping": 1.0, "relaxation": 1.0
}


CLOTHING_CHANGE_DURATION = 10 

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

# Intensity used later for energy logic and pacing
zone_intensity = {
    "thrill": 0.95,         # High energy demand (e.g. roller coasters)
    "water": 0.75,          # Swimming or flume-based attractions
    "family": 0.55,         # Interactive but moderate exertion
    "entertainment": 0.35,  # Low exertion, seated shows
    "food": 0.15,           # Resting and eating
    "shopping": 0.25,       # Low walking activity
    "relaxation": 0.1       # Passive resting (benches, gardens)
}


# Tag wet rides for special scheduling logic
wet_ride_names = {"Water Slide", "Wave Pool", "Splash Battle"}

# ------------------------------------------
# 5A. Fuzzy inputs (user traits and ride traits)
# ------------------------------------------

preference_input     = ctrl.Antecedent(np.arange(0, 11, 1), 'preference')        # 0–10: how much user likes the zone
accessibility_input  = ctrl.Antecedent(np.arange(0.0, 1.1, 0.1), 'accessibility') # 0–1: ease of access
wait_tolerance       = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'wait_tolerance')  # 0–1: patience for waiting
walking_input        = ctrl.Antecedent(np.arange(0.0, 1.1, 0.1), 'walking')       # 0–1: walking comfort

priority_thrill      = ctrl.Antecedent(np.arange(0, 2, 1), 'priority_thrill')
priority_food        = ctrl.Antecedent(np.arange(0, 2, 1), 'priority_food')
priority_comfort     = ctrl.Antecedent(np.arange(0, 2, 1), 'priority_comfort')

intensity_input      = ctrl.Antecedent(np.arange(0.0, 1.1, 0.1), 'intensity')

weight_output        = ctrl.Consequent(np.arange(0, 11, 1), 'weight')

zone_repeat_count = ctrl.Antecedent(np.arange(0, 4, 1), 'zone_repeat_count')  # 0–3 recent repeats

food_interval = ctrl.Consequent(np.arange(60, 241, 1), 'food_interval')

# ------------------------------------------
# 5B. Membership functions
# ------------------------------------------

# Preference score from 0–10
preference_input['low'] = fuzz.trimf(preference_input.universe, [0, 0, 5])
preference_input['medium'] = fuzz.trimf(preference_input.universe, [2, 5, 8])
preference_input['high'] = fuzz.trimf(preference_input.universe, [5, 10, 10])

# Accessibility of the zone (0 = difficult, 1 = easy)
accessibility_input['poor'] = fuzz.trimf(accessibility_input.universe, [0.0, 0.0, 0.5])
accessibility_input['moderate'] = fuzz.trimf(accessibility_input.universe, [0.2, 0.5, 0.8])
accessibility_input['good'] = fuzz.trimf(accessibility_input.universe, [0.5, 1.0, 1.0])

# User’s wait tolerance
wait_tolerance['low'] = fuzz.trimf(wait_tolerance.universe, [0.0, 0.0, 0.4])
wait_tolerance['medium'] = fuzz.trimf(wait_tolerance.universe, [0.2, 0.5, 0.8])
wait_tolerance['high'] = fuzz.trimf(wait_tolerance.universe, [0.6, 1.0, 1.0])

# User’s walking tolerance
walking_input['short'] = fuzz.trimf(walking_input.universe, [0.0, 0.0, 0.4])
walking_input['medium'] = fuzz.trimf(walking_input.universe, [0.2, 0.5, 0.8])
walking_input['long'] = fuzz.trimf(walking_input.universe, [0.6, 1.0, 1.0])

# User priorities: thrill, food, comfort
for priority in [priority_thrill, priority_food, priority_comfort]:
    priority['no'] = fuzz.trimf(priority.universe, [0, 0, 1])
    priority['yes'] = fuzz.trimf(priority.universe, [0, 1, 1])

# Ride intensity (by zone)
intensity_input['low'] = fuzz.trimf(intensity_input.universe, [0.0, 0.0, 0.4])
intensity_input['medium'] = fuzz.trimf(intensity_input.universe, [0.3, 0.5, 0.7])
intensity_input['high'] = fuzz.trimf(intensity_input.universe, [0.6, 1.0, 1.0])

# Final weight score for each zone (0–10)
weight_output['low'] = fuzz.trimf(weight_output.universe, [0, 0, 4])
weight_output['medium'] = fuzz.trimf(weight_output.universe, [3, 5, 7])
weight_output['high'] = fuzz.trimf(weight_output.universe, [6, 10, 10])

food_interval['short'] = fuzz.trimf(food_interval.universe, [60, 90, 120])
food_interval['medium'] = fuzz.trimf(food_interval.universe, [100, 135, 170])
food_interval['long'] = fuzz.trimf(food_interval.universe, [160, 240, 240])

zone_repeat_count['none'] = fuzz.trimf(zone_repeat_count.universe, [0, 0, 1])
zone_repeat_count['few'] = fuzz.trimf(zone_repeat_count.universe, [0, 1, 2])
zone_repeat_count['many'] = fuzz.trimf(zone_repeat_count.universe, [1, 3, 3])


# ------------------------------------------
# 5C. Fuzzy Rules: Inputs → Weight Output
# ------------------------------------------

top_zone = max(preferences, key=preferences.get)

rules = []


# I. Core Logic: Preference × Accessibility
rules += [
    ctrl.Rule(preference_input['high'] & accessibility_input['good'], weight_output['high']),
    ctrl.Rule(preference_input['high'] & accessibility_input['moderate'], weight_output['medium']),
    ctrl.Rule(preference_input['high'] & accessibility_input['poor'], weight_output['medium']),

    ctrl.Rule(preference_input['medium'] & accessibility_input['good'], weight_output['medium']),
    ctrl.Rule(preference_input['medium'] & accessibility_input['moderate'], weight_output['medium']),
    ctrl.Rule(preference_input['medium'] & accessibility_input['poor'], weight_output['low']),

    ctrl.Rule(preference_input['low'], weight_output['low']),
]

# II. User Profile Traits: Walk & Wait Tolerance
rules += [
    ctrl.Rule(wait_tolerance['low'], weight_output['low']),
    ctrl.Rule(wait_tolerance['high'], weight_output['high']),
    ctrl.Rule(walking_input['short'], weight_output['low']),
    ctrl.Rule(walking_input['long'], weight_output['high']),
]

# III. User Declared Priorities
rules += [
    ctrl.Rule(priority_thrill['yes'], weight_output['high']),
    ctrl.Rule(priority_food['yes'], weight_output['medium']),
    ctrl.Rule(priority_comfort['yes'], weight_output['medium']),
]

# IV. Intensity Adjustment
rules += [
    ctrl.Rule(intensity_input['high'] & preference_input['high'], weight_output['medium']),
    ctrl.Rule(intensity_input['high'] & preference_input['low'], weight_output['low']),
    ctrl.Rule(intensity_input['low'], weight_output['medium']),
]

rules += [
    ctrl.Rule(zone_repeat_count['many'], weight_output['low']),
    ctrl.Rule(zone_repeat_count['few'], weight_output['medium']),
    ctrl.Rule(zone_repeat_count['none'], weight_output['high']),
]

# V. Top-Zone Reinforcement

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

# ------------------------------------------
# 5D. Fuzzy Subsystem: Food Interval Estimation
# ------------------------------------------

food_interval_rules = [
    ctrl.Rule(preference_input['high'] & priority_food['yes'], food_interval['short']),
    ctrl.Rule(preference_input['medium'] & priority_food['yes'], food_interval['medium']),
    ctrl.Rule(preference_input['low'] | priority_food['no'], food_interval['long']),
]

food_interval_ctrl = ctrl.ControlSystem(food_interval_rules)
food_interval_sim = ctrl.ControlSystemSimulation(food_interval_ctrl)

# ------------------------------------------
# 5E. Fuzzy Rules: Energy Loss Estimation
# ------------------------------------------

# Input: Ride intensity, walking time, age sensitivity
intensity_input_energy = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'intensity')
walk_time_input = ctrl.Antecedent(np.arange(0, 16, 1), 'walk_time')  # up to 15 minutes walk
age_sensitivity_input = ctrl.Antecedent(np.arange(0.8, 1.4, 0.1), 'age_sensitivity')

# Output: Energy lost per stop
energy_loss_output = ctrl.Consequent(np.arange(0, 21, 1), 'energy_loss')  # 0–20 points per stop

# Membership functions
intensity_input_energy['low'] = fuzz.trimf(intensity_input_energy.universe, [0.0, 0.0, 0.4])
intensity_input_energy['medium'] = fuzz.trimf(intensity_input_energy.universe, [0.3, 0.5, 0.7])
intensity_input_energy['high'] = fuzz.trimf(intensity_input_energy.universe, [0.6, 1.0, 1.0])

walk_time_input['short'] = fuzz.trimf(walk_time_input.universe, [0, 0, 5])
walk_time_input['medium'] = fuzz.trimf(walk_time_input.universe, [3, 7, 11])
walk_time_input['long'] = fuzz.trimf(walk_time_input.universe, [10, 15, 15])

age_sensitivity_input['low'] = fuzz.trimf(age_sensitivity_input.universe, [0.8, 0.8, 1.0])
age_sensitivity_input['medium'] = fuzz.trimf(age_sensitivity_input.universe, [0.9, 1.1, 1.2])
age_sensitivity_input['high'] = fuzz.trimf(age_sensitivity_input.universe, [1.1, 1.3, 1.4])

energy_loss_output['low'] = fuzz.trimf(energy_loss_output.universe, [0, 0, 8])
energy_loss_output['medium'] = fuzz.trimf(energy_loss_output.universe, [5, 10, 15])
energy_loss_output['high'] = fuzz.trimf(energy_loss_output.universe, [12, 20, 20])

# Rules
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

# ------------------------------------------
# 5F. Fuzzy Controller Setup and User Mappings
# ------------------------------------------

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

# Helper: Compute fuzzy-based energy loss per stop
def compute_energy_loss(intensity, walk_time, age_factor):
    try:
        # Clamp to valid fuzzy input ranges
        intensity = min(max(intensity, 0.0), 1.0)
        walk_time = min(max(walk_time, 0), 15)
        age_factor = min(max(age_factor, 0.8), 1.4)

        energy_loss_sim.input['intensity'] = intensity
        energy_loss_sim.input['walk_time'] = walk_time
        energy_loss_sim.input['age_sensitivity'] = age_factor
        energy_loss_sim.compute()

        return energy_loss_sim.output['energy_loss']
    except Exception as e:
        print(f"⚠️ Energy loss fallback due to: {e}")
        return 8  # Safe default

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. Fuzzy Weight Evaluation and Zone Scoring
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

zone_weights = {}

for zone in zones:
    pref = preferences[zone]
    acc = accessibility_factors[zone]
    intensity = zone_intensity[zone]

    repeat_count = 0  # Fallback for now unless using real sequencing context

    weight_sim.input['preference'] = pref
    weight_sim.input['accessibility'] = acc
    weight_sim.input['wait_tolerance'] = wait_val
    weight_sim.input['walking'] = walking_val
    weight_sim.input['priority_thrill'] = 1.0 if zone == "thrill" and priority_thrill_val else 0.0
    weight_sim.input['priority_food'] = 1.0 if zone == "food" and priority_food_val else 0.0
    weight_sim.input['priority_comfort'] = 1.0 if zone == "relaxation" and priority_comfort_val else 0.0
    weight_sim.input['intensity'] = intensity
    weight_sim.input['zone_repeat_count'] = repeat_count

    weight_sim.compute()
    zone_weights[zone] = weight_sim.output['weight']
        
# Cap passive zones
for zone in ["food", "relaxation"]:
    if zone in zone_weights:
        zone_weights[zone] = min(zone_weights[zone], 4.5)  # limit to moderate level

# Normalize weights
total_weight = sum(zone_weights.values())
if total_weight > 0:
    normalized_weights = {z: w / total_weight for z, w in zone_weights.items()}
else:
    normalized_weights = {z: 1 / len(zone_weights) for z in zone_weights}  # equal weighting

# Remove intense rides for children
if data["age"] == "Under 12":
    intense_rides = {"Roller Coaster", "Drop Tower", "Freefall Cannon", "Spinning Vortex"}
    for ride in intense_rides:
        for zone_list in zones.values():
            if ride in zone_list:
                zone_list.remove(ride)
                
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. Attraction Scoring Based on Zone Weights + Rhythm
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WAIT_PENALTY_FACTOR = 0.02     # reduces score if wait is high
INTENSITY_COMFORT_FACTOR = 0.2 # bonus for low intensity zones

attraction_scores = {}
recent_zones = []

# ─── Ensure wet_time_pct has safe default ───
if 'wet_time_pct' not in globals() or wet_time_pct is None:
    wet_time_pct = 50
    

for zone in ["thrill", "water", "family", "entertainment", "shopping"]:
    attractions = zones[zone]
    for attraction in attractions:
        wait_time = attraction_wait_times.get(attraction, 0)
        duration = attraction_durations.get(attraction, 5)
        intensity = zone_intensity.get(zone, 0.5)
        acc = accessibility_factors.get(zone, 1.0)
        pref = preferences.get(zone, 5)
        user_pref = pref / 10.0
        is_wet = attraction in wet_ride_names

        wet_time_threshold = wet_time_pct
        comfort_penalty = 1.0
        if is_wet and priority_comfort_val and wet_time_threshold < 35:
            comfort_penalty = 0.7

        repeat_count = recent_zones.count(zone)
        repeat_count = min(repeat_count, 3)

        fuzzy_weight = get_fuzzy_weight(
            pref, acc, wait_val, walking_val,
            1.0 if zone == "thrill" and priority_thrill_val else 0.0,
            1.0 if zone == "food" and priority_food_val else 0.0,
            1.0 if zone == "relaxation" and priority_comfort_val else 0.0,
            intensity, repeat_count
        )

        score = (
            fuzzy_weight *
            user_pref *
            (1 - WAIT_PENALTY_FACTOR * wait_time) *
            (1 + INTENSITY_COMFORT_FACTOR * (1 - intensity)) *
            comfort_penalty
        )

        attraction_scores[attraction] = score
        recent_zones.append(zone)
        if len(recent_zones) > 4:
            recent_zones.pop(0)

# ⭐️ NEW: Exclude food and rest stops from initial selection
sorted_attractions = sorted(
    attraction_scores, 
    key=lambda a: attraction_scores[a], 
    reverse=True
)

initial_attractions = [
    a for a in sorted_attractions
    if not any(a in zones[z] for z in ["food", "relaxation"])
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. Smart Initial Attraction Selection with Rhythm
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

initial_attractions = []
time_budget = visit_duration + 15
current_time_used = 0
recent_zones = []

# Sort attractions by fuzzy-enhanced score (high to low)
ranked_attractions = sorted(attraction_scores, key=lambda a: attraction_scores[a], reverse=True)

for attraction in ranked_attractions:
    zone = next((z for z, a_list in zones.items() if attraction in a_list), None)
    if not zone:
        continue

    ride_time = attraction_durations.get(attraction, 0)
    wait_time = attraction_wait_times.get(attraction, 0)
    time_required = ride_time + wait_time

    if current_time_used + time_required > time_budget:
        continue

    # 🧠 Rhythm control: avoid same zone 3+ times in a row
    if recent_zones[-2:] == [zone, zone]:
        continue

    # Accept attraction
    initial_attractions.append(attraction)
    current_time_used += time_required
    recent_zones.append(zone)

    # Trim memory
    if len(recent_zones) > 4:
        recent_zones.pop(0)



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. Route Optimization and Wet Ride Scheduling
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def nearest_relaxation_spot(from_attraction):
    last_loc = attraction_coordinates[from_attraction]
    return min(
        zones["relaxation"],
        key=lambda spot: calculate_distance(last_loc, attraction_coordinates[spot])
    )

# ------------------------------------------
# 9A. Route Distance Functions
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

# ------------------------------------------
# 9B. Wet Ride Timing: Fuzzy Control Setup
# ------------------------------------------

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
    

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. Food Timing Estimation (Fuzzy)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

food_pref = preferences["food"]

food_interval_sim.input['preference'] = food_pref
food_interval_sim.input['priority_food'] = priority_food_val
food_interval_sim.compute()

preferred_food_gap = int(np.clip(food_interval_sim.output['food_interval'], 60, 240))  # cap between 1h and 4h



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 11. Final Route Cleanup (No Consecutive Breaks)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def no_consecutive_food_or_break(route, zones):
    """
    Reorders the route so that no two food/rest stops are consecutive.
    Instead of dropping them, it swaps them with next non-food/rest.
    """
    # Helper: identify if a stop is food or rest
    def is_soft(stop):
        zone = next((z for z, a in zones.items() if stop in a), None)
        return zone in {"food", "relaxation"}

    result = []
    i = 0
    while i < len(route):
        current_stop = route[i]
        result.append(current_stop)

        # Check next stop
        if i + 1 < len(route):
            next_stop = route[i + 1]

            if is_soft(current_stop) and is_soft(next_stop):
                # Look ahead for next non-soft to swap
                swap_idx = i + 2
                while swap_idx < len(route):
                    if not is_soft(route[swap_idx]):
                        # Swap next_stop with this
                        route[i + 1], route[swap_idx] = route[swap_idx], route[i + 1]
                        break
                    swap_idx += 1

        i += 1

    return route
    
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 12. Break and Meal Insertion Logic
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
    meal_activity_counter = 0
    last_break_time = -999
    last_meal_time = -999
    total_elapsed_time = 0
    energy_level = 100
    current_location = (0, 0)

    used_break_spots = set()
    used_food_spots = set()
    meal_break_count = 0
    max_meals = 2

    MIN_FOOD_GAP_MINUTES = 180
    MIN_FOOD_GAP_ACTIVITIES = 3
    MIN_BREAK_FOOD_SPACING = 30
    WALKING_SPEED = 50

    start_time_clock = datetime.strptime("10:00", "%H:%M")

    activities_since_last_meal = 0

    # Wet block detection
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

        duration = attraction_durations.get(stop, 5)
        wait = attraction_wait_times.get(stop, 0)
        walk_dist_units = calculate_distance(current_location, attraction_coordinates[stop])
        walk_dist_meters = walk_dist_units * SCALE_FACTOR_METERS_PER_UNIT
        walk_time = max(2, round(walk_dist_meters / WALKING_SPEED))

        total_this_stop = duration + wait + walk_time
        current_clock = start_time_clock + timedelta(minutes=total_elapsed_time)

        total_elapsed_time += total_this_stop
        elapsed_since_break += total_this_stop
        elapsed_since_food += total_this_stop
        meal_activity_counter += 1

        # Count activities for Rule 10
        is_soft = zone in ["food", "relaxation"]
        if not is_soft:
            activities_since_last_meal += 1

        # Energy loss
        intensity_val = zone_intensity.get(zone, 1.0)
        age_sens = energy_settings['loss_factor']
        energy_loss = compute_energy_loss(intensity_val, walk_time, age_sens)
        energy_level = max(0, energy_level - energy_loss)

        if in_wet_block:
            current_location = attraction_coordinates[stop]
            continue

        # ------------------------
        # REST INSERTION - Flexible (emergency)
        if (
            break_pref == "Flexible"
            and energy_level < 20
            and elapsed_since_break > 10
            and (total_elapsed_time - last_break_time) > MIN_BREAK_FOOD_SPACING
            and zone not in ["relaxation", "food"]
        ):
            relax_options = [s for s in zones["relaxation"] if s not in used_break_spots and s not in updated]
            if relax_options:
                best_relax = min(relax_options, key=lambda s: calculate_distance(attraction_coordinates[stop], attraction_coordinates[s]))
                updated.append(best_relax)
                used_break_spots.add(best_relax)
                elapsed_since_break = 0
                energy_level = min(100, energy_level + energy_settings['rest_boost'])
                last_break_time = total_elapsed_time
                activities_since_last_meal = 0

        # ------------------------
        # REST INSERTION - Scheduled (strict Rule 10)
        needs_break = (
            (break_pref == "After 1 hour" and elapsed_since_break >= 60) or
            (break_pref == "After 2 hours" and elapsed_since_break >= 120) or
            (break_pref == "After every big ride" and stop in {"Roller Coaster", "Drop Tower", "Log Flume", "Water Slide"})
        )

        if (
            needs_break
            and energy_level >= 20
            and (total_elapsed_time - last_break_time) > MIN_BREAK_FOOD_SPACING
            and zone not in ["relaxation", "food"]
            and activities_since_last_meal >= 2
        ):
            relax_options = [s for s in zones["relaxation"] if s not in used_break_spots and s not in updated]
            if relax_options:
                best_relax = min(relax_options, key=lambda s: calculate_distance(attraction_coordinates[stop], attraction_coordinates[s]))
                updated.append(best_relax)
                used_break_spots.add(best_relax)
                elapsed_since_break = 0
                energy_level = min(100, energy_level + energy_settings['rest_boost'])
                last_break_time = total_elapsed_time
                activities_since_last_meal = 0

        # ------------------------
        # MEAL INSERTION
        can_add_meal_now = (elapsed_since_food >= MIN_FOOD_GAP_MINUTES)
        min_elapsed_to_allow_meal = 120
        can_schedule_meal_time = total_elapsed_time >= min_elapsed_to_allow_meal

        if (
            can_schedule_meal_time
            and can_add_meal_now
            and meal_activity_counter >= MIN_FOOD_GAP_ACTIVITIES
            and meal_break_count < max_meals
            and zone not in ["relaxation", "food"]
            and (last_break_time == -999 or total_elapsed_time - last_break_time >= MIN_BREAK_FOOD_SPACING)
            and (last_meal_time == -999 or total_elapsed_time - last_meal_time >= MIN_BREAK_FOOD_SPACING)
        ):
            food_options = [f for f in zones["food"] if f not in used_food_spots and f not in updated]
            if food_options:
                best_food = min(food_options, key=lambda f: calculate_distance(attraction_coordinates[stop], attraction_coordinates[f]))
                updated.append(best_food)
                used_food_spots.add(best_food)
                elapsed_since_food = 0
                meal_activity_counter = 0
                meal_break_count += 1
                last_meal_time = total_elapsed_time
                energy_level = min(100, energy_level + energy_settings['food_boost'])
                activities_since_last_meal = 0

        current_location = attraction_coordinates[stop]

    while updated:
        zone = next((z for z, a in zones.items() if updated[-1] in a), None)
        if zone in ["food", "relaxation"]:
            updated.pop()
        else:
            break
    
    return updated

    
def move_meals_after_two_hours(route, min_elapsed=120):
    """
    Ensures meals are only inserted after min_elapsed minutes
    from the start of the day (e.g., 10am + 2 hours = 12pm).
    """
    meals_to_shift = []
    before_limit = []
    after_limit = []

    total_time = 0
    previous_location = (0, 0)

    for stop in route:
        if stop.startswith("[Clothing Change]"):
            total_time += CLOTHING_CHANGE_DURATION
            target_list = after_limit if total_time >= min_elapsed else before_limit
            target_list.append(stop)
            continue

        zone = next((z for z, a in zones.items() if stop in a), None)
        if zone is None:
            total_time += 5
            target_list = after_limit if total_time >= min_elapsed else before_limit
            target_list.append(stop)
            continue

        duration = attraction_durations.get(stop, 5)
        wait = attraction_wait_times.get(stop, 0)
        walk_dist_units = calculate_distance(previous_location, attraction_coordinates[stop])
        walk_dist_meters = walk_dist_units * SCALE_FACTOR_METERS_PER_UNIT
        walk_time = max(2, round(walk_dist_meters / 50))

        total_this_stop = duration + wait + walk_time

        if zone == "food":
            # Always shift meals out
            meals_to_shift.append(stop)
        else:
            if total_time >= min_elapsed:
                after_limit.append(stop)
            else:
                before_limit.append(stop)

        total_time += total_this_stop
        previous_location = attraction_coordinates[stop]

    # Build final route
    final_route = before_limit
    final_route.extend(meals_to_shift)
    final_route.extend(after_limit)

    return final_route
    

def enforce_max_two_meals(route):
    cleaned = []
    food_count = 0
    food_seen = set()

    for stop in route:
        zone = next((z for z, a in zones.items() if stop in a), None)
        if zone == "food":
            if stop not in food_seen and food_count < 2:
                cleaned.append(stop)
                food_seen.add(stop)
                food_count += 1
            # else skip duplicate
        else:
            cleaned.append(stop)
    return cleaned

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 13. Final Route Optimization and Tweaks
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def remove_trailing_breaks(route):
    while route:
        zone = next((z for z, a in zones.items() if route[-1] in a), None)
        if zone in ["food", "relaxation"]:
            route.pop()
        else:
            break
    return route
    
# 1️⃣ After initial reordering
optimized_initial = reorder_by_distance(
    initial_attractions,
    start_location=attraction_coordinates[first_pref_attraction] if first_pref_attraction else (0, 0)
)
def show_breaks_debug(stage, route, zones):
    food_stops = [s for s in route if any(s in zones[z] for z in ["food"])]
    rest_stops = [s for s in route if any(s in zones[z] for z in ["relaxation"])]

    st.markdown(f"**🧭 Debug: {stage}**")
    st.write(f"🍽️ Meal Stops ({len(food_stops)}):", food_stops)
    st.write(f"🌳 Rest Stops ({len(rest_stops)}):", rest_stops)

    st.write(f"📜 **Full Plan ({len(route)} stops):**")
    for i, stop in enumerate(route, 1):
        zone = next((z for z, a in zones.items() if stop in a), "Unknown")
        st.markdown(f"{i}. {stop} *(Zone: {zone})*")
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

first_preference_zone = max(preferences, key=preferences.get)
first_pref_attraction = next(
    (a for a in zones[first_preference_zone] if a in initial_attractions),
    None
)

# ➜ Apply distance optimization
optimized_initial = reorder_by_distance(
    initial_attractions,
    start_location=attraction_coordinates[first_pref_attraction] if first_pref_attraction else (0, 0)
)
show_breaks_debug("After reorder_by_distance", optimized_initial, zones)

# ➜ Schedule wet rides mid-tour
wet_scheduled = schedule_wet_rides_midday(optimized_initial, wet_ride_names, zones)

# ➜ Insert breaks and meals
full_allocated_plan = insert_breaks(wet_scheduled)
full_allocated_plan = list(dict.fromkeys(full_allocated_plan))  # Remove exact duplicates
show_breaks_debug("After insert_breaks", full_allocated_plan, zones)

# ➜ Trim plan to fit within visit duration
trimmed_plan = []
time_used = 0
previous_location = (0, 0)

for stop in full_allocated_plan:
    if stop.startswith("[Clothing Change]"):
        stop_time = CLOTHING_CHANGE_DURATION
    else:
        ride_time = attraction_durations.get(stop, 5)
        wait_time = attraction_wait_times.get(stop, 0)

        if stop in attraction_coordinates:
            walk_units = calculate_distance(previous_location, attraction_coordinates[stop])
            previous_location = attraction_coordinates[stop]
        else:
            walk_units = 0  # Default to 0 if unknown

        walk_meters = walk_units * SCALE_FACTOR_METERS_PER_UNIT
        walk_time = max(1, round(walk_meters / walking_speed))
        stop_time = ride_time + wait_time + walk_time

    if time_used + stop_time > visit_duration + 15:
        break

    trimmed_plan.append(stop)
    time_used += stop_time

show_breaks_debug("After time-based trimming", trimmed_plan, zones)

# ➜ Finally remove any trailing break stops
final_plan = remove_trailing_breaks(trimmed_plan)
show_breaks_debug("After remove_trailing_breaks", final_plan, zones)

import matplotlib.pyplot as plt

# ➜ Use only the filtered plan
energy = 100
energy_timeline = [energy]
time_timeline = [0]
labels = []
stop_label_points = []

elapsed_time = 0
total_time_check = 0
previous_location = (0, 0)

# 💡 THIS IS THE KEY CHANGE
# We will use only those stops that fit in time budget.
energy_plan_used = []
total_time_check_for_plan = 0

for stop in final_plan:
    if stop.startswith("[Clothing Change]"):
        continue

    duration = attraction_durations.get(stop, 5)
    wait = attraction_wait_times.get(stop, 0)
    walk_dist_units = calculate_distance(previous_location, attraction_coordinates[stop])
    walk_dist_meters = walk_dist_units * SCALE_FACTOR_METERS_PER_UNIT
    walk_time = max(1, round(walk_dist_meters / walking_speed))
    total_this_stop = duration + wait + walk_time

    if total_time_check_for_plan + total_this_stop > visit_duration + 15:
        break

    energy_plan_used.append(stop)
    total_time_check_for_plan += total_this_stop
    previous_location = attraction_coordinates[stop]

# Now simulate only these
energy = 100
elapsed_time = 0
total_time_check = 0
previous_location = (0, 0)

for stop in energy_plan_used:
    zone = next((z for z, a in zones.items() if stop in a), None)
    if zone is None:
        continue

    intensity = zone_intensity.get(zone, 1.0)
    duration = attraction_durations.get(stop, 5)
    wait = attraction_wait_times.get(stop, 0)
    walk_dist_units = calculate_distance(previous_location, attraction_coordinates[stop])
    walk_dist_meters = walk_dist_units * SCALE_FACTOR_METERS_PER_UNIT
    walk_time = max(1, round(walk_dist_meters / walking_speed))
    total_this_stop = duration + wait + walk_time

    # Age-adjusted boosts
    adjusted_rest_boost = energy_settings['rest_boost'] * (2 - energy_settings['loss_factor'])
    adjusted_food_boost = energy_settings['food_boost'] * (2 - energy_settings['loss_factor'])

    # ✅ Sample every 5 minutes to reduce plot size
    SAMPLING_INTERVAL = 5

    if zone in ["relaxation", "food"]:
        # Recharge stops only ONCE
        boost = adjusted_rest_boost if zone == "relaxation" else adjusted_food_boost
        for minute in range(duration):
            energy += boost / duration
            energy = min(100, energy)
            if minute % SAMPLING_INTERVAL == 0 or minute == duration - 1:
                energy_timeline.append(energy)
                time_timeline.append(elapsed_time)
            elapsed_time += 1
            total_time_check += 1
        # Add *one* label
        stop_label_points.append((elapsed_time, energy, stop, zone))
    else:
        # Energy loss over entire total_this_stop
        energy_loss = compute_energy_loss(intensity, walk_time, energy_settings['loss_factor'])
        loss_per_minute = energy_loss / max(1, total_this_stop)
        for minute in range(total_this_stop):
            energy -= loss_per_minute
            if intensity < 0.3:
                energy += (adjusted_rest_boost * 0.2) / total_this_stop
            energy = max(0, min(100, energy))
            if minute % SAMPLING_INTERVAL == 0 or minute == total_this_stop - 1:
                energy_timeline.append(energy)
                time_timeline.append(elapsed_time)
            elapsed_time += 1
            total_time_check += 1
        # Add *one* label
        stop_label_points.append((elapsed_time, energy, stop, zone))

    previous_location = attraction_coordinates[stop]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 15. Final Schedule Display with Times
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
        walk_dist_units = calculate_distance(previous_location, attraction_coordinates[stop])
        walk_dist_meters = walk_dist_units * SCALE_FACTOR_METERS_PER_UNIT
        walk_time = max(1, round(walk_dist_meters / walking_speed))
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
            if zone == "food":
                detail_line = f"• Includes: {ride_time}m meal time, {wait_time}m wait, {walk_time}m walk"
            elif zone == "relaxation":
                detail_line = f"• Includes: {ride_time}m rest time, {wait_time}m wait, {walk_time}m walk"
            else:
                detail_line = f"• Includes: {ride_time}m ride time, {wait_time}m wait, {walk_time}m walk"
            st.markdown(detail_line)

        if zone in ["relaxation", "food"]:
            st.markdown("---")

        plan_text_lines.append(f"{formatted_time} — {save_name} — {total_duration} minutes")
        plan_text_lines.append(f"Includes: {ride_time}m ride, {wait_time}m wait, {walk_time}m walk")

        total_time_used += total_duration
        previous_location = attraction_loc

    st.markdown("🏁 **Exit**")
    plan_text_lines.append("Exit")


    
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 16. Saving to Session and Google Sheet
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
leftover_time = visit_duration - total_time_used
st.info(f"Total Used: {int(total_time_used)} mins | Leftover: {int(leftover_time)} mins")

# Save Plan
final_clean_plan = "\n".join(plan_text_lines)
st.session_state.tour_plan = final_clean_plan

# 🧾 Save to Sheet
uid = st.session_state.get("unique_id")
sheet = get_consent_worksheet()
cell = sheet.find(uid, in_column=2)
if cell:
    row_num = cell.row
    sheet.update_cell(row_num, 17, final_clean_plan)
    sheet.update_cell(row_num, 18, str(int(total_time_used)))
    sheet.update_cell(row_num, 19, str(int(leftover_time)))
else:
    st.warning("⚠️ Could not save tour plan. User ID not found in the sheet.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 14. Energy Visualization (Line Plot)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ✅ Downsample to avoid too many points for plotting
if len(energy_timeline) > 800:
    SAMPLING_RATE = len(energy_timeline) // 400
    energy_timeline = energy_timeline[::SAMPLING_RATE]
    time_timeline = time_timeline[::SAMPLING_RATE]

st.markdown("---")
st.markdown("### 📈 Energy Level Graph")
st.markdown("""
This graph shows how your estimated energy level changes throughout the day based on your planned activities.
- High-energy rides tend to reduce energy faster.
- Meal and rest stops help recharge.
- Walking time is also included in energy loss.

Use this to see how well-paced your itinerary is, and where you might want to plan extra breaks!
""")

show_energy_plot = st.checkbox("Show energy level graph", value=True)

if show_energy_plot:
    fig, ax = plt.subplots(figsize=(12, 8))

    # 1️⃣ Energy line plot
    ax.plot(time_timeline, energy_timeline, color='#2E86AB', linewidth=1.5, linestyle='-')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_facecolor('#f9f9f9')

    # 2️⃣ Energy bands
    ax.axhspan(80, 100, color='green', alpha=0.1, label='High Energy (80–100%)')
    ax.axhspan(50, 80, color='yellow', alpha=0.1, label='Moderate Energy (50–80%)')
    ax.axhspan(0, 50, color='red', alpha=0.1, label='Low Energy (<50%)')

    # 3️⃣ Entrance marker
    ax.scatter(time_timeline[0], 100, color='green', marker='o', s=60, zorder=3)
    ax.annotate(
        "Entrance\n100%",
        (time_timeline[0], 100),
        textcoords="offset points",
        xytext=(0, 10),
        ha='center',
        fontsize=8
    )

    # 4️⃣ Custom markers for food/rest/rides
    last_time_point = None
    for i, (time_point, energy_level, stop_name, zone) in enumerate(stop_label_points):
        if time_point > time_timeline[-1]:
            continue  # Don't annotate past truncated end

        label_text = f"{stop_name[:12]}…\n{int(energy_level)}%" if len(stop_name) > 15 else f"{stop_name}\n{int(energy_level)}%"

        if zone == "food":
            marker_style = 's'
            color = 'green'
        elif zone == "relaxation":
            marker_style = 'D'
            color = 'darkgreen'
        else:
            marker_style = 'o'
            color = 'blue'

        # Dynamic offset for overlap
        y_offset = 20
        if last_time_point is not None:
            if abs(time_point - last_time_point) < 5:
                y_offset = 35 if (i % 2 == 0) else -40
            else:
                y_offset = 20 if (i % 2 == 0) else -25
        last_time_point = time_point

        ax.scatter(time_point, energy_level, marker=marker_style, color=color, s=60, zorder=3)
        ax.annotate(
            label_text,
            (time_point, energy_level),
            textcoords="offset points",
            xytext=(0, y_offset),
            ha='center',
            fontsize=8
        )

    # 5️⃣ Legend
    ax.scatter([], [], marker='o', color='blue', label='Ride')
    ax.scatter([], [], marker='s', color='green', label='Meal Stop')
    ax.scatter([], [], marker='D', color='darkgreen', label='Rest Stop')
    ax.legend()

    # 6️⃣ Titles and labels
    ax.set_title("Visitor Energy Level Throughout the Day", fontsize=16, weight='bold')
    ax.set_xlabel("Minutes Elapsed", fontsize=12)
    ax.set_ylabel("Energy Level (%)", fontsize=12)
    ax.set_ylim(0, 110)

    fig.tight_layout()
    st.pyplot(fig)

# Divider before feedback section
st.markdown("---")

#  Feedback & Rating

st.subheader("⭐ Plan Feedback")

st.markdown("""
<span style='font-family:Inter, sans-serif; font-size:17px; font-weight:400'>
Please rate the following aspects of your personalized plan:
</span>
""", unsafe_allow_html=True)

likert_options = [
    "Strongly Disagree",
    "Disagree",
    "Neutral",
    "Agree",
    "Strongly Agree"
]

likert_mapping = {
    "Strongly Disagree": 1,
    "Disagree": 2,
    "Neutral": 3,
    "Agree": 4,
    "Strongly Agree": 5
}

st.markdown("")

# 1️⃣ Spacing question
st.markdown("""
<span style='font-family:Inter, sans-serif; font-size:16px; font-weight:600'>
1. The spacing between activities, including breaks, felt balanced.
</span>
""", unsafe_allow_html=True)
q_spacing = st.radio(
    label="",
    options=likert_options,
    index=2,
    horizontal=True,
    key="spacing",
    label_visibility="collapsed"
)

# 2️⃣ Variety question
st.markdown("""
<span style='font-family:Inter, sans-serif; font-size:16px; font-weight:600'>
2. The variety of attractions matched my interests.
</span>
""", unsafe_allow_html=True)
q_variety = st.radio(
    label="",
    options=likert_options,
    index=2,
    horizontal=True,
    key="variety",
    label_visibility="collapsed"
)

# 3️⃣ Meal timing question
st.markdown("""
<span style='font-family:Inter, sans-serif; font-size:16px; font-weight:600'>
3. The timing of meal/rest breaks was well-distributed.
</span>
""", unsafe_allow_html=True)
q_meal_timing = st.radio(
    label="",
    options=likert_options,
    index=2,
    horizontal=True,
    key="meal_timing",
    label_visibility="collapsed"
)

# 4️⃣ Overall satisfaction
st.markdown("""
<span style='font-family:Inter, sans-serif; font-size:16px; font-weight:600'>
4. Overall, I’m satisfied with the personalized tour plan.
</span>
""", unsafe_allow_html=True)
q_overall = st.radio(
    label="",
    options=likert_options,
    index=3,
    horizontal=True,
    key="overall",
    label_visibility="collapsed"
)

st.markdown("""
<span style='font-family:Inter, sans-serif; font-size:16px; font-weight:600'>
5. Do you have any comments or suggestions?
</span>
""", unsafe_allow_html=True)

feedback = st.text_area(
    label="",
    height=150
)

if st.button("Submit Feedback"):
    try:
        sheet.update_cell(row_num, 20, str(likert_mapping[q_spacing]))
        sheet.update_cell(row_num, 21, str(likert_mapping[q_variety]))
        sheet.update_cell(row_num, 22, str(likert_mapping[q_meal_timing]))
        sheet.update_cell(row_num, 23, str(likert_mapping[q_overall]))
        sheet.update_cell(row_num, 24, feedback)

        st.success("✅ Feedback saved!")
        time.sleep(1)
        st.switch_page("pages/3_final_download.py")
    except Exception as e:
        st.error(f"Error saving feedback: {e}")
