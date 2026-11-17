import io
import json
import os
import uuid
import threading
import webbrowser

from flask import Flask, jsonify, render_template, request, send_file
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
from analyzer.validator import (
    ALLOWED_EXTENSIONS,
    MAX_JOB_DESCRIPTION_LENGTH,
    format_error_response,
    validate_report_download,
    validate_resume_upload,
    wants_json_response,
)


app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
# The optional job description is cut to this many characters
MAX_JOB_DESCRIPTION_LENGTH = 20000

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
@app.route("/api/analyze", methods=["POST"])
def analyze():

    filepath = None

    is_valid, file, extension, error_resp = validate_resume_upload(request)
    if not is_valid:
        return error_resp

    file_type = extension[1:].upper()
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        unique_filename
    )

    try:
        # Save the uploaded resume.
        file.save(filepath)

        # Extract text using the centralized format dispatcher.
        resume_text = extract_resume_text(filepath)

        if not resume_text.strip():
            msg = f"No readable text found in this {file_type}."
            return format_error_response(
                message=msg,
                status_code=422 if wants_json_response(request) else 200,
                error_code="EMPTY_DOCUMENT_TEXT",
                request=request,
                legacy_200_for_html=True,
            )

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

        # Section-wise improvement recommendations
        recommendations = generate_recommendations(resume_text)
        # Keyword analysis (optional job description from the form or JSON payload)
        if request.is_json and request.json:
            job_description = request.json.get("job_description", "")
        else:
            job_description = request.form.get("job_description", "")
        job_description = str(job_description or "")[:MAX_JOB_DESCRIPTION_LENGTH]

        keyword_analysis = analyze_keywords(resume_text, job_description)
        # ATS Compatibility Analysis
        ats_result = analyze_ats(resume_text, found_skills)

        # Job Description Matching
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

        # API JSON response for API clients
        if wants_json_response(request):
            return jsonify({
                "status": "success",
                "score": resume_score,
                "score_breakdown": score_breakdown,
                "skills": found_skills,
                "skill_count": len(found_skills),
                "suggestions": suggestions,
                "recommendations": recommendations,
                "ats_result": ats_result,
                "job_match": job_match,
                "keyword_analysis": keyword_analysis,
                "resume_sections": resume_sections,
                "report": report,
            }), 200

        # Display Results
        return render_template(
            "result.html",
            found_skills=found_skills,
            suggestions=suggestions,
            skill_count=len(found_skills),
            resume_text=resume_text,
            resume_score=resume_score,
            score_breakdown=score_breakdown,
            recommendations=recommendations,
            keyword_analysis=keyword_analysis,
            ats_result=ats_result,
            resume_sections=resume_sections,
            job_match=job_match,
            report_json=json.dumps(report)
        )

    except DocxReadError as error:
        # The message was written for the user, so it is safe to show
        return format_error_response(
            message=str(error),
            status_code=400,
            error_code="INVALID_DOCX_FILE",
            request=request,
            legacy_200_for_html=True,
        )

    except Exception as error:
        print("Analysis Error:", error)
        if extension == ".docx":
            try:
                check_docx_file(filepath)  # explains fake or oversized DOCX files
            except DocxReadError as docx_error:
                return format_error_response(
                    message=str(docx_error),
                    status_code=400,
                    error_code="INVALID_DOCX_FILE",
                    request=request,
                    legacy_200_for_html=True,
                )
        safe_msg = f"Unable to analyze this {file_type}. Please try another {file_type}."
        return format_error_response(
            message=safe_msg,
            status_code=422 if wants_json_response(request) else 200,
            error_code="ANALYSIS_FAILED",
            request=request,
            legacy_200_for_html=True,
        )

    finally:
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as cleanup_error:
                print("Cleanup Error:", cleanup_error)
        try:
            file.close()
        except (OSError, ValueError) as cleanup_error:
            print("Upload Stream Cleanup Error:", cleanup_error)


@app.route("/download-report", methods=["POST"])
@app.route("/api/download-report", methods=["POST"])
def download_report():

    is_valid, report_dict, error_resp = validate_report_download(request)
    if not is_valid:
        return error_resp

    try:
        pdf_bytes = build_report(report_dict)
    except Exception as error:
        print("Report Error:", error)
        return format_error_response(
            message="Unable to create the report. Please analyze your resume again.",
            status_code=400,
            error_code="REPORT_GENERATION_FAILED",
            request=request,
            legacy_200_for_html=False,
        )

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="resume-analysis-report.pdf"
    )


@app.errorhandler(400)
def handle_bad_request(error):
    return format_error_response(
        message="Bad Request: The server could not understand the request.",
        status_code=400,
        error_code="BAD_REQUEST",
        request=request,
        legacy_200_for_html=False,
    )


@app.errorhandler(404)
def handle_not_found(error):
    return format_error_response(
        message="Resource not found.",
        status_code=404,
        error_code="NOT_FOUND",
        request=request,
        legacy_200_for_html=False,
    )


@app.errorhandler(405)
def handle_method_not_allowed(error):
    return format_error_response(
        message="Method not allowed.",
        status_code=405,
        error_code="METHOD_NOT_ALLOWED",
        request=request,
        legacy_200_for_html=False,
    )


@app.errorhandler(413)
def handle_payload_too_large(error):
    return format_error_response(
        message="File size exceeds the 10 MB limit. Please upload a smaller file.",
        status_code=413,
        error_code="FILE_TOO_LARGE",
        request=request,
        legacy_200_for_html=False,
    )


@app.errorhandler(500)
def handle_server_error(error):
    return format_error_response(
        message="An internal server error occurred. Please try again later.",
        status_code=500,
        error_code="INTERNAL_SERVER_ERROR",
        request=request,
        legacy_200_for_html=False,
    )


if __name__ == "__main__":

    url = "http://127.0.0.1:5000"

    threading.Timer(
        1.5,
        lambda: webbrowser.open_new(url)
    ).start()

    app.run(debug=True, use_reloader=False)