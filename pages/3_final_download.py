import streamlit as st
from datetime import datetime
import io
from xhtml2pdf import pisa
import PyPDF2

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

# ✅ Format nicely for PDF
def format_tour_plan_for_html(tour_plan):
    lines = tour_plan.splitlines()

    general_info = []
    route_info = []
    capture_route = False

    for line in lines:
        clean_line = remove_emojis(line).strip()

        if "Planned Route" in clean_line:
            general_info.append("<p><b>Planned Route:</b></p>")
            capture_route = True
            continue

        if capture_route:
            if clean_line.startswith("- "):
                route_info.append(f"<li>{clean_line[2:]}</li>")  # Remove the dash
            else:
                capture_route = False
                if clean_line:  # extra line after route list
                    general_info.append(f"<p>{clean_line}</p>")
        else:
            if clean_line:
                general_info.append(f"<p>{clean_line}</p>")

    # Build final HTML
    html = "".join(general_info)
    if route_info:
        html += "<ul>" + "".join(route_info) + "</ul>"

    return html

# ✅ Generate dynamic PDF from HTML
def generate_dynamic_pdf_html(name, signature, tour_plan, rating, feedback):
    formatted_tour_plan_html = format_tour_plan_for_html(tour_plan)

    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ text-align: center; color: #800000; }}
            h2 {{ color: #333333; border-bottom: 1px solid #cccccc; padding-bottom: 5px; }}
            p {{ font-size: 12pt; line-height: 1.5; }}
            .info-table {{ width: 100%; margin-bottom: 20px; }}
            .info-table td {{ padding: 5px; font-size: 12pt; }}
            .label {{ font-weight: bold; width: 150px; }}
            ul {{ padding-left: 20px; }}
        </style>
    </head>
    <body>
        <h1>Participant Summary Information</h1>

        <table class="info-table">
            <tr><td class="label">Name:</td><td>{name}</td></tr>
            <tr><td class="label">Signature:</td><td>{signature}</td></tr>
            <tr><td class="label">Date:</td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
        </table>

        <h2>Personalized Tour Plan</h2>
        {formatted_tour_plan_html}

        <h2>Tour Plan Feedback</h2>
        <p><span class="label">Rating:</span> {rating}/10</p>
        <p><span class="label">Comments:</span> {remove_emojis(feedback)}</p>

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
