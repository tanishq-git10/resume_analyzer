import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json

# 1. Load the secret key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# 2. Function to get response from Gemini AI
def get_gemini_response(input_prompt):
    # Using the model we found earlier
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(input_prompt)
    return response.text

# 3. Function to extract text from PDF
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += page.extract_text()
    return text

# 4. THE "CAREER COACH" PROMPT
# We now ask for a strict JSON structure with a 'Learning Path' and 'Courses'
input_prompt = """
Act Like a skilled Career Coach and Tech Recruiter.
Evaluate the resume based on the given Job Description (JD).

You must identify the GAPS between the Resume and the JD.
Then, provide a Learning Path to bridge those gaps.

Your response MUST be a valid JSON string with the following structure:
{{
  "JD Match": "85%",
  "MissingKeywords": ["keyword1", "keyword2"],
  "Profile Summary": "Brief assessment of the candidate...",
  "StudyPlan": [
    "Step 1: Learn [Skill] because...",
    "Step 2: Build a project using [Tech]..."
  ],
  "Courses": [
    {{"name": "Course Name", "platform": "NPTEL/Coursera/YouTube", "link_query": "Search query for this course"}}
  ]
}}

Make sure the "Courses" are real, high-quality, free resources (prioritize NPTEL, Coursera Audit, FreeCodeCamp).
resume: {text}
description: {jd}
"""

## --- THE WEBSITE UI ---
st.set_page_config(page_title="Career Coach AI", page_icon="🎓", layout="wide")

st.title("🎓 Smart Career Coach")
st.markdown("### specific advice & course recommendations to land the job.")

# Layout: Two columns
col1, col2 = st.columns(2)

with col1:
    jd = st.text_area("1️⃣ Paste the Job Description", height=200, placeholder="Paste the JD here...")

with col2:
    uploaded_file = st.file_uploader("2️⃣ Upload Your Resume (PDF)", type="pdf", help="Upload your resume")

submit = st.button("🚀 Analyze & Generate Study Plan")

if submit:
    if uploaded_file is not None and jd:
        text = input_pdf_text(uploaded_file)
        formatted_prompt = input_prompt.format(text=text, jd=jd)
        
        with st.spinner('🤖 AI is building your personalized roadmap...'):
            try:
                response = get_gemini_response(formatted_prompt)
                
                # Clean up the response (remove markdown wrappers if AI adds them)
                clean_response = response.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_response)

                # --- DASHBOARD UI ---
                
                # 1. Scorecard
                st.divider()
                st.subheader("📊 Your Scorecard")
                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric(label="Match Percentage", value=data.get("JD Match", "N/A"))
                with metric_col2:
                    st.write("**Profile Summary:**")
                    st.caption(data.get("Profile Summary", "No summary."))

                # 2. Missing Skills (Tags)
                st.subheader("⚠️ Missing Skills")
                keywords = data.get("MissingKeywords", [])
                if keywords:
                    # Display as neat little pills
                    st.markdown(" ".join([f"`{k}`" for k in keywords]))
                else:
                    st.success("You have all the required skills!")

                # 3. The Study Plan (Step-by-Step)
                st.subheader("🗺️ Your Personal Study Roadmap")
                study_plan = data.get("StudyPlan", [])
                for step in study_plan:
                    st.info(f"👉 {step}")

                # 4. Recommended Courses (Table)
                st.subheader("📚 Recommended Free Courses")
                courses = data.get("Courses", [])
                
                if courses:
                    for course in courses:
                        with st.expander(f"🎥 {course['name']} ({course['platform']})"):
                            st.write(f"**Search Query:** {course['link_query']}")
                            # Helpful link to Google Search the course
                            search_url = f"https://www.google.com/search?q={course['link_query'].replace(' ', '+')}"
                            st.markdown(f"[🔗 Click here to find this course]({search_url})")
                else:
                    st.write("No specific courses found.")

            except json.JSONDecodeError:
                st.error("Error parsing the AI response. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please upload a resume AND paste a job description.")