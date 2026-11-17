"""Tests for analyzer/keyword_analyzer.py

Run them from the project folder with:
    python -m unittest discover -s tests -v
"""

import unittest

from analyzer.keyword_analyzer import _stem, analyze_keywords


def find(result, name):
    """Return the keyword entry called `name`, or None."""
    for item in result["keywords"]:
        if item["keyword"] == name:
            return item
    return None


class CountingTests(unittest.TestCase):

    def test_skill_count_ignores_case_and_punctuation(self):
        result = analyze_keywords("Python and python, PYTHON. I use Python daily.")
        self.assertEqual(find(result, "Python")["count"], 4)

    def test_java_is_not_found_inside_javascript(self):
        result = analyze_keywords("JavaScript and Java")
        self.assertEqual(find(result, "Java")["count"], 1)
        self.assertEqual(find(result, "JavaScript")["count"], 1)

    def test_c_is_not_found_inside_cpp(self):
        result = analyze_keywords("I write C++ code")
        self.assertEqual(find(result, "C++")["count"], 1)
        self.assertIsNone(find(result, "C"))

    def test_short_skill_inside_longer_skill_is_not_counted_twice(self):
        result = analyze_keywords("Tailwind CSS and CSS")
        self.assertEqual(find(result, "Tailwind CSS")["count"], 1)
        self.assertEqual(find(result, "CSS")["count"], 1)

    def test_multi_word_skill(self):
        result = analyze_keywords("Machine Learning and machine learning")
        self.assertEqual(find(result, "Machine Learning")["count"], 2)

    def test_emails_and_links_are_ignored(self):
        text = (
            "Contact john.smith@example.com or visit "
            "https://example.com/john github.com/john today"
        )
        result = analyze_keywords(text)
        self.assertEqual(result["total_words"], 4)  # contact, or, visit, today

    def test_stop_words_are_not_keywords(self):
        result = analyze_keywords("the the the and and of of")
        self.assertEqual(result["keywords"], [])

    def test_repeated_normal_word_is_a_keyword(self):
        result = analyze_keywords("optimization optimization optimization performance")
        item = find(result, "optimization")
        self.assertEqual(item["count"], 3)
        self.assertFalse(item["is_skill"])
        self.assertIsNone(find(result, "performance"))  # only once

    def test_empty_text_does_not_crash(self):
        result = analyze_keywords("")
        self.assertEqual(result["total_words"], 0)
        self.assertEqual(result["keywords"], [])
        self.assertIsNone(result["job_match"])
        self.assertTrue(result["tips"])


class DensityAndStatusTests(unittest.TestCase):

    def test_density_is_count_divided_by_total_words(self):
        result = analyze_keywords("python " * 5 + "alpha " * 95)  # 100 words
        item = find(result, "Python")
        self.assertEqual(result["total_words"], 100)
        self.assertEqual(item["density"], 5.0)

    def test_once(self):
        result = analyze_keywords("python alpha beta")
        self.assertEqual(find(result, "Python")["status"], "once")

    def test_repeated(self):
        result = analyze_keywords("python " * 5 + "alpha " * 95)
        self.assertEqual(find(result, "Python")["status"], "repeated")

    def test_overused_needs_high_count_and_high_density(self):
        short = analyze_keywords("python " * 6 + "alpha " * 94)     # 6.0 %
        long = analyze_keywords("python " * 6 + "alpha " * 994)     # 0.6 %
        self.assertEqual(find(short, "Python")["status"], "overused")
        self.assertEqual(find(long, "Python")["status"], "repeated")

    def test_overused_keyword_creates_a_tip(self):
        result = analyze_keywords("python " * 6 + "alpha " * 94)
        self.assertEqual(find(result, "Python")["status"], "overused")
        self.assertGreaterEqual(result["overused_total"], 1)
        self.assertTrue(any('"Python"' in tip for tip in result["tips"]))

    def test_bar_width_is_relative_to_the_biggest_keyword(self):
        result = analyze_keywords("python python python python sql sql")
        self.assertEqual(find(result, "Python")["bar_width"], 100)
        self.assertEqual(find(result, "SQL")["bar_width"], 50)


class JobMatchTests(unittest.TestCase):

    def test_no_job_description_gives_no_match(self):
        self.assertIsNone(analyze_keywords("Python")["job_match"])
        self.assertIsNone(analyze_keywords("Python", "   ")["job_match"])

    def test_matched_and_missing_keywords(self):
        resume = "Python Flask SQL"
        job = "We need Python, Flask and Docker. Docker experience is a plus."
        match = analyze_keywords(resume, job)["job_match"]

        matched = [item["keyword"] for item in match["matched"]]
        missing = [item["keyword"] for item in match["missing"]]

        self.assertEqual(sorted(matched), ["Flask", "Python"])
        self.assertEqual(missing, ["Docker"])
        self.assertEqual(match["match_percent"], 67)  # 2 of 3

    def test_similar_word_forms_match(self):
        match = analyze_keywords(
            "I built a dashboard", "dashboards dashboards"
        )["job_match"]
        self.assertEqual(len(match["matched"]), 1)
        self.assertEqual(match["missing"], [])

    def test_job_description_without_keywords(self):
        match = analyze_keywords("Python", "the and of")["job_match"]
        self.assertEqual(match["keyword_count"], 0)
        self.assertIsNone(match["match_percent"])


class StemTests(unittest.TestCase):

    def test_plural_and_verb_forms_group_together(self):
        self.assertEqual(_stem("projects"), "project")
        self.assertEqual(_stem("developed"), _stem("developing"))
        self.assertEqual(_stem("databases"), _stem("database"))
        self.assertEqual(_stem("managed"), _stem("manage"))
        self.assertEqual(_stem("classes"), _stem("class"))

    def test_words_that_only_look_like_plurals_stay_the_same(self):
        for word in ("analysis", "class", "process", "status", "sql"):
            self.assertEqual(_stem(word), word)


if __name__ == "__main__":
    unittest.main()