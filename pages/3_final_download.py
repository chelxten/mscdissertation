import streamlit as st
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Final Download", layout="centered")

st.image("Sheffield-Hallam-University.png", width=250)
st.title("📥 Final Document Download")

# ✅ Load from session state
name = st.session_state.get("participant_name", "Participant Name")
signature = st.session_state.get("participant_signature", "Signature")
tour_plan = st.session_state.get("tour_plan", "No tour plan generated.")
rating = st.session_state.get("tour_rating", "Not Provided")
feedback = st.session_state.get("tour_feedback", "No comments.")
unique_id = st.session_state.get("unique_id", "Unknown")  # we still use this for filename only


# ✅ Generate personalized dynamic PDF part (without showing Unique ID)
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
    merger.append(master_pdf_path)
    merger.append(dynamic_pdf_buffer)
    final_buffer = io.BytesIO()
    merger.write(final_buffer)
    final_buffer.seek(0)
    return final_buffer

# ✅ Generate download button
if st.button("📄 Generate & Download Final PDF"):
    dynamic_pdf = generate_dynamic_pdf(name, signature, tour_plan, rating, feedback)
    merged_pdf = merge_pdfs("PISPCF.pdf", dynamic_pdf)

    st.download_button(
        label="⬇️ Download Complete File",
        data=merged_pdf,
        file_name=f"{unique_id}_FinalDocument.pdf",  # UID only used in filename, not inside the file
        mime="application/pdf"
    )
