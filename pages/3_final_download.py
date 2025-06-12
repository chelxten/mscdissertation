import streamlit as st
from fpdf import FPDF
from datetime import datetime
import io
import PyPDF2
import textwrap
import unicodedata

st.set_page_config(page_title="Final Download", layout="centered")

st.image("Sheffield-Hallam-University.png", width=250)
st.title("📥 Final Document Download")

# ✅ Load all from session state
name = st.session_state.get("participant_name", "Participant Name")
signature = st.session_state.get("participant_signature", "Signature")
tour_plan = st.session_state.get("tour_plan", "No tour plan generated.")
rating = st.session_state.get("tour_rating", "Not Provided")
feedback = st.session_state.get("tour_feedback", "No comments.")
unique_id = st.session_state.get("unique_id", "Unknown")  # ✅ Still used only for file name

# ✅ Clean text for FPDF stability
def safe_multicell(pdf, text, width=100, chunk_size=80):
    text = ''.join(ch for ch in (text or "") if not unicodedata.category(ch).startswith("C"))
    text = text.encode('ascii', 'ignore').decode('ascii')
    for line in text.split('\n'):
        line = ' '.join([line[i:i+chunk_size] for i in range(0, len(line), chunk_size)])
        wrapped = textwrap.fill(line, width)
        if wrapped.strip() == "":
            pdf.ln(2)
        else:
            pdf.multi_cell(0, 7, wrapped)

# ✅ Generate personalized dynamic PDF
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
    safe_multicell(pdf, f"Name: {name}")
    safe_multicell(pdf, f"Signature: {signature}")
    safe_multicell(pdf, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.ln(10)

    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Personalized Tour Plan", ln=True)
    pdf.set_font("DejaVu", "", 10)
    safe_multicell(pdf, tour_plan)
    pdf.ln(5)

    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Tour Plan Feedback", ln=True)
    pdf.set_font("DejaVu", "", 10)
    safe_multicell(pdf, f"Rating: {rating}/10")
    safe_multicell(pdf, f"Comments: {feedback}")

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# ✅ Merge master + dynamic
def merge_pdfs(master_pdf_path, dynamic_pdf_buffer):
    merger = PyPDF2.PdfMerger()
    with open(master_pdf_path, "rb") as master_file:
        merger.append(master_file)
    merger.append(dynamic_pdf_buffer)
    final_buffer = io.BytesIO()
    merger.write(final_buffer)
    final_buffer.seek(0)
    return final_buffer

# ✅ Download button
if st.button("📄 Generate & Download Final PDF"):
    dynamic_pdf = generate_dynamic_pdf(name, signature, tour_plan, rating, feedback)
    merged_pdf = merge_pdfs("PISPCF.pdf", dynamic_pdf)

    st.download_button(
        label="⬇️ Download Complete File",
        data=merged_pdf,
        file_name=f"{unique_id}_FinalDocument.pdf",
        mime="application/pdf"
    )
