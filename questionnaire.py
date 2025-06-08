# 2. questionnaire.py
import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Questionnaire", page_icon="🧠")

if not st.session_state.get("consent_given"):
    st.warning("Please complete the consent form first from the Home page.")
    st.stop()

st.title("🎡 Visitor Questionnaire")

with st.form("questionnaire"):
    age = st.selectbox("Age group", ["<12", "13–17", "18–30", "31–45", "46–60", "60+"])
    gender = st.selectbox("Gender", ["Male", "Female", "Non-binary", "Prefer not to say"])
    duration = st.selectbox("Visit Duration", ["<2", "2–4", "4–6", "All day"])

    thrill = st.slider("Thrill rides", 1, 10, 5)
    relaxation = st.slider("Relaxation", 1, 10, 5)
    family = st.slider("Family rides", 1, 10, 5)

    priorities = st.multiselect("Priorities", ["High thrill", "Comfort", "Many attractions"])
    wait_time = st.selectbox("Max wait time", ["<10 min", "10–20 min", "20–30 min", "30+ min"])

    submitted = st.form_submit_button("Submit Questionnaire")

if submitted:
    st.session_state.questionnaire_done = True
    st.session_state.preferences = {
        "thrill": thrill,
        "relaxation": relaxation,
        "family": family
    }
    st.session_state.priorities = priorities
    st.session_state.visit_time = 240 if duration == "All day" else 60 * int(duration.split("–")[0].replace("<", "").strip())
    st.success("✅ Questionnaire submitted. View your plan via sidebar.")
