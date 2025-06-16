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
tour_plan = st.session_state.get("tour_plan", "No tour plan generated.")
rating = st.session_state.get("tour_rating", "Not Provided")
feedback = st.session_state.get("tour_feedback", "No comments.")
unique_id = st.session_state.get("unique_id", "Unknown")
agreed = st.session_state.get("consent_agreed", False)

# ✅ Clean out emojis to ensure PDF renders cleanly
def remove_emojis(text):
    return ''.join(c for c in text if 32 <= ord(c) <= 126)

# ✅ Parse fuzzy logic tour plan for HTML rendering
def format_tour_plan_for_html(tour_plan):
    route_lines = []
    estimated_time = ""
    leftover_time = ""
    recording = False

    for line in tour_plan.split('\n'):
        line = line.strip()

        if "Planned Route:" in line:
            recording = True
            continue

        if recording and not line:
            continue

        if line.startswith("Estimated Time Used"):
            estimated_time = line
            recording = False
            continue

        if line.startswith("Leftover Time"):
            leftover_time = line
            continue

        if recording:
            if line.startswith("- "):
                clean_line = line[2:]
                route_lines.append(remove_emojis(clean_line))

    html = "<ul style='line-height: 1.2; font-size: 12pt;'>"
    for l in route_lines:
        html += f"<li>{l}</li>"
    html += "</ul>"

    html += f"<p><b>{estimated_time}</b></p>"
    html += f"<p><b>{leftover_time}</b></p>"

    return html

# ✅ PDF generator function
def generate_dynamic_pdf_html(tour_plan, rating, feedback, agreed):
    formatted_tour_plan_html = format_tour_plan_for_html(tour_plan)

    consent_html = ""
    if agreed:
        consent_html = """
        <h2>Consent Statement</h2>
        <p>I confirm that I have read the Participant Information Sheet and agreed to participate in this study.</p>
        """

    html_content = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ text-align: center; color: #990033; font-size: 14pt;}}
        h2 {{ color: #990033; border-bottom: 1px solid #ddd; padding-bottom: 4px; font-size: 14pt;}}
        table {{ width: 100%; font-size: 12pt; border-collapse: collapse; margin-bottom: 10px; }}
        td {{ padding: 6px; vertical-align: top; }}
        ul {{ font-size: 12pt; }}
        p {{ font-size: 12pt; }}
    </style>
    </head>
    <body>

    {consent_html} 

    <h2>Generated On:</h2>
    <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <h2>Personalized Tour Plan</h2>
    {formatted_tour_plan_html}

    <h2>Tour Plan Feedback</h2>
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

# ✅ Download Button
if st.button("📄 Generate & Download Final PDF"):
    dynamic_pdf = generate_dynamic_pdf_html(tour_plan, rating, feedback, agreed)
    merged_pdf = merge_pdfs("PISPCF.pdf", dynamic_pdf)

    st.download_button(
        label="⬇️ Download Complete File",
        data=merged_pdf,
        file_name=f"{unique_id}_FinalDocument.pdf",
        mime="application/pdf"
    )
