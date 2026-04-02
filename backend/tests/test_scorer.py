"""
tests/test_scorer.py
Unit tests for the Scoring Engine.

NOTE: These tests mock the sentence-transformer model so they run
fast without requiring a GPU or downloading the model.
"""

import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
import numpy as np


# ── Mock the sentence-transformers model ──────────────────────
def make_mock_model(similarity=0.85):
    """Returns a mock SentenceTransformer that always gives fixed embeddings."""
    mock = MagicMock()
    # Produce two unit vectors whose cosine similarity equals `similarity`
    v1 = np.array([[1.0, 0.0]])
    v2 = np.array([[similarity, (1 - similarity**2)**0.5]])
    mock.encode.side_effect = [v1, v2]
    return mock


class TestScorer(unittest.TestCase):

    def _run_score(self, resume_text, jd_text, required, candidate, exp=2.0, similarity=0.85):
        mock_model = make_mock_model(similarity)
        with patch("services.scorer._get_model", return_value=mock_model):
            from services import scorer
            # Reset cached model
            scorer._model = mock_model
            result = scorer.score_resume(
                resume_text=resume_text,
                jd_text=jd_text,
                required_skills=required,
                candidate_skills=candidate,
                candidate_exp_years=exp,
            )
        return result

    # ── Score structure ───────────────────────────────────────
    def test_returns_all_keys(self):
        r = self._run_score("dev resume", "python dev job", ["python"], ["python"])
        for key in ["semantic_score","skill_score","experience_score",
                    "final_score","grade","matched_skills","missing_skills","explanation"]:
            self.assertIn(key, r)

    def test_scores_are_floats(self):
        r = self._run_score("dev resume", "job desc", ["python"], ["python"])
        self.assertIsInstance(r["final_score"], float)
        self.assertIsInstance(r["semantic_score"], float)
        self.assertIsInstance(r["skill_score"], float)

    def test_scores_in_range(self):
        r = self._run_score("dev resume", "job desc", ["python"], ["python"])
        for key in ["semantic_score","skill_score","experience_score","final_score"]:
            self.assertGreaterEqual(r[key], 0)
            self.assertLessEqual(r[key], 100)

    # ── Skill scoring ─────────────────────────────────────────
    def test_perfect_skill_match(self):
        skills = ["python", "flask", "mongodb"]
        r = self._run_score("resume", "jd", skills, skills)
        self.assertEqual(r["skill_score"], 100.0)
        self.assertEqual(r["matched_skills"], sorted(skills))
        self.assertEqual(r["missing_skills"], [])

    def test_no_skill_match(self):
        r = self._run_score("resume", "jd", ["python","flask"], ["java","react"])
        self.assertEqual(r["skill_score"], 0.0)
        self.assertEqual(r["matched_skills"], [])
        self.assertEqual(len(r["missing_skills"]), 2)

    def test_partial_skill_match(self):
        r = self._run_score("resume", "jd", ["python","flask","mongodb"], ["python","flask"])
        self.assertAlmostEqual(r["skill_score"], 66.67, places=1)
        self.assertIn("mongodb", r["missing_skills"])

    def test_empty_required_skills(self):
        r = self._run_score("resume", "jd", [], ["python"])
        self.assertEqual(r["skill_score"], 75.0)  # neutral score when no skills specified

    # ── Experience scoring ────────────────────────────────────
    def test_exceeds_required_exp(self):
        from services.scorer import _experience_score
        self.assertEqual(_experience_score(5.0, 3.0), 100.0)

    def test_meets_required_exp(self):
        from services.scorer import _experience_score
        self.assertEqual(_experience_score(3.0, 3.0), 100.0)

    def test_one_year_short(self):
        from services.scorer import _experience_score
        self.assertEqual(_experience_score(2.0, 3.0), 70.0)

    def test_two_years_short(self):
        from services.scorer import _experience_score
        self.assertEqual(_experience_score(1.0, 3.0), 40.0)

    def test_very_short(self):
        from services.scorer import _experience_score
        self.assertEqual(_experience_score(0.0, 5.0), 10.0)

    def test_no_exp_requirement(self):
        from services.scorer import _experience_score
        self.assertEqual(_experience_score(0.0, 0.0), 75.0)

    # ── Grade boundaries ──────────────────────────────────────
    def test_grade_a(self):
        from services.scorer import _grade
        self.assertEqual(_grade(85.0), "A")
        self.assertEqual(_grade(80.0), "A")

    def test_grade_b(self):
        from services.scorer import _grade
        self.assertEqual(_grade(70.0), "B")
        self.assertEqual(_grade(65.0), "B")

    def test_grade_c(self):
        from services.scorer import _grade
        self.assertEqual(_grade(55.0), "C")
        self.assertEqual(_grade(50.0), "C")

    def test_grade_d(self):
        from services.scorer import _grade
        self.assertEqual(_grade(40.0), "D")

    def test_grade_f(self):
        from services.scorer import _grade
        self.assertEqual(_grade(20.0), "F")
        self.assertEqual(_grade(0.0), "F")

    # ── Weighted formula ──────────────────────────────────────
    def test_weighted_formula(self):
        """Final score must equal 0.40*sem + 0.35*skill + 0.25*exp."""
        r = self._run_score(
            "python developer", "python job",
            required=["python"], candidate=["python"],
            exp=5.0, similarity=0.9,
        )
        expected = round(0.40 * r["semantic_score"] + 0.35 * r["skill_score"] + 0.25 * r["experience_score"], 2)
        self.assertAlmostEqual(r["final_score"], expected, places=1)

    # ── Explanation ───────────────────────────────────────────
    def test_explanation_contains_scores(self):
        r = self._run_score("resume", "jd", ["python"], ["python"])
        self.assertIn("Score", r["explanation"])
        self.assertIn("Grade", r["explanation"])

    def test_explanation_lists_missing(self):
        r = self._run_score("resume", "jd", ["python","docker"], ["python"])
        self.assertIn("docker", r["explanation"])


class TestScorerIntegration(unittest.TestCase):
    """Higher-level tests verifying strong resume scores higher than weak resume."""

    def test_strong_beats_weak(self):
        strong_resume = "Python Flask MongoDB Docker AWS machine learning 5 years experience"
        weak_resume   = "Microsoft Word Excel PowerPoint 1 year experience"
        jd            = "Python developer with Flask MongoDB Docker AWS 3 years experience"
        required      = ["python", "flask", "mongodb", "docker", "aws"]

        from services.skill_extractor import extract_skills
        strong_skills = extract_skills(strong_resume)
        weak_skills   = extract_skills(weak_resume)

        mock_strong = make_mock_model(similarity=0.92)
        mock_weak   = make_mock_model(similarity=0.30)

        import services.scorer as scorer

        scorer._model = mock_strong
        r_strong = scorer.score_resume(strong_resume, jd, required, strong_skills, 5.0)

        scorer._model = mock_weak
        r_weak = scorer.score_resume(weak_resume, jd, required, weak_skills, 1.0)

        self.assertGreater(r_strong["final_score"], r_weak["final_score"])
        self.assertGreater(r_strong["skill_score"], r_weak["skill_score"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
