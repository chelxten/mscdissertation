import streamlit as st
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Final Download", layout="centered")

st.title("📥 Final Document Download")

# ✅ User Inputs (Assume passed from session state or questionnaire)
name = st.session_state.get("participant_name", "Participant Name")
signature = st.session_state.get("participant_signature", "Signature")
tour_plan = st.session_state.get("tour_plan", "No tour plan generated.")

# ✅ Full Info Sheet (you can shorten or update this as needed)
info_sheet = """
Title of Project: The Search of Advanced AI-Powered Service Robots for Amusement Parks

Legal Basis for the Research:
The University undertakes research... [Content trimmed here for brevity]

Contact Details:
- Researcher: Cherry San – c3065323@hallam.shu.ac.uk
- Supervisor: Dr Samuele Vinanzi – s.vinanzi@shu.ac.uk
"""

# ✅ Consent Details
consent_text = """
1. I have read the Information Sheet and understand the study.
2. I understand I can withdraw at any time without reason.
3. I agree to provide information under confidentiality.
4. I wish to participate under the conditions outlined.
5. I consent to anonymised data being used for research purposes.
"""

# ✅ Generate Final PDF
def generate_final_pdf(name, signature, info_sheet, tour_plan):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ✅ Use DejaVu Font
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

    # ✅ Tour Plan Section
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Personalized Tour Plan", ln=True)
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(0, 7, tour_plan)

    # ✅ Export PDF
    filename = f"{name.replace(' ', '_')}_Final_Document.pdf"
    pdf.output(filename)
    return filename

# ✅ Generate and Display Button
if st.button("📄 Generate & Download Final PDF"):
    file_path = generate_final_pdf(name, signature, info_sheet, tour_plan)
    with open(file_path, "rb") as f:
        st.download_button(
            label="⬇️ Click to Download Final Document",
            data=f,
            file_name=file_path,
            mime="application/pdf"
        )
