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

st.set_page_config(page_title="Final Document Download", layout="centered")
st.image("Sheffield-Hallam-University.png", width=250)
st.title("📥 Final Summary & Download")

# -----------------------
# 2. Load Session State
# -----------------------

unique_id = st.session_state.get("unique_id")
rating = st.session_state.get("tour_rating", "Not Provided")
feedback = st.session_state.get("tour_feedback", "No comments.")
consent = st.session_state.get("consent_agreed", False)

if not unique_id:
    st.error("Session expired or missing. Please restart from the beginning.")
    st.stop()

# -----------------------
# 3. Thank You Message
# -----------------------

st.markdown("## 🎉 Thank You for Participating!")

st.markdown("""
We appreciate your time and thoughtful responses.

Your personalized amusement park tour plan — combined with your consent form — is now ready to download.

Please keep the document for your records.
""")

# -----------------------
# 4. Google Sheets Access
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
total_time_used = sheet.cell(row_num, 20).value
leftover_time = sheet.cell(row_num, 21).value

# -----------------------
# 5. Generate PDF
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

    <h1>Amusement Park Tour Summary</h1>

    {"<p><i>Consent confirmed by participant.</i></p>" if consent else ""}

    <h2>Tour Plan Summary</h2>
    """

    for line in plan_text.split('\n'):
        line = line.strip()
        if line.lower() in ["entrance", "exit"]:
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
# 6. Merge with Consent Form
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
# 7. Auto-generate & Show Download
# -----------------------

dynamic_pdf = generate_pdf(plan_text, total_time_used, leftover_time, rating, feedback, consent)
final_pdf = merge_pdfs("PISPCF.pdf", dynamic_pdf)

st.download_button(
    label="⬇️ Download Final Document",
    data=final_pdf,
    file_name=f"{unique_id}_FinalDocument.pdf",
    mime="application/pdf"
)
