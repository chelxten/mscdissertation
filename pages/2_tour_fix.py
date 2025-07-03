# -------------------------------
# 1. Imports and Streamlit Setup
# -------------------------------
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import numpy as np
import math

st.set_page_config(page_title="Personalized Tour Plan")
st.image("Sheffield-Hallam-University.png", width=250)
st.title("Your Personalized Tour Plan")

# -------------------------------
# 2. Load User Questionnaire
# -------------------------------
if "questionnaire" not in st.session_state:
    st.warning("❗ Please complete the questionnaire first.")
    st.stop()

data = st.session_state["questionnaire"]

# User preferences
preferences = {k: 8 - v for k, v in data.items() if k in [
    "thrill", "family", "water", "entertainment", "food", "shopping", "relaxation"
]}

priorities = data["priorities"]
walking_pref = data["walking"]
break_pref = data["break"]

# Visit duration in minutes
duration_map = {
    "<2 hrs": 90, "2–4 hrs": 180, "4–6 hrs": 300, "All day": 420
}
visit_duration = duration_map.get(data["duration"], 180)

# -------------------------------
# 3. Zones and Coordinates
# -------------------------------
SCALE_METERS_PER_UNIT = 2.0

zones = {
    "thrill": ["Roller Coaster", "Drop Tower", "Haunted Mine Train", "Spinning Vortex", "Freefall Cannon"],
    "water": ["Water Slide", "Lazy River", "Log Flume", "Splash Battle", "Wave Pool"],
    "family": ["Bumper Cars", "Mini Ferris Wheel", "Animal Safari Ride", "Ball Pit Dome", "Train Adventure"],
    "entertainment": ["Live Stage", "Street Parade", "Magic Show", "Circus Tent", "Musical Fountain"],
    "food": ["Food Court", "Snack Bar", "Ice Cream Kiosk", "Pizza Plaza", "Smoothie Station"],
    "shopping": ["Souvenir Shop", "Candy Store", "Photo Booth", "Gift Emporium", "Toy World"],
    "relaxation": ["Relaxation Garden", "Shaded Benches", "Quiet Lake View", "Zen Courtyard", "Sky Deck"]
}

zone_coords = {
    "thrill": (100, 400), "water": (400, 400), "family": (100, 100),
    "entertainment": (400, 100), "food": (250, 250),
    "shopping": (300, 300), "relaxation": (200, 200)
}

# Calculate attraction coordinates
attraction_coords = {}
for zone, items in zones.items():
    for i, name in enumerate(items):
        angle = i * (2 * np.pi / len(items))
        r = 80
        x = zone_coords[zone][0] + int(r * np.cos(angle))
        y = zone_coords[zone][1] + int(r * np.sin(angle))
        attraction_coords[name] = (x, y)

# Special location for changing room
attraction_coords["Shower & Changing Room"] = (450, 250)

# -------------------------------
# 4. Durations, Wait Times, Accessibility
# -------------------------------
CLOTHING_CHANGE_DURATION = 10

accessibility = {
    "thrill": 0.7, "water": 0.8, "family": 1.0,
    "entertainment": 0.9, "food": 1.0,
    "shopping": 1.0, "relaxation": 1.0
}

durations = {
    # Thrill
    "Roller Coaster": 5, "Drop Tower": 3, "Haunted Mine Train": 4,
    "Spinning Vortex": 4, "Freefall Cannon": 3,
    # Water
    "Water Slide": 4, "Lazy River": 10, "Log Flume": 6,
    "Splash Battle": 5, "Wave Pool": 10,
    # Family
    "Bumper Cars": 3, "Mini Ferris Wheel": 4,
    "Animal Safari Ride": 6, "Ball Pit Dome": 6,
    "Train Adventure": 8,
    # Entertainment
    "Live Stage": 20, "Street Parade": 15,
    "Magic Show": 25, "Circus Tent": 25,
    "Musical Fountain": 15,
    # Food
    "Food Court": 25, "Snack Bar": 15,
    "Ice Cream Kiosk": 10, "Pizza Plaza": 20,
    "Smoothie Station": 10,
    # Shopping
    "Souvenir Shop": 10, "Candy Store": 8,
    "Photo Booth": 5, "Gift Emporium": 10,
    "Toy World": 10,
    # Relaxation
    "Relaxation Garden": 15, "Shaded Benches": 10,
    "Quiet Lake View": 10, "Zen Courtyard": 10,
    "Sky Deck": 10
}

wait_times = {
    # Thrill
    "Roller Coaster": 30, "Drop Tower": 25,
    "Haunted Mine Train": 20, "Spinning Vortex": 18,
    "Freefall Cannon": 20,
    # Water
    "Water Slide": 15, "Lazy River": 10,
    "Log Flume": 20, "Splash Battle": 12,
    "Wave Pool": 15,
    # Family
    "Bumper Cars": 5, "Mini Ferris Wheel": 5,
    "Animal Safari Ride": 8, "Ball Pit Dome": 6,
    "Train Adventure": 8,
    # Entertainment
    "Live Stage": 10, "Street Parade": 5,
    "Magic Show": 10, "Circus Tent": 10,
    "Musical Fountain": 5,
    # Food
    "Food Court": 10, "Snack Bar": 5,
    "Ice Cream Kiosk": 4, "Pizza Plaza": 8,
    "Smoothie Station": 4,
    # Shopping
    "Souvenir Shop": 3, "Candy Store": 2,
    "Photo Booth": 1, "Gift Emporium": 3,
    "Toy World": 3,
    # Relaxation
    "Relaxation Garden": 0, "Shaded Benches": 0,
    "Quiet Lake View": 0, "Zen Courtyard": 0,
    "Sky Deck": 0
}

zone_intensity = {
    "thrill": 0.95, "water": 0.75, "family": 0.55,
    "entertainment": 0.35, "food": 0.15,
    "shopping": 0.25, "relaxation": 0.1
}

wet_rides = {"Water Slide", "Wave Pool", "Splash Battle"}

# -------------------------------
# 5. Fuzzy Inputs, Outputs, Rules
# -------------------------------
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import numpy as np

# Inputs
preference = ctrl.Antecedent(np.arange(0, 11, 1), 'preference')
accessibility_input = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'accessibility')
wait_tol = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'wait_tolerance')
walking_input = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'walking')
priority_thrill = ctrl.Antecedent(np.arange(0, 2, 1), 'priority_thrill')
priority_food = ctrl.Antecedent(np.arange(0, 2, 1), 'priority_food')
priority_comfort = ctrl.Antecedent(np.arange(0, 2, 1), 'priority_comfort')
intensity_input = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'intensity')
repeat_count = ctrl.Antecedent(np.arange(0, 4, 1), 'zone_repeat_count')

# Output
weight = ctrl.Consequent(np.arange(0, 11, 1), 'weight')

# Memberships
for ante in [preference, intensity_input]:
    ante['low'] = fuzz.trimf(ante.universe, [0, 0, 5])
    ante['medium'] = fuzz.trimf(ante.universe, [2, 5, 8])
    ante['high'] = fuzz.trimf(ante.universe, [5, 10, 10])

accessibility_input['poor'] = fuzz.trimf(accessibility_input.universe, [0.0, 0.0, 0.5])
accessibility_input['moderate'] = fuzz.trimf(accessibility_input.universe, [0.2, 0.5, 0.8])
accessibility_input['good'] = fuzz.trimf(accessibility_input.universe, [0.5, 1.0, 1.0])

wait_tol.automf(3)
walking_input.automf(3)

priority_thrill['no'] = fuzz.trimf(priority_thrill.universe, [0, 0, 1])
priority_thrill['yes'] = fuzz.trimf(priority_thrill.universe, [0, 1, 1])

priority_food['no'] = fuzz.trimf(priority_food.universe, [0, 0, 1])
priority_food['yes'] = fuzz.trimf(priority_food.universe, [0, 1, 1])

priority_comfort['no'] = fuzz.trimf(priority_comfort.universe, [0, 0, 1])
priority_comfort['yes'] = fuzz.trimf(priority_comfort.universe, [0, 1, 1])

repeat_count.automf(3)

weight['low'] = fuzz.trimf(weight.universe, [0, 0, 4])
weight['medium'] = fuzz.trimf(weight.universe, [3, 5, 7])
weight['high'] = fuzz.trimf(weight.universe, [6, 10, 10])

# Rules
rules = [
    ctrl.Rule(preference['high'] & accessibility_input['good'], weight['high']),
    ctrl.Rule(preference['medium'] & accessibility_input['moderate'], weight['medium']),
    ctrl.Rule(preference['low'], weight['low']),
    ctrl.Rule(wait_tol['high'], weight['high']),
    ctrl.Rule(walking_input['long'], weight['high']),
    ctrl.Rule(priority_thrill['yes'], weight['high']),
    ctrl.Rule(priority_food['yes'], weight['medium']),
    ctrl.Rule(priority_comfort['yes'], weight['medium']),
    ctrl.Rule(intensity_input['high'] & preference['high'], weight['medium']),
    ctrl.Rule(repeat_count['many'], weight['low'])
]

# Control system
weight_ctrl = ctrl.ControlSystem(rules)
weight_sim = ctrl.ControlSystemSimulation(weight_ctrl)

# -----------------------------------
# 6. Fuzzy Weight Evaluation & Scoring
# -----------------------------------
zone_weights = {}
for zone in zones:
    pref = preferences.get(zone, 5)
    acc = accessibility_factors.get(zone, 1.0)
    intensity = zone_intensity.get(zone, 0.5)
    repeat_count_val = 0

    # Fuzzy input setup
    weight_sim.input['preference'] = pref
    weight_sim.input['accessibility'] = acc
    weight_sim.input['wait_tolerance'] = wait_val
    weight_sim.input['walking'] = walking_val
    weight_sim.input['priority_thrill'] = 1.0 if zone == "thrill" and priority_thrill_val else 0.0
    weight_sim.input['priority_food'] = 1.0 if zone == "food" and priority_food_val else 0.0
    weight_sim.input['priority_comfort'] = 1.0 if zone == "relaxation" and priority_comfort_val else 0.0
    weight_sim.input['intensity'] = intensity
    weight_sim.input['zone_repeat_count'] = repeat_count_val

    weight_sim.compute()
    zone_weights[zone] = weight_sim.output['weight']

# Cap low-activity zones
for z in ["food", "relaxation"]:
    zone_weights[z] = min(zone_weights.get(z, 0), 4.5)

# Normalize
total = sum(zone_weights.values())
normalized_weights = {z: w/total for z, w in zone_weights.items()} if total else {z: 1/len(zone_weights) for z in zone_weights}

# -----------------------------------
# 7. Attraction Scoring
# -----------------------------------
attraction_scores = {}
recent_zones = []

for zone, attractions in zones.items():
    for attraction in attractions:
        wait = attraction_wait_times.get(attraction, 0)
        duration = attraction_durations.get(attraction, 5)
        intensity = zone_intensity.get(zone, 0.5)
        acc = accessibility_factors.get(zone, 1.0)
        pref = preferences.get(zone, 5) / 10.0
        is_wet = attraction in wet_ride_names

        # Comfort penalty for wet rides
        comfort_penalty = 0.7 if is_wet and priority_comfort_val and wet_time_pct < 35 else 1.0

        # Rhythm-aware repeat count
        repeat_count = min(recent_zones.count(zone), 3)
        fuzzy_weight = get_fuzzy_weight(
            pref * 10, acc, wait_val, walking_val,
            1.0 if zone == "thrill" and priority_thrill_val else 0.0,
            1.0 if zone == "food" and priority_food_val else 0.0,
            1.0 if zone == "relaxation" and priority_comfort_val else 0.0,
            intensity, repeat_count
        )

        # Final score
        score = (
            fuzzy_weight * pref
            * (1 - 0.02 * wait)
            * (1 + 0.2 * (1 - intensity))
            * comfort_penalty
        )

        attraction_scores[attraction] = score
        recent_zones.append(zone)
        if len(recent_zones) > 4:
            recent_zones.pop(0)

# -----------------------------------
# 8. Initial Attraction Selection
# -----------------------------------
initial_attractions = []
time_budget = visit_duration + 15
time_used = 0
recent_zones = []

ranked_attractions = sorted(attraction_scores, key=attraction_scores.get, reverse=True)

for attraction in ranked_attractions:
    zone = next((z for z, lst in zones.items() if attraction in lst), None)
    if not zone:
        continue

    ride_time = attraction_durations.get(attraction, 5)
    wait_time = attraction_wait_times.get(attraction, 0)
    total_time = ride_time + wait_time

    if time_used + total_time > time_budget:
        continue

    if recent_zones[-2:] == [zone, zone]:
        continue

    initial_attractions.append(attraction)
    time_used += total_time
    recent_zones.append(zone)

    if len(recent_zones) > 4:
        recent_zones.pop(0)

# -----------------------------------
# 9A. Distance Helpers
# -----------------------------------
def calculate_distance(a, b):
    a = attraction_coordinates.get(a, a)
    b = attraction_coordinates.get(b, b)
    return math.hypot(b[0] - a[0], b[1] - a[1])

def reorder_by_distance(route, start=(0, 0)):
    ordered, current = [], start
    remaining = [r for r in route if r in attraction_coordinates]
    while remaining:
        next_stop = min(remaining, key=lambda r: calculate_distance(current, r))
        ordered.append(next_stop)
        current = attraction_coordinates[next_stop]
        remaining.remove(next_stop)
    return ordered

# -----------------------------------
# 9B. Wet Ride Scheduling
# -----------------------------------
def schedule_wet_rides_midday(route, wet_rides, zones):
    wet_block = [a for a in route if a in wet_rides]
    dry_block = [a for a in route if a not in wet_rides and not a.startswith("[Clothing Change]")]
    if not wet_block:
        return route

    change_stop = "[Clothing Change] Shower & Changing Room"
    if change_stop not in wet_block:
        wet_block.append(change_stop)

    insert_pos = max(1, min(int((wet_time_pct / 100) * len(dry_block)), len(dry_block) - 1))
    merged = dry_block[:insert_pos] + wet_block + dry_block[insert_pos:]

    # Add 1–2 fillers after wet block
    last_wet_idx = merged.index(wet_block[-1])
    fillers = [a for a in merged[last_wet_idx + 1:] if any(a in zones[z] for z in ["family", "entertainment"])]
    selected = fillers[:2]

    merged = [a for a in merged if a not in selected]
    merged[last_wet_idx + 1:last_wet_idx + 1] = selected

    return merged

# -----------------------------------
# 10. Food Timing Estimation
# -----------------------------------
food_pref = preferences["food"]

food_interval_sim.input['preference'] = food_pref
food_interval_sim.input['priority_food'] = priority_food_val
food_interval_sim.compute()

preferred_food_gap = int(np.clip(food_interval_sim.output['food_interval'], 60, 240))

# -----------------------------------
# 11. Remove Consecutive Breaks
# -----------------------------------
def no_consecutive_food_or_break(route, zones):
    final = []
    prev_soft = False
    for stop in route:
        zone = next((z for z, a in zones.items() if stop in a), None)
        is_soft = zone in {"food", "relaxation"}
        if stop.startswith("[Clothing Change]"):
            final.append(stop)
            prev_soft = False
            continue
        if is_soft and prev_soft:
            continue
        final.append(stop)
        prev_soft = is_soft
    return final

def insert_breaks(route):
    updated = []
    total_time = 0
    energy = 100
    last_break = -999
    last_meal = -999
    meal_count = 0
    used_breaks, used_meals = set(), set()
    start_clock = datetime.strptime("10:00", "%H:%M")

    # Detect wet ride block
    wet_start = wet_end = None
    for i, stop in enumerate(route):
        if stop in wet_ride_names or stop.startswith("[Clothing Change]"):
            wet_start = i if wet_start is None else wet_start
            wet_end = i

    loc = (0, 0)
    since_break, since_meal, meal_activities = 0, 0, 0

    for i, stop in enumerate(route):
        updated.append(stop)
        in_wet = wet_start is not None and wet_start <= i <= wet_end
        if stop.startswith("[Clothing Change]") or in_wet:
            loc = attraction_coordinates[stop]
            continue

        zone = next((z for z, a in zones.items() if stop in a), None)
        duration = attraction_durations.get(stop, 5)
        wait = attraction_wait_times.get(stop, 0)
        walk = max(2, round(calculate_distance(loc, attraction_coordinates[stop]) * SCALE_FACTOR_METERS_PER_UNIT / 50))
        this_time = duration + wait + walk

        total_time += this_time
        since_break += this_time
        since_meal += this_time
        meal_activities += 1

        clock = start_clock + timedelta(minutes=total_time)
        intensity = zone_intensity.get(zone, 1.0)
        energy_loss = compute_energy_loss(intensity, walk, energy_settings['loss_factor'])
        energy = max(0, energy - energy_loss)

        # Automatic rest if low energy
        if energy < 40 and since_break > 10 and (total_time - last_break) > 30 and zone not in ["relaxation", "food"]:
            options = [r for r in zones["relaxation"] if r not in used_breaks and r not in updated]
            if options:
                best = min(options, key=lambda r: calculate_distance(attraction_coordinates[stop], attraction_coordinates[r]))
                updated.append(best)
                used_breaks.add(best)
                energy = min(100, energy + energy_settings['rest_boost'])
                last_break = total_time
                since_break = 0

        # Scheduled breaks
        needs_break = (
            (break_pref == "After 1 hour" and since_break >= 60) or
            (break_pref == "After 2 hours" and since_break >= 120) or
            (break_pref == "After every big ride" and stop in {"Roller Coaster", "Drop Tower", "Log Flume", "Water Slide"})
        )
        if needs_break and energy >= 40 and (total_time - last_break) > 30:
            options = [r for r in zones["relaxation"] if r not in used_breaks and r not in updated]
            if options and zone not in ["relaxation", "food"]:
                best = min(options, key=lambda r: calculate_distance(attraction_coordinates[stop], attraction_coordinates[r]))
                updated.append(best)
                used_breaks.add(best)
                energy = min(100, energy + energy_settings['rest_boost'])
                last_break = total_time
                since_break = 0

        # Meal breaks (after 12:00 only)
        if (
            clock.time() >= datetime.strptime("12:00", "%H:%M").time() and
            since_meal >= 90 and
            meal_activities >= 3 and
            meal_count < 2 and
            zone not in ["relaxation", "food"] and
            (last_break == -999 or total_time - last_break >= 30) and
            (last_meal == -999 or total_time - last_meal >= 30)
        ):
            options = [f for f in zones["food"] if f not in used_meals and f not in updated]
            if options:
                best = min(options, key=lambda f: calculate_distance(attraction_coordinates[stop], attraction_coordinates[f]))
                updated.append(best)
                used_meals.add(best)
                energy = min(100, energy + energy_settings['food_boost'])
                last_meal = total_time
                meal_count += 1
                since_meal = 0
                meal_activities = 0

        loc = attraction_coordinates[stop]

    return updated

def remove_meals_before_noon(route, start_time="10:00"):
    result = []
    time_used = 0
    clock = datetime.strptime(start_time, "%H:%M")
    loc = (0, 0)

    for stop in route:
        if stop.startswith("[Clothing Change]"):
            time_used += CLOTHING_CHANGE_DURATION
            result.append(stop)
            continue

        zone = next((z for z, a in zones.items() if stop in a), None)
        if zone is None:
            result.append(stop)
            continue

        dur = attraction_durations.get(stop, 5)
        wait = attraction_wait_times.get(stop, 0)
        walk = max(2, round(calculate_distance(loc, attraction_coordinates[stop]) * SCALE_FACTOR_METERS_PER_UNIT / 50))
        this_time = dur + wait + walk
        scheduled = clock + timedelta(minutes=time_used)

        if zone == "food" and scheduled.time() < datetime.strptime("12:00", "%H:%M").time():
            time_used += this_time
            loc = attraction_coordinates[stop]
            continue

        result.append(stop)
        time_used += this_time
        loc = attraction_coordinates[stop]

    return result

def enforce_max_two_meals(route):
    result = []
    meals = 0
    for stop in route:
        zone = next((z for z, a in zones.items() if stop in a), None)
        if zone == "food":
            if meals < 2:
                result.append(stop)
                meals += 1
        else:
            result.append(stop)
    return result

def no_consecutive_food_or_break(route, zones):
    final = []
    last_soft = False

    for stop in route:
        if stop.startswith("[Clothing Change]"):
            final.append(stop)
            last_soft = False
            continue

        zone = next((z for z, a in zones.items() if stop in a), None)
        is_soft = zone in {"food", "relaxation"}

        if is_soft and last_soft:
            continue

        final.append(stop)
        last_soft = is_soft

    return final

first_preference_zone = max(preferences, key=preferences.get)
first_pref_attraction = next(
    (a for a in zones[first_preference_zone] if a in initial_attractions),
    None
)

# 1️⃣ Optimize by distance from first preference
optimized_initial = reorder_by_distance(
    initial_attractions,
    start_location=attraction_coordinates.get(first_pref_attraction, (0, 0))
)

# 2️⃣ Schedule wet rides around mid-tour
wet_scheduled = schedule_wet_rides_midday(optimized_initial, wet_ride_names, zones)

# 3️⃣ Insert breaks and meals
final_route = insert_breaks(wet_scheduled)
final_route = enforce_max_two_meals(final_route)
final_route = no_consecutive_food_or_break(final_route, zones)
final_route = remove_meals_before_noon(final_route)

# 4️⃣ Remove duplicates while keeping order
final_route = list(dict.fromkeys(final_route))

final_plan = final_route

if st.checkbox("Show energy level graph", value=True):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(time_timeline, energy_timeline, linewidth=1.5)
    ax.set_title("Visitor Energy Level Throughout the Day")
    ax.set_xlabel("Minutes Elapsed")
    ax.set_ylabel("Energy Level (%)")
    ax.set_ylim(0, 110)
    ax.grid(alpha=0.3)

    # Highlight energy zones
    ax.axhspan(80, 100, color='green', alpha=0.1, label='High (80–100%)')
    ax.axhspan(50, 80, color='yellow', alpha=0.1, label='Moderate (50–80%)')
    ax.axhspan(0, 50, color='red', alpha=0.1, label='Low (<50%)')

    # Mark stops
    for time_point, energy_level, stop_name, zone in stop_label_points:
        marker = 'o'
        color = 'blue'
        if zone == "food":
            marker, color = 's', 'green'
        elif zone == "relaxation":
            marker, color = 'D', 'darkgreen'
        ax.scatter(time_point, energy_level, marker=marker, color=color, s=50)

    ax.legend()
    st.pyplot(fig)

walking_speed = 67
total_time_used = 0
previous_location = (250, 250)
start_time = datetime.strptime("10:00", "%H:%M")
plan_text_lines = []

zone_emojis = {
    "thrill": "🎢", "water": "💦", "family": "👨‍👩‍👧‍👦",
    "entertainment": "🎭", "food": "🍽️", "shopping": "🛍️", "relaxation": "🌿"
}

st.markdown("🏁 **Entrance**")
plan_text_lines.append("Entrance")

for stop in final_plan:
    if stop.startswith("[Clothing Change]"):
        duration = CLOTHING_CHANGE_DURATION
        formatted_time = (start_time + timedelta(minutes=total_time_used)).strftime("%I:%M %p")
        st.markdown(f"**{formatted_time} — 👕 [Clothing Change] Shower & Changing Room — {duration} minutes**")
        plan_text_lines.append(f"{formatted_time} — [Clothing Change] Shower & Changing Room — {duration} minutes")
        total_time_used += duration
        continue

    zone = next((z for z, a in zones.items() if stop in a), None)
    if zone is None:
        continue

    ride_time = attraction_durations.get(stop, 5)
    wait_time = attraction_wait_times.get(stop, 0)
    walk_dist = calculate_distance(previous_location, attraction_coordinates[stop]) * SCALE_FACTOR_METERS_PER_UNIT
    walk_time = max(1, round(walk_dist / walking_speed))
    total_duration = ride_time + wait_time + walk_time

    if total_time_used + total_duration > visit_duration + 15:
        break

    formatted_time = (start_time + timedelta(minutes=total_time_used)).strftime("%I:%M %p")
    emoji = zone_emojis.get(zone, "")
    prefix = f"🌿 [Rest Stop]" if zone == "relaxation" else f"🍽️ [Meal Break]" if zone == "food" else f"{emoji}"
    display_name = f"{prefix} {stop}"

    st.markdown(f"**{formatted_time} — {display_name} — {total_duration} minutes**")
    plan_text_lines.append(f"{formatted_time} — {display_name} — {total_duration} minutes")

    total_time_used += total_duration
    previous_location = attraction_coordinates[stop]

st.markdown("🏁 **Exit**")
plan_text_lines.append("Exit")

leftover_time = visit_duration - total_time_used
st.info(f"Total Used: {int(total_time_used)} mins | Leftover: {int(leftover_time)} mins")

# Save plan text to session
final_clean_plan = "\n".join(plan_text_lines)
st.session_state.tour_plan = final_clean_plan

# Write to Google Sheet
uid = st.session_state.get("unique_id")
sheet = get_consent_worksheet()
cell = sheet.find(uid, in_column=2)

if cell:
    row_num = cell.row
    sheet.update_cell(row_num, 17, final_clean_plan)
    sheet.update_cell(row_num, 18, str(int(total_time_used)))
    sheet.update_cell(row_num, 19, str(int(leftover_time)))
else:
    st.warning("⚠️ Could not save tour plan. User ID not found.")

st.markdown("---")
st.subheader("⭐ Plan Feedback")

likert_options = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
likert_mapping = {opt: i+1 for i, opt in enumerate(likert_options)}

q_spacing = st.radio("1️⃣ The spacing felt balanced.", likert_options, horizontal=True)
q_variety = st.radio("2️⃣ Variety matched my interests.", likert_options, horizontal=True)
q_meal_timing = st.radio("3️⃣ Meal/rest timing was good.", likert_options, horizontal=True)
q_overall = st.radio("4️⃣ Overall satisfaction.", likert_options, index=3, horizontal=True)

feedback = st.text_area("5️⃣ Comments or suggestions", height=120)

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
