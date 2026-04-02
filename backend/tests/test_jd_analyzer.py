"""
tests/test_jd_analyzer.py
Unit tests for JD Analyzer service.
"""

import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.jd_analyzer import analyze_job_description


class TestJDAnalyzer(unittest.TestCase):

    def test_extracts_python(self):
        jd = "We need a Python developer with 3 years experience."
        skills, _ = analyze_job_description(jd)
        self.assertIn("python", skills)

    def test_extracts_multiple_skills(self):
        jd = "Required: Python, React, MongoDB, Docker, AWS experience."
        skills, _ = analyze_job_description(jd)
        self.assertIn("python", skills)
        self.assertIn("react", skills)
        self.assertIn("mongodb", skills)
        self.assertIn("docker", skills)
        self.assertIn("aws", skills)

    def test_returns_keywords(self):
        jd = "Senior machine learning engineer needed. Experience in deep learning required."
        _, keywords = analyze_job_description(jd)
        self.assertIsInstance(keywords, list)

    def test_empty_jd(self):
        skills, keywords = analyze_job_description("")
        self.assertEqual(skills, [])

    def test_case_insensitive(self):
        jd = "Looking for PYTHON and TENSORFLOW expertise."
        skills, _ = analyze_job_description(jd)
        self.assertIn("python", skills)
        self.assertIn("tensorflow", skills)

    def test_no_duplicate_skills(self):
        jd = "Python developer with Python experience and python scripting."
        skills, _ = analyze_job_description(jd)
        self.assertEqual(skills.count("python"), 1)

    def test_ml_skills(self):
        jd = "Must know machine learning, deep learning, NLP, and computer vision."
        skills, _ = analyze_job_description(jd)
        self.assertIn("machine learning", skills)
        self.assertIn("deep learning", skills)
        self.assertIn("nlp", skills)

    def test_cloud_skills(self):
        jd = "AWS or Azure cloud experience required. GCP is a plus."
        skills, _ = analyze_job_description(jd)
        cloud = [s for s in skills if s in ("aws", "azure", "gcp")]
        self.assertGreaterEqual(len(cloud), 2)


class TestSkillExtractor(unittest.TestCase):

    def setUp(self):
        from services.skill_extractor import extract_skills
        self.extract = extract_skills

    def test_finds_python(self):
        text = "Experienced Python developer with Flask background."
        skills = self.extract(text)
        self.assertIn("python", skills)
        self.assertIn("flask", skills)

    def test_no_duplicates(self):
        text = "Python Python Python developer."
        skills = self.extract(text)
        self.assertEqual(skills.count("python"), 1)

    def test_empty_text(self):
        skills = self.extract("")
        self.assertEqual(skills, [])

    def test_returns_list(self):
        skills = self.extract("Java developer.")
        self.assertIsInstance(skills, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
