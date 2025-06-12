import streamlit as st
from datetime import datetime
import weasyprint

st.set_page_config(page_title="Final Download", layout="centered")

st.image("Sheffield-Hallam-University.png", width=250)
st.title("📥 Final Document Download")

# ✅ Load from session state
name = st.session_state.get("participant_name", "Participant Name")
signature = st.session_state.get("participant_signature", "Signature")
tour_plan = st.session_state.get("tour_plan", "No tour plan generated.")
rating = st.session_state.get("tour_rating", "Not Provided")
feedback = st.session_state.get("tour_feedback", "No comments.")
unique_id = st.session_state.get("unique_id", "Unknown")

# ✅ Build full HTML content
html_content = f"""
<html>
<head>
    <style>
        body {{ font-family: "DejaVu Sans", sans-serif; font-size: 12pt; }}
        h1 {{ color: #1a4d80; text-align: center; }}
        h2 {{ color: #333333; margin-top: 30px; }}
        p {{ margin: 5px 0; }}
        .section {{ margin-bottom: 20px; }}
    </style>
</head>
<body>

<h1>Participant Summary Report</h1>

<h2>Participant Information</h2>
<p><b>Name:</b> {name}</p>
<p><b>Signature:</b> {signature}</p>
<p><b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

<h2>Personalized Tour Plan</h2>
<p style="white-space: pre-line;">{tour_plan}</p>

<h2>Tour Plan Feedback</h2>
<p><b>Rating:</b> {rating}/10 ⭐</p>
<p><b>Comments:</b></p>
<p style="white-space: pre-line;">{feedback}</p>

</body>
</html>
"""

# ✅ Generate PDF using WeasyPrint (from HTML)
pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()

# ✅ Download Button
st.download_button(
    label="⬇️ Download Final PDF",
    data=pdf_bytes,
    file_name=f"{unique_id}_FinalDocument.pdf",
    mime="application/pdf"
)
