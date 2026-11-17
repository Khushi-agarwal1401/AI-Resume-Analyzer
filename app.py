import os
import uuid
import threading
import webbrowser

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from analyzer.pdf_reader import extract_pdf_text
from analyzer.skills_extractor import extract_skills, get_suggestions
from analyzer.resume_scorer import calculate_resume_score
from analyzer.suggestions import generate_recommendations


app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

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

    if not file.filename.lower().endswith(".pdf"):
        return "Only PDF files are allowed."

    filename = secure_filename(file.filename)

    if not filename:
        return "Invalid filename."

    unique_filename = f"{uuid.uuid4().hex}_{filename}"

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        unique_filename
    )

    try:
        # Save PDF
        file.save(filepath)

        # Extract PDF text
        resume_text = extract_pdf_text(filepath)

        if not resume_text.strip():
            return "No readable text found in this PDF."

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

        print("\n========== RESUME ANALYSIS ==========")
        print("DETECTED SKILLS:", found_skills)
        print("RESUME SCORE:", resume_score)
        print("SCORE BREAKDOWN:", score_breakdown)
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
            recommendations=recommendations
        )

    except Exception as error:
        print("Analysis Error:", error)
        return "Unable to analyze this PDF. Please try another PDF."

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