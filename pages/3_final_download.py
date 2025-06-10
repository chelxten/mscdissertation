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

# ✅ Full info sheet text
info_sheet = """
Title of Project: The Search of Advanced AI-Powered Service Robots for Amusement Parks

Legal Basis for the Research  
The University undertakes research as part of its function for the community under its legal status.  
Data protection allows us to use personal data for research with appropriate safeguards in place under the legal basis of public tasks that are in the public interest.  

A full statement of your rights can be found at: [Privacy Notice for Research](https://www.shu.ac.uk/about-this-website/privacy-policy/privacy-notices/privacy-notice-for-research)  

However, all University research is reviewed to ensure that participants are treated appropriately and their rights respected. This study has been submitted for ethical review and is awaiting approval by the University’s Research Ethics Committee.  

Further information at: [Ethics and Integrity at SHU](https://www.shu.ac.uk/research/excellence/ethics-and-integrity)

Invitation and Purpose  
You are invited to take part in a research study about the use of advanced artificial intelligence technologies to improve service robots in amusement parks. This study aims to understand how technologies like AI-driven navigation, fuzzy logic, and learning systems can help robots become more adaptable and engaging for visitors.

Why You Were Invited  
You have been invited to take part because people in your age group are typical users of amusement parks and can provide valuable insights into how technology, like service robots, could improve the visitor experience. Your feedback will help us understand what features and behaviours make these robots more useful, engaging, and enjoyable for guests.
    
Voluntary Participation  
Taking part in this study is entirely voluntary. You are free to withdraw at any time, without giving a reason, and without any negative consequences. However, once you begin the questionnaire, all questions must be answered in order to complete the survey.

What You Will Do  
If you choose to take part, you will be asked to complete a short online questionnaire. The questions will include rating scales from 1 to 10, percentage-based responses, and multiple-choice options. There are no open-ended questions, and the survey is designed to be quick and straightforward.

Time & Place  
The questionnaire will be entirely online and takes approximately 5 minutes to complete.

Use of Deception  
There is no deception involved in this study. All information about the purpose and process of the research is explained clearly to participants from the beginning.

Risks  
This is a low-risk study. The questionnaire only includes multiple-choice and rating-scale questions about amusement park experiences and ride preferences. No sensitive or personal topics are involved.

Benefits  
While there is no direct benefit to you as a participant, your responses will contribute to academic research in robotics and help improve the use of service robots in amusement parks. The findings may support future developments that enhance visitor experiences in entertainment environments. All results will be reported anonymously and used solely for educational and research purposes.

Opportunity for Questions  
If you have any questions about the study, you are welcome to contact the researcher at any time using the email provided below.

Confidentiality  
The questionnaire does not ask for your name. Only your age and gender will be required, which are collected solely for demographic analysis. Providing contact details is optional for those who wish to be contacted for a future follow-up. All data will be stored anonymously, and no one will be able to identify you from your responses.

Responsibility for Data  
The researcher is solely responsible for storing and managing the data securely in accordance with the university’s data protection policies.

Access to Data  
Only the researcher and their academic supervisor will have access to the collected data. It will not be shared with anyone else.

Data Retention and Future Use  
All data will be stored securely and retained for up to five years in line with university policy. The data will be used only for this study and will not be shared or used in any other research projects.

Use of Results  
The results of this study will be used in a postgraduate dissertation submitted as part of the researcher’s academic programme. All findings will be reported anonymously.

Study Duration  
The study will take place between June 2025 and September 2025, which includes the period of data collection and analysis.
    
Access to Results  
If you would like a summary of the study’s findings once the research is complete, you may request this by contacting the researcher using the email provided below.

Contact Details  
- Researcher: Cherry San – c3065323@hallam.shu.ac.uk  
- Supervisor: Dr Samuele Vinanzi – s.vinanzi@shu.ac.uk  
- Data Concerns: DPO@shu.ac.uk  
- Research Ethics Queries: ethicssupport@shu.ac.uk  
"""

consent_text = """
1.	I have read the Information Sheet for this study and have had details of the study explained to me.
2.	My questions about the study have been answered to my satisfaction and I understand that I may ask further questions at any point. 
3.	I understand that I am free to withdraw from the study within the time limits outlined in the Information Sheet, without giving a reason for my withdrawal or to decline to answer any particular questions in the study without any consequences to my future treatment by the researcher.          
4.	I agree to provide information to the researchers under the conditions of confidentiality set out in the Information Sheet.
5.	I wish to participate in the study under the conditions set out in the Information Sheet.
6.	I consent to the information collected for the purposes of this research study, once anonymised (so that I cannot be identified), to be used for any other research purposes.
    """

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
    
    pdf.set_font("DejaVu", "", 12)
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
