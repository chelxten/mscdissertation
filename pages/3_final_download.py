import streamlit as st
from datetime import datetime
import io
from xhtml2pdf import pisa
import PyPDF2
import re


st.set_page_config(page_title="Final Download", layout="centered")

st.image("Sheffield-Hallam-University.png", width=250)
st.title("📥 Final Document Download")

# ✅ Load data from session state
name = st.session_state.get("participant_name", "Participant Name")
signature = st.session_state.get("participant_signature", "Signature")
tour_plan = st.session_state.get("tour_plan", "No tour plan generated.")
rating = st.session_state.get("tour_rating", "Not Provided")
feedback = st.session_state.get("tour_feedback", "No comments.")
unique_id = st.session_state.get("unique_id", "Unknown")

def remove_emojis(text):
    # Regex pattern to match most common emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & pictographs
        "\U0001F680-\U0001F6FF"  # Transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # Flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)
    
# ✅ Generate dynamic PDF from HTML
def generate_dynamic_pdf_html(name, signature, tour_plan, rating, feedback):
    tour_plan_clean = remove_emojis(tour_plan)
    feedback_clean = remove_emojis(feedback)

    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 12pt; }}
            h1 {{ text-align: center; font-size: 20pt; margin-bottom: 20px; }}
            h2 {{ font-size: 16pt; margin-top: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            td {{ padding: 8px; }}
            pre {{ font-family: Arial, sans-serif; white-space: pre-wrap; word-wrap: break-word; }}
            .section {{ margin-bottom: 25px; }}
        </style>
    </head>
    <body>

    <h1>Participant Summary Information</h1>

    <table border="0">
        <tr><td><b>Name:</b></td><td>{name}</td></tr>
        <tr><td><b>Signature:</b></td><td>{signature}</td></tr>
        <tr><td><b>Date:</b></td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
    </table>

    <div class="section">
        <h2>Personalized Tour Plan</h2>
        <pre>{tour_plan_clean}</pre>
    </div>

    <div class="section">
        <h2>Tour Plan Feedback</h2>
        <p><b>Rating:</b> {rating}/10</p>
        <p><b>Comments:</b> {feedback_clean}</p>
    </div>

    </body>
    </html>
    """

    result_buffer = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html_content), dest=result_buffer)
    result_buffer.seek(0)
    return result_buffer

# ✅ Merge master file with dynamic PDF
def merge_pdfs(master_pdf_path, dynamic_pdf_buffer):
    merger = PyPDF2.PdfMerger()

    with open(master_pdf_path, "rb") as master_file:
        merger.append(master_file)

    merger.append(dynamic_pdf_buffer)

    final_buffer = io.BytesIO()
    merger.write(final_buffer)
    final_buffer.seek(0)
    return final_buffer

# ✅ Generate Download Button
if st.button("📄 Generate & Download Final PDF"):
    dynamic_pdf = generate_dynamic_pdf_html(name, signature, tour_plan, rating, feedback)
    merged_pdf = merge_pdfs("PISPCF.pdf", dynamic_pdf)

    st.download_button(
        label="⬇️ Download Complete File",
        data=merged_pdf,
        file_name=f"{unique_id}_FinalDocument.pdf",
        mime="application/pdf"
    )
