import streamlit as st
from fpdf import FPDF
from datetime import datetime
from constants import INFO_SHEET, CONSENT_TEXT
import re
import textwrap

st.set_page_config(page_title="Final Download", layout="centered")

st.image("Sheffield-Hallam-University.png", width=250)
st.title("📥 Final Document Download")

# ✅ Load from session state
name = st.session_state.get("participant_name", "Participant Name")
signature = st.session_state.get("participant_signature", "Signature")
tour_plan = st.session_state.get("tour_plan", "No tour plan generated.")
rating = st.session_state.get("tour_rating", "Not Provided")
feedback = st.session_state.get("tour_feedback", "No comments.")

def add_markdown_text(pdf, text, max_char=100):
    def break_long_words(line, limit=80):
        # Insert spaces every `limit` characters in overly long "words" (e.g., URLs)
        return re.sub(r"(\S{" + str(limit) + r",})", lambda m: insert_soft_breaks(m.group(0), limit), line)

    def insert_soft_breaks(word, limit):
        return ' '.join([word[i:i+limit] for i in range(0, len(word), limit)])

    lines = text.strip().split("\n")
    for line in lines:
        line = break_long_words(line.strip())

        match = re.match(r"\*\*(.+?)\*\*\s*:?(.+)?", line)
        if match:
            heading = match.group(1).strip()
            content = match.group(2).strip() if match.group(2) else ""
            pdf.set_font("DejaVu", "B", 11)
            pdf.multi_cell(0, 7, heading)
            if content:
                pdf.set_font("DejaVu", "", 10)
                for wrapped_line in textwrap.wrap(content, width=max_char):
                    pdf.multi_cell(0, 7, wrapped_line)
        elif line.startswith("- "):
            pdf.set_font("DejaVu", "", 10)
            for wrapped_line in textwrap.wrap(line, width=max_char):
                pdf.multi_cell(0, 7, wrapped_line)
        elif line == "":
            pdf.ln(2)
        else:
            pdf.set_font("DejaVu", "", 10)
            for wrapped_line in textwrap.wrap(line, width=max_char):
                pdf.multi_cell(0, 7, wrapped_line)
            
# ✅ PDF Generator
def generate_final_pdf(name, signature, INFO_SHEET, tour_plan, rating, feedback):
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
    add_markdown_text(pdf, INFO_SHEET)

    # ✅ Consent Section
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Consent Confirmation", ln=True)
    pdf.set_font("DejaVu", "", 10)
    add_markdown_text(pdf, CONSENT_TEXT)

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
    try:
        file_path = generate_final_pdf(name, signature, INFO_SHEET, tour_plan, rating, feedback)
        with open(file_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Your Complete File",
                data=f,
                file_name=file_path,
                mime="application/pdf"
            )
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
