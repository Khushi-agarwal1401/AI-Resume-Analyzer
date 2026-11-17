import unittest

from analyzer.section_detector import (
    normalize_heading,
    extract_sections,
    get_detected_sections,
    STANDARD_SECTIONS,
)


class TestSectionDetection(unittest.TestCase):

    def test_resume_containing_all_major_sections(self):
        resume_text = """
John Doe
john@example.com | 123-456-7890

Contact Information
Phone: 123-456-7890
Email: john@example.com

Professional Summary
Experienced software engineer with 5 years of background in Python and web development.

Objective
To secure a challenging software engineering role.

Education
BS in Computer Science, State University, 2016-2020

Work Experience
Software Engineer at Tech Corp (2020-Present)
- Developed APIs using Flask

Professional Experience
Senior Developer at Solutions Inc
- Managed database migrations

Skills
Python, Flask, JavaScript, SQL

Technical Skills
Docker, Kubernetes, AWS

Projects
Resume Analyzer - Built an automated resume parser.

Certifications
AWS Certified Solutions Architect

Achievements
1st place in National Hackathon 2022

Languages
English, Spanish, Hindi

Interests
Open source contributing, Chess

Publications
"Machine Learning in Resume Parsing", IEEE 2021

Internships
Software Engineering Intern at StartUp (Summer 2019)
"""
        sections = extract_sections(resume_text)

        # Verify all sections are recognized and non-empty
        for key, name in STANDARD_SECTIONS:
            self.assertIn(key, sections)
            self.assertTrue(
                len(sections[key]) > 0,
                f"Expected section '{key}' ({name}) to be populated"
            )

        self.assertIn("Phone: 123-456-7890", sections["contact_info"])
        self.assertIn("Experienced software engineer", sections["summary"])
        self.assertIn("To secure a challenging", sections["objective"])
        self.assertIn("BS in Computer Science", sections["education"])
        # Work Experience and Professional Experience both map to 'experience'
        self.assertIn("Software Engineer at Tech Corp", sections["experience"])
        self.assertIn("Senior Developer at Solutions Inc", sections["experience"])
        # Skills and Technical Skills both map to 'skills'
        self.assertIn("Python, Flask", sections["skills"])
        self.assertIn("Docker, Kubernetes", sections["skills"])
        self.assertIn("Resume Analyzer", sections["projects"])
        self.assertIn("AWS Certified", sections["certifications"])
        self.assertIn("1st place", sections["achievements"])
        self.assertIn("English, Spanish", sections["languages"])
        self.assertIn("Chess", sections["interests"])
        self.assertIn("Machine Learning in Resume Parsing", sections["publications"])
        self.assertIn("Software Engineering Intern", sections["internships"])

    def test_resume_containing_only_education_and_skills(self):
        resume_text = """
Education
BS in Mathematics, 2022

Skills
Python, R, Statistics
"""
        sections = extract_sections(resume_text)
        self.assertEqual(sections["education"], "BS in Mathematics, 2022")
        self.assertEqual(sections["skills"], "Python, R, Statistics")

        # Other standard sections should be empty
        self.assertEqual(sections["experience"], "")
        self.assertEqual(sections["projects"], "")
        self.assertEqual(sections["certifications"], "")
        self.assertEqual(sections["summary"], "")

        detected = get_detected_sections(resume_text)
        self.assertEqual(set(detected), {"education", "skills"})

    def test_uppercase_section_headings(self):
        resume_text = """
EDUCATION
MIT, 2020

SKILLS
Python, SQL

EXPERIENCE
Acme Corp, Developer
"""
        sections = extract_sections(resume_text)
        self.assertEqual(sections["education"], "MIT, 2020")
        self.assertEqual(sections["skills"], "Python, SQL")
        self.assertEqual(sections["experience"], "Acme Corp, Developer")

    def test_lowercase_section_headings(self):
        resume_text = """
education
MIT, 2020

skills
Python, SQL

experience
Acme Corp, Developer
"""
        sections = extract_sections(resume_text)
        self.assertEqual(sections["education"], "MIT, 2020")
        self.assertEqual(sections["skills"], "Python, SQL")
        self.assertEqual(sections["experience"], "Acme Corp, Developer")

    def test_mixed_case_and_formatted_headings(self):
        resume_text = """
### Professional Summary:
Passionate developer.

**Technical Skills**
Python, Git

## WORK EXPERIENCE --
Software Engineer at Google
"""
        sections = extract_sections(resume_text)
        self.assertEqual(sections["summary"], "Passionate developer.")
        self.assertEqual(sections["skills"], "Python, Git")
        self.assertEqual(sections["experience"], "Software Engineer at Google")

    def test_heading_synonyms(self):
        # Work Experience vs Professional Experience vs Employment History
        text1 = "Work Experience\nBuilt systems."
        text2 = "Professional Experience\nBuilt systems."
        text3 = "Employment History\nBuilt systems."

        self.assertEqual(extract_sections(text1)["experience"], "Built systems.")
        self.assertEqual(extract_sections(text2)["experience"], "Built systems.")
        self.assertEqual(extract_sections(text3)["experience"], "Built systems.")

        # Academic Background vs Education
        self.assertEqual(
            extract_sections("Academic Background\nCS Degree")["education"],
            "CS Degree"
        )

        # Core Competencies vs Skills
        self.assertEqual(
            extract_sections("Core Competencies\nLeadership")["skills"],
            "Leadership"
        )

    def test_multiple_consecutive_sections(self):
        resume_text = """
Education
Skills
Experience
Software Engineer at XYZ
"""
        sections = extract_sections(resume_text)
        self.assertEqual(sections["education"], "")
        self.assertEqual(sections["skills"], "")
        self.assertEqual(sections["experience"], "Software Engineer at XYZ")

    def test_repeated_section_headings(self):
        resume_text = """
Work Experience
Company A Developer

Skills
Python

Professional Experience
Company B Senior Engineer
"""
        sections = extract_sections(resume_text)
        self.assertIn("Company A Developer", sections["experience"])
        self.assertIn("Company B Senior Engineer", sections["experience"])
        self.assertEqual(sections["skills"], "Python")

    def test_content_before_first_recognized_heading(self):
        resume_text = """John Doe
john@example.com | (555) 000-1111
San Francisco, CA

Education
Stanford University
"""
        sections = extract_sections(resume_text)
        self.assertIn("John Doe", sections["header"])
        self.assertIn("john@example.com", sections["header"])
        self.assertEqual(sections["education"], "Stanford University")

    def test_empty_resume_text(self):
        for empty_val in ["", "   \n\t  ", None]:
            sections = extract_sections(empty_val)
            self.assertIsInstance(sections, dict)
            for key, _ in STANDARD_SECTIONS:
                self.assertEqual(sections[key], "")
            self.assertEqual(sections["header"], "")
            self.assertEqual(get_detected_sections(empty_val), [])

    def test_resume_containing_no_recognizable_headings(self):
        resume_text = """
This is just a block of plain text.
There are no section headings here at all.
Just someone talking about their life and career.
"""
        sections = extract_sections(resume_text)
        self.assertEqual(get_detected_sections(resume_text), [])
        self.assertIn("This is just a block of plain text.", sections["header"])
        for key, _ in STANDARD_SECTIONS:
            self.assertEqual(sections[key], "")

    def test_missing_sections(self):
        resume_text = """
Skills
Python
"""
        sections = extract_sections(resume_text)
        self.assertEqual(sections["skills"], "Python")
        self.assertEqual(sections["education"], "")
        self.assertEqual(sections["experience"], "")
        self.assertEqual(sections["publications"], "")

    def test_normal_sentences_not_treated_as_headings(self):
        resume_text = """
Summary
Experienced developer with great skills in python and education in computer science.

Experience
I managed many projects during my work experience at various startups.
"""
        sections = extract_sections(resume_text)
        self.assertIn("great skills in python and education in computer science.", sections["summary"])
        self.assertIn("I managed many projects during my work experience", sections["experience"])
        # 'education' and 'projects' should not have been triggered as headings
        self.assertEqual(sections["education"], "")
        self.assertEqual(sections["projects"], "")

    def test_pdf_extraction_compatibility(self):
        from analyzer.pdf_reader import extract_pdf_sections, extract_pdf_text
        import unittest.mock as mock

        with mock.patch("analyzer.pdf_reader.PdfReader") as mock_reader_cls:
            mock_page = mock.MagicMock()
            mock_page.extract_text.return_value = "Skills\nPython, Docker\n\nEducation\nMIT"
            mock_reader = mock.MagicMock()
            mock_reader.pages = [mock_page]
            mock_reader_cls.return_value = mock_reader

            text = extract_pdf_text("dummy.pdf")
            self.assertIn("Skills", text)
            self.assertIn("Education", text)

            sections = extract_pdf_sections("dummy.pdf")
            self.assertEqual(sections["skills"], "Python, Docker")
            self.assertEqual(sections["education"], "MIT")


if __name__ == "__main__":
    unittest.main()
