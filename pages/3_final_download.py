import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import io
from xhtml2pdf import pisa
import PyPDF2

# -----------------------
# 1. Setup & Config
# -----------------------

st.set_page_config(page_title="Final Download", layout="centered")
st.image("Sheffield-Hallam-University.png", width=250)
st.title("📥 Final Document Download")

# -----------------------
# 2. Load from Session
# -----------------------

unique_id = st.session_state.get("unique_id", "Unknown")
rating = st.session_state.get("tour_rating", "Not Provided")
feedback = st.session_state.get("tour_feedback", "No comments.")
consent = st.session_state.get("consent_agreed", False)

# -----------------------
# 3. Google Sheets Connection
# -----------------------

@st.cache_resource
def get_consent_worksheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("Survey Responses").worksheet("Sheet1")

sheet = get_consent_worksheet()

# ✅ Find correct row for user:
cell = sheet.find(unique_id, in_column=2)
row_num = cell.row

# ✅ Load directly from Google Sheet:
plan_text = sheet.cell(row_num, 19).value  # Column S (Tour Plan Text)
total_time_used = sheet.cell(row_num, 20).value  # Column T
leftover_time = sheet.cell(row_num, 21).value  # Column U

# -----------------------
# 4. PDF Generator
# -----------------------

def generate_pdf(plan_text, total_time_used, leftover_time, rating, feedback, consent):
    clean_lines = [
        line.strip().replace("🎢", "").replace("💦", "").replace("👨‍👩‍👧‍👦", "")
        .replace("🎭", "").replace("🍔", "").replace("🛍️", "").replace("🌳", "")
        .replace("🌿", "").replace("🍽️", "")
        for line in plan_text.split('\n') if line.strip()
    ]

    html_content = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ text-align: center; color: #990033; font-size: 16pt;}}
        h2 {{ color: #990033; border-bottom: 1px solid #ddd; padding-bottom: 4px; font-size: 14pt;}}
        p, li {{ font-size: 12pt; }}
    </style>
    </head>
    <body>

    <h1>Personalized Amusement Park Tour Report</h1>

    {"<p><b>Consent:</b> I confirm I have given consent to participate.</p>" if consent else "<p><b>Consent:</b> Not provided.</p>"}

    <h2>Tour Plan Summary</h2>
    <ul>
    """

    for line in clean_lines:
        html_content += f"<li>{line}</li>"

    html_content += f"""
    </ul>

    <p><b>Total Time Used:</b> {total_time_used} minutes</p>
    <p><b>Leftover Time:</b> {leftover_time} minutes</p>

    <h2>Participant Feedback</h2>
    <p><b>Rating:</b> {rating}/10</p>
    <p><b>Comments:</b> {feedback}</p>

    <p><i>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i></p>

    </body></html>
    """

    pdf_buffer = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html_content), dest=pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

# -----------------------
# 5. Merge with PISPCF
# -----------------------

def merge_pdfs(master_path, generated_buffer):
    merger = PyPDF2.PdfMerger()
    with open(master_path, "rb") as master:
        merger.append(master)
    merger.append(generated_buffer)
    final_pdf = io.BytesIO()
    merger.write(final_pdf)
    final_pdf.seek(0)
    return final_pdf

# -----------------------
# 6. Generate Button
# -----------------------

if st.button("📄 Generate & Download PDF"):
    dynamic_pdf = generate_pdf(plan_text, total_time_used, leftover_time, rating, feedback, consent)
    final_pdf = merge_pdfs("PISPCF.pdf", dynamic_pdf)

    st.download_button(
        label="⬇️ Download Final Document",
        data=final_pdf,
        file_name=f"{unique_id}_FinalDocument.pdf",
        mime="application/pdf"
    )
