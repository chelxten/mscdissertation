import streamlit as st
from fpdf import FPDF
from datetime import datetime
import io
import PyPDF2
import re

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

# ✅ Emoji removal function
def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text or "")

# ✅ Generate dynamic PDF (text-only version)
def generate_dynamic_pdf(name, signature, tour_plan, rating, feedback):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
    
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "Participant Summary Information", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("DejaVu", "", 11)
    pdf.multi_cell(0, 7, f"Name: {name}")
    pdf.multi_cell(0, 7, f"Signature: {signature}")
    pdf.multi_cell(0, 7, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.ln(10)

    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Personalized Tour Plan", ln=True)
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(0, 7, tour_plan)
    pdf.ln(5)

    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Tour Plan Feedback", ln=True)
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(0, 7, f"Rating: {rating}/10 ⭐")
    pdf.multi_cell(0, 7, f"Comments: {feedback}")

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# ✅ Merge pre-uploaded master PDF with dynamic generated PDF
def merge_pdfs(master_pdf_path, dynamic_pdf_buffer):
    merger = PyPDF2.PdfMerger()
    
    with open(master_pdf_path, "rb") as master_file:
        merger.append(master_file)

    merger.append(dynamic_pdf_buffer)

    final_buffer = io.BytesIO()
    merger.write(final_buffer)
    final_buffer.seek(0)
    return final_buffer

# ✅ Before generating PDF — Clean all text to avoid emoji errors
clean_name = remove_emojis(name)
clean_signature = remove_emojis(signature)
clean_tour_plan = remove_emojis(tour_plan)
clean_feedback = remove_emojis(feedback)

# ✅ Generate download button
if st.button("📄 Generate & Download Final PDF"):
    dynamic_pdf = generate_dynamic_pdf(clean_name, clean_signature, clean_tour_plan, rating, clean_feedback)
    merged_pdf = merge_pdfs("PISPCF.pdf", dynamic_pdf)

    st.download_button(
        label="⬇️ Download Complete File",
        data=merged_pdf,
        file_name=f"{unique_id}_FinalDocument.pdf",
        mime="application/pdf"
    )
