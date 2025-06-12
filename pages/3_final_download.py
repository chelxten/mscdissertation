import streamlit as st
from datetime import datetime
import io
from xhtml2pdf import pisa

st.set_page_config(page_title="Final Download", layout="centered")

st.image("Sheffield-Hallam-University.png", width=250)
st.title("📥 Final Document Download")

# Load from session state
name = st.session_state.get("participant_name", "Participant Name")
signature = st.session_state.get("participant_signature", "Signature")
tour_plan = st.session_state.get("tour_plan", "No tour plan generated.")
rating = st.session_state.get("tour_rating", "Not Provided")
feedback = st.session_state.get("tour_feedback", "No comments.")
unique_id = st.session_state.get("unique_id", "Unknown")

# Build HTML content
html_content = f"""
<html>
<head>
    <style>
        body {{ font-family: DejaVu Sans, Arial, sans-serif; }}
        h1 {{ text-align: center; }}
        h2 {{ color: #d9534f; }}
        .section {{ margin: 20px 0; }}
        pre {{ white-space: pre-wrap; }}
    </style>
</head>
<body>
    <h1>Participant Summary Information</h1>

    <div class="section">
        <b>Name:</b> {name}<br>
        <b>Signature:</b> {signature}<br>
        <b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>

    <h2>Personalized Tour Plan</h2>
    <div class="section"><pre>{tour_plan}</pre></div>

    <h2>Tour Plan Feedback</h2>
    <div class="section">
        <b>Rating:</b> {rating}/10 ⭐<br>
        <b>Comments:</b> {feedback}
    </div>
</body>
</html>
"""

# Convert HTML to PDF
pdf_buffer = io.BytesIO()
pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=pdf_buffer)
pdf_buffer.seek(0)

# Download button
st.download_button(
    label="📥 Download Complete File",
    data=pdf_buffer,
    file_name=f"{unique_id}_FinalDocument.pdf",
    mime="application/pdf"
)
