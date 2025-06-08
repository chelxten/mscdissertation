import streamlit as st

st.set_page_config(page_title="Personalized Tour Plan")

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
# 2. TIME ALLOCATION FUNCTION
# --------------------------

def allocate_park_time(total_time, preferences, priorities, walking_pref, crowd_sensitivity):
    attraction_times = {}
    remaining_time = total_time

    # Walking penalties (optional future expansion)
    zone_penalty = {}
    if walking_pref == "Very short distances":
        zone_penalty = {"water": 0.6, "relaxation": 0.8}
    elif walking_pref == "Moderate walking":
        zone_penalty = {"water": 0.8}

    # Base weights
    total_weight = sum(preferences.values())
    weights = {
        zone: preferences[zone] / total_weight * zone_penalty.get(zone, 1)
        for zone in zones
    }

    # Apply visit priorities
    if "Enjoying high-intensity rides" in priorities:
        weights["thrill"] *= 1.2
    if "Visiting family-friendly attractions together" in priorities:
        weights["family"] *= 1.2
    if "Staying comfortable throughout the visit" in priorities:
        weights["relaxation"] *= 1.3
        weights["entertainment"] *= 1.1
    if "Having regular food and rest breaks" in priorities:
        weights["food"] *= 1.2
        weights["relaxation"] *= 1.1

    QUICK_MODE = "Seeing as many attractions as possible" in priorities

    # Normalize weights
    total_weight = sum(weights.values())
    weights = {k: v / total_weight for k, v in weights.items()}

    allow_medium_crowd = crowd_sensitivity == "Slightly uncomfortable"

    for zone, attractions in zones.items():
        zone_time = weights[zone] * total_time
        for attraction in attractions:
            # Skip crowded rides if needed
            popularity = popularity_scores.get(attraction, 5)
            if crowd_sensitivity == "Very uncomfortable" and popularity >= 7:
                continue
            if crowd_sensitivity == "Slightly uncomfortable" and popularity >= 8 and preferences[zone] < 8:
                continue

            duration = attraction_durations[attraction]

            # Use full or half duration based on QUICK_MODE
            if QUICK_MODE:
                time_spent = min(duration, 15)
            else:
                time_spent = duration

            if remaining_time >= time_spent:
                attraction_times[attraction] = time_spent
                remaining_time -= time_spent

    # Redistribute leftover time to visited attractions
    while remaining_time >= 5:
        for attraction in attraction_times:
            addition = min(5, remaining_time)
            attraction_times[attraction] += addition
            remaining_time -= addition
            if remaining_time < 5:
                break

    return attraction_times, remaining_time

# --------------------------
# 3. GENERATE ROUTE + BREAKS
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
    
if "questionnaire" not in st.session_state:
    st.warning("❗ Please complete the questionnaire first.")
    st.stop()

data = st.session_state["questionnaire"]

st.write("Thanks for your input! Here’s a preview of how we’ll personalize your visit:")
# Get values from session data
preferences = {
    "thrill": data["thrill"],
    "family": data["family"],
    "water": data["water"],
    "entertainment": data["shows"],
    "food": data["food"],
    "shopping": data["shopping"],
    "relaxation": data["relaxation"],
}
priorities = data["priorities"]
crowd_sensitivity = data["crowd"]
walking_pref = data["walking"]
break_pref = data["break"]

# Estimate visit duration in minutes
duration_map = {
    "<2 hrs": 90,
    "2–4 hrs": 180,
    "4–6 hrs": 300,
    "All day": 420
}
visit_duration = duration_map.get(data["duration"], 180)

# Run fuzzy logic planner
attraction_times, leftover = allocate_park_time(
    visit_duration, preferences, priorities, walking_pref, crowd_sensitivity
)
route = generate_navigation_order(attraction_times)
final_plan = insert_breaks(route, break_pref)

# 👁️ Zone emoji mapping
zone_emojis = {
    "thrill": "🎢",
    "water": "💦",
    "family": "👨‍👩‍👧‍👦",
    "entertainment": "🎭",
    "food": "🍔",
    "shopping": "🛍️",
    "relaxation": "🌳"
}

# ✅ Display Visitor Summary
with st.container():
    st.success(f"""
    👤 **Age/Gender**: {data['age']}, {data['gender']}  
    ⏳ **Visit Duration**: {visit_duration} minutes  
    🚶‍♂️ **Walking Preference**: {walking_pref}  
    👥 **Crowd Sensitivity**: {crowd_sensitivity}  
    🛑 **Break Preference**: {break_pref}  
    """)

# ✅ Route Plan with Breaks
with st.expander("🗺️ Route with Breaks", expanded=True):
    st.subheader("Your Route Timeline")

    cumulative_time = 0
    for i, stop in enumerate(final_plan):
        if stop == "Break":
            st.markdown(f"🛑 **Break** – Recharge and relax!")
        elif stop == "Entrance":
            st.markdown(f"🏁 **{stop}** – Start your adventure")
        else:
            zone = next((z for z, a in zones.items() if stop in a), "")
            emoji = zone_emojis.get(zone, "🎡")
            duration = attraction_durations.get(stop, 10)
            cumulative_time += duration
            st.markdown(f"{emoji} **{stop}** – Approx. {duration} mins (⏱️ ~{cumulative_time} mins in)")

# ✅ Time Allocation per Attraction
with st.expander("⏱️ Time Allocation", expanded=False):
    total_time = sum(attraction_times.values())
    for attraction, time in attraction_times.items():
        zone = next((z for z, a in zones.items() if attraction in a), "")
        icon = zone_emojis.get(zone, "🎡")
        pct = time / total_time
        st.markdown(f"{icon} **{attraction}**: {time} min ({round(pct*100)}%)")
        st.progress(pct)

# ✅ Free Time Left
with st.expander("🕒 Leftover Time"):
    st.info(f"You have **{leftover} minutes** remaining. You can revisit your favorite attractions or relax.")
