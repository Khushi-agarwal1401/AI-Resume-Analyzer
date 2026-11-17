import os
import uuid
import threading
import webbrowser

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from analyzer.pdf_reader import extract_pdf_text
from analyzer.docx_reader import extract_docx_text, DocxReadError
from analyzer.section_detector import extract_sections
from analyzer.skills_extractor import extract_skills, get_suggestions
from analyzer.resume_scorer import calculate_resume_score
from analyzer.ats_checker import analyze_ats
from analyzer.job_matcher import match_resume_to_job


app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {".pdf", ".docx"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():

    filepath = None

    if "resume" not in request.files:
        return "Please upload a resume."

    file = request.files["resume"]

    if file.filename == "":
        return "No file selected."

    extension = os.path.splitext(file.filename.lower())[1]

    if extension not in ALLOWED_EXTENSIONS:
        return "Only PDF and DOCX files are allowed."

    # Used in messages shown to the user: "PDF" or "DOCX"
    file_type = extension[1:].upper()

    filename = secure_filename(file.filename)

    if not filename:
        return "Invalid filename."

    unique_filename = f"{uuid.uuid4().hex}_{filename}"

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        unique_filename
    )

    try:
        # Save the uploaded resume
        file.save(filepath)

        # Extract text (the rest of the analysis is the same for both types)
        if extension == ".docx":
            resume_text = extract_docx_text(filepath)
        else:
            resume_text = extract_pdf_text(filepath)

        if not resume_text.strip():
            return f"No readable text found in this {file_type}."

        # Detect and organize sections
        resume_sections = extract_sections(resume_text)

        # Detect Skills
        found_skills = extract_skills(resume_text)

        # Generate Suggestions
        suggestions = get_suggestions(found_skills)

        # Calculate Resume Score
        score_data = calculate_resume_score(resume_text)

        resume_score = score_data["score"]
        score_breakdown = score_data["breakdown"]

        # ATS Compatibility Analysis
        ats_result = analyze_ats(resume_text, found_skills)

        # Job Description Matching
        job_description = request.form.get("job_description", "")
        job_match = match_resume_to_job(found_skills, job_description)

        print("\n========== RESUME ANALYSIS ==========")
        print("DETECTED SKILLS:", found_skills)
        print("RESUME SCORE:", resume_score)
        print("SCORE BREAKDOWN:", score_breakdown)
        if job_match.get("has_job_description"):
            print("JOB MATCH SCORE:", job_match.get("match_percentage"))
        print("=====================================\n")

        # Display Results
        return render_template(
            "result.html",
            found_skills=found_skills,
            suggestions=suggestions,
            skill_count=len(found_skills),
            resume_text=resume_text,
            resume_score=resume_score,
            score_breakdown=score_breakdown,
            ats_result=ats_result,
            resume_sections=resume_sections,
            job_match=job_match
        )

    except DocxReadError as error:
        # The message was written for the user, so it is safe to show
        return str(error)

    except Exception as error:
        print("Analysis Error:", error)
        return (
            f"Unable to analyze this {file_type}. "
            f"Please try another {file_type}."
        )

    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)


if __name__ == "__main__":

    url = "http://127.0.0.1:5000"

    threading.Timer(
        1.5,
        lambda: webbrowser.open_new(url)
    ).start()

    app.run(debug=True, use_reloader=False)