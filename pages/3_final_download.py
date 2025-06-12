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
agreed = st.session_state.get("consent_agreed", False)


# 🔧 Debug output
st.write("Consent agreed?", agreed)

# ✅ Emoji remover (ascii only)
def remove_emojis(text):
    return ''.join(c for c in text if 32 <= ord(c) <= 126)

# ✅ Clean tour plan formatter
def format_tour_plan_for_html(tour_plan):
    route_lines = []
    recording = False

    for line in tour_plan.split('\n'):
        if "Planned Route:" in line:
            recording = True
            continue

        if "Estimated Time Used" in line:
            estimated_time = line.strip()
            recording = False
            continue

        if "Leftover Time" in line:
            leftover_time = line.strip()
            continue

        if recording:
            if line.strip():
                # ✅ Remove the leading '- ' if exists
                clean_line = line.strip()
                if clean_line.startswith('- '):
                    clean_line = clean_line[2:]  # remove the dash and space
                route_lines.append(clean_line)


    html = """
    <ul style="line-height: 1.2; margin-top: 0; margin-bottom: 10px; padding-left: 20px; font-size: 12pt;">
    """

    for l in route_lines:
        l = remove_emojis(l)
        html += f"<li>{l}</li>"
    html += "</ul>"

    
    # ✅ Add summary info separately in bold
    html += f"<p><b>{estimated_time}</b></p>"
    html += f"<p><b>{leftover_time}</b></p>"
    
    return html

# ✅ The full PDF generator function
def generate_dynamic_pdf_html(name, signature, tour_plan, rating, feedback):
    formatted_tour_plan_html = format_tour_plan_for_html(tour_plan)

    
    # ✅ Consent statement if agreed
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

    <h2>Participant Summary Information</h2>
    

    <table>
        <tr><td><b>Name:</b></td><td>{name}</td></tr>
        <tr><td><b>Signature:</b></td><td>{signature}</td></tr>
        <tr><td><b>Date:</b></td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
    </table>

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
