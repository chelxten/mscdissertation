import streamlit as st
from fpdf import FPDF
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Final Download")

# ✅ Load session data
name = st.session_state.get("name", "Participant")
signature = st.session_state.get("signature", "Signed")
tour_plan = st.session_state.get("tour_plan", "Tour plan not generated.")
info_sheet_text = st.session_state.get("info_sheet_text", "Info Sheet not found.")
consent_text = st.session_state.get("consent_text", """
1. I have read the Information Sheet and understand the study.
2. I understand I can withdraw at any time without reason.
3. I agree to provide information under confidentiality.
4. I wish to participate under the conditions outlined.
5. I consent to anonymised data being used for research purposes.
""")

# ✅ Generate combined PDF
def generate_final_pdf(name, signature, info_text, consent_text, tour_plan):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ✅ DejaVu Font
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", "", 11)

    # 🧾 Info Sheet
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "Participant Information Sheet", ln=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.multi_cell(0, 7, info_text)

    # ✅ Consent
    pdf.ln(10)
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "Consent Confirmation", ln=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.multi_cell(0, 7, consent_text)

    pdf.ln(5)
    pdf.cell(0, 7, f"Name: {name}", ln=True)
    pdf.cell(0, 7, f"Signature: {signature}", ln=True)
    pdf.cell(0, 7, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)

    # 🎡 Tour Plan
    pdf.ln(10)
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "Your Personalized Tour Plan", ln=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.multi_cell(0, 7, tour_plan)

    # ✅ Save to buffer
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# ✅ Title
st.title("🎉 Thank You for Participating!")

# ✅ Generate and show download
pdf_data = generate_final_pdf(name, signature, info_sheet_text, consent_text, tour_plan)

st.download_button(
    label="📄 Download Your Participation PDF",
    data=pdf_data,
    file_name=f"{name.replace(' ', '_')}_Participation.pdf",
    mime="application/pdf"
)
