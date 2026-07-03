from flask import Flask, render_template, request
from docx import Document
import os
from dotenv import load_dotenv
import google.generativeai as genai
import markdown

app = Flask(__name__)
latest_result = {}
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    file = request.files["resume"]
    job_description = request.form.get("job_description", "").lower()

    if file.filename != "":

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)

        file.save(filepath)

        document = Document(filepath)

        text = ""

        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"
        text=text.lower()

        word_count = len(text.split())
        char_count = len(text)

        skills=["python","java","sql","html","css","javascript","flask","git","github","aws","docker","machine learning","tensorflow","pandas","numpy"]
        found_skills=[]
        for skill in skills:
            if skill in text:
                found_skills.append(skill)
        missing_skills = []
        for skill in skills:
            if skill not in found_skills:
                missing_skills.append(skill)
        skill_count = len(found_skills)
        missing_count = len(missing_skills)
        
        matched_skills = []

        for skill in found_skills:
            if skill in job_description:
                matched_skills.append(skill)

        if len(found_skills) > 0:
            jd_match = int((len(matched_skills) / len(found_skills)) * 100)
        else:
            jd_match = 0

        skills_html = ""
        missing_html = ""
        suggestion_html = ""

        for skill in found_skills:
            skills_html += f"<p>✅ {skill.title()}</p>"
        for skill in missing_skills:
            missing_html += f"<p>❌ {skill.title()}</p>"
        for skill in missing_skills:
            suggestion_html += f"<p>💡 Learn {skill.title()}</p>"
        score = int((len(found_skills) / len(skills)) * 100)
        if score >= 80:
            strength = "🌟 Excellent"
        elif score >= 60:
            strength = "👍 Good"
        elif score >= 40:
            strength = "🙂 Average"
        else:
            strength = "⚠️ Needs Improvement"
        if "machine learning" in found_skills or "tensorflow" in found_skills:
            job_role = "🤖 Machine Learning Engineer"

        elif "html" in found_skills and "css" in found_skills and "javascript" in found_skills:
            job_role = "🌐 Frontend Developer"

        elif "python" in found_skills and "flask" in found_skills:
            job_role = "🐍 Python Backend Developer"

        elif "java" in found_skills:
            job_role = "☕ Java Developer"

        elif "android" in text:
            job_role = "📱 Android Developer"

        else:
            job_role = "💻 Software Developer"
        if score >= 80:
            score_color = "#28a745"      # Green
        elif score >= 50:
            score_color = "#ffc107"      # Orange
        else:
            score_color = "#dc3545"      # Red
        score_bar = f"""
        <div class="progress">
            <div class="progress-fill" 
                style="width:{score}%;background:{score_color};">
                {score}%
            </div>
        </div>
        """
        prompt = f"""
        You are an experienced HR manager and ATS expert.

        Analyze the following resume professionally.

        Resume:

        {text}

        Provide your response in this format:

        ## Professional Summary

        ## ATS Score (0-100)

        ## Strengths

        ## Weaknesses

        ## Missing Skills

        ## Recommended Job Role

        ## Certifications to Learn

        ## Projects to Build

        ## Interview Preparation Tips

        ## Final Advice

        Keep the language professional and easy to understand.
        """

        try:
            response = model.generate_content(prompt)
            ai_analysis = markdown.markdown(response.text)

        except Exception:
            ai_analysis = """
            <h3>⚠ Gemini API Limit Reached</h3>
            <p>Please wait a few seconds and try again.</p>
            """
        global latest_result

        latest_result = {
            "score": score,
            "strength": strength,
            "job_role": job_role,
            "skills": found_skills,
            "missing": missing_skills,
            "ai": ai_analysis
        }
        
        return render_template(
            "result.html",
            score=score,
            score_bar=score_bar,
            strength=strength,
            job_role=job_role,
            skills_html=skills_html,
            missing_html=missing_html,
            suggestion_html=suggestion_html,
            ai_analysis=ai_analysis,
            word_count=word_count,
            char_count=char_count,
            skill_count=skill_count,
            missing_count=missing_count,
            jd_match=jd_match,
            matched_skills=matched_skills,
            text=text
            
        )
        

    return "<h2>No File Selected</h2>"

from reportlab.pdfgen import canvas
from flask import send_file
import os


@app.route("/download")
def download_report():

    pdf_path = "Resume_Report.pdf"

    c = canvas.Canvas(pdf_path)

    y = 800

    c.setFont("Helvetica-Bold",18)
    c.drawString(50,y,"AI Resume Analysis Report")

    y -= 40

    c.setFont("Helvetica",12)

    c.drawString(50,y,f"ATS Score : {latest_result['score']}/100")

    y -= 25

    c.drawString(50,y,f"Resume Strength : {latest_result['strength']}")

    y -= 25

    c.drawString(50,y,f"Recommended Job Role : {latest_result['job_role']}")

    y -= 40

    c.setFont("Helvetica-Bold",14)
    c.drawString(50,y,"Detected Skills")

    y -= 25

    c.setFont("Helvetica",12)

    for skill in latest_result["skills"]:
        c.drawString(70,y,"• "+skill)
        y -= 20

    y -= 20

    c.setFont("Helvetica-Bold",14)
    c.drawString(50,y,"Missing Skills")

    y -= 25

    c.setFont("Helvetica",12)

    for skill in latest_result["missing"]:
        c.drawString(70,y,"• "+skill)
        y -= 20

    c.save()

    return send_file(pdf_path,as_attachment=True)
@app.route("/interview")
def interview():

    prompt = f"""
    You are a senior technical interviewer.

    Based on this resume:

    {latest_result}

    Generate:

    1. Five Technical Questions
    2. Three HR Questions
    3. Two Project-Based Questions

    Keep the questions suitable for a final-year engineering student.
    """

    try:
        response = model.generate_content(prompt)
        questions = markdown.markdown(response.text)

    except Exception:
        questions = """
        <h2>⚠ Gemini API Limit Reached</h2>
        <p>Please wait and try again.</p>
        """

    return render_template(
        "interview.html",
        questions=questions
    )
@app.route("/cover-letter")
def cover_letter():

    prompt = f"""
    You are an HR manager.

    Based on this resume:

    {latest_result}

    Write a professional one-page cover letter.

    Keep it:
    - Professional
    - ATS Friendly
    - Suitable for a fresher
    - Easy to understand
    """

    try:
        response = model.generate_content(prompt)
        cover = markdown.markdown(response.text)

    except Exception:
        cover = """
        <h2>⚠ Gemini API Limit Reached</h2>
        <p>Please wait a few seconds and try again.</p>
        """

    return render_template(
        "cover_letter.html",
        cover=cover
    )
if __name__ == "__main__":
    app.run(debug=True)