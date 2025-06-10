import streamlit as st
from fpdf import FPDF
from datetime import datetime
from constants import info_sheet, consent_text

st.set_page_config(page_title="Final Download", layout="centered")

st.image("Sheffield-Hallam-University.png", width=250)
st.title("📥 Final Document Download")

# ✅ Load from session state
name = st.session_state.get("participant_name", "Participant Name")
signature = st.session_state.get("participant_signature", "Signature")
tour_plan = st.session_state.get("tour_plan", "No tour plan generated.")
rating = st.session_state.get("tour_rating", "Not Provided")
feedback = st.session_state.get("tour_feedback", "No comments.")
info_sheet = st.session_state.get("info_sheet_text", "No info sheet available.")
consent_text = st.session_state.get("consent_text", "No consent text available.")


# ✅ PDF Generator
def generate_final_pdf(name, signature, info_sheet, tour_plan, rating, feedback):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ✅ Fonts
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "Participant Information, Consent, and Tour Plan", ln=True, align="C")
    pdf.ln(10)

    # ✅ Information Sheet
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Participant Information Sheet", ln=True)
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(0, 7, info_sheet)

    # ✅ Consent Section
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Consent Confirmation", ln=True)
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(0, 7, consent_text)

    pdf.cell(0, 7, f"Name: {name}", ln=True)
    pdf.cell(0, 7, f"Signature: {signature}", ln=True)
    pdf.cell(0, 7, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(10)

    # ✅ Tour Plan
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Personalized Tour Plan", ln=True)
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(0, 7, tour_plan)

    # ✅ Feedback Section
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "📝 Tour Plan Feedback", ln=True)
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 10, f"Rating: {rating}/10 ⭐", ln=True)
    pdf.multi_cell(0, 7, f"Comments: {feedback}")

    # ✅ Save to file
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{name.replace(' ', '_')}_FinalDocument_{timestamp}.pdf"
    pdf.output(filename)
    return filename

# ✅ Generate and Download Button
if st.button("📄 Generate & Download Final PDF"):
    file_path = generate_final_pdf(name, signature, info_sheet, tour_plan, rating, feedback)
    with open(file_path, "rb") as f:
        st.download_button(
            label="⬇️ Download Your Complete File",
            data=f,
            file_name=file_path,
            mime="application/pdf"
        )
