"""
tests/test_resume_parser.py
Unit tests for Resume Parser service.
"""

import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.resume_parser import (
    _extract_email, _extract_phone, _extract_name,
    _extract_experience_years, _extract_education,
)


class TestResumeParser(unittest.TestCase):

    # ── Email extraction ──────────────────────────────────────
    def test_extract_email_standard(self):
        text = "Contact me at john.doe@gmail.com for more info."
        self.assertEqual(_extract_email(text), "john.doe@gmail.com")

    def test_extract_email_work(self):
        text = "Email: priya.sharma@infosys.co.in"
        self.assertEqual(_extract_email(text), "priya.sharma@infosys.co.in")

    def test_extract_email_none(self):
        text = "No email address here."
        self.assertEqual(_extract_email(text), "")

    def test_extract_email_multiple_returns_first(self):
        text = "Primary: a@b.com  Secondary: c@d.com"
        result = _extract_email(text)
        self.assertEqual(result, "a@b.com")

    # ── Phone extraction ──────────────────────────────────────
    def test_extract_phone_10digit(self):
        text = "Phone: 9876543210"
        result = _extract_phone(text)
        self.assertIn("9876543210", result)

    def test_extract_phone_with_country_code(self):
        text = "Call: +91 98765 43210"
        result = _extract_phone(text)
        self.assertTrue(len(result) > 0)

    def test_extract_phone_none(self):
        text = "No phone number available."
        self.assertEqual(_extract_phone(text), "")

    # ── Name extraction ───────────────────────────────────────
    def test_extract_name_simple(self):
        text = "Rahul Sharma\nrahul@email.com\nSoftware Engineer"
        result = _extract_name(text)
        self.assertEqual(result, "Rahul Sharma")

    def test_extract_name_three_parts(self):
        text = "Priya Kumari Singh\npriya@email.com"
        result = _extract_name(text)
        self.assertEqual(result, "Priya Kumari Singh")

    def test_extract_name_unknown(self):
        text = "1234\nno name here"
        result = _extract_name(text)
        self.assertEqual(result, "Unknown")

    # ── Experience years ──────────────────────────────────────
    def test_extract_exp_explicit(self):
        text = "I have 5 years of experience in software development."
        result = _extract_experience_years(text)
        self.assertEqual(result, 5.0)

    def test_extract_exp_abbreviation(self):
        text = "3 yrs exp in Python."
        result = _extract_experience_years(text)
        self.assertEqual(result, 3.0)

    def test_extract_exp_takes_max(self):
        text = "2 years frontend, 4 years overall experience."
        result = _extract_experience_years(text)
        self.assertEqual(result, 4.0)

    def test_extract_exp_zero(self):
        text = "Fresh graduate looking for first job."
        result = _extract_experience_years(text)
        self.assertEqual(result, 0.0)

    # ── Education ─────────────────────────────────────────────
    def test_extract_education_btech(self):
        text = "B.Tech in Computer Science from VIT University."
        result = _extract_education(text)
        self.assertTrue(any("B.TECH" in e or "ENGINEERING" in e or "COMPUTER SCIENCE" in e for e in result))

    def test_extract_education_mba(self):
        text = "MBA from IIM Ahmedabad."
        result = _extract_education(text)
        self.assertIn("MBA", result)

    def test_extract_education_empty(self):
        result = _extract_education("")
        self.assertEqual(result, [])

    def test_extract_education_no_duplicates(self):
        text = "Bachelor of Engineering. B.E. graduate."
        result = _extract_education(text)
        self.assertEqual(len(result), len(set(result)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
