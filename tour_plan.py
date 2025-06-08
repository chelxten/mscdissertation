
import streamlit as st

st.set_page_config(page_title="Tour Plan", page_icon="📍")
st.title("📍 Your Personalized Tour Plan")

if not st.session_state.get("questionnaire_done"):
    st.warning("Please complete the questionnaire first.")
    st.stop()

# Sample attractions and fuzzy allocation
attractions = {
    "Roller Coaster": 25,
    "Ferris Wheel": 15,
    "Haunted House": 20,
    "Water Slide": 20,
    "Snack Bar": 10,
    "Relaxation Garden": 15
}

selected = sorted(attractions.items(), key=lambda x: -st.session_state.preferences.get("thrill", 5))[:4]

for ride, mins in selected:
    st.markdown(f"🎡 **{ride}** – {mins} mins")

st.markdown("☕ **Breaks added based on preference.")
st.markdown(f"🕒 **Total Duration:** {sum(mins for _, mins in selected)} mins")
