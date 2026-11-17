import io
import os
import tempfile
import unittest
from unittest.mock import patch

from app import app


class FlaskWorkflowTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.original_upload_folder = app.config["UPLOAD_FOLDER"]
        cls.upload_directory = tempfile.TemporaryDirectory()
        app.config["UPLOAD_FOLDER"] = cls.upload_directory.name

    @classmethod
    def tearDownClass(cls):
        app.config["UPLOAD_FOLDER"] = cls.original_upload_folder
        cls.upload_directory.cleanup()

    def setUp(self):
        self.client = app.test_client()

    def assert_upload_directory_empty(self):
        self.assertEqual(os.listdir(app.config["UPLOAD_FOLDER"]), [])

    def test_homepage_is_available(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AI Resume Analyzer", response.data)

    def test_missing_resume_file_is_rejected(self):
        response = self.client.post("/analyze", data={})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please upload a resume.", response.data)

    def test_empty_resume_filename_is_rejected(self):
        response = self.client.post(
            "/analyze",
            data={"resume": (io.BytesIO(b""), "")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No file selected.", response.data)

    def test_unsupported_extension_is_rejected(self):
        response = self.client.post(
            "/analyze",
            data={"resume": (io.BytesIO(b"plain text"), "resume.txt")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Only PDF and DOCX files are allowed.", response.data)
        self.assert_upload_directory_empty()

    @patch("app.extract_resume_text", return_value="Skills\nPython")
    def test_pdf_upload_uses_dispatcher_and_cleans_up(self, extract_resume):
        response = self.client.post(
            "/analyze",
            data={"resume": (io.BytesIO(b"%PDF-1.7"), "resume.PDF")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Your Resume Analysis", response.data)
        extract_resume.assert_called_once()
        self.assert_upload_directory_empty()

    @patch("app.extract_resume_text", return_value="Skills\nPython")
    def test_docx_upload_uses_dispatcher_and_cleans_up(self, extract_resume):
        response = self.client.post(
            "/analyze",
            data={"resume": (io.BytesIO(b"docx bytes"), "resume.DOCX")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Your Resume Analysis", response.data)
        extract_resume.assert_called_once()
        self.assert_upload_directory_empty()

    def test_invalid_pdf_returns_safe_error_and_cleans_up(self):
        response = self.client.post(
            "/analyze",
            data={"resume": (io.BytesIO(b"not a PDF"), "resume.pdf")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b"Unable to analyze this PDF. Please try another PDF.",
            response.data,
        )
        self.assert_upload_directory_empty()

    def test_oversized_upload_is_rejected(self):
        original_limit = app.config["MAX_CONTENT_LENGTH"]
        app.config["MAX_CONTENT_LENGTH"] = 10
        try:
            response = self.client.post(
                "/analyze",
                data={"resume": (io.BytesIO(b"x" * 11), "resume.pdf")},
                content_type="multipart/form-data",
            )
        finally:
            app.config["MAX_CONTENT_LENGTH"] = original_limit

        self.assertEqual(response.status_code, 413)
        self.assert_upload_directory_empty()


if __name__ == "__main__":
    unittest.main()
