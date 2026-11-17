import unittest

from analyzer.resume_scorer import calculate_resume_score
from analyzer.skills_extractor import extract_skills, get_suggestions


class ResumeComponentTests(unittest.TestCase):

    def test_skill_extraction_and_suggestions_are_preserved(self):
        skills = extract_skills("Python, SQL, and Git")

        self.assertEqual(skills, ["Python", "SQL", "Git"])
        self.assertIn("Machine Learning", get_suggestions(skills)[0])

    def test_resume_score_keeps_breakdown_shape(self):
        result = calculate_resume_score(
            "john@example.com +1 123 456 7890 "
            "Professional Summary Education Experience Projects "
            "Python SQL Flask"
        )

        self.assertIn("score", result)
        self.assertIn("breakdown", result)
        self.assertEqual(result["breakdown"]["Contact Information"], 10)
        self.assertEqual(result["breakdown"]["Technical Skills"], 6)


if __name__ == "__main__":
    unittest.main()
