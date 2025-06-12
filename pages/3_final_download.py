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
    return ''.join(c for c in text if 32 <= ord(c) <= 126)

# ✅ Format the tour plan into clean bullet list
def format_tour_plan_for_html(tour_plan):
    lines = tour_plan.splitlines()
    html_lines = "<ul>"
    for line in lines:
        clean_line = remove_emojis(line).strip()
        if clean_line:  # avoid empty lines
            html_lines += f"<li>{clean_line}</li>"
    html_lines += "</ul>"
    return html_lines

# ✅ Generate dynamic PDF from HTML
def generate_dynamic_pdf_html(name, signature, tour_plan, rating, feedback):
    formatted_tour_plan_html = format_tour_plan_for_html(tour_plan)

    html_content = f"""
    <h1 style="text-align: center;">Participant Summary Information</h1>
    <p><b>Name:</b> {name}</p>
    <p><b>Signature:</b> {signature}</p>
    <p><b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <h2>Personalized Tour Plan</h2>
    {formatted_tour_plan_html}

    <h2>Tour Plan Feedback</h2>
    <p><b>Rating:</b> {rating}/10</p>
    <p><b>Comments:</b> {remove_emojis(feedback)}</p>
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
