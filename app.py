import io
import json
import os
import uuid
import threading
import webbrowser

from flask import Flask, render_template, request
from docx.opc.exceptions import PackageNotFoundError
from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename

from analyzer.pdf_reader import extract_pdf_text
from analyzer.docx_reader import DocxReadError, check_docx_file
from analyzer.resume_extractor import extract_resume_text
from analyzer.section_detector import extract_sections
from analyzer.skills_extractor import extract_skills, get_suggestions
from analyzer.resume_scorer import calculate_resume_score
from analyzer.suggestions import generate_recommendations
from analyzer.keyword_analyzer import analyze_keywords
from analyzer.ats_checker import analyze_ats
from analyzer.job_matcher import match_resume_to_job
from analyzer.report_generator import build_report
from analyzer.temp_manager import (
    DEFAULT_TEMP_DIR,
    cleanup_stale_temp_files,
    generate_secure_filename,
    get_temp_upload_dir,
    remove_temp_file,
)


app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = os.environ.get("RESUME_UPLOAD_FOLDER", DEFAULT_TEMP_DIR)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
# The optional job description is cut to this many characters
MAX_JOB_DESCRIPTION_LENGTH = 20000

# Ensure dedicated temporary upload directory exists with restricted permissions
get_temp_upload_dir(app.config["UPLOAD_FOLDER"])
cleanup_stale_temp_files(app.config["UPLOAD_FOLDER"])


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():

    filepath = None

    if "resume" not in request.files:
        return "Please upload a resume."

    file = request.files["resume"]

    if not file.filename:
        return "No file selected."

    original_filename = file.filename
    extension = os.path.splitext(original_filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        return "Only PDF and DOCX files are allowed."

    # Used in messages shown to the user: "PDF" or "DOCX"
    file_type = extension[1:].upper()

    filename = secure_filename(original_filename)

    if not filename:
        return "Invalid filename."

    unique_filename = generate_secure_filename(extension)

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        unique_filename
    )

    try:
        # Save the uploaded resume
        # Save the uploaded resume.
        file.save(filepath)

        # Extract text using the centralized format dispatcher.
        resume_text = extract_resume_text(filepath)

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
        category_details = score_data.get("category_details", {})
        overall_explanation = score_data.get("overall_explanation", "")
        scoring_formula = score_data.get("scoring_formula", "")
        improvement_areas = score_data.get("improvement_areas", [])

        # Section-wise improvement recommendations
        recommendations = generate_recommendations(resume_text)
        # Keyword analysis (optional job description from the form)
        job_description = request.form.get("job_description", "")
        job_description = job_description[:MAX_JOB_DESCRIPTION_LENGTH]

        keyword_analysis = analyze_keywords(resume_text, job_description)
        # ATS Compatibility Analysis
        ats_result = analyze_ats(resume_text, found_skills)

        # Job Description Matching
        job_description = request.form.get("job_description", "")
        job_match = match_resume_to_job(
            found_skills,
            job_description,
            resume_text=resume_text,
            resume_sections=resume_sections
        )

        # Results for the PDF report (sent back by the Download button)
        report = {
            "score": resume_score,
            "breakdown": score_breakdown,
            "skills": found_skills,
            "suggestions": suggestions,
            "job_match": job_match,
        }

        print("\n========== RESUME ANALYSIS ==========")
        print("DETECTED SKILLS:", found_skills)
        print("RESUME SCORE:", resume_score)
        print("SCORE BREAKDOWN:", score_breakdown)
        if job_match.get("has_job_description"):
            print("JOB MATCH SCORE:", job_match.get("match_percentage"))
            if job_match.get("semantic_match_percentage") is not None:
                print("SEMANTIC SIMILARITY:", job_match.get("semantic_match_percentage"))
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
            category_details=category_details,
            overall_explanation=overall_explanation,
            scoring_formula=scoring_formula,
            improvement_areas=improvement_areas,
            recommendations=recommendations,
            keyword_analysis=keyword_analysis,
            ats_result=ats_result,
            resume_sections=resume_sections,
            job_match=job_match,
            report_json=json.dumps(report)
        )

    except PackageNotFoundError:
        return "This file is not a valid DOCX document."

    except DocxReadError as error:
        # The message was written for the user, so it is safe to show
        return str(error)
        # A file named .docx that is not a real Word document
        return "This file is not a valid DOCX document."

    except Exception as error:
        print("Analysis Error:", error)
        if extension == ".docx":
            try:
                check_docx_file(filepath)  # explains fake or oversized DOCX files
            except DocxReadError as docx_error:
                return str(docx_error)
        return (
            f"Unable to analyze this {file_type}. "
            f"Please try another {file_type}."
        )

    finally:
        if filepath:
            remove_temp_file(filepath)
        try:
            file.close()
        except (OSError, ValueError):
            pass


@app.route("/download-report", methods=["POST"])
def download_report():

    try:
        pdf_bytes = build_report(json.loads(request.form["report"]))
    except Exception as error:
        print("Report Error:", error)
        return "Unable to create the report. Please analyze your resume again.", 400

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="resume-analysis-report.pdf"
    )


if __name__ == "__main__":

    url = "http://127.0.0.1:5000"

    threading.Timer(
        1.5,
        lambda: webbrowser.open_new(url)
    ).start()

    app.run(debug=True, use_reloader=False)