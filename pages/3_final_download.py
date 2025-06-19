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

st.set_page_config(page_title="🎓 Final Document Download", layout="centered")
st.image("Sheffield-Hallam-University.png", width=250)
st.title("📥 Final Summary & Document")

st.markdown("---")
st.markdown("Below is a summary of your amusement park experience and feedback. You can download your complete personalized report as a PDF document.")

# -----------------------
# 2. Load from Session
# -----------------------

unique_id = st.session_state.get("unique_id")
rating = st.session_state.get("tour_rating", "Not Provided")
feedback = st.session_state.get("tour_feedback", "No comments.")
consent = st.session_state.get("consent_agreed", False)

if not unique_id:
    st.error("Session expired or missing. Please restart from the beginning.")
    st.stop()

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
cell = sheet.find(unique_id, in_column=2)
row_num = cell.row

plan_text = sheet.cell(row_num, 19).value  # Column S
total_time_used = sheet.cell(row_num, 20).value  # Column T
leftover_time = sheet.cell(row_num, 21).value  # Column U

# -----------------------
# 4. Display Questionnaire Responses
# -----------------------

# Load questionnaire answers from columns C to R (3 to 18)
questionnaire_answers = sheet.row_values(row_num)[2:18]  # index 0-based

question_labels = [
    "1. Age Group",
    "2. Accessibility Needs",
    "3. Planned Park Duration",
    "4. Thrill Ride Preference",
    "5. Family Ride Preference",
    "6. Water Ride Preference",
    "7. Live Show Preference",
    "8. Food & Dining Preference",
    "9. Shopping Preference",
    "10. Relaxation Area Preference",
    "11. Top Visit Priorities",
    "12. Max Wait Time Tolerance",
    "13. Walking Willingness",
    "14. Break Preferences",
    "15. Overall Rating",
    "16. Comments"
]

st.subheader("📝 Your Questionnaire Responses")

for label, answer in zip(question_labels, questionnaire_answers):
    st.markdown(f"**{label}:** {answer if answer else '_Not Answered_'}")

# -----------------------
# 5. PDF Generator
# -----------------------

def generate_pdf(plan_text, total_time_used, leftover_time, rating, feedback, consent):
    html_content = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 30px; font-size: 10pt; }}
        h1 {{ text-align: center; color: #990033; font-size: 14pt; margin-bottom: 12px; }}
        h2 {{ color: #990033; border-bottom: 1px solid #ddd; padding-bottom: 2px; font-size: 12pt; margin-top: 20px; }}
        p {{ margin: 4px 0; }}
    </style>
    </head>
    <body>

    <h1>Personalized Amusement Park Tour Report</h1>

    {"<p><i>I confirm I have given consent to participate.</i></p>" if consent else ""}

    <h2>Tour Plan Summary</h2>
    """

    for line in plan_text.split('\n'):
        line = line.strip()
        if line.lower() == "entrance" or line.lower() == "exit":
            html_content += f"<p><b>{line}</b></p>"
        elif line.lower().startswith("includes:"):
            html_content += f"<p style='margin-left: 10px; font-style: italic;'>{line}</p>"
        else:
            html_content += f"<p>{line}</p>"

    html_content += f"""
    <p><b>Total Time Used:</b> {total_time_used} minutes</p>
    <p><b>Leftover Time:</b> {leftover_time} minutes</p>

    <h2>Participant Feedback</h2>
    <p><b>Rating:</b> {rating}/10</p>
    <p><b>Comments:</b> {feedback}</p>

    <p style="margin-top: 30px; font-size: 8pt;"><i>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i></p>

    </body></html>
    """

    pdf_buffer = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html_content), dest=pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

# -----------------------
# 6. Merge with PISPCF
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
# 7. Generate Button
# -----------------------

st.markdown("### 📄 Generate Your Final Report")

if st.button("🖨️ Generate & Download PDF"):
    dynamic_pdf = generate_pdf(plan_text, total_time_used, leftover_time, rating, feedback, consent)
    final_pdf = merge_pdfs("PISPCF.pdf", dynamic_pdf)

    st.download_button(
        label="⬇️ Download Final Document",
        data=final_pdf,
        file_name=f"{unique_id}_FinalDocument.pdf",
        mime="application/pdf"
    )
