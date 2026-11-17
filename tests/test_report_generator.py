import io
import json
import unittest

from pypdf import PdfReader

from analyzer.report_generator import build_report
from app import app

DATA = {
    "score": 82,
    "breakdown": {"Contact Information": 10, "Technical Skills": 14},
    "skills": ["Python", "Flask"],
    "suggestions": ["Add Git experience if applicable."],
    "job_match": {
        "has_job_description": True,
        "match_percentage": 40,
        "total_matching": 2,
        "total_required": 5,
        "matching_skills": ["Python", "Flask"],
        "missing_skills": ["Docker"],
    },
}


def pdf_text(pdf_bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() for page in reader.pages)


class ReportTests(unittest.TestCase):

    def test_report_contains_the_results(self):
        pdf = build_report(DATA)
        text = pdf_text(pdf)

        self.assertTrue(pdf.startswith(b"%PDF"))
        for expected in ("82 / 100", "Contact Information", "14 / 20", "Python, Flask",
                         "Add Git experience", "40% match", "Docker"):
            self.assertIn(expected, text)

    def test_job_section_is_skipped_without_a_job_description(self):
        without = dict(DATA, job_match={"has_job_description": False})
        missing_key = {k: v for k, v in DATA.items() if k != "job_match"}

        self.assertNotIn("Job Description Match", pdf_text(build_report(without)))
        self.assertNotIn("Job Description Match", pdf_text(build_report(missing_key)))

    def test_empty_data_still_gives_a_valid_report(self):
        text = pdf_text(build_report({}))
        self.assertIn("Resume Analysis Report", text)
        self.assertIn("No matching skills detected.", text)

    def test_non_latin_text_does_not_crash(self):
        data = dict(DATA, skills=["Python", "हिन्दी", "😀"])
        self.assertIn("Python", pdf_text(build_report(data)))


class DownloadRouteTests(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_download_returns_a_pdf_file(self):
        response = self.client.post("/download-report", data={"report": json.dumps(DATA)})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn("attachment", response.headers["Content-Disposition"])
        self.assertTrue(response.data.startswith(b"%PDF"))

    def test_bad_data_gives_a_clear_error(self):
        for bad in ("not json", "[1, 2]"):
            response = self.client.post("/download-report", data={"report": bad})
            self.assertEqual(response.status_code, 400)

        self.assertEqual(self.client.post("/download-report").status_code, 400)


if __name__ == "__main__":
    unittest.main()