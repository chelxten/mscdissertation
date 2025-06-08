import streamlit as st

st.set_page_config(page_title="Personalized Tour Plan")

st.title("🎢 Your Personalized Tour Plan")

if "questionnaire" not in st.session_state:
    st.warning("❗ Please complete the questionnaire first.")
    st.stop()

data = st.session_state["questionnaire"]

st.write("Thanks for your input! Here’s a preview of how we’ll personalize your visit:")
st.json(data)
