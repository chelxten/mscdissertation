
import streamlit as st

st.set_page_config(page_title="Tour Plan", page_icon="📍")
st.title("📍 Your Personalized Tour Plan")

if not st.session_state.get("questionnaire_done"):
    st.warning("Please complete the questionnaire first.")
    st.stop()

    # ----------------------
    # 🎢 Fuzzy Logic Planner
    # ----------------------

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

    def allocate_park_time(total_time, preferences, priorities, walking_pref, crowd_sensitivity):
        attraction_times = {}
        remaining_time = total_time

        zone_penalty = {}
        if walking_pref == "Very short":
            zone_penalty = {"water": 0.6, "relaxation": 0.8}
        elif walking_pref == "Moderate":
            zone_penalty = {"water": 0.8}

        total_weight = sum(preferences.values())
        weights = {
            zone: preferences[zone] / total_weight * zone_penalty.get(zone, 1)
            for zone in zones
        }

        if "Enjoying high-intensity rides" in priorities:
            weights["thrill"] *= 1.2
        if "Visiting family-friendly attractions" in priorities:
            weights["family"] *= 1.2
        if "Staying comfortable" in priorities:
            weights["relaxation"] *= 1.3
            weights["entertainment"] *= 1.1
        if "Having food/rest breaks" in priorities:
            weights["food"] *= 1.2
            weights["relaxation"] *= 1.1

        QUICK_MODE = "Seeing many attractions" in priorities
        weights = {k: v / sum(weights.values()) for k, v in weights.items()}

        for zone, attractions in zones.items():
            zone_time = weights[zone] * total_time
            for attraction in attractions:
                pop = popularity_scores.get(attraction, 5)
                if crowd_sensitivity == "Very uncomfortable" and pop >= 7:
                    continue
                if crowd_sensitivity == "Slightly uncomfortable" and pop >= 8 and preferences[zone] < 8:
                    continue

                duration = attraction_durations[attraction]
                time_spent = min(duration, 15) if QUICK_MODE else duration

                if remaining_time >= time_spent:
                    attraction_times[attraction] = time_spent
                    remaining_time -= time_spent

        while remaining_time >= 5:
            for attraction in attraction_times:
                addition = min(5, remaining_time)
                attraction_times[attraction] += addition
                remaining_time -= addition
                if remaining_time < 5:
                    break

        return attraction_times, remaining_time

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
            elif break_preference == "After 1 hour" and time_counter >= 60:
                updated_route.append("Break")
                time_counter = 0
            elif break_preference == "After 2 hours" and time_counter >= 120:
                updated_route.append("Break")
                time_counter = 0

        return updated_route

    # ✅ Generate fuzzy plan
    attraction_times, leftover_time = allocate_park_time(
        total_time=visit_time,
        preferences=preferences,
        priorities=priorities,
        walking_pref=walking,
        crowd_sensitivity=crowd_sensitivity
    )
    route = generate_navigation_order(attraction_times)
    final_plan = insert_breaks(route, break_time)

    st.subheader("🎯 Your Personalized Plan")
    st.markdown("Here is your customized route including breaks:")

    for step in final_plan:
        if step == "Break":
            st.markdown("☕ **Break Time**")
        else:
            st.markdown(f"🎡 **{step}** – {attraction_times.get(step, 'N/A')} min")

    st.markdown(f"🕒 Estimated Total Duration: **{visit_time - leftover_time} minutes**")
