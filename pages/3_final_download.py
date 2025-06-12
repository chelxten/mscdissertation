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
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)
    
# ✅ Generate dynamic PDF from HTML
def generate_dynamic_pdf_html(name, signature, tour_plan, rating, feedback):
    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 11pt;
                margin: 40px;
            }}
            h1 {{
                text-align: center;
                font-size: 16pt;
            }}
            .section-title {{
                margin-top: 20px;
                font-size: 14pt;
                font-weight: bold;
            }}
            .info-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            .info-table td {{
                padding: 6px;
                vertical-align: top;
            }}
            .label {{
                font-weight: bold;
                width: 120px;
            }}
            .value {{
                width: auto;
            }}
            pre {{
                font-family: Arial, sans-serif;
                font-size: 10pt;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
        </style>
    </head>
    <body>
        <h1>Participant Summary Information</h1>

        <table class="info-table">
            <tr><td class="label">Name:</td><td class="value">{name}</td></tr>
            <tr><td class="label">Signature:</td><td class="value">{signature}</td></tr>
            <tr><td class="label">Date:</td><td class="value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
        </table>

        <div class="section-title">Personalized Tour Plan</div>
        <pre>{tour_plan}</pre>

        <div class="section-title">Tour Plan Feedback</div>
        <p><b>Rating:</b> {rating}/10</p>
        <p><b>Comments:</b> {feedback}</p>
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
    tour_plan_clean = remove_emojis(tour_plan)
    dynamic_pdf = generate_dynamic_pdf_html(name, signature, tour_plan_clean, rating, feedback)
    merged_pdf = merge_pdfs("PISPCF.pdf", dynamic_pdf)

    st.download_button(
        label="⬇️ Download Complete File",
        data=merged_pdf,
        file_name=f"{unique_id}_FinalDocument.pdf",
        mime="application/pdf"
    )
