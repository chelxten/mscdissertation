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

# ✅ Emoji remover (ascii only)
def remove_emojis(text):
    return ''.join(c for c in text if 32 <= ord(c) <= 126)

# ✅ Clean tour plan formatter
def format_tour_plan_for_html(tour_plan):
    tour_plan = remove_emojis(tour_plan)
    lines = tour_plan.strip().split('\n')
    formatted_lines = "".join(f"<li>{line}</li>" for line in lines if line.strip())
    return f"<ul>{formatted_lines}</ul>"

# ✅ The full PDF generator function
def generate_dynamic_pdf_html(name, signature, tour_plan, rating, feedback):
    formatted_tour_plan_html = format_tour_plan_for_html(tour_plan)

    html_content = f"""
    <html>
    <head>
    <style>
        @page {{
            size: A4;
            margin: 50px;
            @bottom-center {{
                content: element(footer);
            }}
        }}
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 50px; }}
        h1 {{ text-align: center; color: #990033; font-size: 20pt; }}
        h2 {{ color: #990033; border-bottom: 1px solid #ddd; padding-bottom: 4px; font-size: 16pt; margin-top: 30px; }}
        table {{ width: 100%; font-size: 12pt; border-collapse: collapse; margin-bottom: 20px; }}
        td {{ padding: 6px; vertical-align: top; }}
        ul {{ font-size: 12pt; list-style-position: outside; padding-left: 20px; }}
        p {{ font-size: 12pt; }}

        div.footer {{
            position: running(footer);
            width: 100%;
            font-size: 10pt;
            color: #666;
            margin-top: 20px;
        }}
        div.bar {{
            height: 5px;
            background: linear-gradient(to right, #B21E4B 50%, #660033 50%);
            margin-bottom: 4px;
        }}
        div.footer-table {{
            display: flex;
            justify-content: space-between;
            font-size: 9pt;
        }}
    </style>
    </head>
    <body>

    <h1>Participant Summary Information</h1>

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

    <div class="footer">
        <div class="bar"></div>
        <div class="footer-table">
            <div>PARTICIPANT SUMMARY INFORMATION</div>
            <div>Page <span class="pageNumber"></span></div>
        </div>
    </div>

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
